"""Python wrapper around the headless FCEUX driver (librm2.so)."""
import ctypes
import os

BTN = "RLDUTSBA"  # fm2 column order; char i is bit (7 - i)
A, B, SELECT, START, UP, DOWN, LEFT, RIGHT = 1, 2, 4, 8, 16, 32, 64, 128


def pad_from_fm2(field):
    v = 0
    for i, ch in enumerate(field[:8]):
        if ch not in ". ":
            v |= 1 << (7 - i)
    return v


def pad_to_fm2(v):
    return "".join(BTN[i] if v & (1 << (7 - i)) else "." for i in range(8))


def read_fm2(path):
    """Return (header_lines, list of (cmd, pad))."""
    header, frames = [], []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\r\n")
            if line.startswith("|"):
                parts = line.split("|")
                frames.append((int(parts[1] or 0), pad_from_fm2(parts[2])))
            elif line:
                header.append(line)
    return header, frames


def write_fm2(path, header, pads, rerecords=None):
    with open(path, "w", newline="\n") as f:
        for h in header:
            if rerecords is not None and h.startswith("rerecordCount"):
                h = "rerecordCount %d" % rerecords
            f.write(h + "\n")
        for p in pads:
            f.write("|0|%s|||\n" % pad_to_fm2(p))


class Emu:
    def __init__(self, lib, rom, verbose=0):
        self.lib = ctypes.CDLL(lib)
        L = self.lib
        L.rm2_init.argtypes = [ctypes.c_char_p, ctypes.c_int]
        L.rm2_frame.argtypes = [ctypes.c_int]
        L.rm2_ram.restype = ctypes.POINTER(ctypes.c_uint8)
        L.rm2_xbuf.restype = ctypes.POINTER(ctypes.c_uint8)
        L.rm2_save.argtypes = [ctypes.c_void_p, ctypes.c_int]
        L.rm2_load.argtypes = [ctypes.c_void_p, ctypes.c_int]
        L.rm2_movie_load.argtypes = [ctypes.c_char_p]
        L.rm2_read.argtypes = [ctypes.c_int]
        rc = L.rm2_init(rom.encode(), verbose)
        if rc:
            raise RuntimeError("rm2_init failed: %d" % rc)
        self._ram = L.rm2_ram()
        self._buf = ctypes.create_string_buffer(1 << 20)

    def poweron(self):
        self.lib.rm2_poweron()

    def frame(self, pad):
        return self.lib.rm2_frame(pad)

    def ram(self, addr):
        return self._ram[addr]

    def ramblock(self, a=0, n=0x800):
        return bytes(self._ram[a:a + n])

    def write(self, addr, v):
        self._ram[addr] = v & 0xFF

    def save(self):
        n = self.lib.rm2_save(self._buf, len(self._buf))
        if n < 0:
            raise RuntimeError("state too big")
        return self._buf.raw[:n]

    def load(self, st):
        if self.lib.rm2_load(st, len(st)):
            raise RuntimeError("load failed")

    def lagcount(self):
        return self.lib.rm2_lagcount()

    def screen(self):
        x = self.lib.rm2_xbuf()
        return bytes(x[:256 * 240])


# Standard 2C02 palette (approximate; only used for screenshots).
NES_PAL = [
    (84, 84, 84), (0, 30, 116), (8, 16, 144), (48, 0, 136), (68, 0, 100), (92, 0, 48), (84, 4, 0), (60, 24, 0),
    (32, 42, 0), (8, 58, 0), (0, 64, 0), (0, 60, 0), (0, 50, 60), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (152, 150, 152), (8, 76, 196), (48, 50, 236), (92, 30, 228), (136, 20, 176), (160, 20, 100), (152, 34, 32), (120, 60, 0),
    (84, 90, 0), (40, 114, 0), (8, 124, 0), (0, 118, 40), (0, 102, 120), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (236, 238, 236), (76, 154, 236), (120, 124, 236), (176, 98, 236), (228, 84, 236), (236, 88, 180), (236, 106, 100), (212, 136, 32),
    (160, 170, 0), (116, 196, 0), (76, 208, 32), (56, 204, 108), (56, 180, 204), (60, 60, 60), (0, 0, 0), (0, 0, 0),
    (236, 238, 236), (168, 204, 236), (188, 188, 236), (212, 178, 236), (236, 174, 236), (236, 174, 212), (236, 180, 176), (228, 196, 144),
    (204, 210, 120), (180, 222, 120), (168, 226, 144), (152, 226, 180), (160, 214, 228), (160, 162, 160), (0, 0, 0), (0, 0, 0),
]


def screenshot(emu, path, scale=2):
    from PIL import Image
    raw = emu.screen()
    img = Image.new("RGB", (256, 240))
    img.putdata([NES_PAL[b & 0x3F] for b in raw])
    if scale != 1:
        img = img.resize((256 * scale, 240 * scale), Image.NEAREST)
    img.save(path)


HOOKFN = ctypes.CFUNCTYPE(None, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p)
HOOK_READ, HOOK_WRITE, HOOK_EXEC = 0, 1, 2


def add_hook(emu, kind, pyfunc):
    """pyfunc(addr, value). Returns handle needed for remove_hook."""
    cb = HOOKFN(lambda a, v, ud: pyfunc(a, v))
    emu.lib.rm2_hook_add.argtypes = [ctypes.c_int, HOOKFN]
    emu.lib.rm2_hook_add(kind, cb)
    return cb


def remove_hook(emu, kind, cb):
    emu.lib.rm2_hook_remove.argtypes = [ctypes.c_int, HOOKFN]
    emu.lib.rm2_hook_remove(kind, cb)


def disasm(emu, addr, count=30):
    from py65.disassembler import Disassembler
    from py65.devices.mpu6502 import MPU

    class Mem:
        def __getitem__(self, a):
            if isinstance(a, slice):
                return [emu.lib.rm2_read(x & 0xFFFF) for x in range(a.start, a.stop)]
            return emu.lib.rm2_read(a & 0xFFFF)

    m = MPU(memory=Mem())
    d = Disassembler(m)
    out = []
    for _ in range(count):
        n, txt = d.instruction_at(addr)
        out.append("%04X  %s" % (addr, txt))
        addr += n
    return "\n".join(out)


class Rom:
    """Static view of the MMC1 PRG ROM: 16 x 16KiB banks, bank 15 fixed at $C000."""

    def __init__(self, path):
        data = open(path, "rb").read()
        self.prg = data[16:16 + 16 * 0x4000]
        self.nbanks = len(self.prg) // 0x4000

    def byte(self, bank, addr):
        if addr >= 0xC000:
            return self.prg[(self.nbanks - 1) * 0x4000 + (addr - 0xC000)]
        return self.prg[bank * 0x4000 + (addr - 0x8000)]

    def identify_bank(self, emu):
        probe = bytes(emu.lib.rm2_read(0x8000 + i) for i in range(64))
        for b in range(self.nbanks):
            if self.prg[b * 0x4000:b * 0x4000 + 64] == probe:
                return b
        return None

    def disasm(self, bank, addr, count=30):
        from py65.disassembler import Disassembler
        from py65.devices.mpu6502 import MPU
        rom = self

        class Mem:
            def __getitem__(self, a):
                if isinstance(a, slice):
                    return [rom.byte(bank, x & 0xFFFF) for x in range(a.start, a.stop)]
                a &= 0xFFFF
                return rom.byte(bank, a) if a >= 0x8000 else 0

        d = Disassembler(MPU(memory=Mem()))
        out = []
        for _ in range(count):
            n, txt = d.instruction_at(addr)
            out.append("%X:%04X  %s" % (bank, addr, txt))
            addr += n
        return "\n".join(out)
