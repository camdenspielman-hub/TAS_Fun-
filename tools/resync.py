"""Re-synchronise a modified movie against the original, absorbing lag-frame differences.

After a change that shifts timing (e.g. saving frames before a frame rule), the
rest of the original inputs usually still work, except where lag frames fall
differently: the modified run then is one frame ahead (the original lagged and
ignored that frame's input) or behind (the modified run lagged). This walks the
original frame by frame, compares gameplay RAM with the original's RAM dump,
and fixes those cases by dropping or repeating an input.

Gameplay RAM = all 2 KiB except the frame counter, scratch bytes, controller
bytes, stack, OAM buffer, sound-engine variables ($500-$57F, $E0-$FC) and
Mega Man's idle-animation timers ($680/$6A0 slot 0).
"""
import numpy as np

IGNORE = (set(range(0x00, 0x10)) | set([0x1C, 0x1D, 0x3A, 0x43, 0x44, 0x4A, 0x68, 0x364, 0x365, 0x680, 0x6A0])
          | set(range(0x23, 0x29)) | set(range(0x100, 0x300)) | set(range(0xE0, 0xFD))
          | set(range(0x500, 0x580)))
MASK = np.array([0 if a in IGNORE else 1 for a in range(0x800)], dtype=bool)


def same(ram_a, ram_b):
    a = np.frombuffer(ram_a, dtype=np.uint8)[MASK]
    b = np.frombuffer(ram_b, dtype=np.uint8)[MASK]
    return np.array_equal(a, b)


def diff_addrs(ram_a, ram_b, limit=12):
    a = np.frombuffer(ram_a, dtype=np.uint8)
    b = np.frombuffer(ram_b, dtype=np.uint8)
    idx = [i for i in np.nonzero(a != b)[0] if MASK[i]]
    return ["%03X:%02X/%02X" % (i, a[i], b[i]) for i in idx[:limit]]


def resync(e, orig_pads, orig_rams, new_prefix, orig_index, end_index, log=print, max_fix_look=3):
    """Continue `new_prefix` (already emulated: e is at its end) so it follows the
    original from original frame `orig_index` (the next original input to use)
    until `end_index`. orig_rams[i] is the original RAM after i frames.
    Returns (new_sequence, final_orig_index, fixes) or raises on unfixable divergence."""
    seq = list(new_prefix)
    i = orig_index
    fixes = []
    while i < end_index:
        st = e.save()
        e.frame(orig_pads[i])
        if same(e.ramblock(), orig_rams[i + 1].tobytes()):
            seq.append(orig_pads[i])
            i += 1
            continue
        # Option A: original lagged on frame i (its input was ignored) -> we are ahead; skip it.
        e.load(st)
        if same(e.ramblock(), orig_rams[i + 1].tobytes()):
            fixes.append(("skip", len(seq), i))
            i += 1
            continue
        # Option B: we lag here and the original did not -> repeat the input (insert a frame).
        e.load(st)
        e.frame(orig_pads[i])
        e.frame(orig_pads[i])
        if same(e.ramblock(), orig_rams[i + 1].tobytes()):
            fixes.append(("repeat", len(seq), i))
            seq += [orig_pads[i], orig_pads[i]]
            i += 1
            continue
        # Option C: skip one original frame and use the next input now (ahead by one with input).
        ok = False
        for k in range(1, max_fix_look + 1):
            if i + k >= end_index:
                break
            e.load(st)
            e.frame(orig_pads[i + k])
            if same(e.ramblock(), orig_rams[i + k + 1].tobytes()):
                fixes.append(("skip%d" % k, len(seq), i))
                seq.append(orig_pads[i + k])
                i += k + 1
                ok = True
                break
        if ok:
            continue
        e.load(st)
        e.frame(orig_pads[i])
        err = RuntimeError("unfixable divergence at original frame %d (new frame %d): %s"
                           % (i, len(seq), diff_addrs(e.ramblock(), orig_rams[i + 1].tobytes())))
        err.partial = (seq, i, fixes)
        e.load(st)
        raise err
    return seq, i, fixes
