#!/usr/bin/env python3
"""pfcheck.py - independent CHECKER for search certificates written by pfsearch.py (pf_search, 2026-11-07).

It shares no code with pfsearch.py / pflib.py. It uses only the emulator library and tools/harness/rm2.py (trusted
base and assumption A-HARNESS in docs/proof-standards.md).

usage: pfcheck.py CERT.json[.gz] --rom ROM.nes --lib LIBRM2.so [--movie MOVIE.fm2] [--envelope ENV.json]
                  [--classes] [--sample N] [--taint] [--variants N] [--writers]
  --rom       the Rockman 2 (J) ROM; its md5 must equal the certificate's (and the envelope's sha256, if any)
  --lib       an emulator library built by tools/proof/Makefile or tools/harness/Makefile: librm2.so of FCEUX master
              (working core) or of FCEUX 2.3.0 (judge core), or librm2pf.so (master + observing hooks; needed for
              --taint and --writers)
  --movie     the movie whose pads rebuild the root; default: the envelope's root.movie_file (repository-relative)
  --envelope  the certificate envelope; default: <certificate name without .json[.gz]>.envelope.json next to it.
              Without an envelope the certificate is checked on its own (E0 is skipped and says so).
  --classes   closure only over the certificate's class representatives (default: all 256 pads)
  --sample N  with --classes: also closure over all 256 pads on N randomly chosen entries per layer (C3b)
  --taint     re-run the taint tracker on every (entry, class) transition (C5; needs librm2pf.so)
  --variants N  differential test of the canonicalisation (C6): N random variants of every entry
  --writers   census of the writers of $1D/$FD/$FE/$A9 over every class transition (C7; needs librm2pf.so)
Checks:
  E0 envelope: the certificate's sha256 and claim match the envelope, the ROM matches its hashes
  C0 classes : the class representatives cover all 256 pads
  C1 root    : the root is rebuilt by a CONTINUOUS replay of the movie from power-on in this (fresh) process and has
               the certificate's key hash
  C2 layers  : every listed entry is reproduced by replaying its witness path from the root without intermediate
               save/load and has the listed canonical hash; no listed entry satisfies the goal
  C3 closure : for every entry of layers 0..D-1 and every pad (256, or the classes), the child's canonical hash is in
               layer d+1, or the child is pruned by the certificate's pruning rule, recomputed here by the checker's own
               implementation (menu_cursor_v1 = lemma L-menu)
  C4 witness : the witness reaches the goal at depth D+1 and not before
Exit code 0 iff the verdict is VALID. The checker writes nothing except to stdout."""
import sys, os, json, struct, hashlib, ctypes, random, time, gzip, base64

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'harness'))
import rm2  # noqa: E402

EXPECT_DROP_FIELDS = ['CPUC.TSBS', 'CTRL.FRAM', 'CTRL.JOYS', 'CTRL.LAGC', 'CTRL.LAGF', 'SFMDATA.LRST']
EXPECT_DROP_CHUNKS = ['BACKBUF', 'NEWPPU']
FLAGS = {'--classes': 0, '--taint': 0, '--writers': 0, '--rom': 1, '--lib': 1, '--movie': 1, '--envelope': 1,
         '--sample': 1, '--variants': 1}


class Key:
    """Independent implementation of the canonical key: walk the FCSX chunks; keep every field except the dropped ones."""
    CH = {1: 'CPU', 2: 'CPUC', 3: 'PPU', 31: 'NEWPPU', 4: 'CTRL', 5: 'SND', 8: 'BACKBUF', 16: 'SFMDATA'}

    def __init__(self, drop_fields, drop_chunks, canon):
        self.df = set(drop_fields); self.dc = set(drop_chunks)
        self.canon = {int(a, 16): int(m) for a, m in canon.items()}

    def key(self, st):
        n = len(st)
        assert st[0:4] == b'FCSX'
        tot = struct.unpack_from('<I', st, 4)[0]
        assert tot == n - 16
        parts = []
        p = 16
        while p < n:
            ctype = st[p]; csize = struct.unpack_from('<I', st, p + 1)[0]
            cname = self.CH.get(ctype, '?%d' % ctype)
            q = p + 5; end = q + csize
            if ctype == 8:
                if cname not in self.dc:
                    parts.append(st[q:end])
            else:
                while q < end:
                    name = st[q:q + 4].rstrip(b'\0').decode('latin1')
                    fs = struct.unpack_from('<I', st, q + 4)[0]
                    data = st[q + 8:q + 8 + fs]
                    full = '%s.%s' % (cname, name)
                    if cname not in self.dc and full not in self.df:
                        if full == 'CPU.RAM' and self.canon:
                            data = bytearray(data)
                            for a, m in self.canon.items():
                                data[a] &= (~m) & 0xFF
                            data = bytes(data)
                        parts.append(data)
                    q += 8 + fs
            p = end
        return b''.join(parts)

    def h(self, st):
        return hashlib.sha256(self.key(st)).hexdigest()


def field(st, cname, fname):
    # walk the chunks of an FCSX state; return the data bytes of field cname.fname
    n = len(st); p = 16
    while p < n:
        ctype = st[p]; csize = struct.unpack_from('<I', st, p + 1)[0]
        q = p + 5; end = q + csize
        if Key.CH.get(ctype) == cname and ctype != 8:
            while q < end:
                name = st[q:q + 4].rstrip(b'\0').decode('latin1'); fs = struct.unpack_from('<I', st, q + 4)[0]
                if name == fname:
                    return st[q + 8:q + 8 + fs]
                q += 8 + fs
        p = end
    raise KeyError(cname + '.' + fname)


def ram_byte(st, a):
    # RAM field of chunk 1: CPU chunk starts at 16; fields PC(2) A X Y S P DB(1 each) then RAM; each field has an 8-byte
    # header -> RAM data offset = 16 + 5 + (8+2) + 6*(8+1) + 8 = 93 (asserted below)
    assert st[85:88] == b'RAM'
    return st[93 + a]


_ROMB = None


def set_rom(data):
    global _ROMB
    _ROMB = data[16:]


def rom_byte(bank, addr):
    off = (15 * 0x4000 + addr - 0xC000) if addr >= 0xC000 else (bank * 0x4000 + addr - 0x8000)
    return _ROMB[off]


def h_menu_check(st, target):
    """Checker's own implementation of lemma L-menu's bound (menu_cursor_v1)."""
    pc = struct.unpack('<H', field(st, 'CPU', 'PC'))[0]
    sp = field(st, 'CPU', 'S')[0]
    ram = field(st, 'CPU', 'RAM')
    if pc != 0xC0BA and pc != 0xC0BC:
        return 0
    if ram[0x100 + ((sp + 1) & 0xFF)] != 0x7D or ram[0x100 + ((sp + 2) & 0xFF)] != 0x92:
        return 0
    row, page = ram[0xFD], ram[0xFE]
    if page > 1 or row > (7 - page):
        return 0
    rowbit = [rom_byte(13, 0x9670 + i) for i in range(8)]
    owned = {0: ((ram[0x9A] << 1) | 0x41) & 0xFF, 1: ((ram[0x9B] << 3) | (ram[0x9A] >> 5)) & 0xFF}

    def mv(r, pg, up):
        top = 7 - pg
        n = 0
        while True:
            n += 1
            r = (r - 1 if up else r + 1)
            if r < 0: r = top
            if r > top: r = 0
            if r == 0 or rowbit[r] & owned[pg] or n > 20:
                return r
    tpage = 1 if target >= 6 else 0
    trow = target + 1 - 6 * tpage
    seen = {(row, page): 0}
    frontier = [(row, page)]
    k = 0
    while frontier:
        if (trow, tpage) in frontier:
            return k + 1
        k += 1
        new = []
        for r, pg in frontier:
            for nxt in ((mv(r, pg, True), pg), (mv(r, pg, False), pg)) + (((0, 1 - pg),) if r == 0 else ()):
                if nxt not in seen:
                    seen[nxt] = k; new.append(nxt)
        frontier = new
    return 10 ** 6


# ------------------------------------------------------------------------------------------------ shared set-up
def parse_args(argv, flags=FLAGS):
    """Strict option parser: an unknown option is an error (fail closed)."""
    pos, opt = [], {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith('--'):
            if a not in flags:
                raise SystemExit('unknown option %s (known: %s)' % (a, ' '.join(sorted(flags))))
            if flags[a]:
                if i + 1 >= len(argv):
                    raise SystemExit('option %s needs a value' % a)
                opt[a] = argv[i + 1]; i += 2
            else:
                opt[a] = True; i += 1
        else:
            pos.append(a); i += 1
    if len(pos) != 1:
        raise SystemExit(__doc__)
    for need in ('--rom', '--lib'):
        if need not in opt:
            raise SystemExit('missing %s (see --help in the module docstring)' % need)
    return pos[0], opt


def cert_name(path):
    b = os.path.basename(path)
    return b[:-3] if b.endswith('.gz') else b


def load_cert(path):
    raw = open(path, 'rb').read()
    if path.endswith('.gz'):
        raw = gzip.decompress(raw)
    return raw, json.loads(raw)


def find_envelope(path, opt):
    if '--envelope' in opt:
        return opt['--envelope']
    stem = cert_name(path)
    stem = stem[:-5] if stem.endswith('.json') else stem
    cand = os.path.join(os.path.dirname(os.path.abspath(path)), stem + '.envelope.json')
    return cand if os.path.exists(cand) else None


def envelope_check(env, raw, cert, rom_md5, rom_sha256):
    """E0. Returns (ok, list of problems)."""
    bad = []
    pl = env.get('payload', {})
    if env.get('standard') != 'rm2-proof-1':
        bad.append('standard %r' % env.get('standard'))
    if pl.get('sha256') != hashlib.sha256(raw).hexdigest():
        bad.append('certificate sha256 differs from envelope payload.sha256')
    if pl.get('bytes') is not None and pl['bytes'] != len(raw):
        bad.append('certificate size differs from envelope payload.bytes')
    base = env.get('base', {})
    if base.get('rom_md5') != rom_md5 or base.get('rom_sha256') != rom_sha256:
        bad.append('ROM hashes differ from envelope base')
    m = env.get('claim', {}).get('machine', {})
    res = cert['result']
    want = {'frame_before': cert['root']['frame_before'], 'key_hash': cert['root']['key_hash'], 'goal': cert['goal'],
            'goal_depth': res.get('goal_depth'), 'last_goal_free_depth': res.get('last_goal_free_depth'),
            'classes': cert['alphabet']['classes'], 'kin': cert['alphabet']['kin'],
            'prune_spec': cert.get('prune_spec')}
    for k, v in want.items():
        if k not in m:
            bad.append('envelope claim.machine lacks %s' % k)
        elif m[k] != v:
            bad.append('envelope claim.machine.%s = %r, certificate has %r' % (k, m[k], v))
    if not isinstance(env.get('assumptions'), list):
        bad.append('envelope has no assumptions list')
    return not bad, bad


def setup(argv, flags=FLAGS):
    """Common set-up of both checkers: arguments, certificate, envelope (E0), ROM, emulator, movie, root (C1).
    Returns a dict with everything the checks need."""
    path, opt = parse_args(argv, flags)
    raw, cert = load_cert(path)
    name = cert_name(path)
    rom = open(opt['--rom'], 'rb').read()
    rom_md5 = hashlib.md5(rom).hexdigest(); rom_sha256 = hashlib.sha256(rom).hexdigest()
    set_rom(rom)
    out = {'cert': name, 'cert_sha256': hashlib.sha256(raw).hexdigest(), 'lib': os.path.basename(opt['--lib']),
           'lib_md5': hashlib.md5(open(opt['--lib'], 'rb').read()).hexdigest(),
           'checker_sha256': hashlib.sha256(open(os.path.abspath(sys.argv[0]), 'rb').read()).hexdigest()}
    ok = True
    print('checker %s sha256 %s; certificate %s sha256 %s; library %s md5 %s' % (
        os.path.basename(sys.argv[0]), out['checker_sha256'], name, out['cert_sha256'], out['lib'], out['lib_md5']),
        flush=True)
    # ROM (fail closed)
    if cert['core']['rom_md5'] != rom_md5:
        print('ROM FAIL: md5 %s, certificate wants %s' % (rom_md5, cert['core']['rom_md5']), flush=True)
        ok = False
    # E0 envelope
    envp = find_envelope(path, opt)
    env = None
    if envp:
        env = json.load(open(envp))
        e0, bad = envelope_check(env, raw, cert, rom_md5, rom_sha256)
        for b in bad:
            print('E0 FAIL: ' + b, flush=True)
        print('E0 envelope %s: %s; label %s; assumptions %s' % (os.path.basename(envp), e0, env.get('label'),
                                                               ', '.join(env.get('assumptions', []))), flush=True)
        out['E0_envelope'] = e0; out['label'] = env.get('label'); out['assumptions'] = env.get('assumptions')
        ok &= e0
    else:
        print('E0 envelope: none found (the certificate is checked on its own)', flush=True)
    # movie
    r = cert['root']
    mpath = opt.get('--movie') or r.get('movie_file') or (env or {}).get('root', {}).get('movie_file')
    if not mpath:
        raise SystemExit('no movie: pass --movie (the certificate root names movie %r)' % r.get('movie'))
    if not os.path.isabs(mpath) and not os.path.exists(mpath):
        mpath = os.path.join(REPO, mpath)
    mpath = os.path.abspath(mpath)
    mbytes = open(mpath, 'rb').read()
    msha = hashlib.sha256(mbytes).hexdigest()
    want_msha = r.get('movie_sha256') or (env or {}).get('root', {}).get('movie_sha256')
    if want_msha and want_msha != msha:
        print('MOVIE FAIL: %s sha256 %s, expected %s' % (mpath, msha, want_msha), flush=True)
        ok = False
    header, frames = rm2.read_fm2(mpath)
    fb = r['frame_before']
    hdr = dict(h.split(' ', 1) for h in header if ' ' in h)
    prg_md5_b64 = 'base64:' + base64.b64encode(hashlib.md5(rom[16:]).digest()).decode()
    if hdr.get('romChecksum') != prg_md5_b64:
        print('MOVIE FAIL: romChecksum %s, ROM gives %s' % (hdr.get('romChecksum'), prg_md5_b64), flush=True)
        ok = False
    if len(frames) < fb or any(c != 0 for c, p in frames[:fb]):
        print('MOVIE FAIL: fewer than %d frames, or a non-zero command (reset/power) before the root' % fb, flush=True)
        ok = False
    pads = [p for c, p in frames]
    out['movie'] = os.path.relpath(mpath, REPO) if mpath.startswith(REPO + os.sep) else mpath
    out['movie_sha256'] = msha
    # emulator; C1 root by continuous replay from power-on in this fresh process
    e = rm2.Emu(opt['--lib'], opt['--rom'])
    idn = cert['identity']
    if sorted(idn['drop_fields']) != EXPECT_DROP_FIELDS or sorted(idn['drop_chunks']) != EXPECT_DROP_CHUNKS:
        print('IDENTITY FAIL: unexpected dropped fields %s %s' % (idn['drop_fields'], idn['drop_chunks']), flush=True)
        ok = False
    K = Key(idn['drop_fields'], idn['drop_chunks'], idn['canon'])
    t0 = time.time()
    for i in range(fb):
        e.frame(pads[i])
    root = e.save()
    c1 = K.h(root) == r['key_hash']
    full = hashlib.sha256(root).hexdigest() == r.get('state_sha256')
    print('C1 root key hash matches: %s (power-on + %d frames of %s replayed continuously in this process, %.0fs; '
          'full-state sha256 also equal: %s, informational)' % (c1, fb, out['movie'], time.time() - t0, full), flush=True)
    out['C1_root'] = c1; out['root_full_state_equal'] = full
    ok &= c1
    # goal
    g = cert['goal']
    geq = [tuple(x) for x in g['ram_eq']]; gne = [tuple(x) for x in g.get('ram_ne', [])]
    gany = [tuple(x) for x in g.get('ram_any_eq', [])]
    canon_addrs = set(int(a, 16) for a in idn['canon'])
    assert not any(a in canon_addrs for a, v in geq + gne + gany), 'goal reads a canonicalised byte'

    def goal(st):
        return (all(ram_byte(st, a) == v for a, v in geq) and all(ram_byte(st, a) != v for a, v in gne)
                and (not gany or any(ram_byte(st, a) == v for a, v in gany)))
    ps = cert.get('prune_spec')
    if ps and ps.get('type') != 'menu_cursor_v1':
        raise SystemExit('unknown pruning rule %r: this checker cannot re-justify it (fail closed)' % ps.get('type'))

    def pruned_ok(ch, depth):
        return bool(ps and not goal(ch) and depth + h_menu_check(ch, ps['target']) > ps['bound'])
    classes = cert['alphabet']['classes']; kin = cert['alphabet']['kin']
    c0 = all((p_ & ~kin & 0xFF) in set(classes) for p_ in range(256)) and all((c & kin) == 0 for c in classes)
    print('C0 classes cover all 256 pads: %s' % c0, flush=True)
    out['C0_classes_cover_all_pads'] = c0
    ok &= c0
    t_taint = '--taint' in opt or '--writers' in opt
    if t_taint and not hasattr(e.lib, 'pf_taint_begin'):
        raise SystemExit('--taint/--writers need the analysis library librm2pf.so')
    return dict(path=path, opt=opt, cert=cert, name=name, e=e, K=K, root=root, goal=goal, pruned_ok=pruned_ok,
                classes=classes, kin=kin, out=out, ok=ok, t0=t0)


def verdict(ctx, ok):
    out = ctx['out']
    out['ALL_OK'] = bool(ok)
    out['seconds'] = round(time.time() - ctx['t0'], 1)
    print('VERDICT %s: %s %s' % (ctx['name'], 'VALID' if ok else 'INVALID', json.dumps(out, sort_keys=True)),
          flush=True)
    return 0 if ok else 1


def taint_good(o, tr, allowed):
    return (o[0] == 0 and o[12] != 0 and o[3] == o[4] == o[5] == 0 and o[6] == 0 and o[7] == 0 and o[8] == 0
            and all((tr[a] & ~allowed.get(a, 0) & 0xFF) == 0 for a in range(0x800)))


# ------------------------------------------------------------------------------------------------ main checker
def main(argv):
    ctx = setup(argv)
    cert, e, K, root, goal, out, opt = ctx['cert'], ctx['e'], ctx['K'], ctx['root'], ctx['goal'], ctx['out'], ctx['opt']
    ok_all = ctx['ok']
    t0 = ctx['t0']
    idn = cert['identity']
    nvar = int(opt.get('--variants', 0))
    all256 = '--classes' not in opt
    nsample = int(opt.get('--sample', 0))
    layers = cert['layers']
    D = len(layers) - 1
    sets = [set(x[0] for x in L) for L in layers]
    for d, L in enumerate(layers):
        assert len(L) == len(sets[d]), 'duplicate hash in layer %d' % d
        assert [x[0] for x in L] == sorted(x[0] for x in L), 'layer %d not sorted' % d
    if layers[0] != [[cert['root']['key_hash'], -1, -1]]:
        print('C2 FAIL: layer 0 is not the root', flush=True); ok_all = False

    # C2 reconstruct every entry by continuous replay of its witness path from the root
    def path_of(d, i):
        pth = []
        while d > 0:
            h, pi, pad = layers[d][i]
            pth.append(pad); i = pi; d -= 1
        return pth[::-1]
    recon = [[None] * len(L) for L in layers]
    c2 = True; nframes = 0
    for d, L in enumerate(layers):
        for i, (h, pi, pad) in enumerate(L):
            e.load(root)
            for p_ in path_of(d, i):
                e.frame(p_); nframes += 1
            st = e.save()
            if K.h(st) != h:
                c2 = False; print('C2 FAIL: layer %d entry %d hash mismatch' % (d, i))
            if d > 0 and goal(st):
                c2 = False; print('C2 FAIL: layer %d entry %d satisfies the goal' % (d, i))
            recon[d][i] = st
    out['C2_layers'] = c2; ok_all &= c2
    print('C2 %d entries reproduced by continuous replay (%d frames), hashes and goal-freeness: %s (%.0fs)' % (
        sum(len(L) for L in layers), nframes, c2, time.time() - t0), flush=True)

    # C3 closure over all 256 pads (or the classes)
    padset = list(range(256)) if all256 else list(cert['alphabet']['classes'])
    c3 = True; nchk = 0; npruned = 0
    for d in range(D):
        for i, st in enumerate(recon[d]):
            for p_ in padset:
                e.load(st); e.frame(p_); ch = e.save(); nchk += 1
                if K.h(ch) in sets[d + 1]:
                    continue
                if ctx['pruned_ok'](ch, d + 1):
                    npruned += 1
                    continue
                c3 = False
                if goal(ch):
                    print('C3 FAIL: goal reached at depth %d from layer %d entry %d pad %02X' % (d + 1, d, i, p_))
                else:
                    print('C3 FAIL: child of layer %d entry %d pad %02X not in layer %d' % (d, i, p_, d + 1))
        print('  closure layer %d -> %d checked (%d transitions so far, %.0fs)' % (d, d + 1, nchk, time.time() - t0),
              flush=True)
    if nsample:
        rs = random.Random(777); n3b = 0; c3b = True
        for d in range(D):
            idxs = list(range(len(recon[d])))
            rs.shuffle(idxs)
            for i in idxs[:nsample]:
                st = recon[d][i]
                for p_ in range(256):
                    e.load(st); e.frame(p_); ch = e.save(); n3b += 1
                    if K.h(ch) in sets[d + 1] or ctx['pruned_ok'](ch, d + 1):
                        continue
                    c3b = False; print('C3b FAIL: layer %d entry %d pad %02X' % (d, i, p_))
        out['C3b_256pad_sample'] = c3b; out['C3b_transitions'] = n3b; ok_all &= c3b
        print('C3b closure over all 256 pads on %d sampled entries per layer: %s (%d transitions)' % (nsample, c3b, n3b),
              flush=True)
    out['C3_closure'] = c3; out['C3_transitions'] = nchk; out['C3_pads'] = len(padset); ok_all &= c3
    out['C3_children_pruned_by_lemma'] = npruned
    print('C3 closure over %d pads: %s (%d transitions)' % (len(padset), c3, nchk), flush=True)

    # C4 witness
    res = cert['result']
    if res.get('goal_depth') is not None:
        e.load(root)
        hit = []
        for p_ in res['witness']:
            e.frame(p_)
            hit.append(goal(e.save()))
        c4 = bool(hit) and hit[-1] and not any(hit[:-1]) and len(res['witness']) == res['goal_depth'] == D + 1
        out['C4_witness'] = c4; ok_all &= c4
        print('C4 witness of length %d reaches the goal only at its end: %s' % (len(res['witness']), c4), flush=True)

    allowed = {int(a, 16): int(m) for a, m in idn['canon'].items()}
    # C5 taint verdicts re-run
    if '--taint' in opt:
        L_ = e.lib
        L_.pf_taint_begin.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        L_.pf_taint_end.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_char_p]
        tout = (ctypes.c_int * 16)(); tram = ctypes.create_string_buffer(0x800)
        init = bytearray(0x800)
        for a, m in allowed.items(): init[a] = m
        init = bytes(init)
        kin = cert['alphabet']['kin']
        c5 = True; n5 = 0; maxnint = 0
        for d in range(D):
            for i, st in enumerate(recon[d]):
                jrb = field(st, 'CTRL', 'JYRB')[0]; ls = field(st, 'CTRL', 'LSTS')[0]
                for p_ in cert['alphabet']['classes']:
                    e.load(st)
                    L_.pf_taint_begin(init, kin, jrb, ls)
                    e.frame(p_)
                    L_.pf_taint_end(tout, tram)
                    o = list(tout); n5 += 1; maxnint = max(maxnint, o[11])
                    if not taint_good(o, tram.raw, allowed):
                        c5 = False; print('C5 FAIL layer %d entry %d class %02X: %s' % (d, i, p_, o[:13]))
        out['C5_taint'] = c5; out['C5_transitions'] = n5; ok_all &= c5; out['C5_max_nmi_per_frame'] = maxnint
        print('C5 taint verdicts re-run on %d class transitions: %s' % (n5, c5), flush=True)

    # C6 variants: randomise the canonical bits of the dead RAM bytes, children must keep the same canonical hash
    if nvar:
        rnd = random.Random(12345)
        c6 = True; n6 = 0
        for d in range(D):
            for i, st in enumerate(recon[d]):
                ref = {}
                for p_ in cert['alphabet']['classes']:
                    e.load(st); e.frame(p_); ref[p_] = K.h(e.save())
                for v in range(nvar):
                    flips = {a: rnd.randrange(256) & m for a, m in allowed.items()}
                    for p_ in cert['alphabet']['classes']:
                        kin = cert['alphabet']['kin']
                        p2 = p_ | (rnd.randrange(256) & kin)      # also a random pad of the same class
                        e.load(st)
                        for a, fm in flips.items():
                            e.write(a, e.ram(a) ^ fm)
                        e.frame(p2); n6 += 1
                        if K.h(e.save()) != ref[p_]:
                            c6 = False; print('C6 FAIL layer %d entry %d class %02X variant %s pad %02X' % (
                                d, i, p_, flips, p2))
        out['C6_variants'] = c6; out['C6_runs'] = n6; ok_all &= c6
        print('C6 differential test of the canonicalisation: %d runs: %s' % (n6, c6), flush=True)
    # C7 (L-menu evidence): write watch on $1D/$FD/$FE/$A9 over every class transition of every entry -> writer PCs
    if '--writers' in opt:
        L_ = e.lib
        L_.pf_ww_get.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        wb = (ctypes.c_int * 4)()
        L_.pf_ww_clearmask()
        for a in (0x1D, 0xFD, 0xFE, 0xA9):
            L_.pf_ww_set(a, 1)
        writers = {}
        for d in range(D):
            for i, st in enumerate(recon[d]):
                for p_ in cert['alphabet']['classes']:
                    e.load(st); L_.pf_ww_reset(); L_.pf_ww(1); e.frame(p_); L_.pf_ww(0)
                    for k in range(L_.pf_ww_count()):
                        L_.pf_ww_get(k, wb)
                        key = '%02X@%04X%s' % (wb[2], wb[1], '(0)' if wb[3] == 0 else '(nz)')
                        writers[key] = writers.get(key, 0) + 1
        out['C7_writers'] = writers
        print('C7 writers of $1D/$FD/$FE/$A9 (addr@pc(value zero/nonzero): count):', json.dumps(writers, sort_keys=True),
              flush=True)
    return verdict(ctx, ok_all)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
