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

## 7. Status of the whole-game pass

Committed and verified:
* **v3a: Wily 6, +20 vs v2** (`movies/rockman2-v3a-85254.fm2`, 85,254 frames).
  The ceiling zip starts from the third Item 1 platform's throw pose. The door
  lead is kept a multiple of 4, and the stale Y subpixel of the alien-room
  platform is kept in range.

Verified on both cores up to the start of Wily 5, but not yet complete:
* **Wily 3, +32.**
  * Wily 2 menus: 6 frames give 4 at the Wily 2 fill.
  * Wily 3 pause moved to the stage start, plus capsule re-routing: lead 8.
  * Boss menu: 6 frames.
  * New Guts Tank fight: 18 more frames.
  * That is a lead of 32 at the q16 fade.
* **Wily 4, +2.** One climb frame and two menus give 4 at the Boobeam fill;
  two extra lag frames cost 2. Wily 4 was re-synchronised: 5 input edits
  absorb the changed stale slot fields.
* **Wily 5 (in progress).** Every refight decision needs re-manipulating for
  the new `$1C`.

Searched and not improvable with the current routes:
* Heat and Wood stage ends;
* the Boobeam fight;
* the alien fight (the best near-miss is 0.375 px short of 2 frames);
* Item 1 at the alien (already used);
* Wood's stage-start pause.
