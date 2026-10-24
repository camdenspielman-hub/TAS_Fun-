"""Beam search for the Wily 6 alien fight (Rockman 2).

Objective: the earliest frame of the *last input* such that the alien's HP
reaches 0 without any further input.  States are deduplicated on Mega Man /
bubble / alien features and ranked by hits landed, with per-cell quotas so
that states that are "behind" but positioned differently survive.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "harness"))
import rm2  # noqa: E402

A, B, LEFT, RIGHT = rm2.A, rm2.B, rm2.LEFT, rm2.RIGHT


def default_actions(prev):
    acts = []
    for h in (0, LEFT, RIGHT):
        for j in (0, A):
            acts.append(h | j)
            if not (prev & B):
                acts.append(h | j | B)
    return acts


def features(e):
    r = e.ram
    bub = []
    for s in (2, 3):
        if r(0x420 + s) & 0x80:
            bub.append((s, r(0x460 + s), r(0x4A0 + s)))
    return {
        "hp": r(0x6C1),
        "mmhp": r(0x6C0),
        "x": r(0x460), "xs": r(0x480), "y": r(0x4A0), "ys": r(0x4C0),
        "vy": r(0x640), "vys": r(0x660),
        "st": r(0x400), "fl": r(0x420),
        "inv": r(0x4B), "b4": r(0xB4),
        "ax": r(0x461), "ay": r(0x4A1),
        "bub": tuple(bub),
    }


# RAM bytes that never influence the fight's future (frame counter, sound, OAM).
_IGNORE = set([0x1C, 0x4A]) | set(range(0x200, 0x300))


def dedup_key(e, held):
    ram = bytearray(e.ramblock())
    for a in _IGNORE:
        ram[a] = 0
    return (bytes(ram), held & (A | B))


def finishes_without_input(e, frames=24):
    st = e.save()
    ok = False
    for _ in range(frames):
        e.frame(0)
        if e.ram(0x6C1) == 0:
            ok = True
            break
        if e.ram(0x6C0) == 0:
            break
    e.load(st)
    return ok


def beam_search(e, start_state, start_frame, max_frames, width=400, cell_quota=6,
                actions=default_actions, log=print, prev_input=0):
    beam = [(start_state, [], prev_input)]
    best = None
    for t in range(max_frames):
        frame_no = start_frame + t
        cands = {}
        for st, hist, prev in beam:
            for a in actions(prev):
                e.load(st)
                e.frame(a)
                f = features(e)
                if f["mmhp"] == 0:
                    continue
                key = dedup_key(e, a)
                if key in cands:
                    continue
                cands[key] = (f, e.save(), hist + [a], a)
        # check for completion (alien dead, or will die with no more input)
        done = []
        for key, (f, st, hist, a) in cands.items():
            if f["hp"] == 0:
                done.append((frame_no, hist))
            elif f["hp"] <= 2:
                e.load(st)
                if finishes_without_input(e):
                    done.append((frame_no, hist))
        if done:
            best = done[0]
            log("frame %d: finished (last input frame %d); %d solutions" % (frame_no, frame_no, len(done)))
            return best, done
        # rank: fewer alien HP first; prefer states with bubbles in flight; then invincibility
        ranked = sorted(cands.values(), key=lambda c: (c[0]["hp"], -len(c[0]["bub"]), -min(c[0]["inv"], 1)))
        sel, cells = [], {}
        for c in ranked:
            f = c[0]
            cell = (f["hp"], f["x"] // 6, f["y"] // 8, min(f["inv"], 1), len(f["bub"]))
            n = cells.get(cell, 0)
            if n >= cell_quota:
                continue
            cells[cell] = n + 1
            sel.append(c)
            if len(sel) >= width:
                break
        beam = [(c[1], c[2], c[3]) for c in sel]
        if t % 10 == 0:
            hps = sorted(set(c[0]["hp"] for c in sel))
            log("frame %d: %d cands, beam %d, best alien hp %d (hp levels %s)" % (frame_no, len(cands), len(beam), hps[0], hps[:6]))
    return best, []
