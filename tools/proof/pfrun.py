#!/usr/bin/env python3
"""pfrun.py - run the certified search (pfsearch.bfs) on the pilot problems and write certificates (pf_search).

usage:
  pfrun.py menu  OPEN [OPEN ...]          --rom ROM --lib librm2pf.so --movie MOVIE.fm2 --out DIR [--pauses JSON]
  pfrun.py menuP OPEN [BOUND_EXTRA]       --rom ROM --lib librm2pf.so --movie MOVIE.fm2 --out DIR [--pauses JSON]
  pfrun.py walk  T K DEADBITS C27 [MAXD]  --rom ROM --lib librm2pf.so --movie MOVIE.fm2 --out DIR

  menu   full search of a pause menu: earliest frame at whose end $A9 == target weapon and $FD == 0 (the closing START
         frame: bank 13 $92C9 STX $A9, then $92D3 STX $FD with X = 0). OPEN = frame of the opening START; the root is
         the state before frame OPEN+1. The pause list (open, close, weapons) is data/v63_pauses.json by default.
  menuP  the same with SOUND pruning by lemma L-menu (see below); BOUND = close - open (+ BOUND_EXTRA).
  walk   last K frames of a capsule touch ($0400 == $26 or $2C == $0B at the end of frame T); root = state before
         frame T-K+1; DEADBITS = pad bits treated as dead (hex), proven per transition by the taint tracker;
         C27 = 1 canonicalises all of $27 (new presses), also proven per transition.
Every root comes from ONE continuous replay of MOVIE from power-on in this fresh process. Certificates and logs are
written to DIR as cert_<label>.json and <label>.log (DIR must not be inside the repository's tools/).

Lemma L-menu (bank 13 pause input loop $91EF-$927E, read in the ROM):
  Let s be a frame-boundary state whose CPU is in the wait loop of $C0AB (PC $C0BA/$C0BC) called from $927B (stack
  bytes S+1,S+2 = $7D,$92). From s, every later loop iteration needs a new NMI (C0AB clears $1D, only the NMI sets
  it), i.e. at most one iteration per frame; an iteration does at most ONE of {cursor step up/down (with skipping of
  unowned rows), page toggle (START at row 0), E-tank (START at row 7), close (START at another row)}, and the close
  writes $A9 = row-1+6*page. Hence the goal ($A9 == target, $FD == 0) cannot hold before delta+1 frames, delta = the
  shortest path from ($FD,$FE) to the target row in the cursor graph defined by $9A/$9B (owned masks) and table $9670.
  Pruning: a state at depth d with d + h > BOUND is removed. The checker recomputes h with its own code. The lemma's
  writer assumption is A-MENU-CLOSURE (docs/proof-standards.md); the search also checks the lemma dynamically on every
  explored transition (delta drops by at most 1 per frame; a goal child comes only from delta 0)."""
import sys, os, json, struct

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pfsearch import *  # noqa: E402,F401,F403
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))

K_MENU = A_ | B_ | S_ | L_ | R_          # 0xC7: pad bits the pause menu never uses (proved per transition)
CLASSES_MENU = [0, U_, D_, U_ | D_, T_, T_ | U_, T_ | D_, T_ | U_ | D_]
CANON_MENU = {0x23: K_MENU, 0x25: K_MENU, 0x27: K_MENU}
OPTS = ('--rom', '--lib', '--movie', '--out', '--pauses')


def parse(argv):
    pos, opt = [], {}
    i = 0
    while i < len(argv):
        if argv[i].startswith('--'):
            if argv[i] not in OPTS or i + 1 >= len(argv):
                raise SystemExit('bad option %s\n%s' % (argv[i], __doc__))
            opt[argv[i]] = argv[i + 1]; i += 2
        else:
            pos.append(argv[i]); i += 1
    for k in ('--rom', '--lib', '--movie', '--out'):
        if k not in opt:
            raise SystemExit('missing %s\n%s' % (k, __doc__))
    if not pos or pos[0] not in ('menu', 'menuP', 'walk'):
        raise SystemExit(__doc__)
    return pos[0], pos[1:], opt


class Run:
    def __init__(self, opt):
        self.opt = opt
        os.makedirs(opt['--out'], exist_ok=True)
        self.e = emu(opt['--lib'], opt['--rom'])
        assert self.e.pf, '--lib must be the analysis library librm2pf.so (taint tracker)'
        self.pads = load_movie(opt['--movie'])
        mp = os.path.abspath(opt['--movie'])
        self.movie_file = os.path.relpath(mp, REPO) if mp.startswith(REPO + os.sep) else mp
        self.movie_sha256 = hashlib.sha256(open(mp, 'rb').read()).hexdigest()
        self.movie_name = os.path.basename(mp)

    def roots(self, frames):
        return root_states(self.e, frames, self.pads)

    def root_info(self, f):
        return {'movie': self.movie_name, 'movie_file': self.movie_file, 'movie_sha256': self.movie_sha256,
                'frame_before': f, 'how': 'power-on + pads 0..%d of the movie, one continuous replay in a fresh '
                                          'process' % (f - 1)}

    def logger(self, label):
        logf = open(os.path.join(self.opt['--out'], '%s.log' % label), 'w')

        def log(s):
            print(s, flush=True); logf.write(s + '\n'); logf.flush()
        return log

    def save(self, cert, label, log):
        path = save_cert(cert, os.path.join(self.opt['--out'], 'cert_%s.json' % label))
        log('certificate: %s' % path)


def pauses(opt):
    p = opt.get('--pauses') or os.path.join(HERE, 'data', 'v63_pauses.json')
    return {x['open']: x for x in json.load(open(p))}


def run_menu(args, opt):
    R = Run(opt); P = pauses(opt)
    opens = [int(x) for x in args]
    roots = R.roots([o + 1 for o in opens])
    for o in opens:
        p = P[o]; root = roots[o + 1]
        target = p['w1']
        assert target != p['w0']
        goal = Goal(eq=[(0xA9, target), (0xFD, 0)])
        label = 'menu%d' % o
        log = R.logger(label)
        log('pause open %d close %d (movie) weapon %d -> %d, movie inputs %s' % (o, p['close'], p['w0'], target,
                                                                              p['seq']))
        cert = bfs(R.e, root, goal, CLASSES_MENU, K_MENU, CANON_MENU, max_depth=(p['close'] - o) + 3, label=label,
                   log=log, root_info=R.root_info(o + 1))
        finish_menu(R, cert, label, o, p, log)


def finish_menu(R, cert, label, o, p, log):
    r = cert['result']
    if r['goal_depth'] is not None:
        earliest = o + r['goal_depth']      # frame index of the closing START frame
        log('RESULT %s: earliest close frame %d (movie %d, saving %d); witness %s; status %s; %d taint failures; '
            'pruned %d; lemma-checked transitions %d, violations %d' % (
                label, earliest, p['close'], p['close'] - earliest,
                ' '.join(rm2.pad_to_fm2(x)[2:5].replace('.', '') or '-' for x in r['witness']), cert['proof_status'],
                cert['n_taint_failures'], cert['pruned_states'], cert['lemma_checked_transitions'],
                len(cert['lemma_violations'])))
        cert['result']['earliest_close_frame_movie'] = earliest
        cert['result']['movie_close_frame'] = p['close']
    else:
        log('RESULT %s: no close within %d frames' % (label, r['last_goal_free_depth']))
    R.save(cert, label, log)


# ---------------------------------------------------------------------------------------------- lemma L-menu
def cursor_delta(TAB, ram, target):
    """Shortest number of loop iterations (steps + page toggles) from ($FD,$FE) to the target's row; None = unreachable;
    -1 = state outside the lemma's domain."""
    r, p = ram[0xFD], ram[0xFE]
    if p not in (0, 1):
        return -1
    xmax = 7 if p == 0 else 6
    if r > xmax:
        return -1
    m = [((ram[0x9A] << 1) | 0x41) & 0xFF, ((ram[0x9B] << 3) | (ram[0x9A] >> 5)) & 0xFF]
    pt = 0 if target <= 5 else 1
    rt = target + 1 - 6 * pt

    def step(r, p, dr):
        xm = 7 if p == 0 else 6
        for _ in range(16):
            r = r + dr
            if r > xm: r = 0
            if r < 0: r = xm
            if r == 0 or (TAB[r] & m[p]):
                return r
        return r
    dist = {(r, p): 0}
    q = [(r, p)]
    while q:
        nq = []
        for (a, b) in q:
            if (a, b) == (rt, pt):
                return dist[(a, b)]
            nb = [(step(a, b, 1), b), (step(a, b, -1), b)]
            if a == 0:
                nb.append((0, 1 - b))
            for x in nb:
                if x not in dist:
                    dist[x] = dist[(a, b)] + 1; nq.append(x)
        q = nq
    return None


def in_input_wait(ident, st):
    pc = struct.unpack('<H', ident.field(st, 'CPU', 'PC'))[0]
    sp = ident.field(st, 'CPU', 'S')[0]
    if pc not in (0xC0BA, 0xC0BC):
        return False
    return ident.ram(st, 0x100 + ((sp + 1) & 0xFF)) == 0x7D and ident.ram(st, 0x100 + ((sp + 2) & 0xFF)) == 0x92


def run_menuP(args, opt):
    o = int(args[0]); extra = int(args[1]) if len(args) > 1 else 0
    R = Run(opt); P = pauses(opt)
    ROMV = rm2.Rom(opt['--rom'])
    TAB = [ROMV.byte(13, 0x9670 + y) for y in range(8)]
    assert ROMV.byte(15, 0xC0BA) == 0xA5 and ROMV.byte(15, 0xC0BB) == 0x1D and ROMV.byte(15, 0xC0BC) == 0xF0
    assert ROMV.byte(13, 0x927B) == 0x20 and ROMV.byte(13, 0x927C) == 0xAB and ROMV.byte(13, 0x927D) == 0xC0
    p = P[o]
    target = p['w1']
    BOUND = p['close'] - o + extra
    root = R.roots([o + 1])[o + 1]
    goal = Goal(eq=[(0xA9, target), (0xFD, 0)])

    def h_menu(ident, st):
        if not in_input_wait(ident, st):
            return 0
        dl = cursor_delta(TAB, ident.ram(st, 0, 0x100), target)
        if dl == -1:
            return 0
        if dl is None:
            return 10 ** 6
        return dl + 1

    def prune(ident, st, depth):
        """L-menu: prune iff depth + h_menu(state) > BOUND"""
        return depth + h_menu(ident, st) > BOUND

    def lemma(ident, parent, child, child_goal):
        if not in_input_wait(ident, parent):
            return None
        dp = cursor_delta(TAB, ident.ram(parent, 0, 0x100), target)
        if dp in (-1, None):
            return None
        if child_goal:
            return None if dp == 0 else 'goal reached from delta %d' % dp
        if in_input_wait(ident, child):
            dc = cursor_delta(TAB, ident.ram(child, 0, 0x100), target)
            if dc not in (-1, None) and dc < dp - 1:
                return 'delta dropped %d -> %d' % (dp, dc)
        return None
    label = 'menuP%d' % o
    log = R.logger(label)
    log('pause open %d close %d (movie) weapon %d -> %d, movie inputs %s; BOUND depth %d; h(root)=%d' % (
        o, p['close'], p['w0'], target, p['seq'], BOUND, h_menu(Identity(root), root)))
    cert = bfs(R.e, root, goal, CLASSES_MENU, K_MENU, CANON_MENU, max_depth=BOUND, label=label, log=log, prune=prune,
               lemma=lemma, prune_spec={'type': 'menu_cursor_v1', 'target': target, 'bound': BOUND},
               root_info=R.root_info(o + 1))
    finish_menu(R, cert, label, o, p, log)


def run_walk(args, opt):
    T, K = int(args[0]), int(args[1])
    dead = int(args[2], 16); c27 = int(args[3])
    MAXD = int(args[4]) if len(args) > 4 else K
    classes = sorted(set(p & ~dead & 0xFF for p in range(256)))
    canon = {}
    if dead:
        canon[0x23] = dead; canon[0x25] = dead
    canon[0x27] = 0xFF if c27 else dead
    canon = {a: m for a, m in canon.items() if m}
    R = Run(opt)
    root = R.roots([T - K + 1])[T - K + 1]
    goal = Goal(any_eq=[(0x400, 0x26), (0x2C, 0x0B)])
    label = 'walk%d_k%d_d%02X_c%d' % (T, K, dead, c27)
    log = R.logger(label)
    log('walk: movie touch at end of frame %d; root before frame %d; %d pad classes (dead %02X), canon %s' % (
        T, T - K + 1, len(classes), dead, {'%02X' % a: '%02X' % m for a, m in canon.items()}))
    cert = bfs(R.e, root, goal, classes, dead, canon, max_depth=MAXD, label=label, log=log, track_old=False,
               root_info=R.root_info(T - K + 1))
    r = cert['result']
    if r['goal_depth'] is not None:
        log('RESULT %s: earliest touch at end of frame %d (movie %d, saving %d); status %s; taint failures %d' % (
            label, T - K + r['goal_depth'], T, K - r['goal_depth'], cert['proof_status'], cert['n_taint_failures']))
    else:
        log('RESULT %s: no touch within %d frames; status %s; taint failures %d' % (
            label, r['last_goal_free_depth'], cert['proof_status'], cert['n_taint_failures']))
    R.save(cert, label, log)


if __name__ == '__main__':
    cmd, args, opt = parse(sys.argv[1:])
    {'menu': run_menu, 'menuP': run_menuP, 'walk': run_walk}[cmd](args, opt)
