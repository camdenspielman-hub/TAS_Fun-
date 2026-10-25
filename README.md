# Rockman 2 (J) TAS improvement work

Target: [TASVideos publication #4410](https://tasvideos.org/4410M), *NES Mega Man 2 by
Shinryuu in 23:38.98* (85,279 frames, FCEUX 2.3.0, power-on start, old PPU).

## Result so far

| Movie | Frames | Time (60.0988 fps) | Status |
|---|---|---|---|
| Publication #4410 | 85,279 | 23:38.980 | baseline |
| `movies/rockman2-v1-85278.fm2` | 85,278 | 23:38.963 | verified on FCEUX master core and FCEUX 2.3.0 core |
| `movies/rockman2-v2-85274.fm2` | **85,274** | **23:38.897** | verified on FCEUX master core and FCEUX 2.3.0 core |

v2 is 5 frames (0.083 s) faster than the publication. Both cores play it
through FCEUX's own movie loader to the same final RAM (md5 `f4c94da4…`). The
alien reaches 0 HP one frame after the last input, and the ending plays with no
further input. `tools/make_v2.py` rebuilds it from the published movie and
`movies/rockman2-v2-edits.json`, which lists all 26 input edits with the reason
for each.

### What v2 changes (on top of v1)

1. **Heat Man refight pause (Wily 5, frame 77168).** The pause that selects
   Bubble Lead uses the up+down cursor trick (`U`, `U+D`, –, `U`, `U+D`), which
   reaches the weapon 2 frames sooner. Heat Man's health fill then starts on its
   `$1C & 3 == 0` frame rule instead of waiting 2 frames, so everything after it
   is **4 frames earlier**.
2. **Re-synchronising the six remaining refights.** Being 4 frames earlier
   means `$1C` is 4 lower at every later event, so every RNG decision in Wily 5
   comes out differently. `tools/milestone.py` replays the shifted original
   inputs fight by fight and repairs each missed checkpoint (boss hit, health
   fill, teleport, weapon change) with one-frame input edits. Fights that needed
   more than that:
   * Quick Man made a different jump. Holding Left one frame longer at 80083
     keeps every hit on schedule.
   * Crash Man: Mega Man's X subpixel differs, so a Crash Bomb hit him. Two edits
     (80522, 80534) fix it.
   * Metal Man jumps the moment Mega Man first throws, and the RNG picks the
     height on that frame. The first throw is moved one frame later (80941) to get
     the low jump. This costs 2 frames, but the Flash Man health fill absorbs them:
     with any lead of 1–4 frames that fill still ends 4 frames early.
3. **Hidden projectile subpixels.** Mega Man's shot slots 2–4 never clear their
   X/Y subpixels when a new object spawns. The Wily 6 Item-1 platforms and the
   alien-fight bubbles inherit whatever the last occupant left, and the
   re-synchronised fights leave different values. With wrong values a platform
   runs a pixel behind, and later a bubble lives one frame longer. The pause
   routine (`$C573`) refuses while any object in slots 2–15 is alive, so the
   alien-fight pause fails. Three extra diagonal Metal Blades fix this. A
   diagonal blade adds 44/256 px of subpixel per frame:
   * 80997 (`D+R+B`, mid-air, just before the post-Metal-Man teleport) deletes
     itself after 4 frames: slot 4 +80, exactly the original value;
   * 82143 and 82145 (mid-air during the Wily Machine fight, where Mega Man
     already lands in the throw pose) shift slot 3 to +1 and slot 2 to −6 from
     the original.
   Outcome tests showed both residuals are harmless. Throws on the ground, or in
   the air without a throw pose already pending, freeze Mega Man on landing and
   were rejected. Every candidate was checked for an unchanged Mega Man path and
   boss-HP timeline through the end of Wily 5.

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
  reaches its fill's threshold (+4 frames); this is what v2 uses.
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

* **Alien-fight pause (Wily 6).** With the up+down trick this menu also
  closes 1 frame sooner (weapon selected after frame 85074 instead of 85075 in
  v2). The fight then runs one frame ahead, but the different bubble positions
  cause an extra lag frame at 85192 that gives the frame back. No change of one
  or two inputs between the menu and 85192 avoids that lag while keeping the hit
  schedule. Getting this frame would need a re-planned fight. The final burst
  would then have to hit from slot 2, the even slot, or start one hit earlier,
  because the `$1C` parity changes relative to the alien's path.
* **Still open:** saving 3 frames anywhere in Wily 6 before the alien's health
  fill (fill wait 1) would gain 4. Saving 1 more frame between the Metal Man
  fill and the Flash Man fill would gain 4 more, but the Metal Man fight
  currently loses 2 there. Saving 6 frames in Wily 1 would reach its 16-frame
  stage-end rule. Any of these also changes every Wily 5 RNG decision again;
  `tools/milestone.py` handles that.
* **Opposite directions.** The published movie already presses Up+Down on 17
  frames and Left+Right once. v2 adds Up+Down on two more frames, in the Heat
  pause. FCEUX's "allow Up+Down/Left+Right" option only filters live gamepad
  input; movie playback is unaffected.

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
* `tools/milestone.py` — milestone-guided re-synchronisation of a time-shifted
  section (single-frame edits, back-tracking over earlier milestones, optional
  RNG checkpoints that are skipped when the next required ones hold anyway).
* `tools/make_v2.py` — rebuilds the v2 movie from the publication and the edit list.

Build: `make -C tools/harness FCEUX_SRC=/path/to/fceux/src OUT=build`
(for FCEUX 2.3.0 add `DEFS="-DFCEUDEF_DEBUGGER -DHAVE_ASPRINTF -D__LINUX__ -DRM2_NO_MEMHOOK -DPSS_STYLE=1 -DLSB_FIRST"`).
The ROM is not included.
