# pf_search library: state identity (savestate field classification + canonical hash), emulator wrapper with the
# taint tracker / read watch (librm2pf.so = the FCEUX master core objects + observing hooks, built by
# tools/proof/Makefile), root states rebuilt by a continuous replay from power-on.
#
# STATE IDENTITY (docs/proof-standards.md, A-STATE; the code argument behind every DROP is in the comments below):
#   key(state) = concatenation of every savestate field EXCEPT the DROP list, in file order, with optional
#   canonicalisation masks (RAM bits proven dead per transition by the taint tracker) applied.
#   hash = sha256(key).
# No path is built in: the ROM, the library and the movie are arguments of the caller (pfrun.py).
import sys, os, struct, hashlib, ctypes, json
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'harness'))
import rm2  # noqa: E402
U_, D_, T_, A_, B_, L_, R_, S_ = rm2.UP, rm2.DOWN, rm2.START, rm2.A, rm2.B, rm2.LEFT, rm2.RIGHT, rm2.SELECT

CHUNKNAMES = {1: 'CPU', 2: 'CPUC', 3: 'PPU', 31: 'NEWPPU', 4: 'CTRL', 5: 'SND', 6: 'MOVIE', 7: 'MOVIEDATA', 8: 'BACKBUF',
              16: 'SFMDATA'}
# Fields dropped from the identity hash. Each has a code argument in NOTES.md ("State identity").
DROP_FIELDS = {('CPUC', 'TSBS'),            # timestampbase: absolute cycle count; only read as (TSBS+ts) - lreset in MMC1
               ('CTRL', 'JOYS'),            # joy[0..3]: overwritten by FCEU_UpdateInput before any CPU instruction
               ('CTRL', 'LAGF'),            # lagFlag: set to 1 at frame start before emulation, output only
               ('CTRL', 'LAGC'),            # lagCounter: output counter, never read by emulation
               ('CTRL', 'FRAM'),            # currFrameCounter: movie counter, never read by emulation (no movie)
               ('SFMDATA', 'LRST')}         # MMC1 lreset: set to 0 by MMC1_Restore on every load
DROP_CHUNKS = {'BACKBUF',                   # XBackBuf: output image copy, never read by emulation
               'NEWPPU'}                    # new-PPU fields: newppu == 0, the old PPU never reads them


def desc4(b):
    return b.rstrip(b'\x00').decode('latin1')


def parse_layout(st):
    """-> list of (chunkname, fieldname, off, len) in file order (BACKBUF as one raw field)."""
    assert st[:4] == b'FCSX', 'not an FCSX state'
    total, ver, comp = struct.unpack('<III', st[4:16])
    assert comp == 0xFFFFFFFF, 'compressed state'
    assert total + 16 == len(st), (total, len(st))
    out = []
    p = 16
    while p < len(st):
        t = st[p]; size = struct.unpack('<I', st[p + 1:p + 5])[0]
        cn = CHUNKNAMES.get(t, 'CH%d' % t)
        q = p + 5; end = q + size
        if t == 8:
            out.append((cn, 'XBUF', q, size))
        else:
            while q < end:
                d = desc4(st[q:q + 4]); fs = struct.unpack('<I', st[q + 4:q + 8])[0]
                out.append((cn, d, q + 8, fs))
                q += 8 + fs
            assert q == end
        p = end
    return out


class Identity:
    """Canonical identity of savestates with one fixed layout."""

    def __init__(self, st, canon=None):
        self.layout = parse_layout(st)
        self.len = len(st)
        self.fields = {(c, f): (o, n) for c, f, o, n in self.layout}
        self.keep = [(c, f, o, n) for c, f, o, n in self.layout
                     if c not in DROP_CHUNKS and (c, f) not in DROP_FIELDS]
        self.drop = [(c, f, o, n) for c, f, o, n in self.layout
                     if not (c not in DROP_CHUNKS and (c, f) not in DROP_FIELDS)]
        self.ram_off = self.fields[('CPU', 'RAM')][0]
        # position of RAM inside the key
        pos = 0
        self.ram_kpos = None
        for c, f, o, n in self.keep:
            if (c, f) == ('CPU', 'RAM'):
                self.ram_kpos = pos
            pos += n
        self.keylen = pos
        self.slices = [(o, o + n) for c, f, o, n in self.keep]
        self.set_canon(canon or {})

    def set_canon(self, canon):
        """canon: {ram_addr: dead_bit_mask}. The key keeps only the bits NOT in the dead mask."""
        self.canon = dict(canon)
        self.canon_list = sorted((self.ram_kpos + a, (~m) & 0xFF) for a, m in self.canon.items() if m)

    def check_layout(self, st):
        return len(st) == self.len and parse_layout(st) == self.layout

    def key(self, st):
        k = b''.join(st[a:b] for a, b in self.slices)
        if self.canon_list:
            k = bytearray(k)
            for p, keepmask in self.canon_list:
                k[p] &= keepmask
            k = bytes(k)
        return k

    def h(self, st):
        return hashlib.sha256(self.key(st)).digest()

    def ram(self, st, a, n=1):
        o = self.ram_off + a
        return st[o] if n == 1 else st[o:o + n]

    def field(self, st, c, f):
        o, n = self.fields[(c, f)]
        return st[o:o + n]

    def describe(self):
        kept = sum(n for c, f, o, n in self.keep)
        return 'state %d bytes, key %d bytes (%d fields kept, %d dropped: %s)' % (
            self.len, kept, len(self.keep), len(self.drop), ', '.join('%s.%s' % (c, f) for c, f, o, n in self.drop))


# ---------------------------------------------------------------------------------------------------------------
_E = None


class PfEmu(rm2.Emu):
    def __init__(self, lib, rom):
        super().__init__(lib, rom)
        L = self.lib
        self.lib_path, self.rom_path = lib, rom
        self.frames_since_poweron = 0
        self.pf = hasattr(L, 'pf_taint_begin')
        if self.pf:
            L.pf_taint_begin.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int]
            L.pf_taint_end.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_char_p]
            L.pf_rw_get.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        self._tout = (ctypes.c_int * 16)()
        self._tram = ctypes.create_string_buffer(0x800)
        self._rwb = (ctypes.c_int * 4)()

    # ---- taint tracker ----
    def taint_begin(self, init_ram, kin, jrb, lstrobe):
        assert len(init_ram) == 0x800
        self.lib.pf_taint_begin(bytes(init_ram), kin, jrb, lstrobe)

    def taint_end(self):
        self.lib.pf_taint_end(self._tout, self._tram)
        o = list(self._tout)
        return dict(abort=o[0], abort_pc=o[1], abort_op=o[2], tA=o[3], tX=o[4], tY=o[5], flags=o[6],
                    flags_pre=o[7], last_touch=o[8], ninstr=o[9], ntainted=o[10], nint=o[11], sok=o[12],
                    have_prev=o[13]), self._tram.raw

    # ---- read watch ----
    def rw_start(self, addrs):
        self.lib.pf_rw_clearmask()
        for a in addrs:
            self.lib.pf_rw_set(a, 1)
        self.lib.pf_rw_reset()
        self.lib.pf_rw(1)

    def rw_stop(self):
        self.lib.pf_rw(0)
        out = []
        for i in range(self.lib.pf_rw_count()):
            self.lib.pf_rw_get(i, self._rwb)
            out.append(tuple(self._rwb[k] for k in range(4)))
        return out


def emu(lib, rom):
    """The process's one emulator (FCEUX keeps global state; a second power-on in one process is not clean)."""
    global _E
    if _E is None:
        _E = PfEmu(lib, rom)
    return _E


ABORT_NAMES = {0: 'none', 1: 'illegal opcode', 2: 'tainted index', 3: 'tainted pointer', 4: 'tainted branch',
               5: 'tainted I/O write', 6: 'tainted DMA page', 7: 'tainted P/I flag', 8: 'tainted return address',
               9: 'BRK', 10: 'tainted TXS', 11: 'stack pointer mismatch', 12: 'unpredicted $4016 read',
               13: 'I/O read with non-absolute mode', 14: 'code outside PRG'}


def taint_verdict(res, tram, allowed):
    """allowed: {addr: mask}. True iff the frame provably ends in a state that differs, for every value of the
    tainted bits, only inside the allowed RAM bits."""
    if res['abort']:
        return False, 'abort: %s at pc %04X (op %X)' % (ABORT_NAMES.get(res['abort'], '?'), res['abort_pc'] & 0xFFFF,
                                                          res['abort_op'])
    if res['sok'] == 0:
        return False, 'stack pointer mismatch at end'
    if res['tA'] or res['tX'] or res['tY']:
        return False, 'tainted registers at end A%02X X%02X Y%02X' % (res['tA'], res['tX'], res['tY'])
    if res['flags'] or res['flags_pre']:
        return False, 'tainted flags at end %02X/%02X' % (res['flags'], res['flags_pre'])
    if res['last_touch']:
        return False, 'last instruction touched tainted data (data bus)'
    bad = [(a, tram[a]) for a in range(0x800) if tram[a] & ~allowed.get(a, 0) & 0xFF]
    if bad:
        return False, 'taint escaped to ' + ' '.join('%03X:%02X' % x for x in bad[:12])
    return True, 'ok'


# ---------------------------------------------------------------------------------------------------------------
def load_movie(path):
    """Pads of an .fm2 movie; refuses a movie with a non-zero command column (reset / power cycle), AX-POWERON."""
    header, frames = rm2.read_fm2(path)
    bad = [i for i, (c, p) in enumerate(frames) if c != 0]
    assert not bad, 'movie %s has commands (reset/power) at frames %s' % (path, bad[:5])
    return [p for c, p in frames]


def root_states(e, frames, pads):
    """States BEFORE each frame f in `frames`, from ONE continuous replay of `pads` from power-on in this process.
    The emulator must be fresh (no frame emulated since its power-on; FCEUX's power-on does not reset the PPU's
    fine-X register, so a second power-on in a used process is not the power-on state, AX-POWERON).
    Returns {f: state}."""
    assert e.frames_since_poweron == 0, 'root_states needs a fresh process (no frame emulated since power-on)'
    out = {}
    want = sorted(set(frames))
    i = 0
    for f in want:
        assert f <= len(pads), 'frame %d beyond the movie (%d frames)' % (f, len(pads))
        while i < f:
            e.frame(pads[i]); i += 1
        out[f] = e.save()
    e.frames_since_poweron = i
    return out
