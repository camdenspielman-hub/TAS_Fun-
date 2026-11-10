"""Lemma queries over a sound static-analysis result (sa.py pickle).

  writers(addr)   every instruction that may write RAM byte addr (mirrors folded), with address-set size and the
                  value set it may write there; plus the module contract (A-SND) and interrupt pushes if relevant
  readers(addr)   every instruction that may read addr
  loops_reading(addr)   strongly connected components of the intra-activation CFG that contain a reader of addr,
                  with every exit edge; for each reader the exit condition is computed by exhaustive concrete
                  evaluation of the loop path for all 256 values of the byte (see exit_sets)
usage: lemmas.py ROM.nes result.pkl [addr ...]   (result.pkl = a pf_static sa.py result; not part of this kit)
As a module (used by local_lemmas.py): call set_rom(path) first; importing has no side effects."""
import os, sys, pickle, collections, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m6502 import Rom, OPS  # noqa: E402
import vs  # noqa: E402

rom = None   # the ROM view (m6502.Rom); set by set_rom()


def set_rom(path):
    global rom
    rom = Rom(path)
    return rom


def bank_of(pc, mb):
    return 15 if pc >= 0xC000 else mb


class Result:
    def __init__(self, path):
        self.r = pickle.load(open(path, 'rb'))
        self.WR = self.r['WR']; self.RD = self.r['RD']
        self.SND_W = self.r.get('SND_W', frozenset())
        self.succ = collections.defaultdict(set)
        for a, b in self.r['EDGES']:
            self.succ[a].add(b)

    def writers(self, addr):
        out = []
        for (cb, pc), rec in sorted(self.WR.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
            hit = 0; nadd = 0; anyw = False
            for a, v in rec.items():
                if a == 'ANY':
                    anyw = True; hit |= v
                elif a == 'STACK':
                    if 0x100 <= addr < 0x200:
                        hit |= v; nadd += 1
                elif isinstance(a, int) and a < 0x2000:
                    nadd += 1
                    if (a & 0x7FF) == addr:
                        hit |= v
            if hit or (anyw):
                ram_addrs = [a for a in rec if isinstance(a, int) and a < 0x2000]
                out.append(dict(where='%X:%04X' % (cb, pc), text=rom.text(cb, pc), nram=len(ram_addrs),
                                values=vs.fmt(hit, 16), any=anyw))
        extra = []
        if addr in self.SND_W:
            extra.append('A-SND module (bank 12 $8000/$8003): any value')
        if 0x100 <= addr < 0x200:
            extra.append('interrupt entry pushes (page 1)')
        return out, extra

    def readers(self, addr):
        out = []
        for (cb, pc), s in sorted(self.RD.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
            if any(isinstance(a, int) and a < 0x2000 and (a & 0x7FF) == addr for a in s) or 'ANY' in s:
                out.append(('%X:%04X' % (cb, pc), rom.text(cb, pc), 'ANY' in s))
        return out

    # ---------------- loops
    def sccs(self):
        """Tarjan over instruction nodes (cb, pc) using intra-activation edges"""
        index = {}; low = {}; onst = set(); st = []; res = []; idx = [0]
        nodes = set(self.succ) | {b for v in self.succ.values() for b in v}
        sys.setrecursionlimit(100000)

        def strong(v):
            index[v] = low[v] = idx[0]; idx[0] += 1; st.append(v); onst.add(v)
            for w in self.succ.get(v, ()):
                if w not in index:
                    strong(w); low[v] = min(low[v], low[w])
                elif w in onst:
                    low[v] = min(low[v], index[w])
            if low[v] == index[v]:
                comp = []
                while True:
                    w = st.pop(); onst.discard(w); comp.append(w)
                    if w == v:
                        break
                if len(comp) > 1 or v in self.succ.get(v, ()):
                    res.append(frozenset(comp))
        for v in sorted(nodes):
            if v not in index:
                strong(v)
        return res

    def loops_reading(self, addr):
        readers = {}
        for (cb, pc), s in self.RD.items():
            if any(isinstance(a, int) and a < 0x2000 and (a & 0x7FF) == addr for a in s):
                readers[(cb, pc)] = rom.text(cb, pc)
        out = []
        for comp in self.sccs():
            rs = [r for r in comp if r in readers]
            if not rs:
                continue
            exits = []
            for v in comp:
                for w in self.succ.get(v, ()):
                    if w not in comp:
                        exits.append((v, w))
            out.append(dict(nodes=sorted(comp), readers=sorted(rs), exits=sorted(exits)))
        return out, readers


# ---------------- exhaustive concrete evaluation of a loop path as a function of one RAM byte
def exit_sets(comp, start, addr, maxsteps=200):
    """For every value v of RAM[addr], execute concretely from `start` (registers unknown) following the loop's
    instructions; return {v: outcome} where outcome is ('exit', (from, to)) when control leaves `comp`,
    ('stay',) when it reaches `start` again or a JSR whose return stays in the loop, or ('unknown', reason)."""
    res = {}
    for v in range(256):
        A = X = Y = None; C = Z = N = V = None
        pc = start; cb = start[0]
        out = None
        for step in range(maxsteps):
            b, p = pc
            if step > 0 and pc == start:
                out = ('stay',); break
            op, ops, ln = rom.decode(b, p)
            o = OPS[op]; mn, mode = o['mnem'], o['mode']
            nxt = (b if p + ln < 0xC000 else 15, (p + ln) & 0xFFFF)
            def rd(a):
                if a == addr:
                    return v
                if a >= 0x8000:
                    return rom.byte(b if a < 0xC000 else 15, a)
                return None
            def opval():
                if mode == 'imm':
                    return ops[0]
                if mode == 'zp':
                    return rd(ops[0])
                if mode == 'abs':
                    return rd(ops[0] | ops[1] << 8)
                if mode in ('absx', 'absy'):
                    i = X if mode == 'absx' else Y
                    if i is None:
                        return None
                    return rd(((ops[0] | ops[1] << 8) + i) & 0xFFFF)
                return None
            if mn in ('LDA', 'LDX', 'LDY'):
                m = opval()
                if mn == 'LDA': A = m
                elif mn == 'LDX': X = m
                else: Y = m
                Z = None if m is None else (m == 0); N = None if m is None else (m >> 7)
            elif mn in ('AND', 'ORA', 'EOR'):
                m = opval()
                if A is None or m is None:
                    # AND with 0 gives 0 regardless
                    A = 0 if (mn == 'AND' and (m == 0 or A == 0)) else None
                else:
                    A = A & m if mn == 'AND' else A | m if mn == 'ORA' else A ^ m
                Z = None if A is None else (A == 0); N = None if A is None else (A >> 7)
            elif mn in ('CMP', 'CPX', 'CPY'):
                r = {'CMP': A, 'CPX': X, 'CPY': Y}[mn]; m = opval()
                if r is None or m is None:
                    Z = N = C = None
                else:
                    t, C = vs.c_cmp(r, m); Z = (t == 0); N = t >> 7
            elif mn in ('LSR', 'ASL', 'ROL', 'ROR') and mode == 'acc':
                if A is None or (mn in ('ROL', 'ROR') and C is None):
                    A = None; C = None
                else:
                    A, C = {'LSR': lambda: vs.c_lsr(A), 'ASL': lambda: vs.c_asl(A), 'ROL': lambda: vs.c_rol(A, C), 'ROR': lambda: vs.c_ror(A, C)}[mn]()
                Z = None if A is None else (A == 0); N = None if A is None else (A >> 7)
            elif mn in ('CLC', 'SEC'):
                C = 1 if mn == 'SEC' else 0
            elif mn in ('ADC', 'SBC'):
                m = opval()
                if A is None or m is None or C is None:
                    A = None; C = None; Z = N = None
                else:
                    A, C, V = (vs.c_adc if mn == 'ADC' else vs.c_sbc)(A, m, C); Z = (A == 0); N = A >> 7
            elif mn in ('TAX', 'TAY', 'TXA', 'TYA'):
                s_, d_ = {'TAX': ('A', 'X'), 'TAY': ('A', 'Y'), 'TXA': ('X', 'A'), 'TYA': ('Y', 'A')}[mn]
                val = {'A': A, 'X': X, 'Y': Y}[s_]
                if d_ == 'A': A = val
                elif d_ == 'X': X = val
                else: Y = val
                Z = None if val is None else (val == 0); N = None if val is None else (val >> 7)
            elif mn in ('INX', 'INY', 'DEX', 'DEY'):
                r = X if mn[-1] == 'X' else Y
                r = None if r is None else (r + (1 if mn[0] == 'I' else -1)) & 0xFF
                if mn[-1] == 'X': X = r
                else: Y = r
                Z = None if r is None else (r == 0); N = None if r is None else (r >> 7)
            elif mn in ('STA', 'STX', 'STY', 'NOP'):
                if mode in ('zp', 'abs') and (ops[0] | ((ops[1] << 8) if len(ops) > 1 else 0)) == addr:
                    out = ('unknown', 'stores to the polled byte'); break
            elif mn in ('INC', 'DEC') and mode in ('zp', 'abs'):
                if (ops[0] | ((ops[1] << 8) if len(ops) > 1 else 0)) == addr:
                    out = ('unknown', 'modifies the polled byte'); break
                Z = N = None
            elif o['kind'] == 'branch':
                flag = {'BPL': N, 'BMI': N, 'BVC': V, 'BVS': V, 'BCC': C, 'BCS': C, 'BNE': Z, 'BEQ': Z}[mn]
                if flag is None:
                    out = ('unknown', 'branch %X:%04X on unknown flag' % (b, p)); break
                want = 1 if mn in ('BMI', 'BVS', 'BCS', 'BEQ') else 0
                taken = (int(flag) == want)
                d = ops[0] - 256 if ops[0] >= 128 else ops[0]
                tgt = (b if p < 0xC000 else 15, (p + 2 + d) & 0xFFFF)
                nxt = tgt if taken else nxt
            elif mn == 'JMP' and mode == 'abs':
                t = ops[0] | ops[1] << 8
                nxt = (b if t < 0xC000 else 15, t)
            elif mn == 'JSR':
                # the callee runs; registers become unknown (conservative); control returns to the next instruction
                A = X = Y = None; C = Z = N = V = None
            else:
                out = ('unknown', 'unsupported %s at %X:%04X' % (mn, b, p)); break
            if nxt not in comp:
                out = ('exit', (pc, nxt)); break
            pc = nxt
        if out is None:
            out = ('unknown', 'step limit')
        res[v] = out
    return res


def describe_set(vals):
    """compact description of a set of byte values: '$1C mod m in R' when the set is exactly a union of residue
    classes mod a power of two m (smallest such m), else the explicit list"""
    s = set(vals)
    if not s:
        return 'never'
    if len(s) == 256:
        return 'always'
    for k in range(1, 9):
        m = 1 << k
        res = {v % m for v in s}
        if s == {v for v in range(256) if v % m in res}:
            return 'value mod %d in {%s}' % (m, ','.join(str(x) for x in sorted(res)))
    return 'in {%s}' % ','.join('%02X' % x for x in sorted(s))


if __name__ == '__main__':
    set_rom(sys.argv[1])
    R = Result(sys.argv[2])
    for a in sys.argv[3:]:
        addr = int(a, 16)
        w, extra = R.writers(addr)
        print('== writers of $%03X: %d instructions %s' % (addr, len(w), extra))
        for x in w:
            print('   %(where)s  %(text)-18s nram=%(nram)4d values=%(values)s %(any)s' % x)
