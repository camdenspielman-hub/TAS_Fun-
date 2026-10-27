# Rockman 2 (J) TAS improvement work

Target: [TASVideos publication #4410](https://tasvideos.org/4410M), *NES Mega Man 2 by
Shinryuu in 23:38.98* (85,279 frames, FCEUX 2.3.0, power-on start, old PPU).

## Result so far

| Movie | Frames | Time (60.0988 fps) | Status |
|---|---|---|---|
| Publication #4410 | 85,279 | 23:38.980 | baseline |
| `movies/rockman2-v1-85278.fm2` | 85,278 | 23:38.963 | verified on FCEUX master core and FCEUX 2.3.0 core |
| `movies/rockman2-v2-85274.fm2` | 85,274 | 23:38.897 | verified on both cores |
| `movies/rockman2-v3a-85254.fm2` | 85,254 | 23:38.564 | interim checkpoint (v2 + Wily 6); verified on both cores |
| `movies/rockman2-v3-85220.fm2` | 85,220 | 23:37.998 | verified on both cores |
| `movies/rockman2-v4-85171.fm2` | 85,171 | 23:37.183 | verified on both cores |
| `movies/rockman2-v4.1-85164.fm2` | 85,164 | 23:37.066 | verified on both cores |
| `movies/rockman2-v4.2-85160.fm2` | **85,160** | **23:37.000** | verified on FCEUX master core and FCEUX 2.3.0 core |

**v4.2 is 119 frames (1.98 s) faster than the publication.** It is v4.1 with a
faster Wily 6 climb.
* That climb needs one hidden value in range: slot 4's leftover Y subpixel, in
  0x49–0x53.
* Three Metal Blade directions in the Wily Machine fight set it.
  * Each frame a blade flies up-diagonally adds 0x2C to the subpixel, and each
    frame it flies down-diagonally subtracts 0x2C.
  * The hits land on the same frames, so the play is otherwise identical.
* The alien's door comes 4 frames earlier, a multiple of the alien's 4-frame
  phase, so the whole fight follows unchanged.
* Two independent checks (sync and rules) found it valid.
* `movies/rockman2-v4.2-edits.json` rebuilds it, and the final RAM md5 is
  `f93baf33…` on both cores.

**v4.1 is 115 frames (1.91 s) faster than the publication.** It is v4 with Wily 4
replaced by Shinryuu's own version.
* Shinryuu recorded that version in an unpublished, 174-frame-faster run.
* We reconstructed it frame by frame from his video: every visible frame
  reproduced, with real replays and no RAM pokes.
* Differences from v4's Wily 4:
  * One useless Item 3 sled is dropped, so the hidden Y subpixel that room 33's
    Item 3 descent needs comes out in range: 7 frames.
  * The Boobeam Trap fight hops between cannons instead of walking, which
    avoids 3 lag frames.
* The Wily 5 refights were then re-synchronised for the new frame counter.
  * That took 20 input frames: Heat edits, hub walks that set Mega Man's
    subpixel before the Bubble, Quick and Metal capsules, and RNG-only
    left/right swaps.
  * Every Wily 5/6 event and lag frame lands exactly 7 frames before v4's.
* Two independent checks found it valid: sync, and a rules review of every
  changed input.
* `movies/rockman2-v4.1-edits.json` rebuilds it with `tools/make_movie.py`.
  The final RAM md5 is `2ca14909…` on both cores.

**v4 was 108 frames (1.80 s) faster than the publication.** It is v3 with a new
Wily 4 boss fight, worth 49 frames.
* Both cores play it through FCEUX's own movie loader to the same final RAM
  (md5 `3a74a2ac…`). The alien reaches 0 HP one frame after the last input
  (frame 85170).
* It is identical to v3 up to frame 74324 (Wily 4).
* `tools/make_movie.py` rebuilds it from the published movie and
  `movies/rockman2-v4-edits.json`, which holds 23 replaced input blocks, each
  with its reason.
* Two independent checks found it valid:
  * Sync: frame-by-frame comparison with v3 and playback on both cores.
  * Rules: every changed input, the new up+down menu frames (6, all
    menu-cursor trick), and the emulator dependence, which is unchanged from
    the publication.

### What v4 changes (on top of v3)

1. **Wily 4: Leaf Shield Boobeam Trap fight (+48 at the Wily 5 start).** This
   is warmCabin and Shinryuu's 2022 idea; we rebuilt it from Shinryuu's video,
   which shows the RAM values on screen.
   * Crash Bomb explosion pieces never set their hitbox type. They inherit
     whatever the last object in their slot left.
   * A pause during the Wily 4 ceiling zip selects Leaf Shield. Raising the
     shield once leaves hitbox type 4 in weapon slots 2–5, which gives the
     explosions much larger boxes.
   * A second pause selects Crash Bomber.
   * The two pauses cost 60 frames before the boss door. That is a multiple of
     the boss fill's 4-frame rule, so the fight keeps v3's frame-counter phase.
   * The fight:
     * The bigger explosions break the walls quickly.
     * Two cannons die to the hurt-glitch damage transfer.
     * A touch on a cannon at X = 0xA6 sets the stale hurt value that the
       second transfer needs.
     * The last bomb hits the final cannon directly.
   * Boobeam dies 55 frames earlier than in v3. Mega Man ends on the floor
     rather than the upper ledge, and the longer teleport costs 7 frames.
     Ending on the ledge costs more than that.
2. **Wily 5: re-synchronised 49 frames earlier.** The Wily map's 4-frame rule
   turned the 48 into 49.
   * Only `$1C` and the RNG differ from v3. Leaf Shield's other side effects
     (stale hitbox types, 3 units of Leaf Shield energy) change nothing later.
   * The Heat refight needed 7 edits and Crash 1.
   * The Quick and Metal refights each needed a new hub walk. Mega Man's X
     subpixel when he enters the capsule sets the boss's first random choice.
   * Two Metal Blade timing changes restore the stale Y subpixels that Wily 6's
     Item 1 platforms need:
     * a horizontal instead of a diagonal throw in the Metal refight;
     * a blade thrown 3 frames earlier at the Wily Machine.
   * Every Wily 5/6 event and lag frame is exactly 49 frames before v3's.

Shinryuu's video of this fight is about 9 frames faster again. His shield setup
costs about 6 fewer frames, and that is being investigated.

**v3 was 59 frames (0.98 s) faster than the publication.**
* Both cores play it through FCEUX's own movie loader to the same final RAM
  (md5 `6e02b423…`). The alien reaches 0 HP one frame after the last input
  (frame 85219), and the ending plays with no further input.
* It starts from power-on and is identical to the publication up to frame
  59636 (Wily 2).
* `tools/make_movie.py` rebuilds it from the published movie and
  `movies/rockman2-v3-edits.json`. That file holds 48 replaced input blocks,
  each with its reason.
* `docs/whole-game-analysis.md` explains the frame rules, RNG, pause and boss
  mechanics behind these changes.

Notes for anyone judging or submitting v3. These came out of an independent
rules check, which found the movie valid.
* **Timing.** By TASVideos timing (last input) v3 is 59 frames faster: last
  input 85219 vs 85278. The alien's HP reaches 0 at frame 85220, against
  85278 in the publication, so the visible end comes 58 frames sooner. v2's
  final shot already landed one frame after the last input.
* **Simultaneous directions.** v3 holds Up+Down on 33 frames, against 17 in
  the publication, and Left+Right on 1 frame, as the publication does. All
  of the new Up+Down frames are warmCabin's pause-menu cursor trick, which the
  published movie already uses.
* **Power-on state.** Like the publication, sync depends on FCEUX's default
  power-on RAM pattern (`00 00 00 00 FF FF FF FF`). Both cores tested use it.
* **Header.** The .fm2 header keeps the publication's `comment author Shinryuu`
  and rerecord count (118012), because every input not listed in the edits
  file is his. Update both fields before submitting.

### What v3 changes (on top of v2)

v3 comes from treating the run as one unit. First I measured every frame rule
in the game (section 1 of the analysis), so it was clear which savings survive
to the end:
* before Wily 1 a saving survives only as a lead of 16;
* in Wily 2-3 it must be at least 15;
* from Wily 4 on any 4-frame lead survives.

The searches then targeted those thresholds.

1. **Wily 2-3: +32 frames.** The Wily 3 boss's death fade waits for a 16-frame
   boundary, and v3 reaches it 32 frames early.
   * The Wily 2 pauses use the up+down cursor trick: 6 frames, which give 4 at
     the Wily 2 boss fill.
   * Wily 3's P→Item 1 pause is opened during the stage-start landing
     animation. Every pause ends with a 12-frame teleport-in animation, and at
     the stage start it overlaps the landing, so the pause costs 13 frames
     less.
   * The weapon capsule is touched from the top of a hop, so the refill resumes
     in mid-air without 6 frames of ground inching.
   * One input change keeps the rising enemy's damage boost that the Item 1
     ceiling zip relies on. The stage reaches the boss 8 frames early.
   * The boss pause is 6 frames shorter with the menu trick.
   * New Guts Tank fight:
     * The head becomes hittable a fixed 309 frames after the tank starts
       moving.
     * Two Quick Boomerangs are thrown from the top of an early jump while it
       is still invulnerable. They curve back through it on its first two
       hittable frames.
     * A second jump then throws one boomerang every other frame, each hitting
       3 frames later.
     * All 14 hits land on consecutive same-parity frames, and the boss dies
       18 frames sooner. Replacing a long-lived blocker boomerang also removes
       a lag frame after the kill.
2. **Wily 4: +2 frames.**
   * One frame of a ladder climb and two menu-trick frames give the Boobeam
     Trap's fill its 4-frame gain.
   * The earlier `$1C` phase changes when Mega Man is drawn during his
     invincibility, which costs one lag frame in a crowded room and one in the
     fight.
   * Wily 4 was re-synchronised for the new stale object data (5 input edits).
     One boomerang throw at 68876 in the Wily 3 fight was dropped so that a
     stale subpixel inherited by the Wily 5 Wood refight's tornadoes stays in
     range.
3. **Wily 5: re-synchronised 34 frames earlier**, with v2's Heat-pause gain
   kept.
   * While Mega Man stands still the RNG converges to a function of `$1C` and
     his X subpixel. So each refight's random choice is set by where he rests
     in the hub before teleporting.
   * Metal Blade throws, keeping the same number of blades, set the hidden
     slot subpixels that Wily 6's Item 1 platforms need.
4. **Wily 6: +20 frames** (from v3a). The ceiling zip starts from the third
   Item 1 platform's throw pose.

Checked and found not improvable with the current route (details in the
analysis document):
* Heat Man and Wood Man stage ends;
* Wood's stage-start pause, which breaks its DelayUpScroll in every variant
  tried so far. Shinryuu reports making it work in 2022; being re-examined;
* the Boobeam Trap fight with the published structure. warmCabin's 2022
  43-frame fight has a different structure and is being rebuilt;
* the Metal Man, Crash Man and Air Man stages, for an 8-frame gain each, when
  changed one stage at a time. Shinryuu's unfinished 2022 run gets Air +10,
  Crash +8 and Quick +16 by chaining changes across these stages, through the
  Item 1 "values" (stale Y subpixels) that each stage leaves to the next. That
  route-level work is in progress;
* the alien fight;
* the 9 deliberate frames in Bubble Man's pause.

**v3a (interim).** v2 plus a new Wily 6 climb, 20 frames faster.
* In v2 Mega Man rides the third Item 1 platform up 8 px, jumps, lands and
  turns to start the 16 px/frame ceiling zip.
* The zip only needs him at Y ≤ 36 when he turns facing left with zero speed.
  The throw pose of the third platform already gives such a turn 22 frames
  earlier, with Y = 36.
* Two idle frames at 83951 cost 2 of the 22 frames. They keep the door lead a
  multiple of 4, because the alien's path is door-timed and its fill follows a
  4-frame rule. They also keep the stale Y subpixel inherited by the
  alien-room ledge platform in range.
* `movies/rockman2-v3a-edits-vs-v2.json` holds the one replaced input block.

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
  currently loses 2 there. (Correction: the Wily 1 fade needs a full 16-frame
  lead, not 6. The published run reaches it with zero wait, see
  `docs/whole-game-analysis.md`.) Any of these also changes every Wily 5 RNG
  decision again; `tools/milestone.py` handles that.
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
* `tools/make_movie.py` — the same for any edit list, e.g. `movies/rockman2-v3-edits.json`.

Build: `make -C tools/harness FCEUX_SRC=/path/to/fceux/src OUT=build`
(for FCEUX 2.3.0 add `DEFS="-DFCEUDEF_DEBUGGER -DHAVE_ASPRINTF -D__LINUX__ -DRM2_NO_MEMHOOK -DPSS_STYLE=1 -DLSB_FIRST"`).
The ROM is not included.
