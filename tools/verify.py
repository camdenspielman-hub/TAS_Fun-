"""Verify a Rockman 2 .fm2 with FCEUX's own movie player.

usage: python3 verify.py LIBRM2.so ROM.nes MOVIE.fm2 [screenshot_prefix]

Reports the movie length, the last frame that has input, the frame at which the
final boss (alien) reaches 0 HP after the movie ends, and the RAM hash; then
runs 3600 more frames with no input and checks that the ending sequence starts.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "harness"))
import rm2  # noqa: E402


def verify(lib, rom, movie, shot_prefix=None):
    e = rm2.Emu(lib, rom)
    _, frames = rm2.read_fm2(movie)
    n = len(frames)
    last_input = max(i for i, (c, p) in enumerate(frames) if p)
    if e.lib.rm2_movie_load(movie.encode()) != 0:
        raise SystemExit("movie failed to load")
    for _ in range(n):
        e.frame(0)  # input comes from the movie
    end_md5 = hashlib.md5(e.ramblock()).hexdigest()
    stage = e.ram(0x2A)
    e.lib.rm2_movie_stop()
    alien_dead = 0 if (stage == 0x0D and e.ram(0x6C1) == 0) else None
    shots = {}
    for k in range(1, 3601):
        e.frame(0)
        if alien_dead is None and e.ram(0x2A) == 0x0D and e.ram(0x6C1) == 0:
            alien_dead = k
        if shot_prefix and k in (1, 600, 1800, 3600):
            path = "%s_%04d.png" % (shot_prefix, k)
            rm2.screenshot(e, path, scale=1)
            shots[k] = path
    return {
        "movie": os.path.basename(movie),
        "frames": n,
        "last_input_frame": last_input,
        "stage_at_end": "%02X" % stage,
        "alien_hp0_frames_after_end": alien_dead,
        "end_ram_md5": end_md5,
        "screenshots": shots,
    }


if __name__ == "__main__":
    lib, rom, movie = sys.argv[1:4]
    prefix = sys.argv[4] if len(sys.argv) > 4 else None
    for k, v in verify(lib, rom, movie, prefix).items():
        print("%-28s %s" % (k, v))
