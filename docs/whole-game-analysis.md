# Rockman 2 (J): whole-game analysis

How the game decides how long the run takes, measured in the emulator and read
in the ROM disassembly. Frame numbers are 0-based frames of publication #4410
unless stated otherwise. RAM addresses are NES CPU addresses. "Bank b $XXXX"
is a PRG bank of the MMC1 ROM; bank 15 is fixed at $C000.

## 1. Frame rules and how a saving propagates

`$1C` is a frame counter. The NMI increments it only when the main loop has
finished its frame; on a true lag frame it does not move. Every place where the
game waits polls `$1C`:

* boss health fills: `$1C & 3`
* weapon-get screens and weapon-energy refills: `$1C & 7`
* the Wily 1 and Wily 3 death fades: `$1C & 15`
* the Wily maps: `$1C & 3`
* the title: `$1C & 1`

Everything else between two waits has a fixed length:

* section scrolls: 126 frames
* shutter doors: 179 frames
* boss door to health fill: a fixed length per boss
* pause menus
* stage select and READY
* the robot-master post-death sequence: 650 frames, then a teleport, then 63 + 10 frames

**Propagation rule.** Split a saving into a `$1C` lead `c` (frames on which
`$1C` advanced) and a lag lead (frames on which it did not). At a rule with
period `q`, where the published run waits `w` frames:

* the `$1C` lead becomes `q * floor((w + c) / q)`;
* the lag lead passes unchanged.

So a lead that is a multiple of `q` passes untouched, and a smaller one is lost
unless `w + c >= q`.

The gating rules of the published run (`q` = period, `w` = frames waited):

| frame | rule | q | w |
|---|---|---|---|
| 4995 | Flash Man health fill | 4 | 3 |
| 6137 | Flash stage end (weapon-get screen) | 8 | 3 |
| 13001 | Heat Man health fill | 4 | 1 |
| 14813 | Heat stage end | 8 | 7 |
| 21518 | Air Man health fill | 4 | 0 |
| 22674 | Air stage end | 8 | 0 |
| 28247 | Crash Man health fill | 4 | 0 |
| 29231 | Crash stage end | 8 | 3 |
| 34365 | Quick Man health fill | 4 | 0 |
| 35412 | Quick stage end | 8 | 0 |
| 39442 | Metal Man health fill | 4 | 1 |
| 40493 | Metal stage end | 8 | 0 |
| 45303 | Bubble Man health fill (underwater: also the 5-frame `$FC` cycle) | 4 | 0 |
| 46560 | Bubble stage end | 8 | 1 |
| 49657 | Wood Man health fill | 4 | 0 |
| 50741 | Wood stage end | 8 | 7 |
| 52559 | Wily map before Wily 1 | 4 | 2 |
| 56979 | **Wily 1 end: Mecha Dragon death fade** | **16** | **0** |
| 58242 | Wily map before Wily 2 | 4 | 1 |
| 58868 | Wily 2 weapon refill 1 | 8 | 4 |
| 59087 | Wily 2 weapon refill 2 | 8 | 1 |
| 62236 | Wily 2 boss health fill | 4 | 0 |
| 65427 | Wily 2 end, Wily map | 4 | 1 |
| 66156 | Wily 3 weapon refill | 8 | 1 |
| 69148 | **Wily 3 end: boss death fade** | **16** | **1** |
| 70433 | Wily map before Wily 4 | 4 | 0 |
| 74638 | Boobeam Trap health fill | 4 | 1 |
| 76808 | Wily 4 end, Wily map | 4 | 3 |
| 77410-81208 | Wily 5 refight fills (Heat, Air, Wood, Bubble, Quick, Crash, Metal, Flash) | 4 | 2, 2, 1, 0, 0, 0, 2, 3 |
| 81861 / 82082 | Wily Machine fills | 4 | 2 / 1 |
| 83047 | Wily 5 end | 4 | 0 |
| 84895 | Alien health fill (last rule of the run) | 4 | 1 |

What the table means in practice:

* **Before Wily 1.** Nothing survives Wily 1 unless the `$1C` lead there is 16.
  A lone 8-frame gain at a robot-master stage end is lost. Two such gains, for
  example 1 frame before Heat's weapon-get (w=7) plus 1 frame before Wood's
  (w=7), would add up to 16.
* **Wily 2 and 3.** Leads must be at least 15 at the Wily 3 fade.
* **From Wily 4 on.** Every rule is `q4`, so any 4-frame lead survives to the
  end.
* **After the alien fill.** There is no rule, so in the alien fight every frame
  counts.

**Lag frames.** A lag frame does not advance `$1C`, so removing one never
moves a frame rule. Of the 369 true lag frames in the run, most are fixed stage
loads (9-10 per stage). About 50 are single frames caused by crowded screens.

## 2. The RNG

Each NMI (bank 15 $D0C3) updates the RNG:

`$4A = (($0480 XOR $4A) + $1C + C) >> 1`

Here `$0480` is Mega Man's X subpixel. The update also runs on lag frames.

**Where the run reads it.** Outside that update, the run reads the RNG about
1,100 times. The readers are:

* Heat Man's attack timer;
* Air, Crash, Quick, Metal and Wood Man's choices, and the Mecha Dragon;
* a few stage enemies;
* the item-drop routine (bank 15 $F23D). The big weapon capsule that Wily 2
  refills from is such a drop.
* the Wily Machine.

**Convergence.** The update map halves the difference between two states every
frame. So while Mega Man stands still, the RNG forgets its past within about 8
frames and becomes a function of `$1C` and his X subpixel alone. For example,
in v2's Air Man refight room `$4A = $1C - 0x80` for 100+ frames. Two
consequences:

* **Any saving changes the RNG.** It shifts `$1C` at every later event, so every
  later random decision has to be re-manipulated.
* **The control is the resting subpixel.** For refights whose decision comes
  right after the health fill, that subpixel is the only lever.

## 3. Pauses and menus

* **Pause gate.** A pause is refused while any object in slots 2-15 is alive
  ($C573).
* **Up+Down menu trick.** Holding Up and adding Down on the next frame moves
  the cursor twice. 29 of the 46 pauses can close 1-3 frames sooner, 39 frames
  in total, but frame rules absorb almost all of it.
* **Deliberate delays.** The 9 "wasted" frames in Bubble Man's stage (44755)
  are on purpose: without them the down-scroll after the fall never starts and
  Mega Man dies in the pit.
* **Pause at the stage start.** Every pause ends with a 12-frame teleport-in
  animation (state $1A). A pause opened during the stage-start landing animation
  overlaps it and costs about 13 frames less. The published run already does
  this in Air, Crash, Quick, Metal and Wily 1, 4, 5 and 6. Wily 3 did not, and
  now does.
  * Heat, Bubble and Wily 2 need the Buster before their first pause.
  * Wood fails for a scroll reason (section 6).

## 4. Bosses

**Hit routine (bank 11 $A59D).**
* Each frame it checks only the weapon slots of one parity: 9, 7, 5, 3 on odd
  `$1C` and 8, 6, 4, 2 on even `$1C`.
* A hit needs `$B4 = 0`. `$B4` is cleared only on a checked frame with no
  overlapping weapon, so overlaps can block each other.
* The boss's invincibility timer `$05A8` counts down in the boss's draw routine
  (bank 15 $CE48). On frames where the sprite limit skips drawing the boss, the
  invincibility lasts longer and its AI animation counters stop.

**Heat Man.**
* Buster only (2 per hit, 14 hits) on a 69-frame cycle: hit, 19 frames hurt, a
  random wait `$B2` (31 is the minimum), then a flame dash to Mega Man's X - 15.
* The published kill is a double knockout. Mega Man takes lethal contact on the
  frame before the kill and is frozen in mid-air, which shortens the exit
  teleport. The teleport takes `floor(Y/8)+9` frames.
* Contact needs Y ≥ 161 while a 1-frame-shorter teleport needs Y < 160, and the
  cycle cannot be shortened. So Heat cannot gain.

**Wood Man.**
* Air Shooter: all three tornado slots must be free to fire.
* The leaf shield deflects anything entering from the left.
* His jump timing is driven by his draw-time animation.
* The kill at 49986 is minimal: the fast tornado of the previous volley needs
  39 frames to leave the screen.

**Guts Tank (Wily 3).** The head becomes hittable a fixed 309 frames after the
tank starts moving. The tank does not move during a pause, so the weapon-switch
pause costs its full length. The new fight works like this:
* Two Quick Boomerangs are thrown from the top of an early jump while the head
  is still invulnerable. They return through it on its first hittable frames.
* Then one boomerang per odd frame lands 3 frames after each throw.
* 14 hits arrive on consecutive same-parity frames, so the boss dies at V+26
  instead of V+44.

**Boobeam Trap (Wily 4).**
* Only Crash Bombs hurt it. The fuse starts when the bomb sticks, and the bomb
  keeps slot 2 for 183 frames after sticking.
* Hurt glitch: when a cannon hurts Mega Man, its weapon check runs with the hurt
  spark's stale fields. The box size comes from `$06E0` of slot 14, which is
  Mega Man's X at his previous hurt, so it can be huge.
* The exit teleport starts from where Mega Man lands after the kill, so ending
  on the high ledge matters.
* The published fight is at its limit.

**Wily 5 refights.** The return warp only starts if Mega Man stands on the
room's return teleporter when the boss dies.

**Alien (Wily 6).**
* Its figure-eight path depends only on unpaused, non-lag frames.
* Only Bubble Lead hurts it, 1 per hit, and a pause is needed to select it.
* The single Item 1 platform onto the hidden ledge is worth about 27 frames
  over a floor fight, and it is already frame-perfect.

## 5. Hidden state that carries over

* **Stale weapon-slot fields.** New objects in weapon slots 2-5 do not clear X/Y
  subpixels or hitbox type `$0590`. Item 1/Item 3 platforms, Bubble Lead shots
  and explosion pieces inherit the previous occupant's values. This is why a
  changed fight in Wily 3 broke a platform in Wily 4, and why v2 needed three
  extra Metal Blade throws.
* **Weapon-energy capsules.** A capsule refills the current weapon one unit per
  `$1C & 7 == 0` frame and freezes the game meanwhile: 8 frames per unit.
* **Item 1 energy.** Each platform costs 2 units. The run ends with Item 1
  at 0.

## 6. DelayScrolls (from the Wood stage analysis)

The scroll check (bank 14 $829E) works like this:

1. It calls a bank switch, then reads a table indexed by Y.
2. If the NMI fires inside the bank switch, the sound driver runs there and
   overwrites Y.
3. Whether the scroll fires therefore depends on the CPU cycle at which the
   check runs and on the music's state.

This is why changes in CPU load (enemies, sound effects) or in music timing (a
pause moved) can break a DelayScroll. Moving Wood's weapon-switch pause to the
stage start (Shinryuu's "Wood 13") breaks it for that reason:
* Only one frame of the up-scroll is heavy enough to fire it.
* The only extra load compatible with Atomic Fire selected leaves Mega Man
  1 px too high for screen 5's exit.

## 7. What changed in v3, by rule

`movies/rockman2-v3-85220.fm2`: 85,220 frames, 59 fewer than #4410.

* **Wily 3: +32.**
  * Wily 2 menus: 6 frames give 4 at the Wily 2 fill.
  * Wily 3 pause moved to the stage start, plus capsule re-routing: lead 8.
  * Boss menu: 6 frames.
  * New Guts Tank fight: 18 more frames.
  * That is a lead of 32 at the q16 fade.
* **Wily 4: +2.** One climb frame and two menus give 4 at the Boobeam fill;
  two extra lag frames cost 2. Wily 4 was re-synchronised: 5 input edits
  absorb the changed stale slot fields.
* **Wily 5: re-synchronised 34 frames earlier**, keeping v2's +4 at the Heat
  fill. RNG decisions were re-manipulated through Mega Man's resting X
  subpixel. Metal Blade throws set the hidden slot subpixels that Wily 6
  needs.
* **Wily 6: +20.** The ceiling zip starts from the third Item 1 platform's
  throw pose. The door lead is kept a multiple of 4, and the stale Y subpixel
  of the alien-room platform kept in range.
* **Alien: +1** (from v2: final burst fired one frame early).

Searched and not improvable with the current routes:
* Heat and Wood stage ends;
* Wood's stage-start pause;
* the Metal Man and Crash Man stages, whose fights sit exactly on their hit and
  slot bounds;
* the Boobeam fight;
* the alien fight (the best near-miss is 0.375 px short of 2 frames);
* Item 1 at the alien (already used).

So a 16-frame lead before Wily 1 has not been found. Two robot-master stages
would each have to finish 8 frames early.

## 8. What v4-v5 add (routing level)

Section 7 ends with "a 16-frame lead before Wily 1 has not been found". It was
there, but it took changes across several stages at once, plus the hidden
state that one stage hands to the next. Shinryuu found that route in an
unpublished run. We rebuilt its inputs from his video, matching every visible
frame, and joined the stages into one real movie. These are the mechanics it
relies on, all measured in the emulator.

**Item 1 "values" are stale Y subpixels.**
* An Item 1 platform rises 1 px on each frame where its slot's Y subpixel
  borrows when 0x41 is subtracted. So its rise pattern, and with it every
  platform zip, depends on the subpixel left in slots 2-4 by whatever used the
  slot last.
* That can happen in an earlier stage. Six Item 3 throws in Heat set the value
  Air's platforms need, and Air's two extra platforms set Crash's and Quick's.
* Weapons change these values in fixed steps. A diagonal Metal Blade adds or
  subtracts 0x2C per frame; a Quick Boomerang adds a fixed sum over its 35-step
  flight. That is how the Wily 2 seed and the Wily 6 climb seed were set.

**The Crash → Quick handover is Mega Man's Y high byte ($F9).**
* Crash Man is killed with Mega Man zipped into the boss room's wall. Mega Man
  then falls below the screen, so $F9 becomes non-zero.
* Stage select and stage start never clear $F9. Quick therefore starts with
  Mega Man invisible below the screen, falling to the first down-scroll 38
  frames early.

**DelayScrolls need cycle-exact CPU load on the check frame.**
* The interrupt has to land on the bank switch at $C7A5 (17-50 cycles before
  it), and the deferred sound routine must leave an allowed Y.
* Shinryuu's visible inputs alone were often a few hundred cycles off on our
  timeline. That is because the CPU phase depends on the whole input history,
  including his style-only changes. Two loads that never show on screen closed
  the gap:
  * A sound effect's tail. A landing queues SFX $29, which makes the next ten
    NMIs longer by up to about 1,400 cycles. Wood's screen-4 up-scroll uses a
    hidden landing above the screen 10 frames before the check.
  * A refused pause. START is refused while slots 2-15 hold live objects, but
    the refusal scan costs about 165-190 cycles. Bubble's DelayDownScroll and
    Wood's three DelayDowns use it.
  The music runs in real time from the stage start, so a check can only work on
  frames where the music makes the NMI heavy enough. At Bubble that is every
  10th frame.

**The 16-frame Wily 1 fade needs exact alignment.**
* The end sequence only starts when the frame counter is 0 mod 16. An odd
  misalignment never ends the stage.
* Wily 1's exit is itself a DelayDownScroll timed from the stage start.
* Shinryuu's 15-frame menu delay in pause 3 is that alignment. On our chain,
  which reaches Wily 1 eight counter frames later, the delay is 6 frames and
  one released Right frame re-syncs the kid enemies' RNG.

**Underwater fills keep a stale counter.**
* $FC, the underwater slow-down counter, only ticks in water rooms, so it
  carries over from Wily 3 into the Bubble Man refight.
* On v5's timeline its slow frames fall one frame later. The refight fill
  therefore starts 4 frames earlier, which became v5's last 4 frames.

**Combining runs.**
* Shinryuu's Wily 2/3 gain is an Item 1 energy plan that the 16-frame Wily 3
  fade absorbs, so it nets 0. Our v3 Guts Tank fight stacks on top of it:
  counter lead 128 at the fade.
* Shinryuu's Wily 4 (v4.1) replays verbatim on that state, offset by 96 frames.
  Wily 4 is insensitive to frame-counter offsets of 16k.
* Wily 5 always needs a re-sync. While Mega Man stands in the hub, the RNG
  converges to a function of the frame counter and his X subpixel, so each
  refight's first random decision is set by the capsule walk.

## 9. Larger routing, other glitches, and ACE

After v5 we looked for savings at the route level, not just the input level.
Four studies covered it: route_study, glitch_hunt, w4exit and r2_w23. None
found a larger reroute that can be built. Most of the reasons below are
surveys and paper arguments, not proofs. They rule out the variants that were
tried, not every variant, and no second agent has reviewed them for holes.
An adversarial review of every closure in this document has started.

**Refight order and weapons.**
* v5's Wily 5 order (Heat, Air, Wood, Bubble, Quick, Crash, Metal, Flash) is
  the one the 2006 exhaustive search found.
* Orders with 6 pauses instead of 7 have to backtrack across the bottom row,
  which costs about 100 frames. Each pause costs 32-40 frames net.
* The weapons are forced by the damage tables, and Metal Blade's energy is
  used exactly.

**Robot-master order: open, not proven.** route_study only checked on paper
the three fight savings a reorder would buy:
* Heat Man with Bubble Lead, about −600 frames;
* Air Man with Leaf Shield, about −150;
* Flash Man with Metal Blade, about −140.

Each of these breaks a hand-over the current route relies on: the Item 1 and
Item 3 seeds in weapon slots 2-4, and $F9 (Crash → Quick, Bubble → Wood). That
does not show that another order cannot supply those hand-overs some other
way. It also does not rule out an order with useful hand-overs of its own, or
with hand-overs we have not found.

**Double KOs.**
* If the boss dies 1-15 frames after Mega Man, no life is lost and the stage
  ends normally. The exit teleport then starts from where Mega Man died.
* 16-175 frames softlocks; 176 frames or more costs a life.
* A death high in the air would shorten an exit teleport. It needs:
  * Mega Man's HP at or below the hit's damage;
  * no invincibility;
  * the killing shot already in flight.
* Heat Man's stage already ends with a double KO. It cannot be higher, because
  Heat Man's contact needs Mega Man at Y ≥ 161.
* At the other robot masters, a higher death either saves too little to cross
  the next 8-frame rule, or first needs several extra hits on Mega Man to bring
  his HP down.
* Wily 1 and Wily 2 already end with double KOs.

**Death warps.** The checkpoint after a death comes from the scroll position
($0440) checked against per-stage thresholds. Both of v5's deaths already
warp. No other checkpoint has enough time in it to pay for a death's ~265-frame
overhead.

**Offscreen starts.** $F9 (Mega Man's Y high byte) carries into the next stage.
* Starting below the screen kills Mega Man at every robot-master start except
  Quick (already used), and at Wily 1 and 2.
* A Wily 3 start below the screen would save 10-11 frames, but Wily 2 ends in a
  closed room.
* A Wily 4 start above the screen would save 138 frames raw. It is a dead end:
  Mega Man is frozen for 734 frames after the Guts Tank kill, and the Guts room
  has no screen above it.

**Exit teleports.**
* The teleport length is floor(Y/8) + 9 frames, so a higher exit is shorter.
  The Wily 4 exit cannot be raised:
  * The Boobeam room has no spot where Mega Man can be embedded in a wall.
    180,000 frames of random input found only 1-pixel overlaps.
  * $F9 is not reset before Wily 5, so leaving the room downward costs a life.
  * Standing on the step for a higher teleport costs as many frames as it saves.
* The other Wily exits are already at their best heights.

**Frame-rule levers.**
* Before Wily 1, savings only count in 16s, at the Wily 1 fade.
* R1, +16 at Wily 1: firing Wily 1's exit DelayDownScroll 16 frames earlier
  does not work, because the music makes those check frames too light.
  * It needs the stage to start 16 counter frames earlier instead.
  * That means two pieces before it: 4 more frames in Metal Man's stage, and
    Wood's DelayDowns at Shinryuu's frames. Both are being tested.
* R2, +16 at the Wily 3 fade, needs one Wily 2 Item 1 platform dropped.
  * All six are load-bearing.
  * Item 1 energy across Wily 2 and 3 is used exactly.

**Glitches surveyed** (no new saving). This list covers the documented
glitches we found, plus what code reading around them showed. There was no
systematic search for unknown glitches, so it does not show that no other
time-saving glitch exists.
* **Refight skip** (warmCabin's video):
  * The boss that spawns comes from the touched capsule's slot.
  * The 9th teleporter spawns only when $BC = FF.
  * $BC has two writers: a clear at stage start, and the boss bit set on
    return.
  * No out-of-range index is reachable.
* **Zips.** Facing left with the point at X−8 in a solid tile, Mega Man is
  pushed right 16 px per frame, checked at three heights. An offline predictor
  (agents/glitch_hunt) found no new useful zip.
* **Doors.** A zip into a boss room does not start the boss.
  * Air's first door can be entered from below, which would save 118 frames
    if a DelayDownScroll worked there.
  * It cannot: the room is too light, so its check runs about 14,000 cycles
    too early.
* **Menus.** Stage select, pause, title and password screens handle
  simultaneous inputs safely. The pause U+D cursor trick is the only one, and
  v5 already uses it.
* **Small ones:**
  * Boobeam walls vanishing after a pause: does not happen on the Japanese
    version.
  * Leaf Shield with L+R: works, but gains nothing.
  * Time Stopper on Quick Man: 1 damage per 30 frames, too slow.

**Arbitrary code execution** is its own category and was treated as a separate
question. The code survey found no reachable out-of-range jump index:
* The one candidate dispatch, $AD ≥ $7F through $82D5, needs an object type
  that does not exist.
* That type's AI would hit BRK, which resets the game.

A deeper ACE search was not carried out.

## 10. What v5.1-v6.4 add (Wily 4-6 mechanics)

v5.1 to v6.4 save 35 more frames, almost all in Wily 4, 5 and 6. Each lever below
is small, but they rest on a handful of mechanics that were not documented
before.

**The boss hit check** (bank 11 `$A59D`):
* **Weapon slots by frame parity.** On odd frame counts it checks weapon
  slot 3, on even ones slots 2 and 4. A new Metal Blade takes the highest free
  slot (4, then 3, then 2).
* **The `$B4` latch.**
  * A hit sets `$B4`. It is cleared only on a checked frame where no checked
    weapon overlaps the boss.
  * Checks resume only once the boss's invincibility has run out.
  * So the fastest cadence for a robot master is 19 frames: 18 frames of
    invincibility plus one latch-clearing check.
  * It is 20 for a weapon that can use only one slot parity. Crash Bomber
    always spawns in slot 2.
  * Switching slot parity between hits costs a frame.
* **Most refight levers are scheduling fixes:**
  * the Bubble Man refight with every hit at the 19-frame minimum (v5.7);
  * the Crash Man kill moved onto slot 3 one frame earlier (v5.5);
  * the Wily Machine phases with their slot parity planned (v5.4).
* **Stationary blades.** Up+down on a Metal Blade throw makes the blade stand
  still. A parked blade can kill a target later, keep a slot busy so the next
  throw goes to the right parity, or act as a reserve hit (Wily 2, Bubble Man,
  the Wily Machine).

**Weapon energy is a budget across stages.**
* **Refills.** All weapons refill to 28 only at stage starts up to Wily 1.
* **Metal Blade cost.** A unit is spent on every 4th throw. The throw counter
  `$AC` resets at each weapon switch, so up to 3 throws per weapon segment are
  free.
* **The Metal Blade budget is exact.**
  * Wily 5 starts with what Wily 2 leaves.
  * The Wily 2 boss now takes 39 throws instead of 42 (two parked blades kill
    blocks and hit again later). That frees the unit the 8-blade Bubble Man
    refight needs.
  * The Wily Machine uses all 59 blades left at its fill.
* **Crash Bomber** costs 4 units per bomb.
  * Boobeam takes 4 bombs, leaving Quick Man 3.
  * A 3-bomb Boobeam is possible (two hurt-glitch kills), but it costs 38
    frames. A 4th bomb at Quick Man would save about 18.
* **Item 2 in Wily 1** uses all 28 units. That is what finally closed lever R1.

**Lag frames and the CPU.**
* **Why a removed lag is worth a frame.** A true lag frame does not advance the
  frame counter `$1C`, so removing one moves everything after it 1 frame
  earlier with the same rolls and rules.
* **Why it can still break things.** The music runs in real time, so the
  removal shifts the music against the game. A DelayScroll check or a
  sound-effect start can then land on a lighter or heavier music frame. The
  Bubble removal (v5.6) needed one extra pause-menu frame. The Heat removal
  (v5.8) needed a landing one game frame later.
* **The lag test.** A frame lags unless the main loop reaches `$C08A` by about
  cycle 113 of the next frame.
* **Measured costs and levers:**
  * Mega Man airborne instead of walking: about −330 cycles in his routine.
  * The door loop restarts the boss music every frame, which makes boss-spawn
    frames heavy.
  * A refused START: +165 to +190 cycles.
  * The sound queue is processed last-in-first-out on the NMI. An extra effect
    that wins the priority test costs +600 to +900; one that loses costs about
    +99.

**The alien fight (v5.3).**
* **The pause.** A pause 1 frame shorter (up+down cursor trick) flips the
  frame-counter parity against the alien's path. The final 22-hit burst can then
  start one step earlier.
* **The position.** Mega Man must end his knockback stun at X ≥ 37 on the
  secret ledge. The landing check tolerates a hit up to Y 66.5 / X 52.44, which
  an earlier study missed.

**R1 (16 frames at the Wily 1 fade) is closed.**
* **The plan.** Wood's DelayDownScrolls now fire at Shinryuu's frames, giving
  a Wily 1 start with lead 88.
* **The full version** needs 8 more counter frames before Wood. None of Metal,
  Quick, the Bubble fight or an earlier Bubble DelayDownScroll can supply them.
* **The lite version** (8 lag frames induced in Wily 1, for −8 overall).
  * The 8 lags exist: an extra Item-2 sled adds a Pipi egg swarm.
  * But the sled costs the last Item-2 unit, which the later step sled needs.
  * A left-facing sled costs no energy, but it leaves Mega Man about 3 px
    behind, against 0.25 px of tolerance.

**Invincibility flicker as a CPU lever (v5.9).**
* While Mega Man is invincible, he is drawn only on frames where bit 1 of `$1C`
  is clear. Hiding him saves a whole sprite group's draw time.
* Wily 4's room-32 lag frames, where three homing enemies re-aim, fell on
  frames where he was drawn.
* One extra pause-menu frame shifts the counter, and both lags disappear.
  That costs 1 frame, and the Boobeam fill's 1 frame of slack absorbs the
  counter change.
* **The same trick fails before Wily 4.** A scan of v6.0 finds eight more
  short lags with Mega Man invincible and drawn: four in Bubble's screen 8,
  three in its second spike zip, and one at the Air Man kill.
  * There the stage-end rules come in 8-frame steps with at most 1 frame of
    slack.
  * Running the counter 2 higher costs 8 frames, more than the lags save.
* **v6.4 pairs it with a down throw.** Throwing the Leaf Shield down during
  the zip before the Boobeam corridor saves 2 frames (a left throw's pose
  stops the zip). One extra weapon-menu frame after room 32 gives one back.
  The Boobeam door then comes 1 frame sooner, which moves the boss music 1
  frame further along in the fight and removes one fight lag. The earlier
  closure had only tried the menu frame before room 32, or none.

**The Wily Machine (v6.0).**
* The phase-2 fill needed only 1 frame for the next +4.
* The earlier "impossible" proof had fixed Mega Man's horizontal path. A
  search that leaves his left/right input free found a phase-1 kill 2 frames
  earlier, with a bound that accounts for the slot parity:
  * a blade thrown straight down holds the odd slot, so the next airborne
    blade takes an even slot;
  * the kill-frame throw is a parked blade that becomes phase 2's decoy.
* Phase 2 is now provably optimal. Around every landing, blades thrown from
  below arrive too late to fill the gap with 3 slots. Under any movement, at
  most 27 hits fit by the frame the next rule needs.

**The Wily Machine again (v6.1-v6.2).**
* **Phase 1 dies 3 frames sooner (v6.1).** Mega Man opens with a 1-frame hop,
  and a blade parked with up+down just left of the machine is walked into 24
  frames later. Phase 2 then fills 4 frames earlier.
* **Load lag follows the music.**
  * The Wily 6 stage load starts 325 frames after the phase-2 kill. The music
    runs in real time, so the kill frame decides which music frames the load
    meets, and the load lags 4 or 5 frames accordingly.
  * With v6.1's kill it lagged 5, which took back 1 of the 4 frames. v6.2's
    kill, 1 frame sooner, brings it back to 4.
  * A frame-counter poke cannot show this, because it does not move the music.
* **Wily 6's platform seeds are set in phase 1 (v6.2).** The reserve blade
  inherits slot 2's stale subpixel from phase 1. v6.2 gives slot 2's blades
  exactly 25 diagonal moves there; with v6.1's phase 1 the run fails in
  Wily 6.

**The Heat Man refight (v6.3).**
* **How the fight is timed.**
  * After a hit Heat Man is hurt for 19 frames and then waits 31 frames.
    The wait comes from a random table; it is 31 in the run, the shortest.
  * He then dashes for (distance ÷ 4) + 10 frames, moving 4 pixels a frame
    toward Mega Man for the last part. He becomes hittable 9 frames later.
  * So the fight lasts 276 frames after the first hit, plus one frame for
    every 4 pixels of dash distance. Each of those frames also leaves him 4
    pixels further left.
* **What bounds it.** The bound is not his AI but where he dies: far enough
  right that Mega Man, walking left, is already in the exit box on the next
  frame. v6.3 shortens the third dash and lengthens the last one, so he dies
  8 pixels further right and 2 frames sooner.
* **Why it was missed.** Every earlier study treated this fight as fixed by
  the boss's AI and never measured it. The closure audit (section 9) checks
  the other closures for the same blind spot.

**New platform-seed knobs (v6.3).** These restore Wily 6's platform starting
values when an earlier change moves the leftover weapon subpixels:
* The spare Item 1 platform takes weapon slot 4 when thrown. Each frame of
  delay before the throw moves that slot's leftover subpixel by 0x41.
* The direction of the Wily Machine's killing blade sets slot 3's value. The
  killing blade keeps flying after the kill. A diagonal blade changes the
  value on every frame it flies; a straight horizontal one leaves it as it
  is.
* A stationary blade can replace a diagonal hit whose timing depends on a
  subpixel.

**Also closed after v5.8:**
* **The Wood refight exit.** The killing tornado must start from X ≥ 75, so
  the exit comes at kill+5 at best. A 2-frame gain would cost 4 at the Bubble
  fill.
* **An earlier second Boobeam bomb.** Mega Man's knockback only advances on
  frames where he is drawn, and the bomb pieces keep him off every odd frame,
  so the knockback ends on a fixed frame.
* **A spare Item-1 platform.** There is no free slot during the Wily 6 climb.
  A second platform in the alien room blocks the pause. In Wily 4, all 464
  extra-throw positions either gain nothing or kill Mega Man.

