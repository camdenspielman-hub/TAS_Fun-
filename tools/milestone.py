"""Milestone-guided re-synchronisation of a time-shifted movie section.

After a timing change, the original inputs (shifted) are used as a template.
Milestones are (frame, predicate, label) checks taken from the original run,
e.g. "boss HP <= 22 by frame N" or "Heat Man's timer == 31 at frame N". The
section is replayed milestone by milestone; when one fails, single-frame
edits (replace / insert / delete one input) are tried in the window since the
previous milestone, and if none works the window is widened back over up to
`max_back` earlier milestones (which must all still hold). Among working
edits the one leaving the state closest to the original's is kept.
"""
import numpy as np


def run_to(e, start_state, seq, start, end):
    e.load(start_state)
    for f in range(start, end):
        e.frame(seq[f] if f < len(seq) else 0)
    return e.save()


def state_distance(e, ref_ram, addrs):
    ram = np.frombuffer(e.ramblock(), dtype=np.uint8)
    return int(sum(abs(int(ram[a]) - int(ref_ram[a])) for a in addrs))


def candidate_edits(seq, lo, hi, actions):
    for f in range(lo, hi):
        for a in actions:
            if a != seq[f]:
                s = list(seq)
                s[f] = a
                yield ("set", f, a), s
        s = seq[:f] + [seq[f]] + seq[f:]
        yield ("dup", f, seq[f]), s
        s = seq[:f] + seq[f + 1:] + [0]
        yield ("del", f, None), s


def check_chain(e, state, start, seq, chain):
    """Simulate from (state, start) through each milestone in chain; True if all hold."""
    e.load(state)
    f = start
    for (mf, pred, _label) in chain:
        if mf < start:
            continue
        while f <= mf:
            e.frame(seq[f] if f < len(seq) else 0)
            f += 1
        if not pred(e):
            return False
    return True


def prefix_states(e, state, start, seq, end):
    """Savestates before each frame in [start, end) when playing seq from (state, start)."""
    out = {}
    e.load(state)
    for f in range(start, end):
        out[f] = e.save()
        e.frame(seq[f] if f < len(seq) else 0)
    return out


def milestone_sync(e, start_state, start, template, milestones, actions, ref_rams=None,
                   ref_offset=0, dist_addrs=(0x460, 0x480, 0x4A0, 0x4C0), log=print, max_back=3,
                   max_window=150):
    """milestones: list of (frame, predicate(e) -> bool, label) sorted by frame.
    ref_rams[f + ref_offset] is the reference RAM after new frame f (for ranking).
    Returns (seq, applied_edits) or raises RuntimeError at the first unmet milestone."""
    seq = list(template)
    edits = []
    cks = [(start_state, start)]  # cks[i] = state before milestone i (frame after milestone i-1)
    i = 0
    while i < len(milestones):
        mf, pred, label = milestones[i]
        ck_state, ck_frame = cks[i]
        st = run_to(e, ck_state, seq, ck_frame, mf + 1)
        if pred(e):
            cks.append((st, mf + 1))
            i += 1
            if i % 5 == 0:
                log("ok through %s (%d/%d)" % (label, i, len(milestones)))
            continue
        best = None
        tried = 0
        for back in range(0, max_back + 1):
            j = i - back
            if j < 0:
                break
            bstate, bframe = cks[j]
            chain = milestones[j:i + 1]
            pre = prefix_states(e, bstate, bframe, seq, mf + 1)
            lo = max(bframe, mf + 1 - max_window)
            for edit, s in candidate_edits(seq, lo, mf + 1, actions):
                tried += 1
                ef = edit[1]
                # milestones before the edit frame are unaffected (already verified)
                if not check_chain(e, pre[ef], ef, s, [m for m in chain if m[0] >= ef]):
                    continue
                d = 0
                if ref_rams is not None:
                    d = state_distance(e, ref_rams[mf + 1 + ref_offset], dist_addrs)
                if best is None or d < best[0]:
                    best = (d, edit, s, j)
            if best is not None:
                break
        if best is None:
            err = RuntimeError("milestone '%s' at %d unreachable with single edits (%d tried, back %d)"
                               % (label, mf, tried, max_back))
            err.partial = (seq, edits, cks[i][1])
            raise err
        d, edit, seq, j = best
        edits.append((label, edit, d))
        log("milestone %-28s fixed by %s (dist %d, back %d)" % (label, edit, d, i - j))
        # recompute checkpoints from j
        del cks[j + 1:]
        i = j
    return seq, edits
