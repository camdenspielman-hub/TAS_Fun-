# pf_search engine: exhaustive breadth-first search by frame with full-state identity, proven input-class
# reduction and proven canonicalisation of dead RAM bits (taint tracker), writing a checkable certificate.
#
# Semantics. A state is an FCEUX savestate at a frame boundary. One transition = load(state); frame(pad); save().
# Layer d = the set of canonical hashes of the states reachable from the root in exactly d frames.
# Claim certified: for every pad sequence w over ALL 256 pad values with |w| <= D, the goal predicate is false after
# every prefix of w (D = last goal-free depth); plus a witness of length D+1 reaching the goal (if found).
#
# Soundness obligations discharged per transition (state s, class representative a):
#   taint tracker run with the dead bits `canon` of s and the dead pad bits `kin` of a marked symbolic; verdict ok
#   <=> for every s' that differs from s only in canon bits and every pad a' with a' & ~kin == a & ~kin,
#       frame(s', a') differs from frame(s, a) only in canon bits (same canonical hash).
# Hence the canonical hash of a child depends only on (canonical hash of the parent, class of the pad), and BFS over
# class representatives with dedup by canonical hash enumerates exactly the reachable canonical classes.
# Used through pfrun.py (menu / menuP / walk); the checker is pfcheck.py / pfcheck_stream.py, which share no code
# with this file.
import sys, os, time, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pflib import *  # noqa: E402,F401,F403

VERSION = 'pf_search 1.1 (2026-11-07, repository version: root by power-on replay)'


def md5f(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


class Goal:
    """Goal predicate on RAM after a frame: conjunction of byte equalities (addr, value) and inequalities."""

    def __init__(self, eq=(), ne=(), any_eq=()):
        self.eq = [(int(a), int(v)) for a, v in eq]
        self.ne = [(int(a), int(v)) for a, v in ne]
        self.any_eq = [(int(a), int(v)) for a, v in any_eq]

    def __call__(self, ident, st):
        return (all(ident.ram(st, a) == v for a, v in self.eq) and all(ident.ram(st, a) != v for a, v in self.ne)
                and (not self.any_eq or any(ident.ram(st, a) == v for a, v in self.any_eq)))

    def spec(self):
        return {'ram_eq': [[a, v] for a, v in self.eq], 'ram_ne': [[a, v] for a, v in self.ne],
                'ram_any_eq': [[a, v] for a, v in self.any_eq]}

    def addrs(self):
        return sorted(set(a for a, v in self.eq + self.ne + self.any_eq))


def old_projection_key(ident, st):
    """The key of the old menu BFS (menus agent / critic_rules r04): zero page with $1C, $4A, $E0-$FC zeroed."""
    zp = bytearray(ident.ram(st, 0, 0x100))
    zp[0x1C] = 0; zp[0x4A] = 0
    for x in range(0xE0, 0xFD): zp[x] = 0
    return bytes(zp)


def bfs(e, root, goal, classes, kin, canon, max_depth, label, log=print, root_info=None, stop_at_goal=True,
        prune=None, track_old=True, lemma=None, prune_spec=None):
    """Exhaustive BFS. prune(ident, st, depth) -> True removes a state (only for SOUND pruning rules supplied with a
    proof; recorded in the certificate). Returns the certificate dict."""
    ident = Identity(root, canon)
    allowed = {a: m for a, m in canon.items() if m}
    init = bytearray(0x800)
    for a, m in allowed.items():
        init[a] = m
    init = bytes(init)
    for a in goal.addrs():
        assert not allowed.get(a, 0), 'goal reads a canonicalised byte'
    t_start = time.time()
    hroot = ident.h(root)
    layers = [[(hroot, -1, -1)]]
    states = [root]
    failures = []
    stats = []
    goal_hits = []
    pruned_total = 0
    lemma_viol = []
    nlemma = 0
    if goal(ident, root):
        goal_hits = [(0, -1, -1, hroot)]
    d = 0
    while d < max_depth and not goal_hits:
        nxt = {}
        hits = []
        t0 = time.time()
        ntrans = 0
        nlag = 0
        maxinstr = 0
        maxnint = 0
        for i, st in enumerate(states):
            jrb = ident.field(st, 'CTRL', 'JYRB')[0]
            ls = ident.field(st, 'CTRL', 'LSTS')[0]
            for a in classes:
                e.load(st)
                e.taint_begin(init, kin, jrb, ls)
                lag = e.frame(a)
                res, tram = e.taint_end()
                ok, why = taint_verdict(res, tram, allowed)
                ntrans += 1
                nlag += lag
                maxinstr = max(maxinstr, res['ninstr'])
                maxnint = max(maxnint, res['nint'])
                if not ok:
                    failures.append((d, i, a, why))
                ch = e.save()
                hc = ident.h(ch)
                if lemma is not None:
                    nlemma += 1
                    v = lemma(ident, st, ch, goal(ident, ch))
                    if v:
                        lemma_viol.append((d, i, a, v))
                if goal(ident, ch):
                    hits.append((d + 1, i, a, hc))
                    if hc not in nxt:
                        nxt[hc] = (ch, i, a)
                    continue
                if hc not in nxt:
                    nxt[hc] = (ch, i, a)
        if prune:
            before = len(nxt)
            nxt = {h: v for h, v in nxt.items() if any(x[3] == h for x in hits) or not prune(ident, v[0], d + 1)}
            pruned_total += before - len(nxt)
        order = sorted(nxt)
        layers.append([(h, nxt[h][1], nxt[h][2]) for h in order])
        states = [nxt[h][0] for h in order]
        nold = len(set(old_projection_key(ident, s) for s in states)) if track_old else -1
        st_ = dict(depth=d + 1, states=len(order), transitions=ntrans, lag_transitions=nlag, goal_hits=len(hits),
                   taint_failures=sum(1 for f in failures if f[0] == d), old_projection_classes=nold,
                   seconds=round(time.time() - t0, 2), max_instr=maxinstr, max_nmi_per_frame=maxnint)
        stats.append(st_)
        log('%s depth %d: %d states (old-projection classes %d), %d transitions, %d goal hits, %d taint failures, %.1fs'
            % (label, d + 1, len(order), nold, ntrans, len(hits), st_['taint_failures'], st_['seconds']))
        d += 1
        if hits:
            goal_hits = hits
            if stop_at_goal:
                break
    # result
    cert = {
        'version': VERSION, 'label': label,
        'core': {'search_lib': os.path.basename(e.lib_path), 'search_lib_md5': md5f(e.lib_path),
                 'rom_md5': md5f(e.rom_path),
                 'rom_sha256': hashlib.sha256(open(e.rom_path, 'rb').read()).hexdigest()},
        'root': dict(root_info or {}, state_sha256=hashlib.sha256(root).hexdigest(), key_hash=hroot.hex()),
        'identity': {'drop_fields': sorted('%s.%s' % x for x in DROP_FIELDS), 'drop_chunks': sorted(DROP_CHUNKS),
                     'keylen': ident.keylen, 'canon': {('%03X' % a): m for a, m in sorted(allowed.items())}},
        'alphabet': {'classes': list(classes), 'kin': kin,
                     'meaning': 'pad p is represented by the class c with c == p & ~kin'},
        'goal': goal.spec(),
        'prune': (prune.__doc__ if prune else None), 'pruned_states': pruned_total, 'prune_spec': prune_spec,
        'lemma_checked_transitions': nlemma, 'lemma_violations': [[x[0], x[1], x[2], x[3]] for x in lemma_viol[:100]],
        'stats': stats,
        'taint_failures': [[f[0], f[1], f[2], f[3]] for f in failures[:200]],
        'n_taint_failures': len(failures),
        'seconds': round(time.time() - t_start, 1),
    }
    if goal_hits:
        gd = goal_hits[0][0]
        # witness path for the first goal hit (deterministic: smallest hash among hits)
        best = min(goal_hits, key=lambda x: x[3])
        last = layers[gd]
        idx = [k for k, x in enumerate(last) if x[0] == best[3]][0]
        path = []
        dd, k = gd, idx
        while dd > 0:
            h, pi, pad = layers[dd][k]
            path.append(pad)
            k = pi; dd -= 1
        path.reverse()
        cert['result'] = {'goal_depth': gd, 'last_goal_free_depth': gd - 1, 'witness': path,
                          'n_goal_hits_at_goal_depth': len(goal_hits),
                          'claim': 'no pad sequence of length <= %d reaches the goal; a sequence of length %d does'
                                   % (gd - 1, gd)}
        cert['layers'] = [[[h.hex(), pi, pad] for h, pi, pad in L] for L in layers[:gd]]
        cert['goal_layer_hits'] = sorted(set(x[3].hex() for x in goal_hits))
    else:
        cert['result'] = {'goal_depth': None, 'last_goal_free_depth': d,
                          'claim': 'no pad sequence of length <= %d reaches the goal' % d}
        cert['layers'] = [[[h.hex(), pi, pad] for h, pi, pad in L] for L in layers]
    cert['proof_status'] = ('PROVEN-GIVEN-ASSUMPTIONS' if not failures and not lemma_viol else
                            'UNPROVEN (taint verdict failed)' if failures else 'UNPROVEN (pruning lemma violated)')
    # Merkle-style digest of every layer (sha256 over the sorted hash list)
    cert['layer_digests'] = [hashlib.sha256(b''.join(bytes.fromhex(x[0]) for x in L)).hexdigest()
                             for L in cert['layers']]
    return cert


def save_cert(cert, path):
    with open(path, 'w') as f:
        json.dump(cert, f, separators=(',', ':'))
    return path
