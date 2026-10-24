"""Corridor search: BFS over movement inputs, kept near a reference trajectory.

States are ranked by how far *ahead* along the reference path they are (the
latest reference frame within `radius` pixels), then by distance to it, so the
search explores small deviations from a known-good route (TAS-style
optimisation) instead of the whole level.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "harness"))
import rm2  # noqa: E402

A, LEFT, RIGHT = rm2.A, rm2.LEFT, rm2.RIGHT
MOVE_ACTIONS = [h | j for h in (0, LEFT, RIGHT) for j in (0, A)]


def mm_key(e, a):
    r = e.ram
    return (r(0x460), r(0x480), r(0x4A0), r(0x4C0), r(0x640), r(0x660), r(0x400), r(0x420) & 0x40, a & A)


def corridor_search(e, start_state, start_frame, ref, goal, end_frame, cap=3000, radius=6,
                    lookahead=12, actions=MOVE_ACTIONS, prev_input=0, log=print):
    """ref: dict frame -> (x, y) of the reference run (after that frame's input)."""
    layer = [(start_state, [], prev_input)]
    for f in range(start_frame, end_frame):
        nxt = {}
        for st, hist, prev in layer:
            for a in actions:
                e.load(st)
                e.frame(a)
                if goal(e):
                    log("goal at frame %d" % f)
                    return f, hist + [a]
                k = mm_key(e, a)
                if k in nxt:
                    continue
                x, y = e.ram(0x460), e.ram(0x4A0)
                best_k, best_d = f - 1, 9999
                for kk in range(f - 3, f + lookahead):
                    if kk in ref:
                        d = abs(x - ref[kk][0]) + abs(y - ref[kk][1])
                        if d <= radius and kk > best_k:
                            best_k = kk
                        if d < best_d:
                            best_d = d
                nxt[k] = (e.save(), hist + [a], a, (-best_k, best_d))
        vals = sorted(nxt.values(), key=lambda v: v[3])[:cap]
        layer = [(s, h, p) for s, h, p, _ in vals]
        if (f - start_frame) % 5 == 0:
            log("frame %d: %d states (best ahead=%d)" % (f, len(layer), -vals[0][3][0] - f if vals else 0))
            sys.stdout.flush()
    return None, None
