"""Beam search for the Wily 6 alien fight (Rockman 2).

Objective: the earliest frame of the *last input* such that the alien's HP
reaches 0 without any further input.  States are deduplicated on (almost) the
full RAM and ranked by hits landed, then by how close the next bubble (or a
bubble in flight) is to the alien, with per-cell quotas so that states that
are "behind" but positioned differently survive.

Only the selected beam keeps savestates; candidates are regenerated from
their parent state plus one action, which keeps memory small.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "harness"))
import rm2  # noqa: E402

A, B, LEFT, RIGHT = rm2.A, rm2.B, rm2.LEFT, rm2.RIGHT

# RAM bytes that never influence the fight's future (frame counter, sound, OAM).
_IGNORE = [0x1C, 0x4A] + list(range(0x23, 0x29)) + list(range(0x200, 0x300))


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
            bub.append((r(0x460 + s), r(0x4A0 + s)))
    facing_right = bool(r(0x420) & 0x40)
    return {
        "hp": r(0x6C1), "mmhp": r(0x6C0),
        "x": r(0x460), "y": r(0x4A0), "inv": r(0x4B),
        "ax": r(0x461), "ay": r(0x4A1),
        "right": facing_right, "bub": bub,
    }


def readiness(f):
    """Chebyshev distance from the next bubble spawn / nearest live bubble to the alien."""
    sx = f["x"] + (17 if f["right"] else -17)
    sy = f["y"] - 2
    best = max(abs(sx - f["ax"]), abs(sy - f["ay"]))
    for bx, by in f["bub"]:
        best = min(best, max(abs(bx - f["ax"]), abs(by - f["ay"])))
    return best


def dedup_key(e, held):
    ram = bytearray(e.ramblock())
    for a in _IGNORE:
        ram[a] = 0
    return bytes(ram) + bytes([held & (A | B)])


def rollout_hp(e, prev, frames):
    """Alien HP after a short greedy rollout: keep holding A if held, tap B whenever possible."""
    st = e.save()
    for _ in range(frames):
        a = (prev & A) | (0 if prev & B else B)
        e.frame(a)
        prev = a
        if e.ram(0x6C0) == 0:
            e.load(st)
            return 99
    hp = e.ram(0x6C1)
    e.load(st)
    return hp


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
                actions=default_actions, log=print, prev_input=0, inv_quota=0.25, rollout=6):
    # beam entries: (state, history, previous input)
    beam = [(start_state, [], prev_input)]
    for t in range(max_frames):
        frame_no = start_frame + t
        cands = {}
        done = []
        for bi, (st, hist, prev) in enumerate(beam):
            for a in actions(prev):
                e.load(st)
                e.frame(a)
                f = features(e)
                if f["mmhp"] == 0:
                    continue
                key = dedup_key(e, a)
                if key in cands:
                    continue
                f["roll"] = rollout_hp(e, a, rollout) if rollout else f["hp"]
                cands[key] = (f, bi, a)
                if f["hp"] == 0 or (f["hp"] <= 2 and finishes_without_input(e)):
                    done.append(hist + [a])
        if done:
            log("frame %d: finished (last input frame %d); %d solutions" % (frame_no, frame_no, len(done)))
            return frame_no, done
        ranked = sorted(cands.values(), key=lambda c: (c[0]["roll"], c[0]["hp"], readiness(c[0])))
        sel, cells, rest = [], {}, []
        n_inv = 0
        for c in ranked:
            f = c[0]
            cell = (f["hp"], f["x"] // 6, f["y"] // 8, min(f["inv"], 1), len(f["bub"]))
            if cells.get(cell, 0) >= cell_quota:
                rest.append(c)
                continue
            cells[cell] = cells.get(cell, 0) + 1
            sel.append(c)
            n_inv += f["inv"] > 0
            if len(sel) >= width:
                break
        # quotas only shape diversity; never leave the beam under-filled
        sel += rest[: max(0, width - len(sel))]
        # make sure some invincible states survive (they enable the close-range burst)
        if n_inv < inv_quota * width:
            extra = [c for c in ranked if c[0]["inv"] > 0 and c not in sel]
            sel += extra[: int(inv_quota * width) - n_inv]
        new_beam = []
        for f, bi, a in sel:
            st, hist, prev = beam[bi]
            e.load(st)
            e.frame(a)
            new_beam.append((e.save(), hist + [a], a))
        beam = new_beam
        if t % 10 == 0:
            hps = sorted(set(c[0]["hp"] for c in sel))
            log("frame %d: %d cands, beam %d, best alien hp %d (levels %s)" % (frame_no, len(cands), len(beam), hps[0], hps[:6]))
            sys.stdout.flush()
    return None, []
