"""Local lemmas that do not need the whole-program fixpoint.

(1) L-HIT: path exploration of bank 11 $A59D-$A5FE with RAM[$1C] = v for all 256 v (registers concrete when derived
    from constants or $1C; branches on unknown data fork): the set of X values with which $A5A6 (LDA $0420,X) can
    execute, and the instructions that can write $B4 inside the routine.
(2) L-1C-LOCAL: for each instruction that read $1C in a REAL replay (tools/proof/data/1c_readers.json, or recordings
    made by pfrec.py), the local control-flow graph
    decoded from ROM (branches / JMP abs followed; JSR treated as returning to the next instruction; RTS, RTI,
    JMP (ind), BRK end a path) restricted to a window around the reader; strongly connected components containing the
    reader are loops; for each, exit_sets() gives, for all 256 values of $1C, whether the loop is left (and where).
usage: local_lemmas.py ROM.nes [--readers READERS.json | --recordings PREFIX [PREFIX ...]] [--check EXPECTED.json]
                       [--out RESULT.json]
  --readers     reader list (default: tools/proof/data/1c_readers.json)
  --recordings  PREFIX_r.npy files written by pfrec.py (needs numpy); replaces --readers
  --check       compare the result with EXPECTED.json (e.g. tools/proof/data/local_lemmas.expected.json); exit 1 if
                different
  --out         write the result as JSON (nothing is written without it)
Reads the ROM only (no emulator). Importing this module has no side effects."""
import os, sys, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from m6502 import OPS  # noqa: E402
import lemmas  # noqa: E402
from lemmas import exit_sets, describe_set  # noqa: E402

rom = None   # m6502.Rom, set in main()


def ba(off):
    b = off // 0x4000
    return b, (0xC000 if b == 15 else 0x8000) + off % 0x4000


def succs(n):
    b, p = n
    op, ops, ln = rom.decode(b, p)
    o = OPS[op]
    nb = lambda a: (b if a < 0xC000 else 15, a & 0xFFFF)
    k = o['kind']
    if k in ('rts', 'rti', 'brk', 'kil', 'jmpi'):
        return []
    if k == 'jmp':
        return [nb(ops[0] | ops[1] << 8)]
    if k == 'branch':
        d = ops[0] - 256 if ops[0] >= 128 else ops[0]
        return [nb(p + 2 + d), nb(p + 2)]
    return [nb(p + ln)]


def local_sccs(start, radius=0x180):
    lo, hi = start[1] - radius, start[1] + radius
    nodes = set(); todo = [start]; edges = collections.defaultdict(set)
    while todo:
        n = todo.pop()
        if n in nodes or not (lo <= n[1] <= hi) or n[1] < 0x8000:
            continue
        nodes.add(n)
        for m in succs(n):
            if lo <= m[1] <= hi:
                edges[n].add(m); todo.append(m)
    # nodes that can reach start and are reachable from start
    rev = collections.defaultdict(set)
    for a, bs in edges.items():
        for b_ in bs:
            rev[b_].add(a)
    back = set(); todo = [start]
    while todo:
        n = todo.pop()
        if n in back:
            continue
        back.add(n)
        todo.extend(rev[n])
    comp = nodes & back
    if start not in edges or not any(start in rev[x] or x == start for x in comp if x in rev[start]):
        pass
    loop = comp if any(start in edges[x] for x in comp) else set()
    return loop


def hit_check():
    def explore(v):
        seen = set(); visits = set(); b4w = set()
        todo = [((11, 0xA59D), None, None, None, None, None)]
        while todo:
            item = todo.pop()
            if item in seen:
                continue
            seen.add(item)
            pc, A, X, Z, N, C = item
            b, p = pc
            if p == 0xA5A6:
                visits.add(X)
            op, ops, ln = rom.decode(b, p)
            o = OPS[op]; mn, mode = o['mnem'], o['mode']
            nxt = (b, p + ln)
            if mode in ('zp', 'abs') and o['kind'] in ('store', 'rmw') and (ops[0] | ((ops[1] << 8) if len(ops) > 1 else 0)) == 0xB4:
                b4w.add('%X:%04X %s' % (b, p, rom.text(b, p)))
            if mn == 'LDX' and mode == 'imm':
                X = ops[0]; Z = X == 0; N = X >> 7
            elif mn == 'LDX':
                X = None; Z = N = None
            elif mn == 'LDA' and mode == 'zp' and ops[0] == 0x1C:
                A = v; Z = A == 0; N = A >> 7
            elif mn in ('AND', 'ORA', 'EOR') and mode == 'imm':
                A = None if A is None else (A & ops[0] if mn == 'AND' else A | ops[0] if mn == 'ORA' else A ^ ops[0])
                Z = None if A is None else A == 0; N = None if A is None else A >> 7
            elif mn in ('DEX', 'INX'):
                X = None if X is None else (X + (1 if mn == 'INX' else -1)) & 0xFF
                Z = None if X is None else X == 0; N = None if X is None else X >> 7
            elif mn == 'CPX' and mode == 'imm':
                if X is None:
                    Z = N = C = None
                else:
                    t = (X - ops[0]) & 0xFF; Z = t == 0; N = t >> 7; C = X >= ops[0]
            elif mn in ('CLC', 'SEC'):
                C = (mn == 'SEC')
            elif mn in ('STA', 'STX', 'STY'):
                pass
            elif o['kind'] == 'branch':
                flag = {'BPL': N, 'BMI': N, 'BCC': C, 'BCS': C, 'BNE': Z, 'BEQ': Z}[mn]
                d = ops[0] - 256 if ops[0] >= 128 else ops[0]
                tgt = (b, (p + 2 + d) & 0xFFFF)
                want = 1 if mn in ('BMI', 'BCS', 'BEQ') else 0
                if flag is None:
                    todo.append((tgt, A, X, Z, N, C)); todo.append((nxt, A, X, Z, N, C)); continue
                nxt = tgt if int(flag) == want else nxt
            elif mn == 'RTS' or o['kind'] == 'jmpi':
                continue
            elif mn in ('LDA', 'LDY', 'TAY', 'ADC', 'SBC', 'CMP', 'CPY') or (mn in ('AND', 'ORA', 'EOR') and mode != 'imm'):
                if mn in ('LDA', 'ADC', 'SBC', 'AND', 'ORA', 'EOR'):
                    A = None
                Z = N = None
                if mn in ('ADC', 'SBC', 'CMP', 'CPY'):
                    C = None
            else:
                raise RuntimeError('unexpected %s at %04X' % (mn, p))
            todo.append((nxt, A, X, Z, N, C))
        return tuple(sorted(visits, reverse=True)), tuple(sorted(b4w))
    groups = collections.defaultdict(list)
    for v in range(256):
        groups[explore(v)].append(v)
    return {('slots %s; $B4 writers in routine %s' % (list(k[0]), list(k[1]))): describe_set(vals) for k, vals in groups.items()}


def parse_hex_loc(k):
    b, a = k.split(':')
    return int(b, 16), int(a, 16)


def load_readers(args):
    if '--recordings' in args:
        import numpy as np
        i = args.index('--recordings') + 1
        prefixes = []
        while i < len(args) and not args[i].startswith('--'):
            prefixes.append(args[i]); i += 1
        readers = set()
        for pre in prefixes:
            r = np.load(pre + '_r.npy')
            for key, fr in r:
                key = int(key); iid, addr = key >> 16, key & 0xFFFF
                if iid < 0x80000 and addr == 0x1C:
                    readers.add(ba(iid))
        return readers
    path = args[args.index('--readers') + 1] if '--readers' in args else \
        os.path.join(HERE, '..', 'data', '1c_readers.json')
    return set(parse_hex_loc(k) for k in json.load(open(path))['readers'])


def main(argv):
    global rom
    if not argv or argv[0].startswith('--'):
        raise SystemExit(__doc__)
    rom = lemmas.set_rom(argv[0])
    out = {'L-HIT': hit_check()}
    print(json.dumps(out['L-HIT'], indent=1))
    readers = load_readers(argv)
    loops = []
    for rd in sorted(readers):
        op = rom.byte(*rd)
        if OPS[op]['kind'] not in ('load',):
            continue
        comp = local_sccs(rd)
        if not comp:
            loops.append({'reader': '%X:%04X %s' % (rd[0], rd[1], rom.text(*rd)), 'loop': None})
            continue
        es = exit_sets(comp, rd, 0x1C)
        kinds = collections.defaultdict(list)
        for v, o in es.items():
            kinds[o if o[0] != 'exit' else ('exit', '%X:%04X->%X:%04X' % (o[1][0] + o[1][1]))].append(v)
        desc = {}
        for k, vals in kinds.items():
            key = ('exit via ' + k[1]) if k[0] == 'exit' else ('stay' if k[0] == 'stay' else 'unknown: ' + k[1])
            desc[key] = describe_set(vals)
        loops.append({'reader': '%X:%04X %s' % (rd[0], rd[1], rom.text(*rd)),
                      'loop': '%X:%04X..%04X (%d instr)' % (min(comp)[0], min(comp)[1], max(comp)[1], len(comp)),
                      'exit_condition': desc})
    out['L-1C-LOCAL'] = loops
    for l in loops:
        print(json.dumps(l))
    rc = 0
    if '--check' in argv:
        exp = json.load(open(argv[argv.index('--check') + 1]))
        same = json.loads(json.dumps(out)) == exp
        print('local_lemmas: result equals %s: %s' % (os.path.basename(argv[argv.index('--check') + 1]), same))
        rc = 0 if same else 1
    if '--out' in argv:
        with open(argv[argv.index('--out') + 1], 'w') as f:
            json.dump(out, f, indent=1)
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
