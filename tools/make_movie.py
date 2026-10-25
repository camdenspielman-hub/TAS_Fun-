"""Rebuild one of our movies from the published movie (#4410) and an edit list.

usage: python3 tools/make_movie.py PUBLISHED.fm2 EDITS.json REFERENCE.fm2 [OUT.fm2]

Each edit {"from": i, "to": j, "new": [...]} replaces published frames [i, j)
with the given frames (fm2 "RLDUTSBA" strings). Edits are applied back to front
so the indices always refer to the published movie. The result is compared with
REFERENCE.fm2; with OUT.fm2 it is also written out with REFERENCE's header.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "harness"))
import rm2  # noqa: E402


def build(published, edits):
    _, frames = rm2.read_fm2(published)
    pads = [p for _, p in frames]
    for ed in sorted(json.load(open(edits)), key=lambda d: d["from"], reverse=True):
        pads[ed["from"]:ed["to"]] = [rm2.pad_from_fm2(s) for s in ed["new"]]
    while pads and pads[-1] == 0:
        pads.pop()
    return pads


if __name__ == "__main__":
    published, edits, ref = sys.argv[1:4]
    pads = build(published, edits)
    hdr, rframes = rm2.read_fm2(ref)
    rpads = [p for _, p in rframes]
    while rpads and rpads[-1] == 0:
        rpads.pop()
    print("frames %d (last input %d), identical to %s: %s"
          % (len(pads), len(pads) - 1, os.path.basename(ref), pads == rpads))
    if len(sys.argv) > 4:
        rm2.write_fm2(sys.argv[4], hdr, pads)
