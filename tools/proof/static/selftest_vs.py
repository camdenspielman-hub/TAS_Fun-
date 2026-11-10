"""Soundness test of vs.py abstract ops against the concrete FCEUX semantics (c_* transcribed from x6502.cpp).
Exhaustive for singleton inputs (all 256x256x2 for ADC/SBC/CMP), random small/large sets otherwise."""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vs  # noqa: E402
from vs import *  # noqa: E402,F401,F403
bad = 0
def chk(cond, msg):
    global bad
    if not cond:
        bad += 1
        if bad < 20: print('FAIL', msg)
def main():
    random.seed(1)
    # exhaustive singletons
    for a in range(256):
        for m in range(256):
            for ci in (0, 1):
                for op, f in (('ADC', c_adc), ('SBC', c_sbc)):
                    r, co, ov = f(a, m, ci)
                    R, CM, VM = a_binop(op, c(a), c(m), F1 if ci else F0)
                    chk(R >> r & 1 and CM & (F1 if co else F0) and VM & (F1 if ov else F0), (op, a, m, ci))
            d, co = c_cmp(a, m)
            D, CM = a_cmp(c(a), c(m))
            chk(D >> d & 1 and CM & (F1 if co else F0), ('CMP', a, m))
            for op in ('AND', 'ORA', 'EOR'):
                R, _, _ = a_binop(op, c(a), c(m), F0)
                v = a & m if op == 'AND' else a | m if op == 'ORA' else a ^ m
                chk(R >> v & 1, (op, a, m))
                chk(a_map(op, c(a), m) >> v & 1, ('map', op, a, m))
        for op in ('ASL', 'LSR', 'ROL', 'ROR'):
            for ci in (0, 1):
                R, CM = a_shift(op, c(a), F1 if ci else F0)
                if op == 'ASL': r, co = c_asl(a)
                elif op == 'LSR': r, co = c_lsr(a)
                elif op == 'ROL': r, co = c_rol(a, ci)
                else: r, co = c_ror(a, ci)
                chk(R >> r & 1 and CM & (F1 if co else F0), (op, a, ci))
        for k in range(256):
            chk(add_const(c(a), k) >> ((a + k) & 255) & 1, ('addc', a, k))
    # random sets
    def rset(n):
        return from_iter(random.randrange(256) for _ in range(n))
    for it in range(3000):
        A = rset(random.choice((1, 2, 5, 40, 200))); M = rset(random.choice((1, 3, 20, 256)))
        CI = random.choice((F0, F1, FB))
        ea, em = elems(A), elems(M)
        a, m = random.choice(ea), random.choice(em)
        ci = random.choice([v for v in (0, 1) if CI & (1 << v)])
        for op, f in (('ADC', c_adc), ('SBC', c_sbc)):
            r, co, ov = f(a, m, ci); R, CM, VM = a_binop(op, A, M, CI)
            chk(R >> r & 1 and CM & (F1 if co else F0) and VM & (F1 if ov else F0), ('rand', op))
        d, co = c_cmp(a, m); D, CM = a_cmp(A, M)
        chk(D >> d & 1 and CM & (F1 if co else F0), 'rand cmp')
        for op in ('AND', 'ORA', 'EOR'):
            R, _, _ = a_binop(op, A, M, CI)
            v = a & m if op == 'AND' else a | m if op == 'ORA' else a ^ m
            chk(R >> v & 1, ('rand', op))
        chk(z_mask(c(a)) & (F1 if a == 0 else F0), 'z'); chk(n_mask(c(a)) & (F1 if a & 0x80 else F0), 'n')
    print('selftest_vs: failures =', bad)
    return bad


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
