"""Input-list surgery for .fm2 edits.

An edit is (start, old_len, new_inputs): replace pads[start:start+old_len] with
new_inputs. Edits are given in ORIGINAL frame numbering and applied back to
front so indices stay valid.
"""


def apply_edits(pads, edits):
    out = list(pads)
    for start, old_len, new in sorted(edits, key=lambda x: -x[0]):
        out[start:start + old_len] = list(new)
    return out


def menu_inputs(open_frame, rel_moves, length):
    """Build a pause-menu input block: Start at open_frame, then {offset: pad}
    with offsets relative to open_frame + 1 (as printed by the menu BFS)."""
    from rm2 import START
    block = [0] * length
    block[0] = START
    for off, pad in rel_moves.items():
        block[1 + off] = pad
    return block
