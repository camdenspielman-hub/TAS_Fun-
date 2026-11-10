#!/usr/bin/env python3
"""pfcheck_stream.py - STREAMING checker for large search certificates (pf_search, 2026-11-07).

Same checks and same set-up as pfcheck.py (E0 envelope, ROM, movie, C1 root by continuous power-on replay in this
fresh process, C0), then layer by layer with bounded memory. Differences from pfcheck.py: C2 rebuilds layer d from the
rebuilt states of layer d-1 (load parent, one frame) instead of a continuous replay from the root. Continuity is
covered by pfcheck.py on the smaller certificates and by pf_search's identity test T1 (save/load before every frame of
an 85,206-frame replay changes nothing).

usage: pfcheck_stream.py CERT.json[.gz] --rom ROM.nes --lib LIBRM2.so [--movie MOVIE.fm2] [--envelope ENV.json]
                         [--all256] [--sample N] [--taint] [--writers]
  --all256    closure over all 256 pads for every entry (default: the certificate's class representatives)
  --sample N  closure over all 256 pads on N randomly chosen entries per layer (C3b), in place of their class run
  --taint     re-run the taint tracker on every class transition (C5; needs librm2pf.so)
  --writers   census of the writers of $1D/$FD/$FE/$A9 over every class transition (C7; needs librm2pf.so)
Exit code 0 iff the verdict is VALID. The checker writes nothing except to stdout."""
import sys, os, ctypes, random, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pfcheck import field, setup, verdict, taint_good  # noqa: E402

FLAGS = {'--all256': 0, '--taint': 0, '--writers': 0, '--rom': 1, '--lib': 1, '--movie': 1, '--envelope': 1,
         '--sample': 1}


def main(argv):
    ctx = setup(argv, FLAGS)
    cert, e, K, root, goal, out, opt = ctx['cert'], ctx['e'], ctx['K'], ctx['root'], ctx['goal'], ctx['out'], ctx['opt']
    t0 = ctx['t0']
    out['mode'] = 'stream'
    all256 = '--all256' in opt
    nsample = int(opt.get('--sample', 0))
    do_taint = '--taint' in opt
    do_writers = '--writers' in opt
    idn = cert['identity']
    classes, kin, pruned_ok = ctx['classes'], ctx['kin'], ctx['pruned_ok']
    allowed = {int(a, 16): int(m) for a, m in idn['canon'].items()}
    init = bytearray(0x800)
    for a, m in allowed.items(): init[a] = m
    init = bytes(init)
    if do_taint or do_writers:
        L_ = e.lib
        L_.pf_taint_begin.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        L_.pf_taint_end.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_char_p]
        tout = (ctypes.c_int * 16)(); tram = ctypes.create_string_buffer(0x800)
    if do_writers:
        L_.pf_ww_get.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        wb = (ctypes.c_int * 4)()
        L_.pf_ww_clearmask()
        for a in (0x1D, 0xFD, 0xFE, 0xA9): L_.pf_ww_set(a, 1)
    writers = {}
    layers = cert['layers']; D = len(layers) - 1
    sets = [set(x[0] for x in L) for L in layers]
    c2 = c3 = c3b = c5 = True; n3 = n3b = n5 = npr = 0; maxnint = 0
    for d, L in enumerate(layers):
        if len(L) != len(sets[d]) or [x[0] for x in L] != sorted(x[0] for x in L):
            c2 = False; print('C2 FAIL: layer %d has duplicate or unsorted hashes' % d)
    if layers[0] != [[cert['root']['key_hash'], -1, -1]]:
        c2 = False; print('C2 FAIL: layer 0 is not the root')
    prev = [root]
    rs = random.Random(777)
    for d in range(1, D + 1):
        # C2': rebuild layer d from layer d-1
        cur = []
        for i, (h, pi, pad) in enumerate(layers[d]):
            e.load(prev[pi]); e.frame(pad); st = e.save()
            if K.h(st) != h or goal(st):
                c2 = False; print('C2 FAIL layer %d entry %d' % (d, i))
            cur.append(st)
        # C3 (+C3b, C5, C7) on layer d-1 -> layer d
        padset = list(range(256)) if all256 else classes
        sample = set(rs.sample(range(len(prev)), min(nsample, len(prev)))) if nsample else set()
        for i, st in enumerate(prev):
            jrb = field(st, 'CTRL', 'JYRB')[0]; ls = field(st, 'CTRL', 'LSTS')[0]
            for p_ in (range(256) if i in sample else padset):
                e.load(st)
                tracked = (do_taint and p_ in classes)
                if tracked: L_.pf_taint_begin(init, kin, jrb, ls)
                if do_writers and p_ in classes: L_.pf_ww_reset(); L_.pf_ww(1)
                e.frame(p_)
                if do_writers and p_ in classes:
                    L_.pf_ww(0)
                    for k in range(L_.pf_ww_count()):
                        L_.pf_ww_get(k, wb)
                        kk = '%02X@%04X%s' % (wb[2], wb[1], '(0)' if wb[3] == 0 else '(nz)')
                        writers[kk] = writers.get(kk, 0) + 1
                if tracked:
                    L_.pf_taint_end(tout, tram); o = list(tout); n5 += 1; maxnint = max(maxnint, o[11])
                    if not taint_good(o, tram.raw, allowed):
                        c5 = False; print('C5 FAIL layer %d entry %d class %02X: %s' % (d - 1, i, p_, o[:13]))
                ch = e.save()
                if i in sample: n3b += 1
                else: n3 += 1
                if K.h(ch) in sets[d]:
                    continue
                if pruned_ok(ch, d):
                    npr += 1; continue
                if i in sample: c3b = False
                else: c3 = False
                print('C3 FAIL: child of layer %d entry %d pad %02X not in layer %d%s' % (
                    d - 1, i, p_, d, ' (GOAL)' if goal(ch) else ''))
        print('  layer %d rebuilt (%d), closure %d->%d ok=%s (%.0fs)' % (d, len(cur), d - 1, d, c3 and c3b,
                                                                       time.time() - t0), flush=True)
        prev = cur
    # closure of the last listed layer is not needed (its children are at the goal depth)
    out.update(C2_layers=c2, C3_closure=c3, C3_transitions=n3, C3_pads=('256' if all256 else len(classes)),
               C3b_256pad_sample=c3b, C3b_transitions=n3b, C3_children_pruned_by_lemma=npr)
    if do_taint:
        out.update(C5_taint=c5, C5_transitions=n5, C5_max_nmi_per_frame=maxnint)
    if do_writers:
        out['C7_writers'] = writers
    # C4 witness
    res = cert['result']
    c4 = True
    if res.get('goal_depth') is not None:
        e.load(root); hit = []
        for p_ in res['witness']:
            e.frame(p_); hit.append(goal(e.save()))
        c4 = bool(hit) and hit[-1] and not any(hit[:-1]) and len(res['witness']) == res['goal_depth'] == D + 1
        out['C4_witness'] = c4
    ok = ctx['ok'] and c2 and c3 and c3b and c4 and (c5 if do_taint else True)
    return verdict(ctx, ok)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
