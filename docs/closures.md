# Closure ledger: what is proven and what is not

audit_synth, 2026-11-07. This merges the adversarial closure audit (workflow wf_6d67179b-35d): six area ledgers (`agents/audit/<area>/LEDGER.md`), six hole checks (`agents/audit/holecheck_<area>/NOTES.md`), and the later results that changed a verdict (r1dds, the routing deep-dive and routing-closure agents, the glitch-discovery and proof workflows). Paths such as `agents/...` refer to the project's working notes, which are not part of this repository; each entry here states its evidence on its own.

Committed best: **v6.6 = 84,995 frames**, 284 under publication #4410. Frame numbers are v6.2's unless marked. v6.5 is identical to v6.2 before frame 74299 (Wily 4) and runs 1 to 6 frames earlier after it. v6.6 is identical to v6.5 before frame 80264 (the Wily 5 Crash Man refight) and ends 9 frames earlier.

Contents: 1 The short answer. 2 How to read this. 3 The big questions (R1 and R2, the robot-master order, unknown glitches). 4 Reopened leads, ranked. 5 Recurring blind spots: a checklist. 6 The ledgers, area by area.

## 1. The short answer

**What was reviewed, and how.** Six auditors listed every closure in their area ("dead end", "impossible", "optimal", "not feasible") and classified the argument behind it: 365 entries (a few claims appear in two areas). Each auditor looked for holes and tested the cheap ones. A second agent per area then tried to refute each hole and looked for holes the auditor had missed. So every closure has had one adversarial reading, and every hole that was raised has had two. A closure the auditor judged sound was not re-derived by a second agent unless a hole check ran into it.

**Was the user right?** Yes, on all three points.
* Closures with exactly the hole the user described (a variable held fixed that was in fact free) were worth frames. 85,010 became 84,995 during this review and its follow-up:
  * v6.3, -4: the Wily 5 Heat Man refight had been assumed bound by his AI and was never examined (critic_v62, same review round).
  * v6.4, -1: "the Wily 4 DOWN shield throw gains nothing" had only paired the throw with the two obvious menu-frame placements (audit_wily4).
  * v6.5, -1: a Heat refight lag frame called "1,370 cycles over" was only just over; nobody had moved Mega Man before Heat Man aimed at him (audit_w5).
  * v6.6, -9: the first half of the Wily 5 Crash Man refight had never been varied. With the first volley fired before Crash Man can react, all three hits come 10 frames sooner and the bomb's lag frame disappears (the audit's lead 1, built by crashw5).
* The robot-master order claim was a paper estimate. The follow-up work measured the terms that could have reversed it and found no faster order. That result is an ESTIMATE with a few measured pieces, not a proof (Section 3.2).
* There is no proof that no unknown time-saving glitch exists (Section 3.3).

**Strength of the closures**, by the weakest step of each argument, as the auditors recorded it:

| area | entries | PROVEN | PROVEN-IN-MODEL | SEARCH-LIMITED | ESTIMATE | UNSUPPORTED | OVERTAKEN | other | holes raised | REAL-HOLE | UNCERTAIN | NOT-A-HOLE | frames found |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| prew1 (robot-master stages, before Wily 1) | 75 | 16 | 15 | 20 | 18 | 2 | 3 | 1 | 11 | 8 | 1 | 2 | 0 |
| wily123 (Wily 1-3) | 48 | 11 | 19 | 9 | 5 | 2 | 2 | 0 | 6 | 3 | 1 | 2 | 0 |
| wily4 | 43 | 6 | 21 | 3 | 6 | 1 | 4 | 2 | 6 | 1 | 1 | 4 | -1 (v6.4) |
| w5 (refights, hub) | 69 | 13 | 32 | 10 | 4 | 1 | 9 | 0 | 4 | 2 | 1 | 1 | -1 (v6.5), -9 (v6.6) |
| wmw6 (Wily Machine, Wily 6, alien) | 64 | 19 | 18 | 8 | 5 | 1 | 13 | 0 | 7 | 0 | 0 | 7 | 0 |
| glitchsurvey (glitches, route level) | 66 | 20 | 23 | 3 | 9 | 5 | 6 | 0 | 7 | 0 | 2 | 5 | 0 |
| total | 365 | 85 | 128 | 53 | 47 | 12 | 37 | 3 | 41 | 14 | 6 | 21 | -2 |

prew1's class counts are audit_synth's, from its class column; the others are the auditors' own. The hole checks then upgraded about ten entries (for example the alien-fight and room-0x28 closures). Of the 14 REAL-HOLEs, 2 became the v6.4 and v6.5 frames, and 1 (R1 through the Wily 1 exit scroll) was closed again by a build attempt (r1dds).

So about one closure in four has a complete argument. A third are exhaustive only inside a named model. The rest are searches that found nothing, paper estimates, or bare assertions. pf_doc's lint found that all 16 "impossible/optimal/closed" statements in docs/whole-game-analysis.md, and all 4 in the README, carry no strength label; this ledger supplies one for each underlying claim.

**What "PROVEN" means here.** A complete hand argument from the ROM code or from physics, written by one agent and read adversarially by a second. Nothing is machine-checked end to end. Under the stricter standard pf_doc drafted (ground truth = the ROM plus FCEUX's semantics; every step mechanically checkable), the best closures are PROVEN-GIVEN-ASSUMPTIONS. An example is the nine certified W5/W6 pause searches, which rest on a state-identity and an input-taint assumption; the referee (pf_check) re-ran all 11 search certificates on both FCEUX cores and found them VALID. The whole-program static analysis that would turn the "who writes this byte" lemmas into proofs has not converged (pf_static).

**Closures that now rest on a complete argument or a sound bound** (examples):
* Heat stage, health fill to stage end (prew1-06): Heat Man's AI code, the door clamp that fixes Mega Man's start X, the earliest first hit (REAL), and the contact box that forces the 29-frame teleport.
* The Wily 5 refight skip needs arbitrary code execution (w5-57, glitchsurvey-04): code.
* All nine W5/W6 pause menus are at their minimum: certified exhaustive search (pf_search), re-checked by pf_check.
* Heat refight kill to Air refight fill (w5-16, w5-47): Heat Man's last dash cannot give 4 more frames (the bound fails by 1/256 px), and the hub walk is exactly minimal (969 REAL runs; the last 4 frames certified).
* Wily Machine phase 1 cannot reach the next 4-frame step (wmw6-08): a sound relaxation over every jump schedule and throw allows at most 26 of the 28 hits.
* Wily Machine phase 2 cannot die before fill+60 (wmw6-19): relaxation over every movement; the floor is the only surface (RAM scan).
* The room-0x28 walk before the Wily Machine is exactly minimal (wmw6-13/14): speed and air-frame bound from the ROM map.
* The alien fight allows at most 6 hits before the final burst (wmw6-49): a relaxation calibrated on REAL measurements.
* Wily 4 room 0x1E's Telly hit (wily4-11): exact homing model (bit-exact on the run), REAL BFS, and a dynamic-programming bound over Mega Man's real ladder positions.
* Bubble to Wood hand-over: only Bubble Man's room can end with Mega Man above the screen (rc_offscreen's proof).

**Open (not proven either way):** R1 (+16 before Wily 1) and R2 (+16 at the Wily 3 fade), the robot-master order, the absence of unknown glitches, and the Wily 5 refight order (an ESTIMATE: the walk legs of other orders were never measured; the variant the audit raised costs about +70).

## 2. How to read this

* **Classes** judge the argument behind a closure by its weakest load-bearing step. PROVEN: a complete argument from code or physics covering every case. PROVEN-IN-MODEL (PIM): exhaustive inside a stated model or family; the holes column says what it leaves out. SEARCH-LIMITED (SL): a search found nothing but did not exhaust the space. ESTIMATE (EST): arithmetic or paper reasoning. UNSUPPORTED (UNS): asserted without evidence. OVERTAKEN (OVT): contradicted by later work.
* **Verdicts.** REAL-HOLE: the hole check agrees the closure does not cover the hole (the gain may still be unlikely). NOT-A-HOLE: the hole check refuted the hole. UNCERTAIN: neither. "realised": it became a committed frame. "holds": the auditor found no hole (no second check). "closed": the auditor completed the argument.
* **Labels.** REAL = plain emulator replays of real inputs. ANALYSIS = RAM pokes, hooks or models. code = read from the ROM disassembly.
* **Gains** are frames at the end of the movie, after the frame rules. The game's frame counter (`$1C`, "the counter" below) advances on every frame except true lag frames, and the game's waits poll it: health fills and Wily maps wait for a multiple of 4 (q4), robot-master stage ends and weapon refills for 8 (q8), the Wily 1 and Wily 3 death fades for 16 (q16). So a saving before Wily 1 only counts as a 16-frame lead at Wily 1 ("R1"), one in Wily 2-3 as 16 at the Wily 3 fade ("R2"), and after Wily 3 in steps of 4. A removed true lag frame always counts 1.
* **DelayScroll (DDS):** a scroll triggered when the frame interrupt lands inside a bank switch at an exact CPU cycle. It depends on one frame's CPU load and on the music. **Hidden phase:** FCEUX alternates frame lengths, so shifting the timeline by an odd number of real frames moves every cycle-exact check by a few cycles, even with identical RAM (pf_check confirmed this with REAL pairs of states).

## 3. The big questions

### 3.1 R1 and R2 (16-frame leads)

**R1: +16 frames before Wily 1.** Every robot-master stage ends on a q8 rule, and the Wily 1 end needs the counter exactly at a multiple of 16: it is a double knockout that runs two fade steps in one frame (wily123-04). So the Wily 1 start lead has to go from 80 to 96. The project called R1 closed after v5.6. The audit classed that as an ESTIMATE: it was a conjunction of per-stage verdicts, several of them never searched (prew1-63).

The hole check changed the picture (holecheck_prew1, ANALYSIS). The Wood DelayScroll that was "1 CPU cycle late" (prew1-52) is a parity effect. When the Wood stage starts an odd number of real frames later (RAM identical, only the hidden phase differs), 5-8 configurations land in the window, and a follow-up reaches the frame that a Wily 1 start at 96 needs. So R1 now needs one of:
* one upstream piece worth +8 counter frames whose real-frame lead is odd. Flash qualifies: one stage frame plus the existing fight -1 gives +8 counter frames but +7 real frames, because an odd counter makes the boss-spawn frame lag;
* an even piece plus one removed true lag (which flips the parity);
* Metal's 13th corridor zip plus one more frame before Metal's fill (+16 by itself, no Wood frame needed);
and then the full re-sync downstream: the Air DelayScroll (hidden phase), the cycle-exact checks of Crash, Bubble, Wood and Wily 1, the random rolls, the Wily 1 start-96 recipe, Wily 2 at counter -16 (recipe ready), Wily 5/6. That is many agent-days.

| piece | gives | status after the hole check |
|---|---|---|
| Flash stage frame (prew1-10/62) | +8 at the Flash end, odd real lead | SEARCH-LIMITED (pruned beams); REAL-HOLE; about 5% |
| Heat stage before the fill, 3 frames (prew1-07) | +8 at the Heat end, even | never searched; REAL-HOLE; a 2008 forum post names a 1-frame-faster ladder zip whose frame is lost in the appearing-block room |
| Air pre-fill 4 + double KO (prew1-14/17) | +8 | UNCERTAIN, below 2% |
| Crash in-wall fight (prew1-23) | +8 if the kill reaches 28479 with 3 pre-fill frames, or 28475 | REAL-HOLE, about 3% |
| Metal 13th corridor zip (prew1-36/56) | +8; +16 with 1 more pre-fill frame | REAL-HOLE, low (about 5%) |
| Quick, Bubble | +8 | closed (PROVEN / PROVEN-IN-MODEL) |
| Wood DD1 in the odd parity (prew1-52) | the missing frame | REAL-HOLE; solved in ANALYSIS for odd shifts |

**R1 through Wily 1's own exit DelayScroll** (wily123-01) was reopened by holecheck_wily123 ("works from today's Wily 1 start with about 9-10 more Wily 1 logic frames and 5 induced lags") and closed again by r1dds. At the needed music frame the check lands about 301 cycles late against a 33-cycle window (validated ANALYSIS model), and only 7 of the 16 logic frames exist (REAL). It is SEARCH-LIMITED. It would reopen with 32 Wily 1 logic frames, where the check does work (lead 9).

**R1-lite (-8)** stays closed by code: the extra Item-2 sled spends the last unit (prew1-60/61), unless a zip into building 2 frees the step sled (wily123-10, UNCERTAIN, low).

**R2: +16 at the Wily 3 fade.** r2_w23 closed it over whole route families, with every other Wily 2/3 segment held at the WIP's or the publication's inputs. Those were optimised under a fade that absorbs anything below 16, so nobody had a reason to save 1-15 frames there (wily123-17). The hole check narrowed it: the Wily 2 part is close to forced, the Wily 3 water zip is locked (throw + 94 frames behind a random damage boost; odd leads fail), and the big Wily 3 shortcuts are closed (REAL). Left: a per-frame search of Wily 3 after the refill, the 194 Wily 3 underwater slow-down frames (each one avoided is one counter frame), and skipping the Wily 3 refill (wily123-47). OPEN, low.

### 3.2 The robot-master order (the user's example)

The old claim (route_study; docs section 9) was "no gain once the hidden hand-overs between stages are counted". The user's objection was right: it did not show that another routing cannot supply the hand-overs, or that an unknown hand-over does not favour another order. The audit classed it ESTIMATE (prew1-68). Since then:
* handover_hunt (REAL; hooks that only observe) listed every byte a stage reads that the previous stage left behind, on v6.2's route and on the publication's, plus the hidden CPU phase. The weapon-slot seeds do not tie the order: any vertical weapon can re-create them. `$F9`, the high byte of Mega Man's Y position, does: Bubble to Wood (Wood then starts with a zip) is worth at least about 500 frames, Crash to Quick 19.
* rc_offscreen (code, with a model that matches 649 of 649 REAL frames) showed that only Bubble Man's room can end with Mega Man above the screen, so Bubble to Wood is forced. Crash to Quick could in principle be replaced only by a Wood kill, at a cost of hundreds of frames.
* route_model scored all 40,320 orders, each term with a low and an estimated value. route_judge reviewed it and found four errors. It added a cloud-model lemma: Air without Item 1 costs at least 166 frames (PROVEN-IN-MODEL). It also showed that making the `$F9` hand-overs free from any predecessor still gives no better order: the order is held by the item and weapon chain, not by the hand-overs. Verdict: ESTIMATE, margin at least 140.
* rc_item2 (REAL): an Item-2 sled ride in Heat saves 131 frames when Air and Flash come before Heat. That is more than the ~100 route_model had assumed, so route_judge's closing condition fails. With every other term at its estimate, no order is faster. But three orders (for example Air, Bubble, Wood, Flash, Heat, Crash, Quick, Metal) would be 10-50 frames faster if Bubble without Item 1 cost about 0 and a Buster-only Bubble fight reached its bound (condition b + f <= 2, up to <= 48 in looser scenarios).
* rc_bubble8 (REAL inputs from v6.5's states; only the selected weapon and the weapon ownership bits were poked) measured the missing term:
  * route_judge's Item-2 sled entry into the screen-8 ceiling is impossible. The sled dies when the point 16 px ahead and 32 px above it is solid, and the landing snap lifts Mega Man at most 4 px where 25 are needed (a code reading by one agent that no second agent re-derived: PROVEN-IN-MODEL at best).
  * A new entry without Item 1 exists. The downward scroll from screen 7 places Mega Man at Y 7 at his pixel X, and with X at least 104 he is inside the ceiling and zips as in v6.5 (REAL).
  * Reaching that X costs time. Screen 7's shelf holds Mega Man at X 57 or less until Y 204, and the scroll fires at Y 232, so he has 28 px of fall to cover 47 px sideways. A pause resets his fall speed; 4 pauses give at most 45.1 px (model with exact 8.8 physics, exhaustive over the fall heights and phases, and it reproduces the REAL runs), so at least 5 are needed.
  * The REAL run with 5 pauses ends the zip 65 frames after v6.5 does. Screens 6-7 without Item 1 cost 8 more. So Bubble without Item 1 costs about +73, and at least about +52 after an allowance of 6 frames for savings elsewhere in screens 5-7 (the allowance is an ESTIMATE from warmCabin's zipless TAS).
  * +52 is above every threshold of rc_item2's scenarios (2, 16, 34 and 48). The three orders are slower than v6.5's order, not faster.
* rc_air (a REAL Air crossing without Item 1) was cut off before it finished. Its partial model work points to a cost well above route_judge's lower bound of 166. The verdict does not depend on it: the comparison already used the lower bound, which is the value most favourable to the other orders.

Status: no faster order found (ESTIMATE). Every other order has a margin of at least 140 frames on route_model's numbers, and the last group that could have beaten v6.5's order (Air and Flash before Heat) is closed by rc_bubble8's measurement. What keeps this from being a proof:
* route_model's terms are estimates with lower bounds, not measured costs, except where a later agent measured them (the Item-2 Heat ride, the Bubble entry, the two `$F9` hand-overs).
* rc_bubble8's 6-frame allowance and its argument that the crab on the last shelf before the drop cannot be passed without a weapon pause are a search and a kinematic argument (SEARCH-LIMITED), not a proof over all inputs.
* On unknown hand-overs: the channel list is complete for the three routes replayed (v6.2, the publication, warmCabin's zipless TAS). Another route can read other stale object fields, so the list is SEARCH-LIMITED: it is not a proof for every order.

### 3.3 Unknown glitches

We have no proof that no unknown time-saving glitch exists, and this ledger does not claim one. The glitch-discovery workflow (its own summary, GLITCH_COVERAGE.md by gd_synth, is in progress) gives evidence of three kinds:
* **Lemmas over all inputs**, which therefore also cover glitches nobody has found. The frame counter has one writer and advances exactly once per completed wait call; at most one interrupt runs per frame; a lag frame runs only the sound and one random-number update. So no glitch can make a frame rule fire early; only fewer game, slow-down or menu frames, or fewer true lags, can help (gd_timing). Mega Man has no leftward zip, moves at most 16 px per frame horizontally outside transitions, and his only vertical jump is the -240 px wrap (gd_terrain). Boss HP changes only in the hit handlers, at least 19 frames apart for robot masters (gd_objects). Menus, intros, fills, death waits and Wily maps, 58% of the run's frames, are fixed loops that ignore input (gd_flow). These are argued from code, but the indexed-store part of the "who writes this byte" lists stays open until pf_static converges, so they are PROVEN-GIVEN-ASSUMPTIONS at best.
* **Coverage.** About 6 million REAL fuzz frames from 1,899 starting states saturated code coverage. The reachable code that the runs never execute writes Mega Man's position, screen or `$F9`, the camera, the scroll request or the checkpoint only in death, game-over, ending and password paths. So an unknown time-saving glitch would have to be a new combination of states and timings in code the run already executes.
* **New behaviours.** More than 20 newly documented behaviours, almost all reproduced by a second agent (a few corrected). None saves a frame after the frame rules. Two open leads came out of this work: "desyncs" in Wily 1 and Wily 4, where Mega Man uses the next section's map while the camera stays behind (leads 3 and 9).

That is evidence, not proof.

## 4. Reopened leads, ranked

Ranked by expected frames per agent-day of the first test. Priors are the agents' own where they gave one; "(synth)" marks mine. Every lead that changes the counter also needs the usual downstream re-sync (random rolls, platform seeds, DelayScrolls through the hidden phase).

| # | lead (ledger ids) | verdict | gain at the end | prior | cost | first test |
|---|---|---|---|---|---|---|
| 1 | W5 Crash refight: the never-varied first half (w5-38, "H3") and the bomb-explosion lag (w5-40, "H2") | realised: v6.6 (-9) | done | - | - | The first volley is fired on the first input frame, when Crash Man cannot react; a later B press fires nothing and only makes him jump into it. Hits at 80298 and 80318, kill at 80338 (v6.5: 80308, 80328, 80348); the bomb explodes after the kill, so the lag frame is gone. What is left: an exhaustive search over B presses in a model of the fight finds no kill at 80336 or earlier (PROVEN-IN-MODEL: the model reproduces v6.5's fight; it ignores the bomb and contact damage, which only makes kills easier), and the next 4-frame step needs a kill at 80335 |
| 2 | W4: counter frames saved before room 32 (audit_wily4's rule arithmetic + repro_terrain) | closed in the families searched (SEARCH-LIMITED); no frame found | -3 for 2 real frames plus the spare menu frame, -4 for 3 | low | days for a wider search | Done, all REAL: (a) the free-rise scroll requests at 71106, 71367 and 71848 cannot come earlier with a usable arrival (w4a3, exhaustive over jump and request frames in that family); (b) the screen-1C pause placement is already the best of 18 start frames; (c) every single-input substitution followed by a 1-3 frame deletion, on all nine segments from screen 16 to 1F: 51,453 trials, 0 hits; (d) screen 19's climb (w4s19): only one Item-3 lift can exist, the second cannot be thrown before 71629, and none of 16,416 later or higher throws can be boarded (Mega Man gets at most 11 px above the lift where the landing rule needs 12). Not covered: re-plans that change several inputs at once outside these families, and a second pause on screen 19 to free the lift slot sooner |
| 3 | W4 desync death warp (holecheck_glitchsurvey; missed by the audit) | closed for a one-screen desync (PROVEN-IN-MODEL, one agent, not re-derived by a second); larger desyncs have no known entry (SEARCH-LIMITED) | none: it loses at least about 140 | very low | - | w4warp, with pokes on v6.5's states: a death costs 398 frames from the lethal hit to control at checkpoint 1C, and the respawned Mega Man cannot redo the screen-1C ceiling zip, which costs about 103 more. Falling below the screen does not kill on screens 18-1B (it scrolls down), screens 19 and 1A have no enemies, and the nearest spikes are in map 1E. A one-screen desync skips about 219 frames, so the warp loses. The estimate of -370 assumed a 293-frame death, a pit death and no lost zip; none of the three holds. A two- or three-screen desync needs a second way into a wall: the ladder-top geometry of the known entry exists only at map 18 column 13 (static scan of maps 18-1B). Untested: a lift or the screen-19 pop pushing a desynced Mega Man into a wall |
| 4 | Skip the W3 weapon refill (wily123-47, reformulated) | REAL-HOLE | -16 if at most 28 frames slower, -32 if at most 12 | low | half a day for feasibility | ANALYSIS: climb screen 0x25 with one Item-1 platform. Caveat (synth): since v6.3 the 2 spare Item-1 units set the Wily 6 slot-4 seed, so on v6.5 Wily 3 may use only 1 platform after screen 1A unless that seed gets another knob |
| 5 | W3 Guts Tank double KO (holecheck_wily123; missed by the audit) | open; gd_timing and repro_timing call it likely infeasible | -20 (fade -16, teleport -4); -4 in the weaker form | about 2% | hours | Damage budget: where can Mega Man take 6 hits of at most 4 at forced waits? (At most 3 fit the tank's fixed 309-frame wait with 111-frame invincibility.) Then head contact in the kill frame on a counter multiple of 16 |
| 6 | Pre-W1 Crash kill lag 28484 (prew1-27, -23) | REAL-HOLE | -1 directly | 15-20% | 1-2 days, plus downstream DelayScroll checks | REAL beam over 28440-28483 (volley-2 timing and direction, which slot makes hit 2, floor holds, jump, zip). Keep one object fewer at the kill (the slot-3 tornado, the stuck bomb or a shutter: deleting any one removes the lag, ANALYSIS), Mega Man in the wall, and Quick's seeds (the slot-3 tornado makes `$4C3`), or re-solve Quick |
| 7 | R1 with one odd-lead upstream piece (prew1-63, -52 with -10, -07, -36) | REAL-HOLE | -16 (-15 if the piece costs a lag frame) | about 5-10% per piece | 1-2 days per piece; then many agent-days | Flash: REAL beam over 3546-4427 bucketed by height and air state, without the X/damage pruning, plus a full screen-07 BFS. Heat: read the appearing-block spawn code (the 2008 "randomness"), rebuild the 1-frame-faster ladder zip, keep the frame through the block room. Metal: REAL BFS of every landing height at X 200-216 before pause 4 |
| 8 | R2 via the W3 route after the refill (wily123-17) | REAL-HOLE, narrowed | -16 | low | days | Classify the 194 W3 underwater slow-down frames (avoidable when Mega Man's Y-4 point is out of the water), then REAL per-screen beams over 66285-67253 and screens 0x20-0x25. Route B also needs the water zip re-solved at its odd lead |
| 9 | W1 desync shortcut feeding R1 through the W1 exit DelayScroll (gd_fuzz G3, repro_fuzz; r1dds) | open | -16 to about -30 (needs at least 25 more Wily 1 logic frames before pause 3, plus 2-5 induced lag frames) | low | days | Find an up request out of section 0C from map 26 (no ladder above its floor; candidate: a phantom-ladder rise at column 3 from an item platform near the top) |
| 10 | Air: pre-fill frames + double KO (prew1-14/17, glitchsurvey-44) | UNCERTAIN | -16, as an R1 piece | below 2% | hours to settle | Code: can Mega Man fire in the hurt state? List damage sources during Air's idle Item-1 rides. Close it if neither works |
| 11 | Exile "Pipi + platform sprite" glitch, Air screen 6 (glitchsurvey-38) | UNCERTAIN | at most about 12 raw in Air; an R1 piece only if it reaches 8 | very low | hours | Read the Pipi and egg code for writes to the platform width/top (`$0160`/`$0170`) or slot swaps; one ANALYSIS run in screen 6 |
| 12 | W4 room-34 sled seed FA-FF (wily4-05) | UNCERTAIN | 0 alone; -1 inside a set reaching door lead 4-5 | low | days | Only if lead 2 or another saving after room 32 appears: room-33 descents whose sled lands at least 28 frames earlier |
| 13 | W1 building-2 zip (wily123-10) | UNCERTAIN | frees the step sled's Item-2 unit, which reopens R1-lite (-8, with re-syncs) | low | hours (map) | Embedding mechanisms at X 8032-8159 around frames 53900-54030 (needs 16 px into the wall; item snaps give at most 8) |
| 14 | Robot-master order (prew1-68) | closed as an ESTIMATE (Section 3.2) | 0 expected | very low | days per order | A proof needs measured costs in place of route_model's estimates. The cheapest next check is a REAL Air crossing without Item 1, which rc_air started |

Outside the audit: repro_timing found that FCEUX 2.3.0 honours an fm2 `RAMInitOption` key. A non-default power-on RAM removes 8-9 boot frames, but Air's DelayScroll then breaks and needs re-tuning. Whether TASVideos accepts a non-default power-on state is a rules question, not a closure.

## 5. Recurring blind spots: a checklist for future closures

Each item is the question to ask before calling something closed, with the places where it was missed.

1. [ ] **Fixed trajectory.** Is the bound derived over all inputs, or over the trajectory, route or plan family at hand? (Heat refight "AI-bound": v6.3, -4. "WM1 -1 impossible" held Mega Man's left/right path fixed: v6.0, -4. The W5 Crash first half held fixed: lead 1. quick_fight2's plan families.)
2. [ ] **Window too narrow.** Does the search include the inputs that create the event, not only those near it? (The Heat lag was tested only on the lag frame; the fireballs were aimed at Mega Man 58 frames earlier: v6.5, -1. The Crash refight lag search held Crash Man's jump trigger fixed.)
3. [ ] **Mechanism taken from a profile.** Was the stated cause confirmed by removing it (delete one object: does the lag go)? ("1,370 cycles over" was marginal. The Crash refight lag was the bomb explosion, not the kill frame. The Bubble screen-8 "blink candidates" are not sprite-draw lags. The Telly homing model "other axis proportional" was wrong.)
4. [ ] **Poke models freeze hidden state.** Does the closure depend on a cycle-exact check, the music or the random number, which a counter poke does not move? (wm2_gaps' "+4" was +3, because the real shift moved the Wily 6 load lag through the music. One real frame of shift flips the hidden phase: flash11's broken Air scroll, Wood DD1's parity. RAM-identical REAL states diverge.) Test real shifts of both parities.
5. [ ] **One lever at a time.** Were combinations that reach the next rule step evaluated? (The DOWN throw plus a menu frame after room 32: v6.4. Air pre-fill plus a double KO. Wood's frame plus one upstream piece.)
6. [ ] **Conjunctions.** If a gain needs several pieces, is each piece's status listed? ("R1 is closed" was an AND of piece verdicts, several never searched. "A lone +8 is worthless" ignored that +8 is a piece.)
7. [ ] **Inherited optimality.** Was the segment ever searched under today's rule table, or inherited from a run optimised under a different rule? (WIP/publication Wily 2/3 segments optimised under a q16 fade; the Heat stage before the fill; the chain's in-wall Crash fight; chain pause menus with 1-2 frames of slack; the WIP's Wily 4 rooms 33/34, which hid the DOWN throw.)
8. [ ] **Paper costs.** Is the cost measured or estimated? (Wily 5 order legs never measured; "minimum 6 pauses" was a miscount; route_model's ~100-frame Item-2 "bound" was -131 REAL; its +70 corridor term was +16 REAL.)
9. [ ] **Survey completeness.** Does "we checked all known X" name its source list? (GLITCHES.md missed at least five glitches documented in the forum thread on disk; "only Bubble's room ends above the screen" was unsupported until rc_offscreen proved it.)
10. [ ] **Couplings.** Does the closure list what a change breaks downstream (seeds, `$F9`, energies, random rolls, hidden phase, budgets)? (The Crash kill lag versus Quick's seeds; Wily 6 seed windows valid only for today's Wily 6 inputs; the spare Item-1 units now spent on a Wily 6 seed; the exact Metal Blade budget.)
11. [ ] **Search artefacts.** Is "success" checked with a positive control and against late failures? (Spike deaths that freeze Mega Man were counted as survivors; 30-frame merge tests were fooled by scroll freezes; model bugs such as jmodel's ground-frame X and a START on an underwater skip frame; beams pruned by X.)
12. [ ] **Rule arithmetic.** Were the rules re-measured on the current base with real shifts? (The Wily 1 end is exact, not q16. The Bubble fill needs the joint counter/`$FC` table. Flash's +4 counter frames are +3 real. A Boobeam kill 2-3 frames earlier gives -3, not 0.)

## 6. The ledgers, area by area

Columns: id; claim (short); class; evidence; holes (what the evidence leaves out); verdict (hole check and later work). "-" means nothing to add.

### 6.1 prew1: robot-master stages before Wily 1 (audit_prew1; hole check holecheck_prew1)

75 entries; no frame found yet. Main changes: R1 is open again (Section 3.1); the Heat post-fill segment is now PROVEN; the chain's pause menus have 1-2 frames of slack in six places (REAL BFS), each load-bearing when cut alone; the Heat stage before its fill and the chain's in-wall Crash fight were never searched.

| id | claim | class | evidence | holes | verdict |
|---|---|---|---|---|---|
| prew1-01 | Pre-W1 savings survive the Wily 1 end only in 16s | PIM | counter pokes; fade code | pokes do not move real-time-locked events | holds |
| prew1-02 | The Wily 1 map quantises the Wily 1 start lead to 80/88/96 | PIM | ANALYSIS poke | the poke does not move the music | holds |
| prew1-03 | Pre-W1 rule table (slack per fill and stage end) | PIM | counter pokes (metal4, critic_rules, flash11) | misses parity effects (an odd counter makes Flash's spawn frame lag); Bubble needs the joint counter/`$FC` table | holds, with caveats |
| prew1-04 | A removed pre-W1 true lag is -1 at the end | PROVEN | counter unaffected | cost side: music phase and hidden phase (DelayScrolls need re-tuning) | holds |
| prew1-05 | Pre-W1 loads have fixed lag counts | PROVEN | REAL survey | - | holds |
| prew1-06 | Heat health fill to stage end cannot gain | PROVEN (by the audit) | AI code (integer-X dash); door clamp fixes the start X; max X 143.56 < 145; first hit earliest (REAL); contact box forces Y >= 161, a 29-frame teleport | none | closed |
| prew1-07 | Heat stage before the fill has no saving | UNS | menu BFS only; video comparison | the 4,560-frame stage was never searched | REAL-HOLE: a 2008 forum post names a 1-frame-faster ladder zip lost in the appearing-block room |
| prew1-08 | Flash title and intro inputs are the earliest | PROVEN | REAL | - | holds |
| prew1-09 | The Flash fight -1 exists (kill 5388) | fact (REAL) | beam | breaks Air's DelayScroll through the hidden phase (re-tune needed) | - |
| prew1-10 | No counter frame can be saved in the Flash stage before the fill | SL | REAL beams over 3546-4427 (all died at 3854) | pruned beams; the screen-07 hit only sampled | REAL-HOLE; the preferred R1 partner (odd real lead) |
| prew1-11 | A Flash-end double KO needs 4 more hits | EST | paper | never tested | NOT-A-HOLE: needs 16 more damage inside a minimum-cadence fight; costs more than 6 |
| prew1-12 | +8 at the Air end not reached (publication) | OVT | the WIP gained it before the gate | - | - |
| prew1-13 | Every pre-gate Air frame is lost unless the real lead is 10 | PIM | ANALYSIS music sweep | ignores the hidden phase | holds |
| prew1-14 | Air after the gate: at most 3 verified pre-fill frames | SL | menus + climb | the chain's 21182 menu has 2 frames of slack (REAL; load-bearing when cut) | R1 piece only (see prew1-17) |
| prew1-15 | Air first hit >= 21669; fight saving <= 2 | SL | ANALYSIS BFS, 9 frames | no L or blank input in the alphabet | holds (weak) |
| prew1-16 | Air fight lag 21817 not removable | SL | single/double toggles, beams | blink and sound-queue levers untried | holds (weak) |
| prew1-17 | An Air-end double KO (-6) is less than the 8 needed | EST | judged alone | pre-fill 4 + KO 6 never combined | UNCERTAIN (below 2%): Air Man's contact deals 8, so HP <= 8 is needed (16+ extra damage); pre-fill 4 not verified |
| prew1-18 | Air door 1 from below: no DelayDown possible | EST (strong) | timed log: the check runs ~14.4k cycles early | - | holds; the first-frame case was measured (glitchsurvey-26) |
| prew1-19 | Air spawn lag 21432 not removable | EST | profile | door state fixed by the route | holds (weak) |
| prew1-20 | Air kill lag 21910 not removable | PROVEN (margin) | 3,382 cycles over | - | holds |
| prew1-21 | DelayScroll check-frame lags are inherent | PROVEN | the interrupt must interrupt the check | - | holds |
| prew1-22 | The publication's Crash floor fight is optimal (kill 28476) | PIM (floor family) | bounds + REAL | the chain uses the in-wall structure | holds for its family only |
| prew1-23 | (implicit) The chain's in-wall Crash fight is optimal | UNS | none | never searched; kill 7 frames after the floor fight; kill lag 28484 | REAL-HOLE (see prew1-27) |
| prew1-24 | Crash pre-fill: 1 verified frame | SL | menus | the chain's 25681 menu has 1 frame of slack | R1 piece (with prew1-23) |
| prew1-25 | Crash death warp about minimal | EST | pit wait cut by an Atomic Fire shot | not rechecked on the chain | holds (weak) |
| prew1-26 | The in-wall kill's 9-frame teleport is minimal | PROVEN | teleport = floor(Y/8)+9 | - | holds |
| prew1-27 | Crash kill lag 28484 not removable (173 cycles over) | SL | 4-frame pad grid | fight structure held fixed | REAL-HOLE: deleting one object (slot-3 tornado, stuck bomb or a shutter) removes it (ANALYSIS); lag_audit's 40 "near" paths never kill (REAL); the slot-3 tornado makes Quick's seed `$4C3` |
| prew1-28 | Crash spawn lag 28191 not removable | EST | profile | other entry states untested | holds (weak) |
| prew1-29 | Crash lags 25750/27177/27194/28479 | SL | beams | - | holds (weak) |
| prew1-30 | Quick fight rigid; first hit 34507 earliest | PROVEN (cadence) / SL (first hit) | code; 4,655 REAL patterns (miss by 0.06 px) | - | holds |
| prew1-31 | Quick exit Y148 is the highest; no double KO | PROVEN (height) / EST (KO) | room map | the KO needs 24 free damage | holds |
| prew1-32 | Quick pre-fill: at most 4 speculative frames, 7 needed | SL | scroll/door counts | menu 31758 has 1 frame of slack | holds (weak) |
| prew1-33 | Quick spawn lag 34261 not removable | SL (strengthened) | REAL: all 234 door-reaching corridor variants lag | a walking door state costs 330 more cycles | holds |
| prew1-34 | Quick kill lag not removable | PROVEN (margin) | 1,807 cycles over | - | holds |
| prew1-35 | Metal fight: belt flip fixed at fight frame 120 | PROVEN | `$05A7` = FF after every stage end; no writer in Metal | - | holds |
| prew1-36 | The Metal corridor's 13th zip needs Mega Man about 2.25 px higher | SL + model | REAL 162 variants; pokes | other landing-height sources never enumerated | REAL-HOLE (low): 13th zip + 1 pre-fill frame = +16 alone |
| prew1-37 | Metal double KO implausible | EST | paper | 22 free damage | holds (weak) |
| prew1-38 | Metal segments tight | EST | segment accounting; menus at their BFS minimum (REAL) | - | holds |
| prew1-39 | Bubble fight optimal (no kill before logic index 166) | PIM | layered exhaustive search | only the ceiling family (Bubble Man inert) | holds |
| prew1-40 | Bubble post-kill rigid | PIM | REAL + pokes | - | holds |
| prew1-41 | Bubble boss-room entry pinned; DelayScroll on a heavy music frame | SL / PIM | REAL corridor search | - | holds |
| prew1-42 | A one-crab Bubble DelayScroll is ~2,600 cycles short | SL | lever table; REAL | no 2.6k-cycle lever known | holds |
| prew1-43 | Zip-2 lag removals k = 2/3 cannot pay | PIM | fill table, counter +0..+3 | larger compensations unmeasured | holds (the table is periodic, so nothing to add) |
| prew1-44 | The Bubble zip blink lever costs 8 | EST | stage-end slack <= 1 | the 42202 menu slack could carry a shift | NOT-A-HOLE: the zip-1 lags are not sprite-draw lags (ANALYSIS pokes of -2, -1, +1, +2, +4; REAL menu cut) |
| prew1-45 | The deliberate pause frames before the Bubble DelayScroll are needed | PROVEN (REAL) | the scroll fails without them | - | holds |
| prew1-46 | Bubble spawn lag 45152 not removable | EST | profile | - | holds (weak) |
| prew1-47 | Wood fight kill minimal (publication) | PIM | slot-free rule | not re-proven on the chain | holds |
| prew1-48 | The Wood fight-lag fix is absorbed by the rules | PIM | fill output 0 mod 4 | - | holds |
| prew1-49 | A Wood stage-start pause breaks the DelayUpScroll | OVT | the chain does it | - | - |
| prew1-50 | DD3 at 48491 is the earliest | SL | DFS | - | holds |
| prew1-51 | Wood lag 48120 removable only by dropping DD1's B | SL | REAL | sound-queue lever untried | holds (weak); matters only inside an R1 Wood re-solve |
| prew1-52 | With +8 at the Wood start, Wood is one counter frame short (DD1 1 cycle late) | PIM + SL | counter -8 model; 40,960-leaf DFS | other levers untried | REAL-HOLE: a parity effect (ANALYSIS: odd real shifts put 5-8 configurations in the window; a follow-up reaches a Wily 1 start at 96) |
| prew1-53 | Wood spawn and kill lags not removable | EST / PROVEN (margin) | profile | - | holds |
| prew1-54 | R1 by shifting the Wily 1 exit DelayScroll is infeasible | PIM | music profile; levers | Wily 1 route held fixed | see wily123-01 |
| prew1-55 | No lag can be induced after Wily 1 pause 3 | PROVEN | timing on every frame | - | holds |
| prew1-56 | Metal +4 (an R1 piece) infeasible | SL | as prew1-36 | as prew1-36 | REAL-HOLE (with prew1-36) |
| prew1-57 | +8 at the Quick end infeasible | PROVEN + SL | fight/exit code; pre-fill search | - | holds |
| prew1-58 | +8 at the Bubble end infeasible | PIM | fight and post-kill models | - | holds |
| prew1-59 | R1 via a 20-frame-earlier Bubble DelayScroll infeasible | SL | lever table | - | holds |
| prew1-60 | R1-lite (8 induced Wily 1 lags) infeasible at zero cost | PROVEN | stale-slot kid code; REAL | - | holds |
| prew1-61 | No spare Item-2 unit; the left-facing sled costs 2.875 px | PROVEN | `$A5` writers; REAL | - | holds (route change: wily123-10) |
| prew1-62 | R1 via "Flash 1+1" infeasible as found | SL | as prew1-10 | as prew1-10 | REAL-HOLE (with prew1-10) |
| prew1-63 | "R1 is closed" | EST | conjunction of piece verdicts | pieces never searched | REAL-HOLE, strengthened (Section 3.1) |
| prew1-64 | The other pre-W4 short lags are not removable for free | EST (mixed) | DelayScroll frames, margins, beams | later levers only partly applied | mixed: Bubble 43509 NOT-A-HOLE (DelayScroll music pin + fill table; repro_fuzz: avoidable at no real cost, worth 0); Crash 28484 see prew1-27; Wood 48118 only inside an R1 Wood re-solve |
| prew1-65 | Stage-select loads cannot end earlier | PROVEN (margin) | 1-2k cycles short | - | holds |
| prew1-66 | A counter shift of -1..+3 removes no pre-W1 spawn lag | PIM | pokes | - | holds |
| prew1-67 | The blink lever is not viable before Wily 4 | EST | stage-end slack <= 1 | - | NOT-A-HOLE (with prew1-44) |
| prew1-68 | Robot-master order: no gain once the hand-overs are counted | EST | three fight savings on paper | the user's holes | REAL-HOLE, then closed as an ESTIMATE: no faster order found (Section 3.2) |
| prew1-69 | Below-screen starts kill Mega Man except at Quick | PIM | pokes of `$F9` = 01, FF | other values | holds (any positive value behaves alike: glitchsurvey-50) |
| prew1-70 | No other death warp pays | EST | dwell table | zip death warps untested | holds (strengthened: glitchsurvey-16, -20) |
| prew1-71 | No new useful zip | PIM | offline predictor | multi-segment paths | holds (glitchsurvey-20) |
| prew1-72 | A zip into a boss room starts no boss | PROVEN | code | - | holds for robot-master rooms |
| prew1-73 | Double KOs at other robot-master ends save too little | EST | per stage, alone | combinations | see prew1-11, prew1-17 |
| prew1-74 | The pre-W1 pause menus are at their BFS minimum | OVT (on the chain) | REAL BFS on the publication | - | REAL BFS by the audit: slack 2/1/1/2/2/7 in six chain menus; each is load-bearing when cut alone |
| prew1-75 | Stage select and title are BFS-minimal | PROVEN (REAL BFS) | - | - | holds |

### 6.2 wily123: Wily 1-3 (audit_wily123; hole check holecheck_wily123; r1dds)

48 entries; no frame found. New rule facts (ANALYSIS): the Wily 1 end is an exact double knockout (two fade steps in one frame), so arriving 2-14 frames early costs 16; the Wily 2 boss fill needs only 1 frame for +4; the Wily 3 fade needs a lead of 14. A pause inside the Wily 2 boss room freezes the whole fight (REAL).

| id | claim | class | evidence | holes | verdict |
|---|---|---|---|---|---|
| wily123-01 | R1 by shifting the Wily 1 exit DelayScroll is infeasible | PIM | music profile; 54 check pads; levers | the Wily 1 route before pause 3 held fixed | (a) REAL-HOLE per the hole check, then closed by r1dds (REAL + validated ANALYSIS): at the needed frame the check is ~301 cycles late (window 33), and only 7 of 16 Wily 1 logic frames exist. (b), (c) NOT-A-HOLE. Now SL; reopens with 32 logic frames (lead 9) |
| wily123-02 | No lag can be induced after pause 3 | PIM | timed log | v5's path only | holds |
| wily123-03 | The exit check is pinned to the dragon's spawn + 1 | PROVEN | code | - | holds |
| wily123-04 | The Wily 1 end needs the counter exactly at 0 mod 16 | PROVEN (mechanism) | write-watch: kill and contact in one frame give two fade steps | the docs' "q16" wording | holds; the double KO itself is worth 16 frames |
| wily123-05 | The Wily 1 teleport height is fixed | PIM (was EST) | room geometry | at most -1, absorbed | holds |
| wily123-06 | R1-lite needs exactly 8 lags | SL | REAL sweeps | 7 lags put the check on an untested spike frame | NOT-A-HOLE: that frame is ~1,900 cycles too heavy |
| wily123-07 | The 53793 kid cannot be removed at zero cost | PIM | code; 45 jump timings | candC's path | holds |
| wily123-08 | Pipi 3 trailing gives at most 6 natural lags | SL | model + REAL | - | holds |
| wily123-09 | Item 2 is exactly used up in Wily 1 | PROVEN | `$A5` writers | - | holds |
| wily123-10 | The left-facing extra sled's 2.875-px deficit cannot be recovered | SL | REAL jump sweeps | route changes (a zip into building 2) untested | UNCERTAIN (low): a zip needs 16 px into the wall; item snaps give at most 8 |
| wily123-11 | Item 1 as the step costs a net +8 | PROVEN | refill code | - | holds |
| wily123-12 | The pause-2 menu has no spare frame | PROVEN (REAL) | - | - | holds |
| wily123-13 | No other Wily 1 lag window | PIM | cascade model | base path | holds |
| wily123-14 | A Wily 1 offscreen start gains nothing | PIM | pokes | pads not re-planned | holds |
| wily123-15 | Wily 1 already ends with a double KO | PROVEN | RAM | - | holds |
| wily123-16 | The Wily 1 seeds tolerate few throw variants | SL (info) | REAL | - | info |
| wily123-17 | R2 is not feasible | PIM | route families; REAL segment lengths; refill code | every other Wily 2/3 segment held at inherited inputs | REAL-HOLE, narrowed (Section 3.1) |
| wily123-18 | All six Wily 2 Item-1 platforms are load-bearing | SL | REAL drop tests | Item 3 considered only for #4 | holds (the spawn-block path is closed: glitchsurvey-38/58) |
| wily123-19 | The Wily 2/3 Item-1 economy is closed | PIM | refill code | assumes Item 1 is the only platform weapon | holds within Item 1 |
| wily123-20 | The capsule-3 detour has no slack | PIM | REAL | - | holds |
| wily123-21 | A Wily 3 offscreen start is blocked | EST | room map | roof-zip exit only | holds (low value) |
| wily123-22 | +8 at Wily 2 refill 2 impossible | SL | REAL | - | holds |
| wily123-23 | +8 at Wily 2 refill 1 impossible | PIM | RAM trace | capsule position not re-planned | holds |
| wily123-24 | The Wily 2 fight is fixed (124-frame block timer) | PROVEN | code; fight model; REAL (a pause freezes the timer) | - | holds |
| wily123-25 | Pause 4 moved into the Wily 2 boss room gains, but is absorbed | PIM (was EST) | REAL: an in-room pause freezes the fight, net +3 | pause 4 is also the shaft's speed reset | holds (0) |
| wily123-26 | The Wily 2 double KO at Y130 is the highest | PIM | room map | - | holds |
| wily123-27 | A Wily 2 offscreen start kills Mega Man | PIM | poke | - | holds |
| wily123-28 | Wily 2 blocks never drop items | PROVEN | code | - | holds |
| wily123-29 | Wily 2 zip death warp: no single zip from 1B to 1F | SL | predictor | multi-segment paths | NOT-A-HOLE: wrapped 1E has no zip path; 1F's left wall is solid; no death source in wrapped 1F-23 |
| wily123-30 | The Wily 2 menus are BFS-minimal | PROVEN (REAL BFS) | - | - | holds |
| wily123-31 | (implicit) Pause 4's position is free | PIM (was UNS) | REAL 105-variant scan | - | holds |
| wily123-32 | No simple death warp in Wily 1-3 | EST | dwell below overhead | - | holds |
| wily123-33 | Item 2 in Wily stages breaks the Item-1 plan | UNS | none | - | holds (glitchsurvey-60: at least +50) |
| wily123-34 | Guts Tank head hittable at a fixed time; 14 hits need 26 frames | PROVEN | code | - | holds |
| wily123-35 | Moving the Wily 3 boss pause gives nothing | EST | pause formula | in the room it gives +1 at the fade | holds (0 alone) |
| wily123-36 | The Wily 3 kill lag is not removable | OVT | - | - | - |
| wily123-37 | The Wily 3 water zip breaks at leads 9/10/11/32 | SL | REAL perturbations | small sets | open with wily123-17 |
| wily123-38 | The Wily 3 opening is tight | SL | beam | - | holds |
| wily123-39 | The Wily 3 exit teleport stays at 25 frames | PIM | room map; HP 28 | HP 28 is a route choice | holds for heights; see lead 5 (double KO) |
| wily123-40 | A Wily 4 start above the screen is a dead end | PIM | pokes | - | holds |
| wily123-41 | A Wily 3 below-screen start is blocked | EST | poke | - | holds |
| wily123-42 | Wily 3 and Wily 4 replay verbatim at counter -16 | PIM | re-checked on v6.2 | -32 breaks the water zip | holds for 16 |
| wily123-43 | The docs' Wily 1-3 rule table | OVT | - | - | replaced by the v6.2 table |
| wily123-44 | The Wily 1 map acts as q8 | PIM | poke | - | holds |
| wily123-45 | Wily 1-4 loads are at their lag floor | PIM | sound state at each load | - | holds |
| wily123-46 | Wily 1-3 have no removable short lag | PROVEN | event list | - | holds |
| wily123-47 | (implicit) Item 1 is the only platform weapon worth using in Wily 2/3 | UNS | none | Item 3 never considered | REAL-HOLE, reformulated: Item 3 is near-dead (at least +19); the real hole is skipping the Wily 3 refill with at most 2 Item-1 platforms after screen 1A (synth caveat: at most 1 on v6.5's budget) |
| wily123-48 | The Atomic Fire underflow is useless | EST | Atomic Fire unused | - | holds |

### 6.3 wily4: Wily 4 (audit_wily4; hole check holecheck_wily4)

43 entries; frame found: v6.4 (-1). Rule arithmetic for further work (v6.2 numbering): with c = net counter frames saved between room 32 (73507) and the Boobeam door, the gain against v6.2 is 4 floor(c/4) + (5 - fight lags), with 5/4/7/6 fight lags for c mod 4 = 0/1/2/3. v6.4 has c = 1, so the next payoffs are c = 4 (-3) and c = 5 (-4). A saving a before room 32 must keep room 32's blink phase: a = 0 or 3 (mod 4).

| id | claim | class | evidence | holes | verdict |
|---|---|---|---|---|---|
| wily4-01 | The room-32 lags cannot be removed | OVT | pad and music sweeps | never moved the counter | removed by v5.9 |
| wily4-02 | Blink shifts +1, +2 and -2 remove both room-32 lags | PIM | ANALYSIS pokes; REAL for +1 only | other shifts unverified REAL | holds for +1; -2/+2 unverified (needed by lead 2) |
| wily4-03 | "-2 needs a 1-frame saving after room 32, or shift 2 plus the DOWN throw" | OVT | small search | a menu frame after room 32 | REAL-HOLE, realised: v6.4 (-1) |
| wily4-04 | The DOWN shield throw gains nothing | OVT | REAL on v4.1; arithmetic | the cannon timers do not move | realised (v6.4) |
| wily4-05 | Room-34 sled seed lead, and its dismissal | EST / UNS | ANALYSIS of all 256 seeds; REAL seed sources | a room-33 sled landing earlier | UNCERTAIN: worth 0 alone; -1 only inside a set reaching c = 4/5 |
| wily4-06 | The 45-frame Item-3 wait is needed | PIM | REAL | seeds FA-FF save 1 | holds |
| wily4-07 | Rooms 28-32 micro-closures | PIM | single REAL variants | combinations with the 72202 pause | holds (low) |
| wily4-08 | Shortening any other Wily 4 run desyncs | SL | REAL run shortening | pad substitutions never tried | NOT-A-HOLE for substitution + deletion (REAL scan over 73646-74298, validated by a positive control) |
| wily4-09 | The Wily 4 menus are at their BFS minimum | PROVEN (REAL BFS) | - | a longer menu can help (v5.9, v6.4) | holds as a length statement |
| wily4-10 | 464 extra Item-1 throws give no earlier exit | SL | REAL | - | holds |
| wily4-11 | The room 0x1E Telly hit at 72780 is bound | EST | paper + REAL invincibility count | wrong homing model; Telly steering never searched | NOT-A-HOLE: exact aim model (bit-exact), REAL BFS, the column-3 crossing constraint and a shaft bound all give >= 72780 |
| wily4-12 | Rooms 0x1F/0x20 routes are forced | EST | RAM | Telly damage boosts | holds (low); re-check with the exact Telly model |
| wily4-13 | Rooms 0x21/0x22 need the Item-1 to Item-3 pause | PIM | code | - | holds |
| wily4-14 | A Wily 4 start above the screen is a dead end | PIM | code + poke | - | holds |
| wily4-15 | Wily 4 death warps: dwell below the overhead | EST | dwell table | desync deaths | holds for plain deaths; see lead 3 |
| wily4-16 | Boobeam fill rule (needs 4) | PIM | pokes | - | updated: next steps c = 4 (-3), c = 5 (-4) |
| wily4-17 | The first fill call always lags | PIM | REAL | - | holds |
| wily4-18 | Music phase d = 0 gives the minimum, 4 fight lags | PIM | music-copy model + REAL | - | holds |
| wily4-19 | The fight lags cannot be removed | SL | REAL pads | sound-queue priority untried | NOT-A-HOLE in practice: only a hurt or a menu sound could lose priority, and both cost far more than 1 |
| wily4-20 | The Boobeam chain is pinned link by link | PIM | code + REAL BFS per link | 4-bomb structure; standstill and contact assumptions | holds |
| wily4-21 | The 4-bomb role assignment is forced | PIM | room geometry | - | holds |
| wily4-22 | Wily 4-end map arithmetic | PIM | pokes | the post-kill phase lag may follow the music | holds in the model |
| wily4-23 | Crash Bomber budget | PROVEN | code | - | holds |
| wily4-24 | A 3-bomb Boobeam costs +38 | PIM | REAL | - | holds |
| wily4-25 | The Leaf Shield setup is needed | PROVEN | `$D4CA` code | - | holds |
| wily4-26 | The walls do not vanish after a pause (Japanese ROM) | PIM | write-watch | other fight states | holds |
| wily4-27 | No pause before the fill | PROVEN | code | - | holds |
| wily4-28 | No embedding or offscreen Wily 4 exit | PIM | map + code + 180,000 random REAL frames | - | holds |
| wily4-29 | A higher Wily 4 ending costs as much as it saves | PIM | REAL | the rule is asymmetric (needs a delay >= 5) | NOT-A-HOLE (argument strengthened) |
| wily4-30 | The Wily 4 exit double KO is blocked | PROVEN | code | - | holds |
| wily4-31 | Mega Man is locked from kill+2 | PROVEN | code + REAL | - | holds |
| wily4-32 | +4 at the Wily 4-end map needs 2 more frames | EST | status | - | holds |
| wily4-33 | Wily 4 load lags are fixed | PIM | REAL | - | holds |
| wily4-34 | The door depends only on the number of zip frames | PIM | REAL | - | holds |
| wily4-35 | Early "Boobeam is at its limit" claims | OVT | - | - | - |
| wily4-36 | The room-31 seed fix needs more than 3 edits | PIM | DFS | - | historical |
| wily4-37 | Spare Item-3 energy has no use | EST | - | Item 3 can rewrite the room-34 seed | open, low |
| wily4-38 | The 2006 boss-room crash | n/a (ACE) | - | the user closed ACE | recorded only |
| wily4-39 | The room-32 exit needs Y >= 232 | PIM | REAL; code | - | holds |
| wily4-40 | The 49-frame C2 knockback cannot be shortened | PIM | code + 40 REAL runs | - | holds |
| wily4-41 | The stage-start pause overlap is already used | PIM | REAL | - | holds |
| wily4-42 | v4's rooms 16-32 beat the WIP's by 1 | fact (REAL) | - | - | holds |
| wily4-43 | (implicit) The WIP's rooms 33/34 and zip route are optimal | UNS | reproduced from video | the DOWN throw was hidden in it | NOT-A-HOLE for single-pad substitutions + 1-3-frame deletions (REAL scan); multi-input re-plans not covered |

### 6.4 w5: Wily 5 refights and hub (audit_w5; hole check holecheck_w5)

69 entries; frames found: v6.5 (-1) and v6.6 (-9). The Crash refight lag and first half followed the same pattern as the Heat lag (lead 1) and became v6.6.

| id | claim | class | evidence | holes | verdict |
|---|---|---|---|---|---|
| w5-01 | Capsule-to-fill timings are fixed per boss | PIM | constant-input REAL tests | 4 rooms untested | holds (gd_flow: intros and fills ignore input, by code) |
| w5-02 | Refight exit object + 9-frame teleport | PROVEN | code + REAL | - | holds |
| w5-03 | "The return warp starts only if Mega Man stands on the teleporter at the kill" | OVT (wording) | - | - | docs fix |
| w5-04 | Hub pause on the room-change frame; net cost 32-40 | PROVEN | REAL; an earlier START is ignored | - | closed by the audit |
| w5-05 | Hub pauses at their BFS minimum | PIM | BFS deduplicated on the zero page | alphabet and dedup | holds; now certified (pf_search) |
| w5-06 | Wily 5 rule needs | PIM | pokes | pokes do not move the music | updated on v6.3 |
| w5-07 | The Wily 5 order is optimal | EST | 2006 program; geometry | obsolete cost model; legs unmeasured | NOT-A-HOLE as a gain: Air-only Quick needs 30 units of 28; the other variant costs about +70 (legs still estimates) |
| w5-08 | "The minimum is 6 pauses" | OVT | - | miscount | - |
| w5-09 | Weapons forced by the damage tables | PIM | ROM tables | Quick's plan is an order variable | holds |
| w5-10 | An Atomic Fire charge cannot be carried into a refight | PIM | REAL | - | holds |
| w5-11 to 13 | Time Stopper only hurts Quick; Metal Blade and Air Shooter budgets exact | PROVEN | code; counts | - | hold |
| w5-14 | 3 Crash Bombers at Wily 5; a 3-bomb Boobeam costs +38 | PIM | REAL | - | holds |
| w5-15 | (implicit) The Heat refight is AI-bound | OVT | v6.3 (-4) | verdict from one trajectory | - |
| w5-16 | The Heat refight cannot give more than -2 | PIM (was EST) | arithmetic (dash sum >= 24) | an unproven premise | strengthened by the hole check: a transit bound plus the mandatory turn frame make 24 fail by 1/256 px |
| w5-17 | The Heat first hit is bound | PIM | REAL + code | - | holds |
| w5-18 | Heat waits the table minimum | PROVEN | code | - | holds |
| w5-19 | Heat lag 77396 cannot be removed ("1,370 over") | SL | pads on the lag frame | fire pillars aimed at Mega Man earlier | REAL-HOLE, realised: v6.5 (-1) |
| w5-20 | The Air refight -4 is impossible | PIM | code + relaxation | - | holds |
| w5-21 | Leaf hits only on slot 2 and an even counter | PROVEN | code | - | holds |
| w5-22 | Air first hit >= 78136 in every layout | PIM | optimistic bound | - | holds |
| w5-23 | No Leaf fight changes the slots' stale subpixels | PROVEN | code | - | holds |
| w5-24 | Leaf Shield with L+R gains nothing | UNS | stated | moot | holds |
| w5-25 to 28 | Wood exit -4 infeasible; exit at kill+3 impossible; third hit at 78715 impossible; slot-4 subpixel only 04/37 | PIM (27: SL) | code + REAL | - | hold |
| w5-29 | The Wood exit -2 is harmful | PIM | REAL + the full `$FC` table (audit) | - | closed |
| w5-30 | Bubble refight at the 19-frame minimum | PIM | validated model + bound | - | holds |
| w5-31 | 3 hub slow-down frames after Bubble are forced | PROVEN | code + RAM (audit) | - | closed |
| w5-32 | Quick fill: nothing left | PIM | bounds | the walk -1 is untested (the rule needs 3) | holds |
| w5-33 to 37 | Quick -4 infeasible (best -2); earliest hurt; Crash stage change = Quick kill + 90; the kill+89 claim; 4-bomb floor | SL / PIM / OVT | REAL + pokes | plan families | hold |
| w5-38 | Crash fight: only schemes S1/S2; first half fixed | PIM | scans + REAL BFS | the first half was never varied | REAL-HOLE, realised: v6.6 (-9). The opening was free: a volley fired before Crash Man can react makes hits 1 and 2 |
| w5-39 | The Crash to Metal hub walk is optimal | PIM | exhaustive pruned BFS | - | holds |
| w5-40 | Crash kill lag 80349 cannot be removed | SL (wrong mechanism) | pads; profile | it is the bomb-explosion frame; the trigger was held fixed | REAL-HOLE, realised: v6.6. The trigger now comes at 80288, so the bomb explodes after the kill |
| w5-41 | Crash hits limited by geometry | OVT | - | - | refined |
| w5-42 | The Metal refight is minimal | PIM | blade-travel bound | - | closed by the audit |
| w5-43 | Flash fight at the 19-frame cadence | PIM | cadence lemma | - | holds |
| w5-44 | WM1 fill: nothing left | PIM | REAL + speed bound | - | holds (the room-0x28 walk is exact: wmw6-13) |
| w5-45 | Blade throws in room 0x28 stop Mega Man | PIM | REAL | - | holds |
| w5-46 | Start to Heat walk | SL | waypoint BFS | bound >= 70 frames; the rule needs 4 | holds |
| w5-47 | The Heat to Air walk is geometry-bound | SL | waypoint BFS | - | strengthened: exactly 0 (969 REAL runs; last 4 frames certified); the Heat kill to Air fill segment is closed |
| w5-48 | Air to Wood walk: no 2-frame saving | EST | paper | never searched | holds (bound about 66 vs 67; the rule needs 4) |
| w5-49 to 54 | Other hub walks at the speed limit; walks start on the first input frame; floor capsules need a hop | PIM / SL | traces, beams, REAL | - | hold (each at most 1 frame against a need of 3-4) |
| w5-55 | Each refight's first random roll is set by the capsule X subpixel | PIM | code + REAL | - | holds |
| w5-56 | List of random-number readers | PIM (dated) | v2 read hooks | the route changed | holds (re-run on v6.x) |
| w5-57 to 60 | Refight skip needs ACE; above-screen Wily 5 is a dead end; weapon hitboxes fixed; double KOs cannot help | PROVEN | code | - | hold |
| w5-61 | Refight spawns and loads are lag-free | PIM | REAL list | - | holds |
| w5-62 to 66 | Older lag, lever, corridor and hub claims | OVT | - | - | - |
| w5-67 | Air first-hit bound (5,472 policies) | SL | REAL grid | superseded by w5-22 | holds |
| w5-68 | Unused Wily 5 energy has no use | EST | damage tables | - | holds |
| w5-69 | Hub walks are order-independent except through the order | PIM | RAM | - | holds |

### 6.5 wmw6: Wily Machine, Wily 5 to 6, Wily 6, alien, ending (audit_wmw6; hole check holecheck_wmw6)

64 entries; all 7 holes refuted; no frame found. The hole check upgraded wmw6-13/14 to exact and wmw6-48/49/53 to PROVEN-IN-MODEL.

| id | claim | class | evidence | holes | verdict |
|---|---|---|---|---|---|
| wmw6-01, 02, 04 | Earlier "WM1 cannot die earlier" claims | OVT | per-trajectory DFS | Mega Man's left/right path or jump timing held fixed | overtaken by v6.0/v6.1 |
| wmw6-03 | v5.9's jump timing cannot kill at 81848 for any path | PIM | decomposition + exact DFS | - | holds |
| wmw6-05 | The H1x1 opening cannot kill by 81844 | PIM | 1.55 million nodes | one profile | holds |
| wmw6-06 | Only three first-jump frames reach 28 hits by 81844 | PIM | relaxation per jump | - | holds |
| wmw6-07 | Contact with the machine is never part of a fast kill | EST | REAL contact cost | - | moot |
| wmw6-08 | WM1 by 81840 (the next 4-frame step) | PIM (was SL) | sound relaxation over all jump schedules and throws: 26 hits, 28 needed | relaxation premises | NOT-A-HOLE (the premises are code facts) |
| wmw6-09 to 12 | Boss X depends only on time; Metal Blade is the only weapon; 59-blade budget; hit/slot rules | PROVEN | code + REAL | - | hold |
| wmw6-13 | WM1 fill +4 does not exist | PROVEN (was SL) | 860 REAL runs; bound | the Flash fight bound is Wily 5's | NOT-A-HOLE: the room-0x28 walk is exactly optimal (71 frames; 70 would need at most 14 air frames, the map forces at least 24) |
| wmw6-14 | The room-0x28 walk is minimal | PROVEN (was SL) | as wmw6-13 | - | NOT-A-HOLE (exact) |
| wmw6-15, 16 | Flash exit to room 0x28 is fixed; the WM intro and post-kill ignore input | PROVEN | pokes; code | - | hold |
| wmw6-17 | Blade throws in room 0x28 stop Mega Man | SL | REAL | other directions | holds |
| wmw6-18 | The WM-room X subpixel is carried from the touch | PIM | pokes | - | holds |
| wmw6-19 | WM2 cannot die before fill+60 | PIM | relaxation over all movements; floor-only surfaces (RAM scan) | assumptions | NOT-A-HOLE (the root latch is a REAL fact; v6.5 kills at +61, at most 1 frame against a need of 3) |
| wmw6-20, 21 | "WM2 -8 needs a free hit"; "-4 needs a slot-3 kill" | OVT | - | - | - |
| wmw6-22 | No WM2 beam reaches 82014 without the reservoir blade | SL / PIM | beam / DFS | - | moot |
| wmw6-23 | Wily 6 seed windows | PIM | pokes | valid for today's Wily 6 inputs only | open (no lever blocked now) |
| wmw6-24 | Blade subpixel arithmetic | PROVEN | code | - | holds |
| wmw6-25 | Nothing after the WM2 kill can be gained | PROVEN | timer code; pokes | - | holds |
| wmw6-26 | Wily 5 to 6 map needs 3; "+4 for 4 frames" | EST (partly OVT) | pokes | pokes do not move the music | superseded by the REAL kill-frame table |
| wmw6-27 | The stage-0D load is at its music floor (4 lags) | PIM | sound-RAM copies over 81 phases | only the sound state varies | holds |
| wmw6-28 | Delaying the WM2 kill keeps 4 lags but starts Wily 6 later | PROVEN (REAL) | - | - | holds |
| wmw6-29, 30 | The Wily 6 load is fixed; an offscreen Wily 6 start gives 0 | PIM | - | - | hold |
| wmw6-31 | The Wily 6 landing-frame pause is the cheapest | SL | REAL | a pause inside a transition | holds (low) |
| wmw6-32, 33 | Wily 6 falls and transitions fixed; no 4th platform slot | PROVEN | code + REAL | - | hold |
| wmw6-34 | The zip needs Y <= 36; the ride takes 13 frames | PIM | code; REAL | - | holds |
| wmw6-35, 36 | The zip cannot start from column 15; the 16 px/frame zip is fixed | PROVEN | code | - | hold |
| wmw6-37 | The Wily 6 climb is optimal | SL | directions-only BFS | jump/throw timing never searched jointly | NOT-A-HOLE for the 3-4 frames that would pay (REAL joint scan of step 1; re-balancing gives at most about 1) |
| wmw6-38 | The spare Item-1 platform saves no frames | OVT (partly) | - | - | used as a seed knob since v6.3 |
| wmw6-39 | The alien door lead must be 0 mod 4 | EST | pokes | - | conditional (only with 3 Wily 6 frames) |
| wmw6-40 | The alien pre-pause has no usable slack | SL | ANALYSIS retunes | - | holds |
| wmw6-41, 42 | An extra platform blocks the alien pause; a Wily 6 death warp is useless | PROVEN | code; ROM | - | hold |
| wmw6-43 | Item 3 has no use in Wily 6 | UNS, now map argument | ROM map | - | holds |
| wmw6-44, 45 | The alien intro ignores input; the room-entry X is fixed | PROVEN | code | - | hold |
| wmw6-46, 47 | The alien path counts unpaused frames; menu -2 impossible | PIM | pokes; REAL BFS (certified by pf_search) | - | hold |
| wmw6-48 | The shot-2 spawn lag is unavoidable | PIM (was SL) | 660 REAL variants all lag; lag-free plans allow at most 5 hits | - | NOT-A-HOLE |
| wmw6-49 | Six hits before the burst is the maximum | PIM (was EST) | Mega Man must be invincible to the kill, so shot 2 must hit him at idx 153-160; measured flight table + DP: at most 6 | the relaxation's assumptions, listed by the hole check | NOT-A-HOLE |
| wmw6-50, 51 | The burst cannot start before idx 190; a slot-2 chain is impossible | PIM | ANALYSIS + REAL | - | hold |
| wmw6-52 | The end trick (last input earlier) is impossible | PIM | REAL DFS; stray bubbles (REAL) | - | NOT-A-HOLE |
| wmw6-53 | A shot-1 invincibility plan is impossible | PIM (was EST) | end contact | - | NOT-A-HOLE (with wmw6-49) |
| wmw6-54, 55 | The alien fill needs 3; only Bubble Lead hurts it | PIM / PROVEN | pokes; ROM | - | hold |
| wmw6-56 to 58 | Ledge "frame-perfect"; 0.375-px near miss; menu -1 given back | OVT | - | - | overtaken by alien2 (v5.3) |
| wmw6-59, 60 | After the alien fill every frame counts; the last input is at kill-1 | PROVEN / PIM | - | - | hold |
| wmw6-61 to 64 | Older tables and single-change claims | OVT | - | - | - |

### 6.6 glitchsurvey: glitch survey and route-level closures (audit_glitchsurvey; hole check holecheck_glitchsurvey)

66 entries; no frame found. The survey was not complete even for documented glitches (the forum thread on disk documents at least five it never examined); each missing item has now been costed, without a saving. The death-warp lead was mapped exactly.

| id | claim | class | evidence | holes | verdict |
|---|---|---|---|---|---|
| glitchsurvey-01 | "No macro reroute is buildable; each fails on a measured mechanism" | EST | per-item studies | 3 of 9 rows were paper | wording overtaken |
| glitchsurvey-02 | No surveyed glitch gives a proven saving | SL | 16 items | completeness | holds for its 16 items |
| glitchsurvey-03 | The survey covers the documented glitches | UNS | - | at least 5 forum-documented glitches never examined | open as a listing gap; items costed in -28 and -38 |
| glitchsurvey-04, 05 | The refight skip needs ACE; warmCabin's checkpoint state skips nothing | PROVEN | code + write-watch | - | hold |
| glitchsurvey-06 | No out-of-range dispatch is reachable | OVT (ACE) | - | a 2014 community ACE exists | out of scope (the user closed ACE) |
| glitchsurvey-07, 08 | No level list or drop creates object types $7C-$7F; a death keeps `$BC` | PIM / PROVEN | ROM scan; code | - | hold |
| glitchsurvey-09 | Zip rule; "facing right is the mirror" | OVT in part | code | there is no leftward zip (gd_terrain) | the rightward half holds |
| glitchsurvey-10, 11 | Zip probe heights; with no input the zip moves 16 px/frame | PROVEN / PIM | code; ANALYSIS | solid sprites are matched on low bytes only | hold |
| glitchsurvey-12 | No new useful zip | SL | static decoder | stability, sprites, multi-segment paths | holds for single zips (exact-physics scan before 13 checkpoints) |
| glitchsurvey-13, 14 | Static zip-run lengths; no single continuous Metal/Wily 2 run | PIM | ROM decode | static runs overstate (stability) | hold |
| glitchsurvey-15 | The checkpoint is a function of Mega Man's screen | PROVEN | code | - | holds |
| glitchsurvey-16 | v5's deaths are warps; overhead about 263 frames | PIM | RAM | about 263 only with a held Atomic Fire charge; otherwise about 422-470 | holds (every simple-warp closure gets stronger) |
| glitchsurvey-17 | Simple death warps do not pay | EST | dwell table | - | holds |
| glitchsurvey-18 | Wrapped walking in Crash is break-even at best | SL | one REAL walk | items in wrapped screens | holds (REAL: items do not spawn there) |
| glitchsurvey-19 | Door screens cannot be wrapped past profitably | EST | code | - | holds |
| glitchsurvey-20 | Zip-extension death warps: "expect nothing" | UNS | - | new embeddings; multi-segment paths | single zips closed (PIM, exact physics); multi-segment NOT-A-HOLE in robot-master stages (lagging-camera basins are either worse than v6's door/scroll or 30+ px inside enclosed floor slabs); Wily stages: lead 3 |
| glitchsurvey-21 | Lives are not a constraint | PROVEN | 4 spare | - | holds |
| glitchsurvey-22 | Boss init has three callers | PIM | code | the Mecha Dragon starts itself (a 4th start) | holds for robot-master rooms |
| glitchsurvey-23 to 25 | Door and transition lengths; door request rules; a low door-1 entry exists only in Air | PROVEN / PIM | code; write-watch | - | hold |
| glitchsurvey-26 | The door-less Air entry is impossible | EST (strong) | timed log | the first-corridor-frame case | NOT-A-HOLE (measured: the check runs at 19.6-20.0k cycles; about 29.8k needed) |
| glitchsurvey-27 | Shuttertech cannot remove a gate door | PROVEN | code | - | holds |
| glitchsurvey-28 | The Wily warp has no useful exit | PIM (model gap) | code | the dragon kill "counts as Heat Man" (forum 2015) | conclusion holds (at least +1,000 frames slower) |
| glitchsurvey-29 to 31 | Stage select, pause, title and password are closed under simultaneous inputs | PROVEN | code | - | hold |
| glitchsurvey-32 | Up+Down is the only menu trick | EST | code + BFS | - | holds |
| glitchsurvey-33 | Weapon hitbox types are fixed per weapon | PIM | code + Wily 5/6 write-watch | explosion pieces keep stale boxes (used in Wily 4) | holds |
| glitchsurvey-34 to 37 | MadWidth and the fart shot are used; Leaf L+R, Time Stopper gain nothing; Boobeam walls stay | PROVEN / PIM | - | - | hold |
| glitchsurvey-38 | Zipless-era tricks "not tested; any% skips them" | UNS | none | the Crusher spawn block touches R2's platforms #5/#6; the Exile Pipi glitch is at an Air screen | Crusher: NOT-A-HOLE (code + REAL); Exile Pipi: UNCERTAIN (very low, at most about 12 raw; lead 11) |
| glitchsurvey-39 | The Atomic Fire underflow is useless | PIM | - | - | holds |
| glitchsurvey-40 to 43 | Double-KO timing and conditions; teleport formula; Heat KO height | PROVEN / PIM | code | - | hold |
| glitchsurvey-44 | Other robot-master double KOs save too little | EST | per stage | combinations | UNCERTAIN (low) = prew1-17 |
| glitchsurvey-45 | "A lone +8 is worthless" | OVT (wording) | - | +8 is an R1 piece | - |
| glitchsurvey-46 to 49 | Wily 4 exit (KO blocked, cannot be raised); Wily 1/2 double KOs; other Wily exits at their best heights | PROVEN / PIM | - | the Wily 3 caveat (lead 5) | hold |
| glitchsurvey-50 | `$F9` = 01 at a stage start kills except at Quick | PIM | pokes | - | holds (any positive value behaves alike) |
| glitchsurvey-51 | Only Bubble's room ends above the screen | UNS ("only") | - | - | now PROVEN by rc_offscreen |
| glitchsurvey-52 to 56 | Offscreen starts at robot-master and Wily stages give nothing | PIM / EST / PROVEN | pokes | - | hold |
| glitchsurvey-57 | Docs section 9: "R1 is being tested" | OVT | - | - | stale text |
| glitchsurvey-58 | R2 needs a dropped Wily 2 platform; all six are load-bearing | PIM | REAL drop tests | the spawn-block path | the spawn-block path is NOT-A-HOLE; R2 itself is open (wily123-17) |
| glitchsurvey-59 | The spare Item-1 platform has no use | OVT | - | - | a Wily 6 seed knob since v6.3 |
| glitchsurvey-60 | Item 2 in Wily stages breaks the Item-1 plan | UNS | - | never priced | NOT-A-HOLE (cost model with REAL sled constants: at least +50) |
| glitchsurvey-61 | Unused Wily 5 energy has no use | PIM | - | - | holds |
| glitchsurvey-62, 63 | The Wily 5 order is the 2006 search's; 6-pause orders backtrack | EST / OVT in part | - | - | NOT-A-HOLE for the stated variant (= w5-07) |
| glitchsurvey-64, 65 | Weapons forced; an Atomic charge is not carried into a refight | PIM | - | - | hold |
| glitchsurvey-66 | A DelayScroll needs an already heavy screen | EST | two references | - | holds |
