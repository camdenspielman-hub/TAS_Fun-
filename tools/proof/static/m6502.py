"""6502 opcode table mirroring FCEUX's x6502.cpp / ops.inc EXACTLY (the ground truth for this project).

Every one of the 256 opcodes is listed with:
  mnem   : mnemonic (undocumented ones use FCEUX's semantics; names follow common usage)
  mode   : imp acc imm zp zpx zpy abs absx absy ind indx indy rel
  length : bytes consumed by FCEUX (KIL = 1 and jams: PC is decremented, CPU stops; interrupts are ignored)
  kind   : what the instruction does to memory / control flow (used by the analyzer):
           'load'  reads memory operand            'store' writes memory operand (no read)
           'rmw'   reads then writes the operand   'nopr'  reads memory operand, no other effect (TOP)
           'none'  no memory operand access        'branch' 'jmp' 'jmpi' 'jsr' 'rts' 'rti' 'brk' 'kil'
           'push' 'pull'
  undoc  : True for opcodes outside the documented 151.

Write semantics that matter for write sets (checked against ops.inc):
  * RMW_ZP / RMW_ZPX: ONE write (WrRAM) to the zero-page address (index wraps in page 0).
  * RMW_AB / RMW_ABX / RMW_ABY / RMW_IX / RMW_IY: TWO writes to the same address (dummy write of the old
    value, then the new value).  LAS ($BB) is implemented by FCEUX with RMW_ABY, so it WRITES memory (the
    unchanged value) twice.
  * ST_ABI (abs,X / abs,Y stores) and RMW_ABI: dummy READ at (base & $FF00) | ((base+i) & $FF).
  * GetABIRD (abs,X/abs,Y loads): dummy READ at target ^ $100 when a page is crossed.
  * GetIYWR (zp),Y stores/RMW: dummy READ at (ptr & $FF00) | ((ptr+Y) & $FF); GetIYRD: dummy read on crossing.
  * (zp),Y and (zp,X) fetch the pointer with 8-bit wrap: ptr = RAM[t] | RAM[(t+1)&$FF] << 8.
  * JMP (ind): high byte from ((a+1)&$FF)|(a&$FF00)  (page-wrap bug).
  * SHY $9C: address = ((Y & (H+1)) << 8) | ((base+X) & $FF), value = that high byte.
  * SHX $9E: address = ((X & (H+1)) << 8) | ((base+Y) & $FF), value = that high byte.
  * SHA $9F/$93, TAS $9B: normal abs,Y / (zp),Y address; TAS also sets S = A & X.
  * DOP opcodes ($04 $14 ... $F4, $80 $82 $89 $C2 $E2): FCEUX only skips the operand, NO memory read.
  * Stack: PUSH writes RAM[$100+S] then S--; POP pre-increments S.  JSR pushes PC+2 (hi then lo);
    BRK pushes PC+2 (it skips a padding byte), P|B|U, sets I, jumps via ($FFFE).  NMI/IRQ push PC hi, lo,
    P&~B|U, set I.  RTS: PC = pop | pop<<8, PC+1.  RTI: P = pop, PC = pop | pop<<8.
"""

MODES_LEN = {'imp': 1, 'acc': 1, 'imm': 2, 'zp': 2, 'zpx': 2, 'zpy': 2, 'abs': 3, 'absx': 3, 'absy': 3,
             'ind': 3, 'indx': 2, 'indy': 2, 'rel': 2}

OPS = {}


def _d(op, mnem, mode, kind, undoc=False, length=None):
    assert op not in OPS, hex(op)
    OPS[op] = dict(op=op, mnem=mnem, mode=mode, kind=kind, undoc=undoc,
                   length=length if length is not None else MODES_LEN[mode])


# ---- documented ----
_ALU = [('ORA', 0x00), ('AND', 0x20), ('EOR', 0x40), ('ADC', 0x60), ('STA', 0x80), ('LDA', 0xA0), ('CMP', 0xC0),
        ('SBC', 0xE0)]
for m, base in _ALU:
    k = 'store' if m == 'STA' else 'load'
    for off, mode in ((0x01, 'indx'), (0x05, 'zp'), (0x09, 'imm'), (0x0D, 'abs'), (0x11, 'indy'), (0x15, 'zpx'),
                      (0x19, 'absy'), (0x1D, 'absx')):
        if m == 'STA' and mode == 'imm':
            continue
        _d(base + off, m, mode, 'none' if mode == 'imm' else k)
for m, base in (('ASL', 0x00), ('ROL', 0x20), ('LSR', 0x40), ('ROR', 0x60)):
    _d(base + 0x06, m, 'zp', 'rmw'); _d(base + 0x0A, m, 'acc', 'none'); _d(base + 0x0E, m, 'abs', 'rmw')
    _d(base + 0x16, m, 'zpx', 'rmw'); _d(base + 0x1E, m, 'absx', 'rmw')
for m, base in (('DEC', 0xC0), ('INC', 0xE0)):
    _d(base + 0x06, m, 'zp', 'rmw'); _d(base + 0x0E, m, 'abs', 'rmw')
    _d(base + 0x16, m, 'zpx', 'rmw'); _d(base + 0x1E, m, 'absx', 'rmw')
_d(0x24, 'BIT', 'zp', 'load'); _d(0x2C, 'BIT', 'abs', 'load')
_d(0x84, 'STY', 'zp', 'store'); _d(0x8C, 'STY', 'abs', 'store'); _d(0x94, 'STY', 'zpx', 'store')
_d(0x86, 'STX', 'zp', 'store'); _d(0x8E, 'STX', 'abs', 'store'); _d(0x96, 'STX', 'zpy', 'store')
_d(0xA0, 'LDY', 'imm', 'none'); _d(0xA4, 'LDY', 'zp', 'load'); _d(0xAC, 'LDY', 'abs', 'load')
_d(0xB4, 'LDY', 'zpx', 'load'); _d(0xBC, 'LDY', 'absx', 'load')
_d(0xA2, 'LDX', 'imm', 'none'); _d(0xA6, 'LDX', 'zp', 'load'); _d(0xAE, 'LDX', 'abs', 'load')
_d(0xB6, 'LDX', 'zpy', 'load'); _d(0xBE, 'LDX', 'absy', 'load')
_d(0xC0, 'CPY', 'imm', 'none'); _d(0xC4, 'CPY', 'zp', 'load'); _d(0xCC, 'CPY', 'abs', 'load')
_d(0xE0, 'CPX', 'imm', 'none'); _d(0xE4, 'CPX', 'zp', 'load'); _d(0xEC, 'CPX', 'abs', 'load')
for op, m in ((0x10, 'BPL'), (0x30, 'BMI'), (0x50, 'BVC'), (0x70, 'BVS'), (0x90, 'BCC'), (0xB0, 'BCS'),
              (0xD0, 'BNE'), (0xF0, 'BEQ')):
    _d(op, m, 'rel', 'branch')
_d(0x00, 'BRK', 'imp', 'brk')
_d(0x20, 'JSR', 'abs', 'jsr')
_d(0x40, 'RTI', 'imp', 'rti')
_d(0x60, 'RTS', 'imp', 'rts')
_d(0x4C, 'JMP', 'abs', 'jmp')
_d(0x6C, 'JMP', 'ind', 'jmpi')
_d(0x08, 'PHP', 'imp', 'push'); _d(0x48, 'PHA', 'imp', 'push')
_d(0x28, 'PLP', 'imp', 'pull'); _d(0x68, 'PLA', 'imp', 'pull')
for op, m in ((0x18, 'CLC'), (0x38, 'SEC'), (0x58, 'CLI'), (0x78, 'SEI'), (0xB8, 'CLV'), (0xD8, 'CLD'),
              (0xF8, 'SED'), (0xAA, 'TAX'), (0x8A, 'TXA'), (0xA8, 'TAY'), (0x98, 'TYA'), (0xBA, 'TSX'),
              (0x9A, 'TXS'), (0xCA, 'DEX'), (0x88, 'DEY'), (0xE8, 'INX'), (0xC8, 'INY'), (0xEA, 'NOP')):
    _d(op, m, 'imp', 'none')

# ---- undocumented, exactly as FCEUX implements them ----
_d(0x0B, 'ANC', 'imm', 'none', True); _d(0x2B, 'ANC', 'imm', 'none', True)
_d(0x87, 'SAX', 'zp', 'store', True); _d(0x97, 'SAX', 'zpy', 'store', True)
_d(0x8F, 'SAX', 'abs', 'store', True); _d(0x83, 'SAX', 'indx', 'store', True)
_d(0x6B, 'ARR', 'imm', 'none', True)
_d(0x4B, 'ALR', 'imm', 'none', True)
_d(0xAB, 'LXA', 'imm', 'none', True)
_d(0xCB, 'AXS', 'imm', 'none', True)
for m, ops in (('DCP', (0xC7, 0xD7, 0xCF, 0xDF, 0xDB, 0xC3, 0xD3)),
               ('ISB', (0xE7, 0xF7, 0xEF, 0xFF, 0xFB, 0xE3, 0xF3)),
               ('RLA', (0x27, 0x37, 0x2F, 0x3F, 0x3B, 0x23, 0x33)),
               ('RRA', (0x67, 0x77, 0x6F, 0x7F, 0x7B, 0x63, 0x73)),
               ('SLO', (0x07, 0x17, 0x0F, 0x1F, 0x1B, 0x03, 0x13)),
               ('SRE', (0x47, 0x57, 0x4F, 0x5F, 0x5B, 0x43, 0x53))):
    for op, mode in zip(ops, ('zp', 'zpx', 'abs', 'absx', 'absy', 'indx', 'indy')):
        _d(op, m, mode, 'rmw', True)
for op in (0x04, 0x14, 0x34, 0x44, 0x54, 0x64, 0x74, 0x80, 0x82, 0x89, 0xC2, 0xD4, 0xE2, 0xF4):
    _d(op, 'DOP', 'imm', 'none', True)        # FCEUX: _PC++ only, no memory access
for op in (0x02, 0x12, 0x22, 0x32, 0x42, 0x52, 0x62, 0x72, 0x92, 0xB2, 0xD2, 0xF2):
    _d(op, 'KIL', 'imp', 'kil', True)
_d(0xBB, 'LAS', 'absy', 'rmw', True)         # FCEUX uses RMW_ABY: writes the (unchanged) value twice
for op, mode in ((0xA7, 'zp'), (0xB7, 'zpy'), (0xAF, 'abs'), (0xBF, 'absy'), (0xA3, 'indx'), (0xB3, 'indy')):
    _d(op, 'LAX', mode, 'load', True)
for op in (0x1A, 0x3A, 0x5A, 0x7A, 0xDA, 0xFA):
    _d(op, 'NOP', 'imp', 'none', True)
_d(0x93, 'SHA', 'indy', 'store', True); _d(0x9F, 'SHA', 'absy', 'store', True)
_d(0x9C, 'SHY', 'absx', 'store', True); _d(0x9E, 'SHX', 'absy', 'store', True)
_d(0x9B, 'TAS', 'absy', 'store', True)
_d(0x0C, 'TOP', 'abs', 'nopr', True)
for op in (0x1C, 0x3C, 0x5C, 0x7C, 0xDC, 0xFC):
    _d(op, 'TOP', 'absx', 'nopr', True)
_d(0x8B, 'XAA', 'imm', 'none', True)
_d(0xEB, 'SBC', 'imm', 'none', True)

assert len(OPS) == 256, len(OPS)
# number of writes per execution for memory-writing kinds (used for documentation / validation)
for o in OPS.values():
    if o['kind'] == 'rmw':
        o['nwrites'] = 1 if o['mode'] in ('zp', 'zpx') else 2
    elif o['kind'] == 'store':
        o['nwrites'] = 1
    else:
        o['nwrites'] = 0

DOCUMENTED = {op for op, o in OPS.items() if not o['undoc']}
assert len(DOCUMENTED) == 151, len(DOCUMENTED)


def fmt(op, operand_bytes, pc):
    """Assembler text for one instruction (operand_bytes: list of 0..2 ints)."""
    o = OPS[op]
    m, mode = o['mnem'], o['mode']
    b = operand_bytes
    if mode in ('imp',):
        return m
    if mode == 'acc':
        return m + ' A'
    if mode == 'imm':
        return '%s #$%02X' % (m, b[0])
    if mode == 'zp':
        return '%s $%02X' % (m, b[0])
    if mode == 'zpx':
        return '%s $%02X,X' % (m, b[0])
    if mode == 'zpy':
        return '%s $%02X,Y' % (m, b[0])
    w = (b[0] | (b[1] << 8)) if len(b) > 1 else None
    if mode == 'abs':
        return '%s $%04X' % (m, w)
    if mode == 'absx':
        return '%s $%04X,X' % (m, w)
    if mode == 'absy':
        return '%s $%04X,Y' % (m, w)
    if mode == 'ind':
        return '%s ($%04X)' % (m, w)
    if mode == 'indx':
        return '%s ($%02X,X)' % (m, b[0])
    if mode == 'indy':
        return '%s ($%02X),Y' % (m, b[0])
    if mode == 'rel':
        d = b[0] - 256 if b[0] >= 128 else b[0]
        return '%s $%04X' % (m, (pc + 2 + d) & 0xFFFF)
    raise ValueError(mode)


class Rom:
    """MMC1 PRG ROM: 16 banks x 16 KiB.  Code location = (bank, addr): addr >= $C000 -> bank 15 (fixed)."""

    def __init__(self, path):
        data = open(path, 'rb').read()
        assert data[:4] == b'NES\x1a'
        self.nbanks = data[4]
        assert data[5] == 0 and (data[6] >> 4) | (data[7] & 0xF0) == 1, 'expects MMC1 with CHR RAM'
        self.prg = data[16:16 + self.nbanks * 0x4000]

    def off(self, bank, addr):
        if addr >= 0xC000:
            return (self.nbanks - 1) * 0x4000 + (addr - 0xC000)
        assert 0x8000 <= addr < 0xC000, hex(addr)
        return bank * 0x4000 + (addr - 0x8000)

    def byte(self, bank, addr):
        return self.prg[self.off(bank, addr & 0xFFFF)]

    def word(self, bank, addr):
        return self.byte(bank, addr) | (self.byte(bank, addr + 1) << 8)

    def decode(self, bank, addr):
        """(op, operand list, length) at (bank, addr).  Operand bytes beyond $FFFF wrap like FCEUX's PC."""
        op = self.byte(bank, addr)
        o = OPS[op]
        n = o['length']
        ops = []
        for i in range(1, n):
            a = (addr + i) & 0xFFFF
            if a < 0x8000:
                ops.append(None)          # operand fetched from non-ROM: caller must treat as unknown
            elif addr < 0xC000 <= a:
                ops.append(self.byte(15, a))   # crossing from switchable into fixed bank
            else:
                ops.append(self.byte(bank if a < 0xC000 else 15, a))
        return op, ops, n

    def text(self, bank, addr):
        op, b, n = self.decode(bank, addr)
        if None in b:
            return '%02X ??' % op
        return fmt(op, b, addr)
