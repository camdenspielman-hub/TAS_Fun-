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
| `movies/rockman2-v4.2-85160.fm2` | 85,160 | 23:37.000 | verified on both cores |
| `movies/rockman2-v5-85056.fm2` | 85,056 | 23:35.269 | verified on both cores |
| `movies/rockman2-v5.1-85040.fm2` | 85,040 | 23:35.003 | verified on both cores |
| `movies/rockman2-v5.2-85039.fm2` | 85,039 | 23:34.987 | verified on both cores |
| `movies/rockman2-v5.3-85037.fm2` | 85,037 | 23:34.953 | verified on both cores |
| `movies/rockman2-v5.4-85029.fm2` | 85,029 | 23:34.820 | verified on both cores |
| `movies/rockman2-v5.5-85025.fm2` | 85,025 | 23:34.754 | verified on both cores |
| `movies/rockman2-v5.6-85024.fm2` | 85,024 | 23:34.737 | verified on both cores |
| `movies/rockman2-v5.7-85020.fm2` | 85,020 | 23:34.671 | verified on both cores |
| `movies/rockman2-v5.8-85019.fm2` | 85,019 | 23:34.654 | verified on both cores |
| `movies/rockman2-v5.9-85018.fm2` | 85,018 | 23:34.637 | verified on both cores |
| `movies/rockman2-v6.0-85014.fm2` | 85,014 | 23:34.571 | verified on both cores |
| `movies/rockman2-v6.1-85011.fm2` | 85,011 | 23:34.521 | verified on both cores |
| `movies/rockman2-v6.2-85010.fm2` | 85,010 | 23:34.504 | verified on both cores |
| `movies/rockman2-v6.3-85006.fm2` | 85,006 | 23:34.438 | verified on both cores |
| `movies/rockman2-v6.4-85005.fm2` | **85,005** | **23:34.421** | verified on FCEUX master core and FCEUX 2.3.0 core |

**v6.4 is 274 frames (4.56 s) faster than the publication**, and 1 frame
faster than v6.3. The Wily 4 Boobeam fight lags 4 times instead of 5.
* **The change.**
  * Before the Boobeam corridor, Mega Man zips through a wall at 16 pixels a
    frame with the Leaf Shield up. v6.3 threw the shield left, and the throw
    pose stopped the zip for 2 frames. v6.4 throws it straight down, so the zip
    goes on and he is 2 frames ahead.
  * One blank frame more in the next weapon menu gives one of them back, so he
    reaches the Boobeam door 1 frame sooner.
  * The boss's health fill still ends on the same frame, but the boss music
    starts at the door, so it is now 1 frame further along during the fight.
    One of the fight's lag frames disappears, and everything after it comes 1
    frame earlier.
* **Why it was missed.** An earlier study tried the down throw alone (the
  music then meets heavier frames and adds lags) and with an extra menu frame
  before room 32 (that breaks room 32's invincibility-flicker fix). The
  adversarial closure audit found the third combination: the menu frame after
  room 32.
* **Verification.**
  * FCEUX's movie player on both cores gives 85,005 frames, with the alien dead
    one frame after the last input (end-RAM md5 `0912b0f0…`).
  * From the Boobeam fight on, every lag frame and every boss event comes
    exactly 1 frame before v6.3's.
  * An independent sync check and an independent rules check both found it
    valid; each change was reverted alone and each one is needed.
  * `movies/rockman2-v6.4-edits.json` (61 blocks) rebuilds it from the
    publication with `tools/make_movie.py`.

**v6.3 is 273 frames (4.54 s) faster than the publication**, and 4 frames
faster than v6.2. The Wily 5 Heat Man refight is won 2 frames sooner. The
Air Man refight's health fill needed only 2 frames for its next 4-frame step,
so it now comes 4 frames earlier. Everything after it, the alien's death
included, is 4 frames earlier.
* **Heat Man's fight is not limited by his AI.**
  * After each hit he waits, then dashes toward Mega Man at 4 pixels a frame.
    The dash lasts one frame for every 4 pixels between them, so he dies
    wherever his last dash leaves him.
  * Mega Man now hops in place before the third dash, which is then 12 pixels
    long instead of 24. Before the last dash he walks left with a jump, and
    that dash is 64 pixels instead of 60.
  * Heat Man dies 8 pixels further right, 2 frames sooner, and Mega Man
    reaches the exit on the next frame.
  * Every earlier study had treated this fight as fixed by the boss's AI. A
    completeness review found it had never been examined.
* **Putting the later refights back in step.** With the frame counter 4
  lower, the bosses' random choices would change. Small changes restore them:
  * the Air Man capsule is touched on another subpixel (same tornado layout);
  * the Wood Man exit hop starts a frame later (same Bubble Man pattern);
  * the jump to the Quick Man capsule is a frame later, one press in that
    fight is Right instead of Left, and its exit is re-timed;
  * the Air Shooter shot in the hub before Crash Man is fired 14 frames later;
  * the path to the Metal Man capsule and one step in that fight change, and
    the walk to the Flash Man capsule is re-found.
* **Wily 6 platform values.** The changes above alter the leftover weapon
  subpixels that Wily 6's platforms start from. Three changes bring them back
  in range (53/9F/4F):
  * one first-phase Wily Machine blade becomes a stationary blade;
  * one second-phase blade and the killing blade are thrown straight right;
  * the one spare Item 1 platform is thrown during the first fall in Wily 6.
    Item 1 energy now runs out exactly on the alien's ledge platform.
* **Verification.**
  * FCEUX's movie player on both cores gives 85,006 frames, with the alien dead
    one frame after the last input (end-RAM md5 `dba77825…`).
  * From the Air Man fill to the end, every boss fill, hit and kill and every
    lag frame comes exactly 4 frames before v6.2's.
  * An independent sync check and an independent rules check both found it
    valid.
  * The rules check found three inputs that change nothing: one is an exact
    no-op, and the other two only move CPU timing inside a frame. They are
    removed. The end RAM and every lag frame are unchanged on both cores.
  * `movies/rockman2-v6.3-edits.json` (61 blocks) rebuilds it from the
    publication with `tools/make_movie.py`.

**v6.2 is 269 frames (4.48 s) faster than the publication**, and 1 frame
faster than v6.1. The second Wily Machine phase dies 1 frame sooner. The wait
before Wily 6 absorbs that frame, but the stage load that starts 325 frames
after the kill now meets a lighter music frame. It lags 4 frames, as before
v6.1, instead of 5.
* **Phase 2.**
  * The kill now lands on the odd weapon slot, so the fight can no longer keep
    a decoy there. Mega Man throws the phase-change decoy straight up, and it
    leaves the screen before the fight.
  * He fights from the machine's right side. After 13 hits on the even slot, a
    blade thrown up-right, which the machine deflects up-left, holds the even
    slot. Ten point-blank throws on the odd slot then finish the machine, and
    that blade leaves the screen on the kill frame.
* **Phase 1 now sets up Wily 6.**
  * The Wily 6 platforms start from stale weapon-slot subpixels. The reserve
    blade inherits slot 2's from phase 1.
  * With v6.1's phase 1 that value is out of range, and the run fails in
    Wily 6.
  * A 7-frame change in phase 1 gives slot 2's blades exactly 25 diagonal
    moves, so the value ends in range. The 28 hits stay on the same frames.
  * The seeds are 4D/87/4B, and the Metal Blade energy covers exactly the 59
    throws.
* **Verification.**
  * FCEUX's movie player on both cores gives 85,010 frames, with the alien dead
    one frame after the last input (end-RAM md5 `74998560…`).
  * From the Wily 6 screen to the end, Mega Man, the bosses, the stage and the
    lag frames match v6.1's one frame later.
  * An independent sync check and an independent rules check both found it
    valid.
  * The rules check found six point-blank throws that did not need up+down.
    They are now plain up-right throws, with the same result on every compared
    frame, so up+down appears on 70 frames (v6.1: 66).
  * `movies/rockman2-v6.2-edits.json` (62 blocks) rebuilds it from the
    publication with `tools/make_movie.py`.

**v6.1 is 268 frames (4.46 s) faster than the publication**, and 3 frames
faster than v6.0. The first Wily Machine phase dies 3 frames sooner, so the
second phase fills and dies 4 frames earlier.
* **Phase 1.**
  * Mega Man opens with a 1-frame hop and two full jumps.
  * A blade thrown with up+down as he passes over the machine's path parks
    motionless just left of it, on the odd weapon slot. The machine, moving
    left, walks into it 24 frames later, so the hits keep a 2- or 3-frame
    rhythm while he is low.
  * A blade thrown straight down then holds the even slot, so the last ten
    throws go to the odd slot.
  * 28 hits; he is untouched until the machine's rolling ball hits him.
* **The phase change.** He parks a stationary blade for phase 2's first hit,
  then a decoy on the floor and a reserve blade near the top of a jump.
* **Phase 2** keeps its 62-frame fight, re-searched. The Metal Blade budget is
  exactly 59 blades again, and the Wily 6 seeds stay in range (4D/63/53).
* **Why 3 and not 4.**
  * The Wily 6 stage load starts a fixed 325 frames after the kill, and the
    music runs in real time.
  * With the kill 4 frames earlier, the load meets a heavier music frame and
    lags 5 frames instead of 4.
  * A frame-counter poke can't show this, because it doesn't move the music.
* **The search.** It uses a model of the fight in which Mega Man's left/right
  input is free, with a parity-aware bound. An earlier draft (85,010) failed
  in the real game because the model got one ground frame wrong. The fixed
  model matches the real game on every compared frame.
* **Verification.**
  * FCEUX's movie player on both cores gives 85,011 frames, with the alien dead
    one frame after the last input (end-RAM md5 `c42c4588…`).
  * An independent sync check and an independent rules check both found it
    valid.
  * `movies/rockman2-v6.1-edits.json` (62 blocks) rebuilds it from the
    publication with `tools/make_movie.py`.

**v6.0 is 265 frames (4.41 s) faster than the publication**, and 4 frames
faster than v5.9. The first Wily Machine phase dies 2 frames sooner, and the
second phase's fill rule turns that into 4.
* **The new start.**
  * Mega Man jumps 3 frames earlier.
  * His second floor blade is thrown straight down, so it holds the odd
    weapon slot.
  * His third blade, thrown in the air, then takes an even slot and hits 3
    frames sooner.
  * Left/right steering in the air keeps the remaining hits on a 2- or 3-frame
    rhythm.
* **The kill-frame throw is a stationary blade parked low on the odd slot.**
  It becomes the second phase's decoy. The phase change then needs only the
  first-hit blade and the reserve, so the Metal Blade budget is exactly the 59
  blades available.
* **Phase 2** was re-searched with the Wily 6 platform values checked. They end
  at 4D/A7/53, in range.
* **Why earlier searches missed it.**
  * The previous proof that this was impossible held Mega Man's horizontal
    path fixed.
  * The new search treats his left/right input as a variable. It uses a bound
    that accounts for the slot parity.
  * It also showed that v5.9's own jump timing can never reach the earlier
    kill.
* **Found by** the completeness review's lead: that fill now needed just 1
  frame.
* **Verification.**
  * FCEUX's movie player on both cores gives 85,014 frames, with the alien dead
    one frame after the last input (end-RAM md5 `3436aa0e…`).
  * An independent sync check and an independent rules check both found it
    valid.
  * One no-op edit they found was reverted, with the same end RAM.
  * `movies/rockman2-v6.0-edits.json` (62 blocks) rebuilds it from the
    publication with `tools/make_movie.py`.

**v5.9 is 261 frames (4.34 s) faster than the publication**, and 1 frame
faster than v5.8. Two Wily 4 lag frames are traded for one.
* **The lags.** In Wily 4's room 32, Mega Man is invincible after a hit there.
  The room's two lag frames are the frames where three homing enemies re-aim.
* **The fix.** While invincible, Mega Man is drawn only when bit 1 of the
  frame counter is clear.
  * One more frame in the Wily 4 weapon menu (the menu-closing START one frame
    later) runs the counter one higher through room 32.
  * On both aim frames he is then not drawn, and neither frame lags.
  * One Left on the way down is dropped to keep his fall.
* **Side effects.**
  * The Boobeam fill steps follow the counter, so the fill ends one frame
    sooner.
  * The fight gets one extra lag from the music phase.
  * Net: 1 frame. From Wily 5 on, the run is v5.8 one frame earlier.
* **Found by** an independent review of everything against v5.8. Earlier lag
  searches had shifted only the music phase, never the counter.
* **Verification.**
  * FCEUX's movie player on both cores gives 85,018 frames, with the alien dead
    one frame after the last input (end-RAM md5 `062d939d…`).
  * An independent sync check and an independent rules check both found it
    valid. The rules check showed that one more of the original edits was
    neutral; it was put back, with the same end RAM.
  * `movies/rockman2-v5.9-edits.json` (62 blocks) rebuilds it from the
    publication with `tools/make_movie.py`.

**v5.8 is 260 frames (4.33 s) faster than the publication**, and 1 frame
faster than v5.7. One lag frame is gone from the Heat Man refight.
* **The lag frame.** It is the frame Heat Man's second fireball lands and
  spawns a 4-object fire pillar.
  * With Mega Man holding Right, that frame finished about 130 cycles too late.
  * Turning left the frame before and giving no input on it brings it in time.
* **Side effect, and its fix.** Removing a lag shifts the music, which runs
  in real time, against the game.
  * Mega Man's landing sound would then start on a heavier music frame and
    cause a new lag 4 frames later.
  * Holding A one frame longer in the jump before lands him one game frame
    later, on the same real frame as in v5.7.
* **No other change to the fight.**
  * Mega Man ends up 4 px behind. Every hit still lands on its frame, because
    Heat Man's dash length follows the distance to Mega Man.
  * Two re-timed steps on the walk out keep the exit.
* **The other post-Wily-3 lags were all checked:** room 32's homing-enemy
  re-aims, the Boobeam fight, Heat's music spike, the Crash kill and the alien's
  shot. None can be removed without changing the route.
* **Verification.**
  * FCEUX's movie player on both cores gives 85,019 frames, with the alien dead
    one frame after the last input (end-RAM md5 `3d6e7ee7…`).
  * An independent sync check and an independent rules check both found it
    valid.
  * One edit the rules check found to be a no-op was dropped. The end RAM is the
    same.
  * `movies/rockman2-v5.8-edits.json` (61 blocks) rebuilds it from the
    publication with `tools/make_movie.py`.

**v5.7 is 259 frames (4.31 s) faster than the publication**, and 4 frames
faster than v5.6. The Bubble Man refight is 5 frames shorter, so the Quick Man
fill and everything after it come 4 frames earlier. Two energy budgets made it
possible.
* **A spare Metal Blade unit, found in Wily 2.**
  * Wily 5 already used every Metal Blade throw it had, and the faster Bubble
    fight needs one more throw. Each 4th throw costs a unit, and the count
    resets at weapon switches.
  * The Wily 2 boss is now beaten with 39 blades instead of 42. New paths
    around two blocks let a stationary (up+down) blade kill each block and then
    stay parked for a later hit. That makes one hit throw and two decoy throws
    unnecessary.
  * The Wily 2 end is on the same frame, and Wily 5 starts with 19 units
    instead of 18.
* **The Bubble Man refight.**
  * Every hit now lands at the 19-frame minimum (invincibility plus the hit
    check's latch).
  * Two stationary blades sit in his path. One extra blade holds slot 4, so
    the last three hits land on slot 3, the only slot the hit check looks at on
    odd frames.
  * He dies 5 frames sooner. The fill rule keeps 4.
* **Re-syncs.**
  * Quick Man's random jumps: three steps of his fight are re-timed so Mega
    Man's X subpixel steers the same rolls.
  * Crash Man's fight depends on the leftover subpixels of the Air Shooter
    tornado slots. One extra Air Shooter shot on the hub walk restores them.
    That uses Air Shooter's last spare shot.
  * Metal capsule subpixel A0, for the low jump.
  * Three Wily Machine blade directions keep all 56 hits on their frames and
    the Wily 6 seeds in range (4D/5B/4B).
* **Verification.**
  * FCEUX's movie player on both cores gives 85,020 frames, with the alien dead
    one frame after the last input (end-RAM md5 `95d684fd…`).
  * An independent sync check and an independent rules check both found it
    valid. From the Quick fill on, every event is v5.6's, 4 frames earlier.
  * Metal Blade and Air Shooter energy both end at exactly 0.
  * `movies/rockman2-v5.7-edits.json` (61 blocks) rebuilds it from the
    publication with `tools/make_movie.py`.

**v5.6 is 255 frames (4.24 s) faster than the publication**, and 1 frame
faster than v5.5. One more lag frame is gone, this time in Bubble Man's stage.
* **The second spike zip.**
  * An A press removes one of its lag frames.
  * An L keeps Mega Man in the water one frame longer, which shifts the
    underwater slow-down counter.
* **The Bubble DelayDownScroll stays on its heavy music frame.**
  * Removing the lag would put the check on a lighter music frame. One extra
    frame in the Metal Blade menu restores the timing, with the frame counter
    1 higher.
  * The hit check then favours the other slot parity. So a first blade thrown
    straight down frees slot 4 in time, and the crab killer goes to slot 3.
  * One blade is thrown 8 frames before the check. Its sound effect is at a
    heavy point of its playback on the check frame, which supplies the CPU load
    the check needs.
* **The boss fill ends 1 frame earlier.**
  * The counter is 1 higher, and the underwater counter is shifted by the
    later exit from the water. Together they make the fill end 1 frame sooner.
  * From there the run is v5.5 one frame earlier, with the same frame counter.
  * Two blade directions restore the stale Y subpixels that Wily 1's Item 1
    platforms need.
  * A one frame earlier avoids a new lag on the kill frame.
* **Verification.**
  * FCEUX's movie player on both cores gives 85,024 frames, with the alien dead
    one frame after the last input (end-RAM md5 `5a731ab4…`; v5.5's end RAM
    except the sound engine's frame counter).
  * The lever was built on v5.2 and checked by an independent sync check and an
    independent rules check. Both found it valid.
  * **Caveat for console verification:** Bubble's DelayDownScroll now lands
    only about 2 CPU cycles inside its window (v5.5: about 22). Both FCEUX
    cores agree, but this is the most cycle-sensitive moment in the run.
  * `movies/rockman2-v5.6-edits.json` (61 blocks) rebuilds it from the
    publication with `tools/make_movie.py`.

**v5.5 is 254 frames (4.23 s) faster than the publication**, and 4 frames
faster than v5.4. The Metal Man refight's fill comes 4 frames earlier, and
everything after it moves with it.
* **The Crash Man refight is 1 frame faster.**
  * Mega Man walks left to dodge Crash Man's bomb, then jumps, so his second
    Air Shooter volley comes 1 frame earlier.
  * The hit check uses the even weapon slots on even frame counts and slot 3
    on odd ones.
  * The new volley lands hit 2 on slot 4 and the kill on slot 3, one frame
    sooner.
* **The hub pause before Metal Man uses the up+down menu trick.** Control
  comes back 1 frame sooner.
* **The Metal fill rule** (every 4 frames) turns those 2 frames into 4.
* **Re-syncs.**
  * The Metal capsule is entered with a different X subpixel (90), so Metal
    Man still makes his low first jump.
  * The Flash capsule walk is re-timed.
* **The Wily Machine needed a small fix.**
  * The new Crash fight leaves different stale subpixels in the weapon slots.
  * With v5.4's Wily Machine inputs unchanged, one phase-2 blade was checked
    1 px too low, the hit slipped 2 frames, and Mega Man died in Wily 5.
  * Two phase-1 throws aimed up-right instead restore it: all 56 hits land on
    v5.4's frames, and the Wily 6 platform seeds end at 4D/87/4F, in range.
* **Verification.**
  * FCEUX's movie player on both cores gives 85,025 frames, with the alien dead
    one frame after the last input (end-RAM md5 `39824f19…`).
  * An independent sync check and an independent rules check both found it
    valid. From the Metal fill on, every event is v5.4's, 4 frames earlier.
  * `movies/rockman2-v5.5-edits.json` (61 blocks) rebuilds it from the
    publication with `tools/make_movie.py`.

**v5.4 is 250 frames (4.16 s) faster than the publication**, and 8 frames
faster than v5.3. Both Wily Machine fights are faster, so Wily 6 starts 8
frames earlier.
* **Phase 1.**
  * Mega Man takes a new route: two jumps, staying 14-15 px left of the
    machine (13 px would be contact damage).
  * The Metal Blade throws come from an exact search in a model of the boss
    hit routine. The model reproduces all 56 of v5.1's hits.
  * The hit check looks at even and odd weapon slots on alternate frames, and
    a hit needs the check to clear first. The new schedule lands every hit on
    the earliest frame those rules allow.
  * The machine dies 6 frames earlier. The phase-2 fill rule rounds that to 4.
* **The phase change.**
  * The machine's ball hits Mega Man right after the kill. That gives him
    invincibility that lasts through all of phase 2.
  * Meanwhile he parks four stationary blades. Up+down throws make a blade
    stand still, the same trick the publication uses in this fight:
    * a filler that dies before phase 2;
    * a decoy in slot 3, which keeps every phase-2 hit on the even slots;
    * a parked blade that lands the first hit;
    * a reserve that fills the first gap while he falls and lands.
* **Phase 2** dies 62 frames after its fill (v5.1: 66). The Wily 6 map rule
  turns that into 4 more frames.
* **Limits.**
  * It uses all 59 blades the Metal Blade energy allows.
  * The Wily 6 climb needs the leftover blade Y subpixels in range. A phase-1
    schedule was chosen that ends them at 4D/67/4F, which works.
* **Verification.**
  * FCEUX's movie player on both cores gives 85,029 frames, with the alien dead
    one frame after the last input (end-RAM md5 `3c0c1bf0…`).
  * The fights were built on v5.1 (85,032 frames there) and checked by an
    independent sync check and an independent rules check. Both found them
    valid.
  * They were then moved onto v5.3 by a 1-frame shift, with v5.3's alien fight 8
    frames earlier. Mega Man's state and the alien's HP match v5.3's alien fight
    frame for frame.
  * Up+down appears on 65 frames: v5.3's 57, plus 12 stationary throws, minus
    4 old ones.
  * The first commit of this file carried alien2's original menu inputs, with
    two up+down frames that gain nothing. This version uses v5.1's inputs there,
    as v5.3 does, with the same end RAM on both cores.
  * `movies/rockman2-v5.4-edits.json` (62 blocks) rebuilds it from the
    publication with `tools/make_movie.py`.

**v5.3 is 242 frames (4.03 s) faster than the publication**, and 2 frames
faster than v5.2. The final alien fight is 2 frames shorter. The alien fight
is the last thing in the run, with no frame rule after it, so both frames come
off the movie.
* **The pause is 1 frame shorter.** The pause-menu up+down cursor trick is used
  on the menu's second page.
  * That flips the frame-counter parity relative to the alien's path.
  * The boss hit check looks at Bubble Lead's slot only on every other frame.
    So the final burst (22 hits from that one slot) can now land on even alien
    steps, starting at step 190 instead of 191.
* **But only if Mega Man stands far enough right on the secret ledge when his
  knockback stun ends.** He needs X 37.0 or more. Our earlier study of this
  fight (on v2) got within 0.375 px. Two details close the gap:
  * The knockback landing tolerates a hit up to Y 66.5 / X 52.44. Mega Man
    crosses the ledge top only 0.28 px deep, and the next left move still lands
    him.
  * Jump 2 starts one alien step later from X 37 + 13/16, and jump 3 is timed so
    that shot 2 hits him at X 52.25 near the apex. His stun then ends at
    X 37.06.
* **The burst.** A hop right of the ledge, then left+B and right on alternate
  frames: each bubble flies the way Mega Man faced the frame before. The burst
  hits from alien step 190 to the kill at step 232.
* **Verification.**
  * FCEUX's movie player on both cores gives 85,037 frames, with the alien dead
    one frame after the last input (end-RAM md5 `ed4cd1c7…`).
  * The fight was first built and checked on v5.1 (alien2's 85,038-frame movie).
    An independent sync check and an independent rules check both found it
    valid.
  * It was then moved onto v5.2 by a 1-frame shift. v5.3's final RAM equals the
    85,038-frame movie's except for $EA, a sound-engine counter that is one
    frame behind because of v5.2's removed lag frame.
  * The rules check found two up+down frames on the menu's first page that gain
    nothing. v5.3 uses v5.1's inputs there, with the same end RAM, so the only
    new up+down frame is the one that saves the frame (57 in all).
  * `movies/rockman2-v5.3-edits.json` (62 blocks) rebuilds it from the
    publication with `tools/make_movie.py`.

**v5.2 is 240 frames (3.99 s) faster than the publication**, and 1 frame
faster than v5.1. It removes one lag frame before Wily 4.
* **What changed.** Mega Man hops on the last frame before Metal Man's boss
  door instead of walking in, so he enters the room airborne.
  * The boss-spawn frame is very heavy: the door-closing loop restarts the boss
    music every frame.
  * An airborne Mega Man's routine costs about 330 fewer cycles than a walking
    one. That brings the frame under the limit, so it no longer lags.
* **Why it is a clean frame.** That lag frame did not advance the frame
  counter, so every later frame rule and random roll is unchanged. Everything
  after it is v5.1 one frame earlier.
* **The other 34 short lags before Wily 4 were all checked** (lag_audit). They
  are DelayScroll check frames (inherent), boss-spawn and boss-kill frames that
  are hundreds to thousands of cycles over, or loads.
  * Three lags in Bubble's second spike zip can be removed with free A presses.
  * But then Bubble's DelayDownScroll needs about 1,200 more cycles on its check
    frame, and no source of that much load has been found yet.
* **Verification.** FCEUX's movie player on both cores gives 85,039 frames, with
  the alien dead one frame after the last input (end-RAM md5 `9a681a1c…`).
  * The independent rules check found it valid. It replayed the movie from
    power-on and compared every frame with v5.1: after the removed frame, the
    frame counter, lag flags, HP, boss HP, stage, screen, lives and energies
    equal v5.1's one frame later.
  * The independent sync check also found it valid. Both cores give identical
    RAM and lag flags on every frame. Every DelayScroll check still lands
    inside its window: the gap to the interrupt moves by at most 2 cycles.
  * `movies/rockman2-v5.2-edits.json` (62 blocks) rebuilds it from the
    publication with `tools/make_movie.py`.

**v5.1 is 239 frames (3.98 s) faster than the publication**, and 16 frames
faster than v5. It is v5 with two faster Wily 5 refights, plus the
re-synchronisation they need.
* **Air Man refight.**
  * Leaf Shield goes up in the air right after the first hit and is thrown
    while Mega Man is still rising.
  * Hits 2 and 3 land 10 and 8 frames earlier, and the kill 12 frames earlier
    (78204 instead of 78216).
  * Mega Man is back in the hub 11 frames earlier. The 4-frame rule at the
    next refight rounds that to 12.
* **Metal Man refight.**
  * The first Metal Blade is thrown at HP 28+2, standing, while Metal Man
    makes his low jump. The kill comes 2 frames earlier.
  * A lower jump into the Flash Man capsule saves 1 more frame. That crosses
    the next 4-frame rule, so the lead becomes 16.
* **Re-synchronisation.** The new frame counter changes every later random
  roll, so:
  * Hub walks put Mega Man's X subpixel at 60, 00 and A0 for the Quick, Crash
    and Metal capsules. The later bosses then make the same choices as in v5.
  * Four Metal Blade direction changes in the Wily Machine fight keep the
    hidden Y subpixel that the Wily 6 climb needs in range (slot 4: 0x4B).
* **Verification.**
  * FCEUX's movie player on both cores gives the same final RAM (md5
    `654f73d9…`), with the alien dead one frame after the last input (85039).
  * An independent sync check and an independent rules check both found it
    valid.
    * Before frame 78140 it is identical to v5. From 82043 on, every input is
      v5's input 16 frames earlier.
    * It adds no up+down, left+right, START or SELECT input, and no refused
      START.
    * Boss hits, Mega Man's HP, lives and lag frames match v5 at the shift.
  * `movies/rockman2-v5.1-edits.json` (62 blocks, each with its reason)
    rebuilds it from the publication with `tools/make_movie.py`.
* **Credit.** The credit notes for v5 below apply unchanged. The .fm2 keeps
  `comment author Shinryuu`.

**v5 is 223 frames (3.71 s) faster than the publication**, and 104 frames faster
than v4.2. It combines two sources:
* **Shinryuu's own unpublished improvement of his run,** up to Wily 3.
  * He recorded it as a video, 174 frames faster than his publication, but
    never released the movie file.
  * We rebuilt its inputs stage by stage, using the video as the reference.
    Each rebuilt stage reproduces every visible frame.
  * We then joined them into one real movie from power-on, with no RAM pokes.
    Five independent checks verified the joined movie link by link.
* **Our own improvements** from Wily 3 on:
  * the Guts Tank fight (v3);
  * Shinryuu's Wily 4, transplanted in v4.1;
  * the Wily 6 climb (v4.2);
  * a re-synchronised Wily 5.

**Where the time comes from** (frames saved vs the publication, cumulative at
each stage start):

| Stage | Lead | What |
|---|---|---|
| Air | 10 | Kaminari Goros deleted at spawn (no lag), mid-air pause, DelayRightScroll 10 frames earlier |
| Crash | 18 | wall zip in the boss room and a kill from inside the wall, so no exit teleport |
| Quick | 34 | Mega Man starts below the screen (Y high byte left over from Crash) and falls to the first scroll |
| Bubble | 73 | Item 2 route, spike zips, DelayDownScroll |
| Wood | 84 | Atomic Fire in the landing pause, DelayUpScroll on screen 4, no pause on screen 5 |
| Wily 1 | 116 | Mecha Dragon killed on a 16-frame boundary |
| Wily 3 end | 132 | Shinryuu's Wily 2/3 route with our Guts Tank fight; 128-frame counter lead at the 16-frame fade |
| Wily 5 | 190 | Leaf Shield Boobeam Trap fight |
| alien death | 223 | Bubble refight fill 4 frames earlier, faster Wily 6 climb |

**Mechanics this build depends on** (details in the scratch notes; summary in
`docs/whole-game-analysis.md`):
* **DelayScrolls need cycle-exact CPU load.** On the check frame the interrupt
  must land inside a bank switch, so the inputs have to be tuned until it does.
  Two loads that never show on screen supplied the missing cycles:
  * The tail of a sound effect queued 10 frames earlier: a hidden landing
    above the screen in Wood.
  * A **refused pause**. START while weapons are on screen is refused, but the
    refusal check still costs about 165 cycles. It is used at Bubble 44765 and
    at Wood's three DelayDowns (48122, 48323, 48498).
* **Stale slot values.**
  * New objects inherit leftover subpixels, hitbox types and the like from the
    previous occupant of their slot.
  * Platform heights, zips and the Wily 6 climb depend on them, so each stage's
    weapon use was tuned to leave the next stage the values it needs.
* **RNG.** The RNG depends on the frame counter and Mega Man's X subpixel.
  * Every refight and enemy roll was re-manipulated for the new counter.
  * One example is the Wily 2 capsule drop, which must roll 88–92.

**Verification.**
* FCEUX's movie player on both cores gives the same final RAM (md5
  `f85c3aa9…`), with the alien dead one frame after the last input (85055).
* An independent sync check replayed every frame. An independent rules check
  found every input legitimate.
* Its notes for a judge:
  * Up+Down appears on 56 frames: the publication's 17 plus 39 pause-menu
    cursor tricks.
  * Four refused STARTs affect the CPU timing, and the publication has none.
    They are legitimate inputs, but their effect depends on cycle-accurate
    emulation (both FCEUX cores agree).
  * By the visible alien death v5 is 222 frames faster; by movie length, 223.
* `movies/rockman2-v5-edits.json` (61 blocks, each with its reason) rebuilds
  it from the publication with `tools/make_movie.py`.

**Credit and submission.** Most of v5's gain is Shinryuu's unpublished work,
plus warmCabin's discoveries (the menu trick, the Leaf Shield Boobeam idea,
the Crash→Quick setup). The .fm2 header keeps `comment author Shinryuu` and
his rerecord count. Any TASVideos submission of v5 needs Shinryuu's agreement
or co-authorship, and correct header fields.

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
