"""Rebuild movies/rockman2-v2-85274.fm2 from the published movie (#4410) and the edit list.

usage: python3 tools/make_v2.py PUBLISHED.fm2 [OUT.fm2]

movies/rockman2-v2-edits.json lists replacements on the published input
sequence: each {"from": i, "to": j, "new": [...]} replaces published frames
[i, j) with the given frames (fm2 "RLDUTSBA" strings). Edits are applied back to
front so the indices always refer to the published movie.
"""
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "harness"))
import rm2  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
EDITS = os.path.join(HERE, "..", "movies", "rockman2-v2-edits.json")
REF = os.path.join(HERE, "..", "movies", "rockman2-v2-85274.fm2")


def build(published):
    hdr, frames = rm2.read_fm2(published)
    pads = [p for _, p in frames]
    for ed in sorted(json.load(open(EDITS)), key=lambda d: d["from"], reverse=True):
        pads[ed["from"]:ed["to"]] = [rm2.pad_from_fm2(s) for s in ed["new"]]
    while pads and pads[-1] == 0:
        pads.pop()
    return hdr, pads


if __name__ == "__main__":
    hdr, pads = build(sys.argv[1])
    _, ref = rm2.read_fm2(REF)
    same = pads == [p for _, p in ref]
    print("frames %d, identical to %s: %s" % (len(pads), os.path.basename(REF), same))
    if len(sys.argv) > 2:
        out = [("guid " + str(uuid.uuid4()).upper()) if h.startswith("guid") else h
               for h in hdr if not h.startswith("comment")]
        rm2.write_fm2(sys.argv[2], out + ["comment author Shinryuu"], pads)
