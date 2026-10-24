# Rockman 2 (J) TAS improvement work

Target: [TASVideos publication #4410](https://tasvideos.org/4410M), *NES Mega Man 2 by
Shinryuu in 23:38.98* (85,279 frames, FCEUX 2.3.0, power-on start, old PPU).

## Result so far

| Movie | Frames | Time (60.0988 fps) | Status |
|---|---|---|---|
| Publication #4410 | 85,279 | 23:38.980 | baseline |
| `movies/rockman2-v1-85278.fm2` | **85,278** | **23:38.963** | verified on FCEUX master core and FCEUX 2.3.0 core |

### What v1 changes

TASVideos times a movie to its last input. In the published run the last input
(frame 85278, 0-based) is the B press whose bubble lands the final hit on the
alien.

The boss-collision routine (bank 11, `$A59D`) only checks half of the
projectile slots each frame: odd slots when `$1C` (frame counter) is odd, even
slots when it is even. Bubble Lead spawns in slot 3 first, so in the published
final burst every bubble lands on an odd-`$1C` frame, on the frame it is fired.

v1 presses B one frame earlier for every shot of the final burst (frames
85237–85277 instead of 85238–85278). Each bubble spawns on an even frame, is
not checked that frame, drifts 1 px, and is checked (and hits) on the following
odd frame, the same frames as before. The alien therefore dies on the same
frame, but the last input is one frame earlier, so the movie is one frame
shorter. Everything else is byte-identical to the publication.

Verification (`tools/verify.py`): played through FCEUX's own movie loader
(`FCEUI_LoadMovie`) on the current FCEUX core and on the FCEUX 2.3.0 core. Both
reach the same final RAM (md5 `730eaf56…`), the alien's HP reaches 0 one frame
after the last input, and the ending sequence plays with no further input.

## Findings that matter for further improvement

* **Boss health-fill frame rule.** Every boss fill adds 1 HP only when
  `$1C & 3 == 0` (bank 11 `$812F` robot masters, `$A118` Wily bosses). If the
  fill routine first runs at phase 1 (wait `w = 3`), saving a single frame
  anywhere before it moves that fight and everything after it 4 frames
  earlier. Waits measured in the published run:

  | Fill (first call) | Fight | w | frames needed for +4 |
  |---|---|---|---|
  | 4995 | Flash Man | 3 | 1 |
  | 68606 | Wily 3 boss | 3 | 1 |
  | 77410 | W5 Heat refight | 2 | 2 |
  | 78144 | W5 Air refight | 2 | 2 |
  | 78681 | W5 Wood refight | 1 | 3 |
  | 79295 | W5 Bubble refight | underwater rule (`$FC`) | — |
  | 80829 | W5 Metal refight | 2 | 2 |
  | 81208 | W5 Flash refight | 3 | 1 |
  | 84895 | W6 alien | 1 | 3 |

* **Pause-menu up+down trick** (warmCabin, 2021): holding Up and adding Down
  makes two upward cursor moves on consecutive frames. Not used in #4410.
  Exhaustive search of every Wily 5/6 pause: Heat pause (77168) **−2 frames**;
  Bubble, Crash, Metal, W6 cave and alien pauses −1 each. The Heat pause alone
  reaches its fill's threshold (+4 frames) — but see RNG below.
* **RNG.** `$4A` is updated every NMI as
  `$4A = (($0480 XOR $4A) + $1C + C) >> 1` (Mega Man's X subpixel and the frame
  counter). Any 4-frame shift changes every later random decision. RNG
  consumers in Wily 5: Heat (4 timer picks), Air (2), Bubble (1), Quick (6),
  Crash (2), Metal (1), Wily Machine phase 2 (9, during its fill — cosmetic
  debris). Nothing after the Flash refight's fill reads the RNG for gameplay.
* **Alien fight mechanics** (W6): bubble/alien hit window |dx|,|dy| < 20;
  `$B4` hit latch allows at most one hit per two frames; at most two bubbles;
  the alien's path depends only on unpaused frames since the fight began;
  contact damage 20, projectile 6, 110 invincibility frames after a hit.

## Tools

* `tools/harness/` — headless driver around the unmodified FCEUX core
  (`driver.cpp`, `Makefile`), Python bindings (`rm2.py`): power-on, per-frame
  input, in-memory savestates, FCEUX's own `.fm2` playback, exec/read/write
  hooks, native exec breakpoints, ROM-bank disassembly.
* `tools/verify.py` — plays an `.fm2` through FCEUX's movie loader and checks the
  ending.
* `tools/resync.py` — continues a modified movie along the original, absorbing
  lag-frame differences.
* `tools/splice.py`, `tools/bots/` — input surgery, menu/BFS/beam searches.

Build: `make -C tools/harness FCEUX_SRC=/path/to/fceux/src OUT=build`
(for FCEUX 2.3.0 add `DEFS="-DFCEUDEF_DEBUGGER -DHAVE_ASPRINTF -D__LINUX__ -DRM2_NO_MEMHOOK -DPSS_STYLE=1 -DLSB_FIRST"`).
The ROM is not included.
