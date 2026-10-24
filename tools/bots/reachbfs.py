"""Breadth-first search over movement inputs until a goal predicate holds.

Layers are deduplicated on RAM (minus counters, controller bytes, OAM and the
sound engine) and capped by a caller-supplied ranking when they grow too big.
Returns (frame_index_of_goal, input_list) for the earliest goal frame.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "harness"))
import rm2  # noqa: E402

A, B, LEFT, RIGHT, UP, DOWN = rm2.A, rm2.B, rm2.LEFT, rm2.RIGHT, rm2.UP, rm2.DOWN
MOVE_ACTIONS = [h | j for h in (0, LEFT, RIGHT) for j in (0, A)]

_IGNORE = [0x1C, 0x4A] + list(range(0x23, 0x29)) + list(range(0x200, 0x300)) + list(range(0xE0, 0x100))


def ram_key(e, held, held_mask=A | B):
    ram = bytearray(e.ramblock())
    for a in _IGNORE:
        ram[a] = 0
    return bytes(ram) + bytes([held & held_mask])


def reach_bfs(e, start_state, start_frame, goal, max_frames, cap=4000, rank=None,
              actions=MOVE_ACTIONS, log=print, prev_input=0):
    layer = [(start_state, [], prev_input)]
    for t in range(max_frames):
        nxt = {}
        for st, hist, prev in layer:
            for a in actions:
                e.load(st)
                e.frame(a)
                if goal(e):
                    log("goal reached at frame %d" % (start_frame + t))
                    return start_frame + t, hist + [a]
                k = ram_key(e, a)
                if k in nxt:
                    continue
                nxt[k] = (e.save(), hist + [a], a, rank(e) if rank else 0)
        vals = list(nxt.values())
        if len(vals) > cap:
            vals.sort(key=lambda v: v[3])
            vals = vals[:cap]
        layer = [(s, h, p) for s, h, p, _ in vals]
        if t % 10 == 0:
            log("frame %d: layer %d" % (start_frame + t, len(layer)))
            sys.stdout.flush()
    return None, None
