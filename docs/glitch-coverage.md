# Rockman 2 (J): glitch coverage map

gd_synth, 2026-11-07 (UTC). This synthesises the glitch-discovery round (`wf_88df5d5c-1c2`): seven subsystem auditors (gd_terrain, gd_scroll, gd_objects, gd_weapons, gd_flow, gd_timing, gd_fuzz), each re-checked by an independent reproducer (repro_*). It also uses the earlier documented-glitch survey (glitch_hunt) and its audit (audit_glitchsurvey, holecheck_glitchsurvey), plus a few checks of my own (section 6).

* Base: the round used v6.2 savestates. v6.6 = 84,995 frames is the committed movie now; it equals v6.2 before frame 74299. Frame numbers below are v6.2 frames.
* Labels: **REAL** means a plain `e.frame()` replay from power-on or from a REAL savestate. **ANALYSIS** means pokes, hooks, PRG patches or models.
* Trust classes follow pf_doc's proof standard (section 1).
* `SP/...` paths refer to the project's working notes and scripts, which are not part of this repository.

---------------------------------------------------------------------------------------------------------------------

## 0. Bottom line (the user's two questions)

**1. Do we have a proof that no other time-saving glitch exists? No.** We have three narrower results (section 7):

* **Where an unknown glitch could live.** The TAS runs plus the fuzzers executed 95.0% of the statically reachable code (98.3% of the gameplay banks). The rest is listed and read, and none of it moves Mega Man, the camera, the section, the scroll request or the checkpoint outside death, game-over, password and title paths. So an unknown time saver must be one of two things:
  * a new combination of states or CPU timing inside code the TAS already runs;
  * ACE, which the user excluded.
* **Whole classes are impossible for every input:**
  * a frame-rule bypass;
  * a shorter transition, intro, fill, post-kill sequence, map or READY;
  * a skipped boss, refight, weapon, stage or section;
  * created weapon energy;
  * a leftward zip, or horizontal movement above 16 px per frame;
  * a robot-master hit cadence under 19 frames.

  These are careful code readings with REAL whole-run cross-checks. Formally they are PROVEN-GIVEN-ASSUMPTIONS, not machine-checked, because pf_static did not converge.
* **A large search found nothing.** About 7.4M REAL fuzz frames and 12,800 menu trials turned up about 27 behaviours not in our documents. After the frame rules, none of them saves a frame.

Movement and state combinations are the residual. They are sampled, not exhausted. The best example: the vertical-section desync (G3) was found by the fuzzer only in this round.

**2. Have the dead-end arguments been adversarially reviewed?**

* **The glitch claims: yes.**
  * Every one of the 40 "new glitch" claims was re-run by a second agent with its own scripts, often on another core build.
  * 7 of the 40 did not reproduce as stated, and about 10 were not new.
  * Several closure-type sentences were false: "boss invincibility is frozen during the post-pause freeze", "16 live enemy slots never happen during play", "the Bubble 43509 lag cannot be avoided", "no site writes Mega Man's screen", "the KOOK byte carries the hidden phase".
* **The per-subsystem impossibility lists (section 3): no.** They were corroborated only where two agents happened to overlap. Section 4 lists who checked what.
* **The earlier closures did get this review.** The closure audit after the user's challenge found real frames: v6.3 to v6.6, -15 in total.

**This synthesis closes the round's biggest open lead (section 6).** The W1 vertical-section desync would have been worth -32 frames, and it cannot be completed:

* no open left crossing exists in W1 screens 22-26, so the desync cannot be undone;
* screen 26 has no up exit for a desynced Mega Man;
* items do not help a desynced Mega Man (REAL).

**Ranked open leads (section 5)** are all low or very low:

* a W4 desync death warp, up to about -368 frames, which needs two more desync entries;
* W4 free-rise scroll requests, -3 if three sites give a frame each;
* Crash 27207 plus the c5 fuzz hit, as one part of R1;
* the Bubble 43509 burst split as a phase knob;
* spawn flooding.

---------------------------------------------------------------------------------------------------------------------

## 1. Trust classes and the assumption register

* **PROVEN-GIVEN-ASSUMPTIONS (PGA):** a code argument quantified over all inputs, checked by at least one REAL whole-run measurement (write-watch, taint, timing log). It holds if the assumptions below hold.
* **PROVEN-IN-MODEL (PIM):** exhaustive within a named model.
* **SEARCH-LIMITED (SL)**, **ESTIMATE (EST)**: as in the closure audit.
* **2nd:** the same fact was derived or measured independently by another agent, named.

Assumptions shared by every PGA item:

| id | assumption | status |
|---|---|---|
| A-CORE | FCEUX 2.3.0 semantics equal our master core | cross-core equality on every verified movie; pf_check re-ran 11 certificates on both cores |
| A-NOACE | no data is executed as code and no out-of-range dispatch happens | user decision; one-line ACE notes in 3.9 |
| A-DISPATCH | indirect jumps go only through the 26 executed `JMP ($0008)` tables (entries listed in `fuzz/work/a02_dispatch.txt`) and the sound engine's `JMP ($00F4)`; no RTS dispatch | ROM scan of executed code (gd_fuzz P1) |
| A-INDEX | every indexed or indirect store stays inside the range read from its loop. The bounds are: B:9260 X<=8, E:808C X<=10, E:8351 X=$A9<=11, E:8A3D/8AAB/8C88 X<=2, F:CB96 Y<=16, F:D0E9 X<=1, D:A419 Y<=1. The sound engine's `STA ($EC),Y` needs pointer corruption (ACE). | loop reading plus observed index sets (gd_fuzz index bitmaps over 3 runs and 6.06M fuzz frames) |
| A-NMI | at most one NMI per frame; the NMI restores bank and registers except on the deferred path, which matters only at F:C7A5/C7AE, E:8EE9 and the PPU-off F:C628 | REAL whole run (84,760 NMIs, never 2 in a frame). pf_check notes the hit-check lemma also needs the bank-restore part. |

The formal layer is unfinished. pf_static's sound whole-program fixpoint did not converge, so its writer-set lemmas are OPEN. By pf_doc's standard no impossibility claim in the project is plain PROVEN today.

---------------------------------------------------------------------------------------------------------------------

## 2. Whole-game numbers

### 2.1 Code coverage

These are REAL counts, re-counted by me from gd_fuzz's novelty maps (`SP/agents/glitchdisc/fuzz/work/*_ins|br|idx.npy`).

| run | opcode starts | branch outcomes | index-value bits |
|---|---|---|---|
| v6.2 (+600 ending frames) | 16,199 | 3,386 | 25,836 |
| publication #4410 | 16,281 | 3,398 | 25,915 |
| warmCabin zipless m4057 (order Q M B F H A W C) | 16,912 | 3,529 | 26,966 |
| union of the three | 17,171 | 3,654 | 28,307 |
| union after 6 fuzz campaigns (6,061,192 REAL frames) | **18,351** | **3,986** | 33,557 |

Static reach after fuzzing is a recursive descent from executed code through the known dispatch tables (`a04_frontier_final.txt`):

| bank | executed | reachable, never executed | share |
|---|---|---|---|
| B (bosses) | 3,905 | 121 | 97.0% |
| C (sound) | 1,216 | 33 | 97.4% |
| D (menus, title, password, ending) | 2,667 | 698 | 79.3% |
| E (Mega Man, enemies, flow) | 6,010 | 16 | 99.7% |
| F (fixed: NMI, objects, collision) | 4,530 | 106 | 97.7% |
| 9 | 23 | 0 | |
| **total** | **18,351** | **974** | **95.0%** |

* The gameplay banks B, C, E and F are at 98.3%.
* Mega Man's routine E:84EE-8EDC is fully executed.
* Banks 0-8 and A hold data only.
* The never-executed code is identified block by block in gd_fuzz R1.3. Its only key-RAM writes are:
  * boss HP and state (Time Stopper, HP clamps, dragon);
  * `$2A` in the reset, stage-select and password paths;
  * Mega Man's HP in the E-tank path;
  * object position arrays in the title intro.
* None of it writes `$0440/$0460/$04A0/$F9/$20/$1F/$38/$37/$B0` outside death, game-over, password and title code. I checked the frontier list's key-RAM column myself.

### 2.2 Fuzz volume (all REAL, with stored inputs that replay)

| fuzzer | volume | result |
|---|---|---|
| gd_fuzz c1-c6 (coverage-guided, 1,899 seed states = every v6.2 room/screen start plus periodic states) | 6,061,192 frames | coverage saturated (c6: +15 instructions in 1.19M frames); every anomaly explained |
| of which "ahead of v6.2" (1-3 edits, then v6.2's inputs) | 1,667,000 frames (c4a + c5) | every hit removes a deliberate cost or breaks later |
| gd_terrain f01 (840 states x 16 x 60 frames) | 570,308 frames | 200 deduplicated anomalies, all known mechanics |
| gd_objects f01_bossfuzz (202 in-fight states, invariant checks) | ~390,000 frames | 0 invariant violations |
| gd_weapons f01_wfuzz (440 states, random weapon picks) | ~350,000 frames | all anomalies explained |
| gd_flow t06_menufuzz (every v6.2 pause, select and weapon-get menu) | 12,800 trials | 0 violations; minima equal the code bounds |

The total is about 7.4M REAL frames, roughly 87 times the length of the run.

### 2.3 Where the frames are (v6.2, gd_flow's per-frame labelling)

| loop type | frames |
|---|---|
| gameplay main loops | 35,717 |
| scroll and door transitions | 14,150 |
| boss intro, fill and post-kill | 13,858 |
| weapon and item get | 6,675 |
| Wily maps | 4,676 |
| select and showcase | 3,628 |
| READY | 3,072 |
| pause menus | 1,723 |
| W5 events | 633 |
| loads and lag | 366 |
| refills, title, teleport-in, death waits | 512 |

* 49,293 frames (58%) are in loops whose length is fixed by code, given the known $1C-phase rules, Mega Man's exit height and the music phase of a few load lags.
* An unknown glitch can therefore save time only in the 35,717 gameplay frames or by skipping a whole loop. The flow lemmas in 3.5 exclude skipping one.

---------------------------------------------------------------------------------------------------------------------

## 3. Map by subsystem

Each subsection lists:
* the routines audited;
* the edge cases tested;
* the glitches found, with the reproduction verdict;
* what is proven impossible, with its class and any second check;
* what was fuzzed;
* what remains unknown.

### 3.1 Terrain collision and Mega Man physics (gd_terrain; reproduced by repro_terrain)

**Routines audited.**
* The main-loop order (E:8171 / W5 E:8223).
* Mega Man's routine E:84EE and its state handlers: E:8508 teleport-in, 8545 frozen, 8546 hurt, 8569 stand, 85A6 tiptoe, 85D3 walk, 85FB air, 868C decelerate/land, 86BC ladder, 8776 locked.
* Fire and ladder grab E:879B/87AF; facing E:87F2; speed and ice E:880D; belt, wind and platform carry E:889E.
* Horizontal move E:8922 (right) / E:89B6 (left), and the three-height wall check E:8A20 with flags E:8A75.
* Environment and ladder bits E:8A84, including the predicted point E:8B41.
* Vertical move E:8B83, including the head push E:8BF8; floor and ceiling E:8C6A; platform landing E:8CF4.
* Tile and solid-sprite lookup F:CB89/CB9F/CBC0; hurt F:D32F; stage-start descent F:C7B2.
* repro_terrain re-read E:8A20-8D85, E:86BC-8708, E:87AF-87EE, E:889E-88F5, F:CB9F-CBF5 and F:C4CD.

**Edge cases tested (REAL unless noted).**
* Wall ejection with every input class (no input, U+D, R, L, L+R): only rightward zips.
* Rising across Y=0 with $F9=00 and with $F9=FF: the ceiling bob and the phantom bit. A whole-run scan found 17 bobs in v6.2.
* Up-transition arrival height, three cases.
* U, D and U+D on ladder tops: Heat, W4, Crash.
* Stale $40 at every stage start (whole run, 5 cases).
* Solid-sprite low-byte matches: REAL at the Air door 2; ANALYSIS for a Heat Yoku block.
* The platform X alias under a desync (REAL, W4 lift).
* $F9=FE, plus a single-frame U variant from each of v6.2's 3,734 $F9=FF frames.
* Yoku timing and door-sprite vertical solidity (code).

**Glitches.**

| glitch | new? | verdict | value |
|---|---|---|---|
| 240-px ceiling bob: the E:8BF8 head push has no $F9 carry after F:CBD6 clobbers $0a | phenomenon known; exact code path new | REPRODUCED; v6.2 uses it 17 times (none in W2) | 0 new |
| Phantom ladder bit: E:8B41 drops the borrow, so rising across Y=0 reads rows 14-15 | new | REPRODUCED at Crash 26688/27673; the other 6 listed frames are not uses (DIFFERENT) | 0 (already used) |
| U+D ladder-top pop: +16 px in one frame, facing flips | new to our docs | REPRODUCED; used at Crash 25497. The W4 72360 pop-zip follow-up is closed: the desync can never be undone. | 0 |
| Stale $40/$4F/$50/$AF carry after a stage start or transition | new write-up | REPRODUCED (Bubble +1.0 px by luck; W1 56853 -1.0 px, forced) | 0 |
| Solid sprites matched on X/Y low bytes only (F:CB9F) | new | REPRODUCED with REAL input (Air door 2 stops a wrapped Mega Man) | 0 |
| Platform X alias (E:8CF4), $F9=FE, door sprite not vertically solid | new | REPRODUCED or code | 0 |

**Proven impossible (PGA unless noted).**
* **No leftward zip.** The right branch ejects at most 15 px, once; only the left branch steps 16 px, and it pushes right. REAL t02. This corrects glitch_hunt's "mirror zip". 2nd: accepted in audit_glitchsurvey-09.
* **Horizontal displacement is at most 16 px per frame outside transitions**, so $0440 changes by at most 1 per frame. 2nd: no unexplained position jump in about 7.4M fuzz frames.
* No screen before the section's first screen can be reached without a backward transition.
* **The only vertical discontinuity is the -240 px wrap.** Every other snap is at most about 28 px. 2nd: fuzz detectors.
* No section can be skipped by physics alone.
* **The scroll request $37 has exactly five setters:** E:8945, E:8A52, E:8BC2, E:8BD0, E:8CE8. 2nd: gd_scroll (code) and pf_static (REAL writer sets of v6.3 and #4410).
* **$F9 has 9 writers plus the reset clear.** 2nd: pf_static saw 8 of them executed.
* Mega Man cannot be hurt while $F9 != 0.
* A desynced Mega Man never spawns a boss.
* No Yoku-block zip in Heat (PIM, from block timing).

**Fuzzed.** 570,308 REAL frames, plus gd_fuzz.

**Unknown.**
* Multi-segment wrapped paths to death-warp thresholds. holecheck_glitchsurvey found no hole in the robot-master stages; the W4 desync case stays open (rank 1).
* U+D-pop sites, one by one.
* The full list of "ladder top next to a wall at a screen edge" sites, which is the G3 pattern. Only W1 and W4 were looked at.

### 3.2 Scrolling, screens and transitions (gd_scroll; reproduced by repro_scroll)

**Routines audited.**
* Scroll handler E:8278: backward check E:8287, forward check E:829E/82A1, boss init after E:82B5.
* Permission read F:C7A1, with bank switches C7A5 and C7AE; F:C000 with the deferred sound C022.
* The five request sites.
* Camera E:8DF5/8E65 with clamps E:8E0E/8E7E.
* Forward transition E:8F39: clear E:9220, loader E:907D, door loops, horizontal E:90C9 and vertical E:9185 scrolls, length read E:8FAB.
* Backward transition E:8EDD, with its length read E:8EE9.
* Death F:C10B; checkpoint F:C19D; respawn F:C4CD; pause camera save/restore D:90EC/9363.
* Door tables E:9061/906F; the $B400 permission tables of all 8 banks; the exit-teleport length.

**Edge cases tested (REAL).**
* Every one of the 10 deferred NMIs in v6.2, and which bank switch it hit.
* The garbage-Y histogram over all 84,691 NMIs.
* Crash 27193 accepted, which gives the first in-play backward transition.
* Air door 1 with no input (push-wrap), and door 2 from the wrapped corridor.
* A wrapped Mega Man walking left (camera drag).
* The cycle of the section-length read in every v6.2 transition.
* A whole-run write-watch of the transition counters.

**Glitches.**

| glitch | new? | verdict | value |
|---|---|---|---|
| Phantom shutter / door-push wrap: the shutter request and its push carry Mega Man one screen ahead into the corridor | the wrap is new; the low-byte match came from gd_terrain | REPRODUCED. Door 2 then costs at least about +100 frames: the right-wall request at 21309; the left gap needs an extra pause. | 0 |
| Scroll-check NMI windows: the 2nd bank switch always refuses; a deferral during the backward check clobbers X, so the forward check is skipped (refused, or a pit death for a down request); a 1st-switch deferral during the backward check can grant a backward scroll | new (window (a) is the known DelayScroll) | REPRODUCED (Crash 27194 refusal). Corrections: (d) works for any Y whose $B400 entry has the reverse bit; E:8EE9 is a 5th deferral site (harmless). | 0. The 27207 request is -1 but needs a Crash rebuild, and the q8 stage end absorbs it alone (rank 4). |
| Camera drag by a wrapped Mega Man | corollary of the desync | REPRODUCED | 0 (hazard) |
| Backward transition reached in play | not new, not a glitch | REPRODUCED | 0 |

**Proven impossible (PGA).**
* **Transition lengths are fixed.** The loop counters ($FD, the stack, $39, $08) are written only by the loops (whole-run write-watch). 2nd: gd_flow's REAL three-run comparison and audit_glitchsurvey-23.
* **Section geometry ($14/$15/$38) cannot be corrupted.** Its writers are the transitions, the respawn, the W5 events and the dragon init, all from ROM tables. The forward length read runs 3,518-7,980 cycles into its frame in every v6.2 transition.
* **The camera stays in [$14,$15]** and moves only by Mega Man's displacement or in transitions.
* **No vertical wrap and no vertical screen skip.** $F9>0 reads air, $F9<0 reads row 0, and the screen comes only from $0440. 2nd: gd_terrain.
* **Request and acceptance rules are exactly as listed.** The garbage-Y set {1C,01,0B,09,00,0F,03,04} is closed only over v6.2's NMIs (SL). Y=1C (50% of NMIs) already grants every direction, so completeness of the set barely matters.
* Deferred register clobbers matter only at the scroll check. 2nd: gd_timing's whole-run taint.
* **The checkpoint is a function of $0440 and the bank.** The $FF index of Metal and Crash is unreachable.
* READY (192), the pit wait (224) and the damage wait (16+160) are fixed; the only lever is the known $36 cut.
* The left-edge clamp stops zips at X<20 on a section's first screen.
* The pause restores the camera exactly.

**Fuzzed.** No dedicated fuzzer; whole-run instrumentation plus gd_fuzz.

**Unknown.**
* Wrapped boss fights: now negative after repro_scroll's REAL door-2 cost.
* A list of one-screen sections where a near-lag request falls in a backward-check window. This is a builder hazard.
* The backward length read E:8EE9 hit by an NMI (code only; harmless).
* The dragon init and the W1 auto-scroll under unusual camera states (code only).
* Bank-13 camera writers outside gameplay.

### 3.3 Objects, enemies, bosses and combat (gd_objects; reproduced by repro_objects)

**Routines audited.**
* Main-loop order; intro and death loop F:C816.
* Spawner F:D655 / D750 / D7C9; free slot F:DA40; child spawns F:F137/F13E and B:A352/A359; init F:D779; transition clear E:9220.
* Generic ticks F:EE98/EF91; despawn F:EF6A; contact F:E557; item pickup F:E5CA; enemy weapon check F:E5E9 and its handlers; drops F:F238; hurt F:D32F; Mega Man's death F:C10B/C352.
* Boss dispatcher B:8003 and the Time Stopper path B:8063; init B:A451; intro and fill B:80D3/812F/A118; contact B:A52D.
* Hit check B:A59D and handlers B:A601-A8FC; heal B:A903; robot-master death B:9FD3-A0FF; all 14 boss state tables; Wily Machine guard B:9A15.
* Stage clear F:C1F0/C289; item and W5 events E:82D5-84A3; capsule AI E:BD08.
* Draw F:CC74 (Mega Man's $4B and the boss's $05A8 timers); freeze table E:93F0.

**Edge cases tested.**
* Read-before-write of every boss AI in all 22 v6.2 fights.
* Energy writers; hit dispatch with $A9 9-11 (a scan of all v6.2 frames).
* Stack depth.
* Hurt knockback against the pause (6 hurts).
* Slot exhaustion; phantom platforms.
* 75 child-spawn sites, 30 of them unchecked (a register log).
* The hurt X-clobber for each enemy class.
* Wily Machine guards (REAL).
* Softlock window edges, g = 1..200 (ANALYSIS).

**Glitches.**

| glitch | new? | verdict | value |
|---|---|---|---|
| Post-pause freeze ($AA=3, 12 frames) while boss invincibility keeps ticking | not new (quick_fight2) | REPRODUCED in 5 fights | 0 now (rank 7) |
| The dead Guts deck is a phantom platform that holds Mega Man at Y132 for the W3 exit | cause new | REPRODUCED | already used |
| A contact-only hurter skips its movement on the hurt frame | new detail | REPRODUCED 4/4 | 0 |
| A failed child spawn writes through a stale Y. At W2 B:9275 with Y=$10 this would write Mega Man's subpixels and his screen byte $0440. | new (code) | NOT-REPRODUCED: unreachable | 0 |
| Wily Machine guards: phase 1 deflects Air and Quick, phase 2 Atomic Fire | new | REPRODUCED REAL | 0 |
| The hurt glitch applies to every generic-tick enemy; cause of the 16-175 double-KO softlock | generic form new | REPRODUCED (observer; ANALYSIS edges 16 and 176) | 0 |

**Proven impossible (PGA).**
* **Boss HP $06C1 changes only through:** the B:A59D handlers (one per frame, damage = table[$A9][$B3]), the fills, init, Time Stopper (Quick -1 per 30 frames; Flash Man and the alien set to 28), the A903 heal, and the Wily-object sites.
* No robot-master hit during the intro or fill, and none while $05A8 != 0. Robot-master hits are at least 19 frames apart (20 for single-parity Crash Bomber); Wily-boss hits at least 2.
* The robot-master death and the W5 capsule, return and 9th-teleporter sequences are fixed counters. Only Mega Man's teleport Y and OAM stalls vary, and stalls only lengthen them.
* No weapon-energy underflow except Atomic Fire: Air and Item 1 are always even.
* Hit dispatch with $A9 9-11 is unreachable.

2nd checks:
* gd_weapons P5 and P1/P2, derived independently.
* pf_static L-HIT, a local lemma for any input; pf_check re-read it (gap: the NMI bank-restore assumption).
* The boss fuzz found 0 violations.

**Fuzzed.** About 390k REAL in-fight frames.

**Unknown.**
* About 100 enemy AI routines (table E:92F0/9370) are executed (bank E 99.7%) but not audited one by one. Enemy-specific bugs turned up only incidentally:
  * the Telly aim step function, from the STX $09 bug at F:C871 (holecheck_wily4);
  * the RNG writer E:9E8A;
  * the phantom widths.
* A later spawn into a dead platform slot that inherits its box: code only.

### 3.4 Weapons and items (gd_weapons; reproduced by repro_weapons)

**Routines audited.**
* Fire F:DA4E and the fire routines DA69-DC9A; spawn F:D3DD/D3F9.
* Weapon loop F:DCCD and every AI: Atomic DD31, Air DE45, Leaf DE71, Bubble DF6C, Quick DFCB, Crash E013, Time Stopper E155, Item 1 E18D, Item 2 E20D, Item 3 E2DA, and the deflected types E46E/E4E1.
* Object move and kill F:EECD; object-tile checks F:F0AD/F00A/E3EA; hit checks F:E5E9 and B:A59D; Time Stopper freeze B:8009.
* Item landing E:8CF4/8D86; clear E:9220; pause D:90EC-9392; refills E:808C/8327/832B/8351.
* The census of energy writers (static, executed plus reachable code).

**Edge cases tested (REAL unless noted).**
* All 16 d-pad combinations for a Metal Blade throw.
* An Atomic release on every frame from 48623 to 48650, across $F9=FF.
* Atomic Fire and Time Stopper carried through transitions and capsules, including a full charge carried into the Wood refight.
* Leaf Shield destroyed before the throw; Leaf Shield killed by a d-pad press while $F9 != 0.
* The post-pause freeze; Time Stopper on Flash Man and the alien.
* Ghost item widths during the death wait (4 cases).
* Deflections.
* $0590 aliasing (code).

**Glitches.** Value 0 for all of them.

| glitch | new? | verdict |
|---|---|---|
| G1: Metal Blade stationary with L+R as well as U+D | not new (wm_fights) | REPRODUCED |
| G2: an Atomic release while $F9 != 0 costs 7 units through a stale table index | the mechanism of the known underflow | REPRODUCED |
| G3: Atomic charges survive transitions but fire on the first boss-intro frame | not new | REPRODUCED, plus a full-charge test |
| G4: Leaf Shield energy is charged only at the throw | not new; the $F9 kill and Y=0 details are new | REPRODUCED |
| G5: the post-pause freeze | | DIFFERENT: boss invincibility keeps ticking |
| G6: Time Stopper freezes every boss and heals Flash Man and the alien to 28 | the heal is new | REPRODUCED |
| G7: ghost item widths during the death wait | new, harmless | REPRODUCED |
| G8: deflected weapons become types $3B/$3C/$3D | ordinary game behaviour | REPRODUCED for Leaf |

**Proven impossible (PGA).**
* P1: no energy is ever created.
* P2: Air Shooter and Item 1 never underflow.
* P3: at most 1/7/3 free Bubble/Quick/Metal shots per weapon selection.
* P4: no other underflow, except Atomic Fire with $F9 != 0.
* P5: damage comes from the selected weapon, and $A9 cannot change while a projectile lives.
* P6: stale piece hitboxes are type 4 at most.
* P7: no ghost item platform can be landed on.
* P8: no item can move Mega Man between the killing throw and the end of the stage. So the $F9 hand-over needs terrain movement after the throw. rc_offscreen built on this: Bubble is the only room that ends with $F9=FF, so Bubble -> Wood is forced.
* P9: no Atomic charge reaches a boss fight (REAL).
* P10: no item can start an up transition.
* P11: item speed bounds.

2nd checks: P1/P2 were derived independently by gd_objects; P9 was confirmed REAL by repro_weapons with a full charge.

**Fuzzed.** About 350k REAL frames with random weapon selection.

**Unknown (code only).**
* Time Stopper carried through a boss door or capsule.
* An Atomic release with no free slot.
* The ladder-carry quirk G10.

### 3.5 Game flow and menus (gd_flow; reproduced by repro_flow)

**Routines audited.**
* Reset and stage start: E:8000-80AB, READY E:813A, teleport-in F:C7B2.
* Title and intro D:9EE7/A1D9-A31E; password D:A325-A4E5.
* Stage select D:8015, with its cursor table D:82CA; boss showcase D:80E3-829D.
* Pause gate F:C573 and pause menu D:90EC; E-tank D:9292; pickups E:82D5-837D.
* Boss intro F:C805/C816; post-kill B:9FE8/A08B; stage clear F:C1F0; weapon get D:B9F9/BAE6.
* Wily maps D:9678-9945; game over D:B01A; W5 events; ending.
* A complete list of joypad reads: a static descent from the REAL coverage union and every dispatch table.

**Edge cases tested (REAL).**
* 12,800 random menu trials.
* Buttons held through all 20 boss intros.
* The dead frame after a fill (11 of 11 fights).
* Game over and CONTINUE in W2.
* START injected at all 42 event-return and stage-init gates.
* A held at all 8 showcases.
* The refight HP drop.
* A hub desync (ANALYSIS poke).

**Glitches.**
* **G1, W5 held-button buffer:** new; REPRODUCED; 0.
* **G2, dead frame after a fill:** not new.
* **G3, W5 events change screens relatively, and contact ignores Mega Man's screen:** code REPRODUCED. An ANALYSIS poke shows a carried desync breaks the refight. Reachability is open.
* **G4, CONTINUE refills everything even in Wily stages:** REAL; negative value.
* **G5, pause +1 frame with $47 pending:** NOT-REPRODUCED; the guard is dead.
* **G6, showcase A recolours the stars:** DIFFERENT. #4410 uses it at all 8 showcases and v6.2 at 6. Adding A at 24346 and 46950 is frame-neutral (REAL), a free cosmetic fix.
* **G7, refight HP drop:** normal behaviour.

**Proven impossible (PGA).**
* **P1:** input is never read during READY, teleport-in, boss intros and fills, post-kill, stage clear, weapon/item get (except its 2-frame menu), Wily maps, W5 events, door and scroll loops, refill loops and death waits.
* **P2:** each of these loops exits on its own counter, the documented $1C phase or Mega Man's exit height.
* **P3:** no out-of-order progress, from the $9A and $2A writer sets: no weapon without its fight, no return to a beaten stage, and every Wily stage is entered through its map.
* **P4:** menus are at their code minimum.

2nd checks:
* REAL: identical loop lengths in v6.2, #4410 and the zipless run.
* pf_search certified all 9 W5/W6 pause minima (PGA: A-STATE, A-TAINT, A-MENU-CLOSURE); pf_check re-ran them on both cores.

Correction to carry: load-lag counts cannot drop (at least 3,045 cycles of margin), but they can rise with the music phase (the W6 load lags 4 or 5).

**Unknown.**
* Whether a W5 hub desync is reachable (G3).
* The password route, which is a category change.

### 3.6 Timing: NMI, lag, RNG, sound and the frame counter (gd_timing; reproduced by repro_timing)

**Routines audited.**
* NMI F:CFED-D0D3: PPU path, deferred-sound test D08A, sound D092, RNG D0C3.
* Waits F:C07F/C0AB/C0D7/C100; pad read F:D0D4.
* Bank switch F:C000 and the deferred path C022-C04E; sound queue F:C051; MMC1 control F:C05D.
* Palette animation F:C427; column builder F:C968; underwater slow-down E:819D/F:C832/E:8253.
* F:C816, C1F0, C10B/C352; stage start E:80A1-8170; draw F:CC74.
* Every reader of $1C; the RNG writers F:D0CB, E:9E8A and E:A51A.

**Edge cases tested (REAL).**
* Timing of all 84,760 NMIs.
* Every $1C increment against a completed wait.
* Lag frame equals no pad read (0 mismatches).
* Where lag NMIs land.
* X/Y taint after every bank switch.
* RNG carry-in on every NMI.
* Load-lag margins.
* Column-buffer overflow.
* Logic doubling on kill and death frames (Air, Heat, W1, W2).
* The W3 Guts double KO (code plus REAL damage table).
* Time Stopper against fills (code).
* The C05D timing.
* Power-on RAM.

**Glitches.**
* **1, column-buffer overflow, $1B unbounded:** the mechanism is new. DIFFERENT: the palette stays wrong for about 1,380 frames (the last corridor and the whole Crash Man fight). The symptom has been known since 2013 (forum70 l.6336/6435). Value 0.
* **2, logic doubling on kill and death frames:** REPRODUCED; the general rule is new; the W1 instance was known.
* **3, hidden CPU/PPU phase:** REPRODUCED with a correction. The carrier is the sub-cycle X.count; the KOOK byte is not it.
* **4, RNG carry-in and the extra writer E:9E8A:** REPRODUCED.
* **5, immediate NMI after select-screen loads:** 7 of 8 frames right. "The first NMI after a stage load takes the lag path" was NOT reproduced (0 of 16).
* **6, power-on garbage run:** not new.

All of these save 0.

**Proven impossible (PGA).**
* P1: $1C's only writer is F:D088, plus the reset clear. 2nd: pf_static's REAL writer sets.
* P2: each $1C increment is exactly one completed wait (84,709 = 84,709).
* P3: at most one NMI per frame.
* P4: a lag frame runs only the sound tick and one RNG update, and its pad is never read.
* P5: the sound engine never feeds game logic.
* P6: the APU cannot change CPU timing.
* P7: controller 2 is ignored.
* P8: the column overflow cannot reach object RAM. The bound is a code argument of about 8 entries. My own check of gd_fuzz's index bitmaps at F:C9D5/C9F9: the maximum entry index is 5 (6 entries) in the three TAS runs and in all 6.06M fuzz frames. 7 or more entries, which would reach game-read RAM at $0370 and above, never occurred.
* P9: load-lag counts cannot drop.
* P10: deferred X/Y clobbers matter only at the scroll check.
* P11: $4A <= $7F.
* P12: logic doubles only on Mega Man death frames and boss kill frames.

**So no timing effect can advance a frame rule.** Only fewer game, slow-down or menu frames, or fewer true lags, can help.

**Unknown.**
* The W3 Guts double KO: it needs Mega Man's HP at 4 or less, i.e. 6 or more hits (EST infeasible).
* A drier W3 water path: every avoided slow-down frame is one $1C frame, 192 in W3, and would feed R2.
* The C051 queue race (never hit).
* A lag NMI while a stage bank is selected.
* Console-versus-FCEUX differences: FCEUX's unconditional dot skip, no $2002 NMI suppression, a flat 512-cycle OAM DMA.

**Not a glitch: the power-on RAM setting.** FCEUX 2.3.0 honours an fm2 `RAMInitOption`. Option 2 ($00 fill) or option 1 ($FF fill) boots 9 or 8 frames earlier with identical RAM afterwards. Air's DelayScroll 18983 then breaks through the CPU phase, so the most this could give is -8/-9 after a re-tune, and only if TASVideos accepts a non-default power-on state. It is not controller input, so it does not count under our rules. This is a rules question for the user.

### 3.7 Whole-run coverage-guided fuzzing (gd_fuzz; reproduced by repro_fuzz)

The tools and campaigns are in 2.1 and 2.2.

**Glitches.**
* **G1, spawn flood.** When the spawner's side flag $42 turns right after the camera advanced to the left, every pending entry spawns in one pass, up to 16. The rightmost entries, which are on screen, lose their slot and are skipped until the camera re-crosses them. REPRODUCED. Novelty corrected: v6.2 itself floods at W6 83838 and skips two on-screen enemies, and its Heat 10519 R tap splits a burst. Value 0 found (rank 6).
* **G2, the Bubble 43509 true lag is that spawn burst.** REPRODUCED. Conclusion corrected: an R tap plus L at 43458 or 43460 avoids the lag. The result is zero true lags, the same Mega Man time, and $1C one higher. That is worth 0 under the existing Bubble DelayScroll and fill closure (rank 5).
* **G3, vertical-section desync entries.** A U+D pop or top-out into a wall, then a zip across the right edge of a one-screen vertical section. REPRODUCED directly from v6.2: W4 at 71262, and W1 at 54736, 88 frames earlier than the fuzz found it.
  * W4: closed (repro_fuzz, repro_terrain).
  * W1: closed by me (section 6).
  * The W4 death-warp use stays open (rank 1).
* **G4, W4 0D->0E request timing.** v6.2's 72067 request is the earliest one compatible with the long zip (2,592 REAL variants).

**Proven impossible.**
* **P1 (PGA: A-DISPATCH, A-NOACE):** no never-executed instruction writes Mega Man's position, screen or $F9, the camera or section, $37 or $B0, outside the backward transition (now executed) and the death, game-over, password and title paths. So a time-saving glitch must be a new state or timing combination of code the TAS runs already execute.
* **P2:** a hurt with no free spark slot (F:D371) is unreachable.
* **P3:** the Time Stopper entries of both hit dispatches are unreachable.
* **P4:** Mega Man's state 1 is unreachable.
* **P5 (PIM):** the only phantom platform is the dead Guts deck.

**"Ahead of v6.2" fuzz.** Every hit removed a deliberate cost (the W3 refill, a weapon-switch pause, a page toggle, the W4 Telly hit, death avoidance) or broke a later timing event. Two small hits were not re-optimised (SL):
* Crash 0C->0D requested 3 frames early with D at 27524;
* Air's DelayRightScroll 2 frames early.

Each is below its stage-end rule alone.

**Unknown.**
* The fuzz samples only 1-3-edit neighbourhoods of v6.2 and random rollouts of up to 60-700 frames.
* Index-value novelty was still growing (+5,250 bits).
* Bank C's 33 never-executed paths were not triaged one by one.

### 3.8 The documented-glitch survey (glitch_hunt, audited by audit_glitchsurvey and holecheck_glitchsurvey)

**Coverage.**
* glitch_hunt's 16 items are all worth 0.
* The list was not complete for documented glitches (UNSUPPORTED as a completeness claim). Items found later in forum70 and costed:
  * the Heat-bank Wily warp, where killing the dragon "counts as Heat Man": at least +1,000 frames;
  * Crusher spawn block: NOT-A-HOLE (code plus REAL);
  * Exile Pipi with a platform-type sprite: UNCERTAIN, very low, about 12 frames raw at most;
  * FinalFighter's DelayScroll family: covered by gd_scroll's window proof.
* Several community clips were never reproduced: "velocity zip", "Blocky glitch", "Visan's Ride / rapid respawns", "Egg swaps", "Zombie Anko" (Bubble only; no Crash walls on the route). All are zipless-era tricks, judged irrelevant to any% by argument, not by test.

**Closed by exact physics (ANALYSIS, PIM).**
* Single-zip death warps. The only basins are 30-32 px inside Metal's floor slab.
* Multi-segment wraps: not a hole in robot-master stages or W2.

**Corrections the audit made.**
* There is no mirror (leftward) zip.
* There is a 4th boss start: the Mecha Dragon object at E:B891.
* The ~263-frame death overhead holds only with a held Atomic charge.

### 3.9 Areas no agent owned

* **Per-enemy AI routines (about 100 types).** They are executed, not audited (3.3).
* **Special objects** (Yoku blocks, Crash walls, lifts, clouds, Boobeam walls, dragon blocks). Only their aliasing, timing and phantom-width aspects were checked.
* **Level data.** Zip and death-warp scans exist. Ladder tops next to walls at screen edges (the G3 pattern) were checked only in W1 and W4.
* **Sound-engine internals.** Isolated from game logic by code (3.6 P5).
* **Hardware behaviour.** Not hunted; FCEUX 2.3.0 is the judge.
* **ACE.** Out of scope by the user's decision. Recorded once, not pursued:
  * the W5 dispatch with $AD >= $7F;
  * the hit dispatch with $A9 9-11;
  * about 80 bytes of stack margin above the page-1 object arrays;
  * the sound engine's `STA ($EC),Y`;
  * the unprotected MMC1 control writes at C05D;
  * the 2006 "shutterwily4boss" crash.

---------------------------------------------------------------------------------------------------------------------

## 4. Review status: who checked what

| subsystem | glitch claims | re-run by | as stated | lemma list adversarially reviewed? | corroboration that exists |
|---|---|---|---|---|---|
| terrain | 6 | repro_terrain | 5 (1 DIFFERENT) | no | $37 setters (gd_scroll, pf_static), $F9 writers (pf_static), no leftward zip (REAL t02, audit) |
| scroll | 4 | repro_scroll | 4 (model corrections) | no | transition lengths (gd_flow three-run REAL, audit-23) |
| objects | 6 | repro_objects | 5 (1 NOT-REPRODUCED, with a factual error) | no | boss HP (gd_weapons P5, pf_static L-HIT, boss fuzz) |
| weapons | 8 | repro_weapons | 7 (1 DIFFERENT) | no | energy lemmas (gd_objects, independent) |
| flow | 7 | repro_flow | 5 (1 NOT-REPRODUCED, 1 DIFFERENT) | no | pause minima (pf_search certificates, pf_check) |
| timing | 6 | repro_timing | 4 (2 DIFFERENT) | no | $1C writer (pf_static) |
| fuzz | 3 | repro_fuzz | 3 (2 conclusions corrected) | no | coverage numbers and frontier re-counted by gd_synth |
| **total** | **40** | | **33** | | |

**Errors the reviews caught, showing a single agent's error rate:**
* "Boss invincibility is frozen during the post-pause freeze": false; it ticks from 16 to 5.
* "16 live enemy slots never happen during play": false. It happens in Heat in the fuzz, and in v6.2 itself at W6 83838.
* "No site writes Mega Man's screen": false in code (W2 B:9275 with Y=$10).
* "The Bubble 43509 lag cannot be avoided": false. The same false claim appeared earlier in lag_audit.
* "The first NMI after every stage load takes the lag path": 0 of 16.
* "KOOK carries the hidden phase": false; the carrier is X.count.
* The phantom-ladder frame list was over-inclusive (6 of 8 were not uses).
* "Door 2 costs >= 35 frames from the wrapped corridor": the left route is not reachable at all.
* Window (d) is wider than Y=$1C; a 5th deferral site was missed.
* The pause-+1 guard is dead.
* The showcase A was already used by #4410.
* Novelty: about 10 "new" items were already in our notes or the community record.

Earlier in the project:
* glitch_hunt's "mirror zip" was false.
* glitch_hunt's "boss init has 3 callers" missed a 4th.
* The formal layer also has review findings (pf_check):
  * the hit lemma needs the NMI bank-restore assumption;
  * sa.py computes SHX/SHY addresses wrongly, mitigated because any reachable undocumented opcode raises an OPEN item;
  * three hub-walk sub-claims are false.

**Conclusion.** The glitch claims are independently reproduced. The impossibility lemmas are single-author code arguments with dynamic cross-checks, and two agents overlap on some of them, but no one was assigned to break them.

---------------------------------------------------------------------------------------------------------------------

## 5. New reproduced glitches, ranked by possible saving after the frame rules

Frame rules:
* robot-master stage ends are q8 (pre-W1 savings count only in 16s at the W1 fade);
* the W1 end is exact (a double KO at $1C = 0 mod 16, so savings come in multiples of 16);
* W2 and W3 count in 16s at the W3 fade;
* from W4 on, every rule is q4;
* a removed true lag is worth -1.

| # | glitch (subsystem, verdict) | where | possible saving after the rules | prior | first test |
|---|---|---|---|---|---|
| 1 | Vertical-section desync entry G3 (fuzz; REPRODUCED from v6.2), used for a W4 death warp | W4 sections 0A-0D | If Mega Man reaches k=3 while the camera is still in screen 19 and dies with $0440 >= 1C, he respawns at checkpoint 1C, skipping sections 0B-0D: up to about -370 raw (holecheck_glitchsurvey), about -368 after the q4 rules | very low. It needs two more desync entries above section 0A, none known. k=1 alone loses about 100, k=2 is about 0. The k=1 traversal itself is closed. | Static scan of W4 screens 19-1B for ladder tops next to a solid column whose zip crosses the right screen edge (coll.py); then REAL from repro_fuzz `g3_own.py`'s W4 state |
| 2 | The same G3 entry in W1 | W1 sections 09-0C | It skips map 22, and the walk-only desync route reaches the map-23 exit 83 frames earlier. With at least 32 logic frames saved before pause 3, r1dds's music data (the exit DelayScroll works at s_real -38/-37/-35) would make it -32. | **CLOSED** (section 6) | none |
| 3 | 240-px bob and arrival rule (terrain; REPRODUCED), used as a free-rise request: jump off the virtual floor and request at the apex, instead of at Y244/$F9=FF | W4 71106, 71367, 71848 | At most about 1-2 frames each. In those sections v6.2 jumps off the arrival ladder at once (my s04c), so a higher arrival saves only part of the extra jump. Three frames before room 32 with a ≡ 3 (mod 4) would be audit_wily4's c = 4 step: -3 against v6.5. | low | REAL local search at each site (jump length x request frame), scored by the frame Mega Man reaches the next section's ladder top; then the room-32 blink phase and the Telly aims on the shifted timeline (holecheck_wily4 `aimmodel.py`) |
| 4 | Scroll-check NMI windows (scroll; REPRODUCED), plus the c5 "ahead" fuzz hit | Crash 27207 (request -1, REAL) and 27524 (0C->0D request -3, REAL hit) | Both are $1C frames before the Crash fill. Crash's end is q8 with w=3, so +8 needs 4 frames before the fill plus 1 after (or 8 before), and the cycle-exact DelayScroll 27834 re-timed. As R1's single upstream +8 piece this would be -16 at the end. | low. Both edits fall back later with v6.2's inputs. | REAL joint replay of both edits from 27190; a twlib search for a working DelayScroll check frame 4 earlier; then the chain's in-wall Crash fight for the fifth frame |
| 5 | Bubble burst split (fuzz G2, corrected by repro_fuzz; REAL) | Bubble 43458/43460 | 0 on its own ($1C one higher at the same real time). It is a free $1C-phase knob before the Bubble DelayScroll, useful only inside an R1 build (holecheck_prew1's parity condition). | low | Inside an R1 candidate: re-sync Bubble's zip-2 lags and the DelayScroll with $1C+1 (REAL) |
| 6 | Spawn flood (fuzz G1; REPRODUCED; v6.2 already uses it) | any right turn after a facing-left camera advance | Unknown; 0 found. It can suppress on-screen enemies and specials for one pass, but the burst frame may itself lag. | low | List v6.5 frames where an on-screen object costs time (lags, forced hits or detours), then check for a facing-left advance passing at least 16 entries before them |
| 7 | Post-pause freeze with ticking boss invincibility (objects; REPRODUCED; known from quick_fight2) | mid-fight weapon-switch pauses | Up to 12 frames per pause in a route that switches weapons right after a hit; 0 in the current route, where every in-fight pause is already placed | n/a | Use in robot-master reorder studies only |
| 8 | Door-push wrap / phantom shutter (scroll; REPRODUCED) | Air and Metal door 1 | 0. Door 2 then costs at least about +100, against a 4-12-frame shorter Metal exit teleport. | closed | none |
| 9 | All other new behaviours | | 0 | | none |

Row 9 covers:
* the phantom ladder bit, U+D pop, stale $40 carry, solid-sprite and platform aliasing, $F9=FE and door verticality;
* the camera drag;
* the dead-deck cause, contact-only hurt, child-spawn stale Y (unreachable), Wily Machine guards and the generic hurt glitch;
* the Atomic $F9 cost, Leaf $F9 kill, Time Stopper heal and ghost widths;
* the W5 held-button buffer and relative W5 screens;
* the column overflow, logic doubling, the X.count phase, RNG carry-in and select-load NMIs;
* the W4 0D->0E closure.

---------------------------------------------------------------------------------------------------------------------

## 6. Closed in this synthesis: the W1 vertical-section desync (gd_fuzz G3, repro_fuzz's open lead)

All of this is in `SP/agents/glitchdisc/synth/`.

**1. No open left crossing (ANALYSIS, static ROM, `a01_w1maps.py`).**
* In W1 ($2A=8), the screen pairs 21|22, 22|23, 23|24, 24|25 and 25|26 have no row where column 15 of the left screen and column 0 of the right screen are both non-solid.
* Only 26|27 is open, at rows 10-11.
* So a Mega Man who is one screen ahead of the camera in sections 09-0C can never walk back into the camera's map.

**2. No up exit from section 0C.**
* Screen 26's only ladder is column 3, rows 12-15; rows 0-11 are air, and row 0 is air (no virtual floor and no ladder above the screen).
* Screen 25's only ladder (column 3, full height) is where every section-0B up request must leave from. This holds for all three request rules: the Y<4 ladder rule, the $F9<0 rule (which reads row 0) and the phantom bit (which reads rows 14-15). So the desynced Mega Man always arrives at column 3 of screen 26.
* There he either tops out at Y244 with $F9=FF over air and falls, or climbs to the floor at Y180.
* The phantom-ladder bit would need him rising across Y=0 at column 3, and nothing near the top can support him.

**3. Items cannot help a desynced Mega Man (REAL, `s03`).**
* From the REAL W1 desync (v6.2 to 54736, U x4, U+D x2: Mega Man in screen 23, camera on 22), Item-1 throws from X 54, 52 and 13 are removed on the throw frame: slot flags $61/$41, F:EECD's camera test.
* A throw from X8 facing left spawns on the camera's screen (22:232). It lives, but platform landing (E:8CF4) compares low-byte X, which leaves it 32 px from Mega Man.
* This agrees with audit_glitchsurvey-18 (REAL, Crash).
* `s01` was inconclusive by itself: its throws, desync and control alike, were under a ceiling, so the Item-1 AI at F:E1E4 zeroed the width.

**4. Other routes are dead.**
* W1 deaths with $0440 >= 21 respawn at screen 21 (BB06 = 00 09 16 18 21 21), which is behind.
* The only residual is a hurt (vy +1.25) at Y < 1.25 over column 3 while Mega Man falls from the arrival top-out. Contact uses only low-byte X, so a screen-25 enemy could do it. REAL `s05`: in v6.2's section 0C the only objects are two id-21 emitters at 25:16 (Y56 and Y136) and their shots, all gone 71 frames into the section. There is no candidate.

**Verdict.** Closed (PROVEN-IN-MODEL on the ROM maps plus the request-rule lemma). Had it worked, it was the round's largest lead (-32).

---------------------------------------------------------------------------------------------------------------------

## 7. What we can and cannot claim about "no other glitches exist"

**We can claim:**

1. **Where an unknown glitch would have to live (PGA: A-DISPATCH, A-NOACE).**
   * Every instruction reachable without ACE was either executed (18,351 opcode starts) or listed and read (974).
   * The listed remainder cannot move Mega Man, the camera, the section, the scroll request or the checkpoint outside death, game-over, password and title code.
   * So an unknown time saver is a new combination of states or CPU timing in code the TAS already runs, or ACE, or an FCEUX-specific effect.
2. **Classes that save nothing for any input (PGA; assumptions in section 1):**
   * no frame-rule bypass;
   * no shorter transition, door, READY, boss intro, fill, post-kill sequence, weapon-get screen, Wily map, W5 event or death wait, except the known levers (exit height, $1C phase, the Atomic $36 cut; OAM stalls only lengthen);
   * no skipped boss, refight, weapon, stage or section;
   * no created energy;
   * no leftward zip;
   * no horizontal motion above 16 px per frame and no vertical jump other than the -240 wrap;
   * robot-master hits at least 19 frames apart;
   * no item movement between a killing throw and the stage end.

   Together these fix 58% of the run's frames and bound the rest.
3. **What the search found.** About 7.4M REAL fuzz frames and 12,800 menu trials found about 27 new behaviours. None saves a frame after the frame rules (section 5).

**We cannot claim:**

* **That the lemmas are proven in the formal sense.** pf_static's sound analysis did not converge; the lemmas are hand-derived readings with REAL cross-checks.
* **That the lemma lists were adversarially reviewed.** Section 4 shows they were not, and that single-author statements were wrong at a measurable rate.
* **That state combinations are exhausted.** Instruction coverage saturates long before state coverage. G3 was found only in this round, and its two uses were closed by hand-written map arguments, not by a search over all states. Three kinds of setup are searched only locally:
  * long multi-step setups (desync chains, stale-slot seeds carried across stages, combinations of wraps and aliases);
  * CPU-cycle effects at new places (DelayScroll-type, which depend on load and music phase);
  * enemy-specific behaviour.
* **Anything about ACE** (excluded by decision) **or about hardware differences** (the judge is FCEUX 2.3.0).

**In short:**
* for the classes in item 2, "no, under named assumptions";
* for new movement and state combinations, "none found by a large search; not proven";
* for ACE, "not examined, by decision".

---------------------------------------------------------------------------------------------------------------------

## 8. What a real proof would need

1. **A converged sound static analysis (pf_static)** for the flow-critical bytes ($1C $37 $F9 $0440 $0460 $04A0 $20 $1F $38 $14 $15 $B0 $2A $9A $BC $05AA $06C1 $B1 $2C $36) and for the joypad-read sites. The lemmas of 7.2 would then become PROVEN up to A-CORE.
2. **A holecheck pass on every gd_* lemma list**, the same method as the closure audit, which found 6 frames.
3. **For movement:** an exact physics model and certified per-section searches with sound pruning lemmas.
   * rc_offscreen's rcmodel.py is REAL-exact on 1,296 post-kill frames.
   * pf_search handles only about 4 gameplay frames exhaustively today.
   * Ladder-top-beside-wall sites (the G3 pattern) should be enumerated in every stage.
4. **For CPU timing:** for every section end on the route, the cycle gap to a DelayScroll over all music phases. glitch_hunt did this only for Air's corridor (14.4k cycles short).
5. **For the robot-master order's "unknown hand-over X":**
   * handover_hunt's channel census repeated for each candidate order;
   * plus the structural rule that the weapon spawn F:D3DD never writes $0480,X, $04C0,X or $06E0,X.

   The order itself stands as an ESTIMATE with a margin of at least 140 frames (route_judge), PROVEN-IN-MODEL for the Air link.

ACE and hardware differences would stay outside even then.

---------------------------------------------------------------------------------------------------------------------

## 9. Files

* **Subsystem notes and reports** (REPORT sections inside each NOTES.md, because report files are refused for subagents): `SP/agents/glitchdisc/{terrain,scroll,objects,weapons,flow,timing,fuzz}/NOTES.md`.
* **Reproductions:** `SP/agents/glitchdisc/repro_{terrain,scroll,objects,weapons,flow,timing,fuzz}/NOTES.md`.
* **Coverage maps:** `SP/agents/glitchdisc/fuzz/work/{base_*,final_union}_{ins,br,idx,pg}.npy`, `a04_frontier_final.txt` and `a02_dispatch.txt`. Every fuzz rollout replays REAL with `fuzz/r00_repro.py CAMPAIGN RID`.
* **Earlier survey and audit:** `SP/agents/glitch_hunt/GLITCHES.md`, `SP/agents/audit/glitchsurvey/LEDGER.md` and `SP/agents/audit/holecheck_glitchsurvey/NOTES.md`.
* **Proof layer:** `SP/agents/proof/{static,search,check,doc}/NOTES.md`.
* **This synthesis** (`SP/agents/glitchdisc/synth/`):
  * `NOTES.md`;
  * `a01_w1maps.py` (ANALYSIS, static);
  * `s01_w1desync_items.py`, `s02_i1trace.py`, `s03_w1desync_items2.py`, `s04_w4requests.py`, `s04b_w4requests.py`, `s04c_w4sec.py`, `s05_w1sec0c_enemies.py` (all REAL, plain master core);
  * logs in `work/`.
