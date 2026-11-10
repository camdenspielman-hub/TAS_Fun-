# Proof standards

Written 2026-11-07. This applies to every claim, in README.md, in docs/ and in working notes, about what a movie of Rockman 2 (J) can or cannot do. The tools and certificates it names are in `tools/proof/`; section 7 says how to re-check everything from a clean clone.

This document is about labels itself, so `tools/proof/label_lint.py` should not be run on it.

## 0. Why this document exists

There are two kinds of statement.

* **Existence claims.** Example: "this input file reaches the ending in 85,004 frames." One replay proves it.
* **Universal claims.** Examples: "no input can close this menu sooner", "this fight is optimal", "dead end". A universal claim speaks about all 256^L input sequences of length L. No number of replays proves it.

Most of the project's "dead ends" are universal claims. They rest on searches that were not exhaustive, on paper estimates, or on code reading that nobody checked for missed cases.

This document covers three things:
* what it takes to turn such a claim into a proof;
* how to record the proof so that anyone can re-check it;
* how to label claims that are not, or not yet, proofs.

The model is a proof assistant such as Lean.

* **Axioms** (section 1) are a short list of things accepted without proof: the ROM, the emulator, the power-on state and the timing rule.
* **Lemmas** (section 2) are statements derived from the axioms by steps that a program, or a careful reader, can re-check.
* **Certificates** (section 4) are the data a small, independent checker needs to confirm a lemma. The checker does not have to trust the program that found the lemma.
* **Open assumptions** (section 6) are facts a lemma uses that are neither axioms nor proven. Each one has a name, and every claim that uses it says so.

Two rules come before everything else.

1. **Soundness.** An argument may over-approximate, that is, allow behaviour the game can never show. Its conclusion is then weaker, but still true. An argument that misses even one behaviour the game *can* show proves nothing, however much evidence surrounds it. A glitch nobody has found is exactly such a missed behaviour. So only an argument that covers every behaviour can rule out unknown glitches.
2. **No silent assumptions.** If a step uses something that is neither an axiom nor proven, that thing gets a name in the register, and the claim carries a weaker label.

Terms used below:

* **frame**: one step of the emulator, and one line of input in the movie. Frames are counted from 0 at power-on.
* **pad**: the 8-bit controller value for one frame. Bit 0 is A, 1 is B, 2 Select, 3 Start, 4 Up, 5 Down, 6 Left, 7 Right.
* **state**: the complete emulator state between two frames.
* **`$1C`**: the game's frame counter.
  * A **counted frame** is one on which `$1C` advances.
  * An **uncounted frame** (a true lag frame) is one on which it does not.
* **REAL / ANALYSIS**: the project's evidence tags.
  * REAL means a plain replay from power-on, or from a savestate made by such a replay, with no RAM writes.
  * ANALYSIS means anything with pokes, hooks, patched code or models.

## 1. The trusted base (axioms)

The four items in this section are axioms: they are accepted without proof. Everything else is either derived from them or listed as an open assumption.

### 1.1 AX-ROM: the game

The ROM file is `Rockman 2 - Dr. Wily no Nazo (Japan).nes`. It is never committed to the repository.

| property | value |
|---|---|
| size | 262,160 bytes: a 16-byte iNES header and 256 KB of PRG ROM. There is no CHR ROM (the cartridge has 8 KB of CHR RAM). Mapper 1 (MMC1). |
| md5 of the file | `055fb8dc626fb1fbadc0a193010a3e3f` |
| sha1 of the file | `fb51875d1ff4b0deee97e967e6434ff514f3c2f2` |
| sha256 of the file | `deb88223311aca8ca566b99d4063ca29d389d939fee455f83afaec97c6f0a5d1` |
| md5 without the header | `770d55a19ae91dcaa9560d6aa7321737`. This is the `romChecksum` in every .fm2 file (`base64:dw1VoZrpHcqpVg1qpzIXNw==`). |

A certificate names the ROM by md5 or sha256, and a checker refuses to run on any other file.

### 1.2 AX-FCEUX: the machine

Formally, the game is a deterministic function T(s, p) = s′: the state after one frame, starting from state s with pad p.

We do not write T down. It is defined as whatever FCEUX's C++ code computes with these settings:
* NTSC;
* old PPU (`NewPPU 0`);
* port 0: standard gamepad;
* port 1: nothing;
* no Four Score, no cheats, no Game Genie.

Two builds of this code are used.

| role | core | source | library |
|---|---|---|---|
| judge | FCEUX 2.3.0. The movie header names it (`emuVersion 20300`), and publication #4410 was made on it. | TASEmulators/fceux, tag `fceux-2.3.0` (commit `65c5b0d2`) | `librm2.so` from `make -C tools/proof FCEUX_SRC=<2.3.0>/src OUT=<build>/v230 core` |
| working core | FCEUX master | TASEmulators/fceux, commit `fa248734` | `librm2.so` from `make -C tools/proof FCEUX_SRC=<master>/src OUT=<build>/master` |

A core is identified by its FCEUX source revision, not by the md5 of a library: two builds of the same source on different machines or paths need not be byte-identical. Every checker prints the md5 of the library it ran on, and the certificate envelopes record it for each re-check (for example, the project's first master build has md5 `a4165ff633a105971c343d84912f1406` and its 2.3.0 build `e53b31c958ce0038ee6d9dd3fe04c07e`; the re-checks made from the repository layout on 2026-11-07 used fresh builds of the same two revisions).

**The judge core defines the truth** for this project, because a judge would replay the movie on the emulator it declares. Our analysis tools exist only for the working core. A lemma proven on the working core therefore holds for the judge core only under assumption A-CORE-EQ, unless its checker has also been run on the judge core.

The evidence for A-CORE-EQ:
* Both cores give identical per-frame CRC and lag flags on v6.5's 85,004 frames plus 3,000 blank frames.
* Certificates re-checked on the judge core, starting from power-on (section 4.6).

Both libraries are built by `tools/harness/Makefile` (driven by `tools/proof/Makefile`) from the unmodified FCEUX source. For FCEUX 2.3.0 the Makefile adds the defines that README.md gives for that version (`-DRM2_NO_MEMHOOK -DPSS_STYLE=1 -DLSB_FIRST`).
* The harness calls FCEUX's own `FCEUI_Emulate` once per frame.
* `tools/verify.py` plays .fm2 files through FCEUX's own movie loader (`FCEUI_LoadMovie`).
* That this wrapping changes nothing about emulation is assumption A-HARNESS.

The **analysis builds** (`librm2pf.so` and `librm2rec.so`, from `make -C tools/proof`) are the working core's object files linked with the harness driver plus hooks that only observe: the taint tracker and read and write watches (`tools/proof/native/pf_taint.inc`), and coverage and value recorders (`tools/proof/native/pf_rec.inc`).
* They may be used to find things and to check certificates.
* A movie input never comes from them.
* Any certificate that relies on a hook's verdict names that dependency.

### 1.3 AX-POWERON: the start

A run starts from FCEUX's power-on state in a fresh process:
* RAM holds the repeated pattern `00 00 00 00 FF FF FF FF`. The movie's sync depends on it.
* A = X = Y = 0 and S = $FD.
* There is no savestate, no SRAM and no console reset: the .fm2 commands column is 0 on every frame.

**Pitfall.** FCEUX's power-on does not reset the PPU's fine-X register (XOffset). A second power-on, in a process that has already emulated, starts with XOffset = 7 and differs from a fresh power-on for 17 frames. So every verification and every certificate root starts in a fresh process, or from a state made in one.

### 1.4 AX-TIME: what is minimised

TASVideos times a movie to its last input. As this project applies that rule (counting from power-on, lag frames included):
* The **length** L of a movie is the index of its last frame with a non-zero pad, plus 1. For v6.5 the last input is at frame 85,003, so L = 85,004 (23:34.404 at the NTSC rate).
* The movie is complete only if, after frame L−1, the game reaches its ending with no further input.

**Formal version.**
* Let s₀ be the power-on state, and s_L the state after pads p₀ … p_{L−1}.
* Let E(s) mean: "from s, with every later pad 0, the game reaches the ending".
* The quantity to minimise is L* = min { L : some p₀ … p_{L−1} gives E(s_L) }.

The bounds:
* **Upper bound: L\* ≤ 85,004.** This is PROVEN. v6.5 replays on both cores, the alien's HP reaches 0 one frame after the last input, and the ending plays on blank input.
* **Lower bound:** everything else in this document is about it.

The end of a run is its last input, not the alien's death. A lower bound D on the frame of the alien's death becomes a lower bound on L only through lemma L-END. L-END bounds how many frames can separate the last input from the kill under blank input, for example with shots already in flight. v1 saved a frame in exactly this way. L-END is open (section 6).

The exact wording of the TASVideos rule should be quoted from TASVideos at submission time. This section only records how the project applies it.

### 1.5 Where FCEUX differs from a real console

All proofs here are about FCEUX, because FCEUX is the judge. How a console behaves neither strengthens nor weakens them. Still, readers should know which results are specific to the emulator, because some of them sit within a few CPU cycles of failing.

| difference | FCEUX as used here | real console | what depends on it |
|---|---|---|---|
| power-on RAM | a fixed pattern, `00 00 00 00 FF FF FF FF` (measured) | not defined; varies between units | the sync of the whole movie |
| CPU/PPU clock alignment at power-on | one fixed alignment | one of several, at random | every cycle-exact effect in this table |
| PPU timing model | Old PPU: scanline-based, not exact to the dot. Measured here: normal NMIs start at CPU timestamp 127 or 130 into the frame, and frames alternate between 89,342 and 89,341 PPU dots by frame-index parity. | Exact to the dot. The short frame happens only on odd frames while rendering is on. | DelayScroll checks (the NMI must land 17-50 cycles before the bank switch at `$C7A5`); lag frames (the main loop must reach `$C08A` by about cycle 113 of the next frame); the RNG's carry |
| PPU warm-up after power-on; the race between a `$2002` read and the NMI; the OAM DMA length (513 or 514 cycles) | not checked against the FCEUX source here | documented hardware behaviour | power-on timing and per-frame cycle budgets |
| MMC1 writes on consecutive cycles | ignored, using a timestamp test (`mmc1.cpp`, `lreset + 2`) | ignored by the chip | the bank-switch sequences, which the static analysis models as FCEUX does |
| sound | The harness runs with sound output off. The APU's CPU-visible state still advances (assumption A-HARNESS). | the real APU | nothing the CPU can see, if A-HARNESS holds |

The certified search's state-identity test T4 shows how fine the margins are. In otherwise identical states, moving the CPU's cycle overshoot by 1-3 cycles changed the RAM 6-272 frames later in 23 of 297 tries. So no claim in this project says anything about a console, and "this movie syncs on a console" is UNSUPPORTED.

### 1.6 What is not trusted

Everything else is code or text that can be wrong, and it is treated that way:
* our Python tools and the analysis builds;
* the transcriptions of FCEUX's semantics (`tools/proof/static/m6502.py`, `tools/proof/static/vs.py`);
* search engines and checkers;
* working notes, and this document.

Each of these is either checked (by tests or an independent re-implementation) or listed in the assumption register.

## 2. Kinds of lemmas and how each is proven

### 2.0 Shapes of claims

Write R for the set of states reachable from s₀ by some pad sequence. Claims have one of two shapes.

* **(∃)** "Some pad sequence from s reaches G within d frames." A replay that does it proves it.
* **(∀)** "No pad sequence from s reaches G within d frames", or "every state in R satisfies P". These are the impossibility claims, and the rest of section 2 is about them.

### 2.1 Replay facts

A REAL replay proves an (∃) claim for the core it ran on. It proves nothing about other inputs. "We tried this input and it failed" shows that this input fails, not that the idea fails.

A REAL observation over a whole run is evidence for a (∀) claim, never a proof of one. An example is "only these instructions wrote `$37` in v6.3".

### 2.2 Code lemmas over all inputs

A code lemma has the form "for every reachable state and every pad, P holds", where P is about the code. Examples of P:
* which instructions can write a byte;
* which values a byte can hold;
* when a loop exits;
* how far Mega Man can move in one frame;
* that a code region never reads the controller.

Such a lemma holds whether or not anyone knows a glitch, because it is about everything the code can do.

**How it is proven.** A sound static analysis (an abstract interpretation) of the ROM under FCEUX's semantics computes, for every reachable instruction, a description that includes every concrete state that can occur there. The soundness argument has three parts:
1. Every transfer function over-approximates FCEUX's semantics of its instruction.
   * In the static toolkit, `tools/proof/static/m6502.py` is transcribed from FCEUX's `x6502.cpp` and `ops.inc`.
   * The ALU in `vs.py` agrees with it exhaustively on single values and on 3,000 random set cases (`tools/proof/static/selftest_vs.py`).
2. Joins and widening only add behaviours.
3. The result is a fixpoint: applying every transfer function once more adds nothing.

Under these conditions every concrete execution is represented, for every pad and for every value read from the PPU, the APU or the open bus.

**Hazards.** A code lemma is only as good as its handling of the following. Each must be handled soundly, or named as an assumption.
* **Indexed and indirect stores** (`STA $00,X`, `STA ($08),Y`) can write any byte their address can reach. A scan for direct stores such as `STA $1C` misses them.
* **Instruction decoding** must start from every reachable entry point. This includes jumps into the middle of an instruction, jump tables (`JMP ($0008)`), and the RTS trick (push an address, then return to it).
* **The mapped bank**: the same CPU address means different code in different banks.
* **Code run from RAM**: none ran in two full replays, but that is evidence, not proof.
* **The NMI handler** can run between any two instructions wherever PPUCTRL bit 7 allows it, and its writes must be accounted for.
* **Page-1 data writes** could hit live stack bytes.
* **Bus details**: read-modify-write instructions make two writes; dummy reads can touch I/O registers; reads can return open-bus values.
* **All 256 opcodes**, including the undocumented ones, BRK, and the KIL opcodes that jam the CPU.

**Local code lemmas** analyse one routine instead of the whole program. They hold "given entry at the routine's first instruction". They need a separate lemma, from the whole-program analysis, that nothing jumps into the middle of the routine. Example: L-HIT (section 4.5).

**What does not count as a code lemma.** These are evidence for a lemma, not proofs of it:
* a census of writers observed in replays;
* a scan of direct stores;
* a list of writers someone found by reading code.

For example, the board's "`$1C`'s only writer is F:D088 (exhaustive store scan)" stays in this class until indexed and indirect stores are bounded. Until then, the claim is at best PROVEN-GIVEN-ASSUMPTIONS, with the open assumption that no indexed or indirect store reaches `$1C`.

**Status today (static toolkit).** The whole-program abstract interpreter exists and is sound by construction, but its fixpoint does not converge, so it is not part of `tools/proof/`; only the pieces the local lemmas use are (`m6502.py`, `vs.py`, `lemmas.py`, `local_lemmas.py`). Its flow-insensitive RAM model makes 1,921 of 2,048 RAM bytes "any value", so no whole-program lemma is proven yet.

**Proposed certificate.** The fixpoint itself (one invariant per instruction), plus a small checker that applies every transfer function once more and confirms that nothing grows. Checking a fixpoint is much simpler than finding one: it needs no worklist and no widening, only the transfer functions.

### 2.3 Exhaustive search from a state

This kind of lemma has the form "from state s, no pad sequence of length ≤ d reaches goal G". The menu results are proven this way (`tools/proof/pfsearch.py`, run by `tools/proof/pfrun.py`).

**The theorem**, in plain words. Run a breadth-first search from s and keep one representative per state class, under three conditions:
* **State identity.** Two states count as equal only if their whole FCEUX savestates are equal, except for 8 fields that emulation never reads after a load.
  * That these fields are never read is a code argument about FCEUX's source.
  * Test: saving and reloading before every frame of an 85,206-frame replay changes nothing.
  * RAM alone is not a valid identity (test T4, section 1.5).
* **Input classes.** Inputs are grouped into one class only when the taint tracker proves the other pad bits dead for that transition.
* **Pruning.** A branch is cut only by a proven pruning lemma, that is, a proof that the state cannot reach G within the remaining frames.

If no listed state satisfies G, then no pad sequence of length ≤ d reaches G.

The certificate lists every layer of the search. So a checker can confirm **closure**: every child of every listed state, under every pad, is either listed in the next layer or pruned by the lemma.

**What it costs.**
* Menu searches grow about 3-4 times per frame.
* Gameplay searches grow about 12 times per frame (with 32 input classes). So 4 frames from a gameplay state is the practical limit on this machine.
* Longer claims need pruning lemmas, which are code lemmas (2.2) or relaxations (2.4).

**What it proves**: a statement about one exact state s. Section 2.6 explains why that is weaker than "this segment is optimal".

Checking closure over all 256 pads removes the dependence on the taint tracker. The state identity (A-STATE) remains an assumption in every search certificate.

### 2.4 Sound relaxations

A relaxation replaces the game by a simpler model M that can do at least everything the game can. The steps:
1. Define M (its states, moves and goal) and a map α from game states to states of M.
2. **Prove the simulation lemma**, which has two parts:
   * For every reachable s and every pad p, M can reach α(T(s, p)) from α(s) in one step, or can reach a state at least as far along.
   * Every goal state of the game maps into M's goal.
3. Compute in M, exhaustively, that M cannot reach its goal in fewer than d steps.
4. Conclude that the game cannot either.

Step 2 is a code lemma (2.2). Without it, the result is only PROVEN-IN-MODEL.

Examples:
* **The route study's Air Man cloud model** ("Air screens 0-7 without Item 1 cost at least 166 frames") is PROVEN-IN-MODEL. The model is exhaustive over cloud spawn phases, and its pieces match REAL replays to 0.000 px. But its simulation lemma (no other platform, no faster movement) is only a paper argument.
* **The old hub-walk search** assumed a speed limit of 1.5 px/frame, so it is an ESTIMATE. The limit was assumed, not proven, and zips move Mega Man 16 px in one frame.
* **A future speed lemma** would allow a much stronger model: "Mega Man's X changes by at most k px per frame, from every source": walking, conveyors, knockback, platforms, zips and transitions. Proving k needs the writer set of his position bytes, that is, a converged whole-program analysis.

The most common error is a model that leaves out a way to be faster: a zip, a carry, a damage boost, a death warp, or an unknown glitch. The simulation lemma exists to catch exactly that.

### 2.5 Frame-rule arithmetic

Many waits end only when the frame counter reaches a given phase (docs/whole-game-analysis.md, section 1):
* `$1C & 3 == 0` for boss health fills;
* `$1C & 7 == 0` for weapon-get screens and refills;
* `$1C & 15 == 0` for the Wily 1 and Wily 3 death fades.

Two code lemmas are needed. Both are open today.
* **L-CLK (the clock).** `$1C` changes only by +1 in the NMI (at F:D088) and by the reset's RAM clear, and it advances exactly once on every counted frame.
  * REAL evidence: over v6.2, 84,709 increments match 84,709 completed wait calls, and there is at most one NMI per frame.
  * It is not proven for all inputs until the writer set of `$1C` is proven.
* **L-GATE(k)**, one per rule k. The event becomes possible when its routine first runs, at counter value R, and it happens at the first counter value E ≥ R with E ≡ φ (mod q).

Given these lemmas, the rest is arithmetic. `tools/proof/frule.py` checks it against a brute-force version of the definition on a large finite range, and it also has a two-line paper proof.

Let q be a rule's period, w the reference run's wait at that rule, and c a lead in counted frames. Then:
* a lead of c becomes q·⌊(w + c)/q⌋ after the rule;
* the rule therefore absorbs completely every lead with c ≤ q − w − 1;
* a delay of d costs q·⌈max(0, d − w)/q⌉.

Uncounted frames are not affected by rules: removing one moves everything after it one frame earlier.

**Consequence for proofs.** Let the reference movie's rules be k = 1 … n. Let g_k be the largest counted-frame gain any run can make in the interval just before rule k.
* If g_k ≤ q_k − w_k − 1 for every k, then no lead ever passes a rule.
* In that case the counter value at every rule, including the last one, equals the movie's.

So "the movie is optimal up to rule k" does not need exact bounds for each segment. It only needs a proof that no interval can gain a full period. This is the main reason a partial optimality proof is within reach (section 5).

### 2.6 Composition into segment lower bounds

A **segment** is the part of the run between two cuts. A **cut** is a predicate C on states, for example "the pause menu has just opened", "the health fill starts" or "Mega Man is on the capsule".

Four things are needed to turn segment facts into a bound on L*:
1. **Necessity.** Every run that reaches the ending passes the cuts C₁, …, C_n in this order. This is a code lemma (for example about the stage flags and their writers). If only the current route is covered, the claim carries assumption A-ROUTE.
2. **Hand-over sets.** For each cut, a set H_i containing every reachable state that satisfies C_i.
   * Taking H_i = "every state that satisfies C_i" is sound, but usually far too weak: it includes nonsense such as Mega Man already standing at the exit.
   * Narrowing H_i needs invariants, which are code lemmas.
3. **Segment bounds.** For every s in H_i, the time from s to C_{i+1} is at least b_i, counted separately in counted and uncounted frames.
4. **Composition.** Apply the frame-rule arithmetic of 2.5 to the counted frames, then add the uncounted frames that are provably forced. Bounding the two parts separately is sound (the minimum of a sum is at least the sum of the minima), but it can be loose.

**What "this segment is optimal" can mean.** Three different statements are often confused.
* **O1 (local).** From the movie's own hand-over state s, no input reaches the next cut sooner.
  * A search certificate proves this.
  * Example: all 9 Wily 5/6 pause menus of v6.3.
* **O2 (uniform).** The same holds for every state in H_i. Proving it needs one of two things:
  * an enumeration of H_i; or
  * a lemma that the segment's length depends only on a few bytes, followed by an enumeration of those bytes. For a menu, those bytes are the cursor and the owned weapons, and the lemma can be proven with the taint tracker or a code lemma.
* **O3 (contribution).** The O2 bound, combined with necessity and composition, gives a bound on L*.

Only O3 says anything about the whole run. **O1 is neither sufficient nor necessary for the movie to be optimal.**
* *Not sufficient:* a slower segment can hand over a better state. This run routinely gives up frames to set the RNG, the `$1C` phase, a stale subpixel or the music phase. Examples: the 9 deliberate frames in Bubble Man's stage, and the Wily 1 pause-3 delay.
* *Not necessary:* the Quick C->A pause in Wily 5 can close 1 frame sooner. Certificate `cert_menuP79781` shows the earliest close is 79806, not 79807, and nothing earlier. The movie does not take that frame, because it flips the `$1C` parity that a later fight needs. The movie is not locally optimal there, and that is correct.

**Cut and goal adequacy.** A certificate proves exactly its goal predicate and nothing more.
* The menu certificates use "`$A9` = target weapon and `$FD` = 0".
* Reading one as "the menu cannot end sooner" needs a further lemma, GA. GA says that the predicate marks the closing frame, and that what follows has a fixed length.

Every certificate either states its goal-adequacy lemma or lists it as an open assumption.

### 2.7 The kinds of lemma at a glance

| kind | what it proves | what must be trusted besides the axioms | label when complete |
|---|---|---|---|
| replay | (∃), for one input | the harness | PROVEN |
| code lemma, whole program | (∀), over all inputs | the transcription of FCEUX's semantics; the fixpoint checker | PROVEN-GIVEN-ASSUMPTIONS (A-TRANSCRIBE), until the transcription is checked exhaustively against the core |
| code lemma, local | (∀), given entry at its first instruction | the above, plus an entry lemma | PROVEN-GIVEN-ASSUMPTIONS |
| exhaustive search | (∀), from one state, up to a depth | the state identity; the taint tracker (unless closure is checked over all 256 pads); any pruning lemmas; the checker | PROVEN-GIVEN-ASSUMPTIONS |
| relaxation | (∀), through a model | the simulation lemma | PROVEN-IN-MODEL while the simulation lemma is unproven |
| arithmetic | pure mathematics | nothing | PROVEN |

## 3. Claim labels

Every statement that something is impossible, optimal, minimal, closed, at its limit or a dead end carries exactly one label. From strongest to weakest:

1. **PROVEN.** It follows from the axioms of section 1 alone, either by a certificate that a checker accepted or by an argument in which every step can be checked. It uses no open assumption.
2. **PROVEN-GIVEN-ASSUMPTIONS.** As PROVEN, except that it uses open assumptions from the register. It lists them by name.
3. **PROVEN-IN-MODEL.** It is exhaustive or complete inside a named model M, but the lemma "M can do everything the game can" is not proven. It names the model and says what the model leaves out.
4. **SEARCH-LIMITED.** A search that was not exhaustive found nothing. The label says why the search was not exhaustive, for example: a beam width, sampling, a reduced input set not proven complete, an unsound merging of states, or a depth cap.
5. **ESTIMATE.** Arithmetic or reasoning on measured or assumed numbers, without an exhaustive argument.
6. **UNSUPPORTED.** No evidence that survives review.

**OVERTAKEN** is not on this scale. It marks a claim that was later shown false or superseded. The text stays, with a pointer to what replaced it.

Rules:
* **Weakest link.** A claim gets the label of its weakest load-bearing part. A PROVEN-IN-MODEL step inside an otherwise PROVEN argument makes the whole claim PROVEN-IN-MODEL.
* **Scope.** A label applies to one precise statement. Write down the quantifier and the starting point, for example "from the v6.3 state before frame 79782", "for every reachable state", or "within the current route".
* **Assumptions are named.** Example: `[PROVEN-GIVEN-ASSUMPTIONS: A-STATE, A-TAINT, A-MENU-CLOSURE; cert tools/proof/certs/cert_menuP79781.json.gz]`.
* **Evidence tags are not labels.** REAL and ANALYSIS say how a test was run. A REAL test can support a claim of any label, but on its own it proves only (∃) claims.
* **Changing a label.**
  * An upgrade needs the certificate or the argument, plus one independent re-check.
  * A downgrade needs only a stated reason.
  * A claim refuted by a REAL replay becomes OVERTAKEN at once.
* **Labels already in use.** The project's audit notes use these same classes, but they define PROVEN as "complete code/physics argument". Under this standard most of those become PROVEN-GIVEN-ASSUMPTIONS, because their code arguments bound neither indexed or indirect writes nor entry points. They should be re-read once, not carried over unchanged.
* **What PROVEN means today.** By this standard, the project's only PROVEN statements are existence claims (replays) and pure arithmetic. Every impossibility result is at best PROVEN-GIVEN-ASSUMPTIONS. That is not a flaw in the results; it is an honest list of the work that remains.

**The docs rule.** In README.md and docs/, every unit of text that claims impossibility, optimality, minimality, closure or a dead end carries a label in the same unit. A unit is one bullet, one table row or one paragraph.

`tools/proof/label_lint.py` enforces the mechanical part of this rule:
* It finds such units by keyword, and fails if one has no label.
* A unit whose keyword is not a claim is waived with the HTML comment `<!-- no-claim -->`, which shows up in review. Examples: "a closed room", or history such as "the 2006 exhaustive search found".
* It cannot judge whether a label is right, and it misses claims worded without its keywords. Reviewers still read the text.

When the lint was written on 2026-11-07 it found 20 unlabelled units in `docs/whole-game-analysis.md` and `README.md`. Each has since been labelled or reworded, and the lint passes on both files (`python3 tools/proof/label_lint.py docs/whole-game-analysis.md README.md --list`).

`docs/closures.md` is not held to the lint. Its ledger tables carry the label in a column of their own, in short form (PIM, SL, EST, UNS, OVT), which the lint does not read.

## 4. Certificates and re-checking

### 4.1 Principles

* **The finder and the checker are different programs.**
  * The finder may be large, clever and fast.
  * The checker should be small and simple, and share no logic with the finder.
  * `tools/proof/pfcheck.py` and `pfcheck_stream.py` share no code with `pfsearch.py` or `pflib.py`. They do share the emulator library and `tools/harness/rm2.py`, which fall under the trusted base and A-HARNESS.
* **A checker fails closed.** Any situation it does not expect is a failure, never a skip.
* **A checker has no side effects.** It writes nothing except its own output.
  * Counter-example found on 2026-11-07: importing the first version of `local_lemmas.py` ran its `main()` and rewrote its result file. The content came out identical, but a checker must never be able to change what it checks.
  * Fixed in `tools/proof/`: every module has a `__main__` guard and no import-time side effects, and `local_lemmas.py` writes a file only when given `--out`.
* **The final check of any certificate:**
  * runs in a fresh process;
  * rebuilds its root by a continuous replay from power-on, not from a pickled savestate;
  * runs on the judge core as well as the working core.
* **A certificate states its claim.** It is useless without the exact claim it supports, written both in words and as data.

### 4.2 The common envelope

Every certificate comes with an **envelope** with the fields below. For the search certificates in `tools/proof/certs/` the certificate itself (`<id>.json.gz`) is kept byte-identical to what the search wrote (gzip-compressed; `SHA256SUMS` lists the sha256 of each `.json.gz` and of each decompressed `.json`), and the envelope is a separate file, `<id>.envelope.json`, which records the decompressed certificate's sha256. The fields marked * exist only in the envelope; the others are in the envelope, the certificate, or both.

| field | content |
|---|---|
| `standard`* | `"rm2-proof-1"` |
| `id`, `label` | a short id, and the claimed label |
| `claim` | the statement in words, with its quantifier and scope; and the machine form (goal predicate, depth, root) |
| `assumptions`* | the register ids the claim uses |
| `base` | ROM md5 and sha256; the core's name, commit and library md5 |
| `root` | how to rebuild the starting state (movie, frame, power-on replay), plus its full-state sha256 and its key hash |
| `kind`, `payload` | `kind` is one of `replay`, `search`, `code-local`, `code-fixpoint`, `model` or `arith`; `payload` holds the kind-specific data |
| `producer` | the tool, its version and its md5 |
| `checker`* | the tool, its md5, the exact command, and the expected verdict line |
| `checked`* | one entry (date, who, core, library md5, options, how the root was rebuilt, verdict, seconds) for every re-check |

What the payload holds for each kind:
* **search**:
  * the identity specification (dropped fields, masked bits);
  * the input classes and the dead-bit mask;
  * the goal predicate;
  * the pruning rule and its lemma id;
  * the layers, as (hash, parent, pad) entries, sorted, with a digest per layer;
  * the witness and the result.
* **code-local**: the routine's address range and bank; its entry assumption; the enumerated cases (for example all 256 values of the byte read) and the outcome of each.
* **code-fixpoint** (proposed): the invariant for each (instruction, bank, context); the property; and the list of OPEN items, which must be empty for a PROVEN-GIVEN-ASSUMPTIONS label.
* **model**: the model's code and parameters; a reference to the simulation lemma, or "open"; and the exhaustive computation in the model.
* **arith**: the formula, the paper proof, and an executable exhaustive check over the stated range.

### 4.3 What the search checker verifies

* **E0**: the envelope matches. The decompressed certificate has the envelope's sha256, the ROM has the envelope's md5 and sha256, and the envelope's machine-readable claim (root frame, key hash, goal, depths, input classes, pruning rule) equals the certificate's. Without an envelope the checker says so and checks the certificate on its own.
* **ROM and movie**: the ROM's md5 equals the certificate's; the movie's sha256 equals the envelope's, its `romChecksum` matches the ROM, and its commands column is 0 before the root.
* **C0**: the input classes cover all 256 pads.
* **C1**: the root is rebuilt by one continuous replay of the movie from power-on in the checker's own fresh process, and its key hash matches.
* **C2**: every listed state is rebuilt with the listed hash, and none satisfies the goal. It is rebuilt either by a continuous replay from the root, or layer by layer for large certificates.
* **C3**: closure. Every child of every listed state, under every pad (or every class), is in the next layer or is pruned. The checker recomputes the pruning bound with its own implementation.
* **C3b**: when classes are used, closure over all 256 pads is also checked on sampled entries.
* **C4**: the witness reaches the goal at the stated depth, and not before.
* **C5**: every taint verdict is re-run.
* **C6**: the masked bits are randomised, and the children must not change.
* **C7**: a census of the writers of the bytes that the pruning lemma reads.

### 4.4 Re-check commands

Run these from the repository root, one emulator process at a time. `$ROM` is the path of the ROM file and `$BUILD` the
directory given as `OUT` to `tools/proof/Makefile` (section 7 shows the whole sequence). Each checker exits with 0 only
when its last line is `VERDICT <certificate>: VALID`.

```
# search certificates: working core, then judge core (closure over all 256 pads; root by power-on replay)
python3 tools/proof/pfcheck.py tools/proof/certs/cert_menu77716.json.gz --rom "$ROM" --lib "$BUILD/master/librm2.so"
python3 tools/proof/pfcheck.py tools/proof/certs/cert_menu77716.json.gz --rom "$ROM" --lib "$BUILD/v230/librm2.so"
# taint verdicts (C5) and the canonicalisation test (C6) need the analysis library
python3 tools/proof/pfcheck.py tools/proof/certs/cert_menu77716.json.gz --rom "$ROM" --lib "$BUILD/master/librm2pf.so" \
    --classes --taint --variants 4
# a pruned certificate: classes, plus all 256 pads on 2 sampled entries per layer
python3 tools/proof/pfcheck.py tools/proof/certs/cert_menuP78839.json.gz --rom "$ROM" --lib "$BUILD/v230/librm2.so" \
    --classes --sample 2
# large certificates: the streaming checker (layer by layer, bounded memory)
python3 tools/proof/pfcheck_stream.py tools/proof/certs/cert_menuP79781.json.gz --rom "$ROM" \
    --lib "$BUILD/master/librm2pf.so" --taint --writers --sample 2
# local code lemmas (ROM only, no emulator; writes nothing unless --out is given)
python3 tools/proof/static/local_lemmas.py "$ROM" --check tools/proof/data/local_lemmas.expected.json
python3 tools/proof/static/selftest_vs.py
# frame-rule arithmetic
python3 tools/proof/frule.py
# labels in the docs
python3 tools/proof/label_lint.py docs/whole-game-analysis.md README.md --list
```

Every certificate's envelope holds its own command (`checker.command`, and `checker.judge_core_command`) and the
expected verdict line. The checkers find the envelope next to the certificate and the movie from the envelope
(`movies/rockman2-v6.3-85006.fm2` for all pilot certificates); `--envelope` and `--movie` override them.

To re-run a search (it writes a new certificate and log to `--out`; `$OUTDIR` should be outside the repository):

```
python3 tools/proof/pfrun.py menu 77716 --rom "$ROM" --lib "$BUILD/master/librm2pf.so" \
    --movie movies/rockman2-v6.3-85006.fm2 --out "$OUTDIR"
python3 tools/proof/pfrun.py menuP 79781 --rom "$ROM" --lib "$BUILD/master/librm2pf.so" \
    --movie movies/rockman2-v6.3-85006.fm2 --out "$OUTDIR"        # about 11 minutes
python3 tools/proof/pfrun.py walk 77811 4 34 1 --rom "$ROM" --lib "$BUILD/master/librm2pf.so" \
    --movie movies/rockman2-v6.3-85006.fm2 --out "$OUTDIR"        # about 4 minutes
```

### 4.5 Worked examples

**Example 1: a menu with no saving.** `cert_menu77716`, the Heat → Air pause in Wily 5.
* *Claim:* from the v6.3 state before frame 77717 (just after the opening START), no pad sequence of 15 frames or fewer reaches "`$A9` = 3 and `$FD` = 0", and some sequence of 16 frames does. So the menu closes at frame 77732 at the earliest, as in v6.3.
* *Kind:* search. 16 layers and 391 listed states. Closure was checked over all 256 pads (92,160 transitions), so the claim does not depend on the taint tracker. No pruning.
* *Assumptions:* A-STATE. Reading it as "the menu cannot end sooner" also needs GA-MENU.
* *Label:* PROVEN-GIVEN-ASSUMPTIONS (A-STATE).
* *Re-checked 2026-11-07:*
  * working core: VALID in 77 s;
  * judge core, with the root rebuilt by a power-on replay in a fresh process: VALID in 96 s, with the same key hash as on the working core;
  * from the repository layout (clean clone plus `tools/proof/`, fresh builds of both cores, root by power-on replay): VALID on both cores (see the envelope's `checked` list).

**Example 2: a menu with exactly one frame to save.** `cert_menuP79781`, the weapon C → A pause in the Wily 5 Quick Man fight.
* *Claim:* from the v6.3 state before frame 79782, the menu closes at frame 79806 at the earliest (v6.3 closes at 79807). Exactly one frame can be saved here, and no more.
* *Kind:* search, with two reductions:
  * 8 input classes. A, B, Select, L and R are proven dead for each transition by the taint tracker.
  * Pruning by lemma L-menu: "at most one cursor step per frame, and the menu closes only by START on the target row".
* *Size:* 25 layers, 68,564 states, 428,656 class transitions; 27,786 children pruned, each re-justified by the checker.
* *Assumptions:*
  * A-STATE;
  * A-TAINT;
  * A-MENU-CLOSURE: no other code writes `$1D`, `$FD`, `$FE` or `$A9`, and at most one NMI runs per frame. A census over all 428,656 transitions supports it.
  * GA-MENU.
* *Label:* PROVEN-GIVEN-ASSUMPTIONS (A-STATE, A-TAINT, A-MENU-CLOSURE).
* *Meaning:* this is an O1 fact. The frame is not a saving for the movie, because it flips the `$1C` parity that a later fight needs.
* *Re-checked 2026-11-07* on the judge core, with the root rebuilt by a power-on replay and the stream checker: VALID in 453 s. Its transition count matches the working-core run once the two runs' different 256-pad samples are accounted for.

**Example 3: the 4-frame limit.** `cert_walk77811`, the hub walk from Heat Man's capsule to Air Man's.
* *Claim:* from the v6.3 state before frame 77808, no pad sequence touches the capsule (`$0400` = `$26` or `$2C` = `$0B`) before the end of frame 77811, which is when v6.3 touches it.
* *Size:* 32 input classes (Select, Up and Down are dead). The layers hold 32, 416, 4,832 and 37,664 states. A fifth frame would need about 450,000 states.
* *Label:* PROVEN-GIVEN-ASSUMPTIONS (A-STATE, A-TAINT).
* It says nothing about the 30 frames of walking before frame 77808.

**Example 4: a local code lemma.** L-HIT, the boss hit check at bank 11 `$A59D`.
* *Claim:* for every machine state, an execution entered at `$A59D` does the following.
  * It checks weapon slots 8, 6, 4, 2 if `$1C` is even, or 9, 7, 5, 3 if it is odd, in that order, until the first slot whose box test passes.
  * Inside the routine, only `$A5E8` writes `$B4` (with 0), and only when no checked slot passes.
* *Method:* path exploration of the real instructions for all 256 values of `$1C`, forking on every branch that depends on other data. The result is exactly two classes, "even" and "odd".
* *Assumptions:*
  * A-ENTRY-A59D: no jump into `$A5A6`-`$A5ED` except through `$A59D`. This needs the whole-program control-flow graph.
  * A-NMI: an NMI returns with X restored.
  * A-TRANSCRIBE.
* *Label:* PROVEN-GIVEN-ASSUMPTIONS.
* It also corrects the wording in the docs: "odd → slot 3, even → slots 2 and 4" is the Metal Blade special case of this rule.
* *Re-run 2026-11-07:* the same two classes.

**Example 5: the exits of `$1C` waits.** L-1C-LOCAL takes the loop around each `$1C` reader seen in the replays and gives its exit condition over all 256 values of `$1C`:
* D:9981 waits while `$1C` mod 4 ≠ 0;
* D:BA45, D:BC3B and E:833F wait while `$1C` mod 8 ≠ 0;
* D:A218 waits while `$1C` is odd.

*Label:* PROVEN-GIVEN-ASSUMPTIONS (A-TRANSCRIBE; it also treats each JSR as a normal return). It does not prove that these are all the `$1C` waits. That needs the reader set over all inputs, which is open.

**Example 6: arithmetic.** `tools/proof/frule.py` checks the three frame-rule formulas of 2.5, and the chain rule, against the brute-force definition:
* on 1,073,988 single-rule cases (q up to 32, leads and delays up to 200);
* on 20,000 random chains of rules.

This is PROVEN for that range, and the paper proof covers all values. It is the part a proof assistant could formalise today in a few lines.

**Example 7: a replay.** v6.5 reaches the ending with its last input at frame 85,003, on both cores (`tools/verify.py`). This is a PROVEN (∃) claim: L* ≤ 85,004.

### 4.6 Status of the pilot certificates

All 11 are in `tools/proof/certs/`, each with its envelope (claim, assumptions, checker command, expected verdict, and
every re-check so far). Every one was checked VALID on the working core on 2026-11-07: closure over its 8 or 32 input
classes plus all 256 pads on sampled entries, with every taint verdict re-run (C5); `cert_menu77716` also over all 256
pads on every entry. The labels below leave out A-HARNESS, which every emulator-based claim uses; the envelopes list
it.

On 2026-11-10 all 11 were checked again, independently of the packaging: a fresh clone of the repository with this
kit, fresh builds of both cores, and only the steps of section 7. Each certificate was checked with the command its
envelope names. The result was VALID for 11 of 11 on the working core and for 11 of 11 on the judge core, every root
rebuilt by a replay from power-on. The envelopes record these 22 runs. What such a run covers is what the command
covers: all 256 pads on every entry for `cert_menu77716`, and the input classes plus all 256 pads on sampled entries
for the other ten.

| certificate | claim | label | re-checked on the judge core from power-on |
|---|---|---|---|
| `cert_menu77716` (full search, closure over all 256 pads) | no earlier close | PROVEN-GIVEN-ASSUMPTIONS (A-STATE) | yes, all 256 pads, also from the repository layout |
| `cert_menu76975`, `78207`, `79403`, `83185` (full search, checked over classes) | no earlier close | PROVEN-GIVEN-ASSUMPTIONS (A-STATE, A-TAINT; A-CORE-EQ for the pads outside the class representatives), until re-checked over all 256 pads on both cores | yes, over the classes plus sampled entries over all 256 pads, from the repository layout |
| `cert_menuP76975`, `P80360`, `P84783` (pruned by L-menu) | no earlier close | PROVEN-GIVEN-ASSUMPTIONS (A-STATE, A-TAINT, A-MENU-CLOSURE; A-CORE-EQ for the pads outside the class representatives) | yes, over the classes plus sampled entries over all 256 pads, from the repository layout |
| `cert_menuP78839`, `cert_menuP79781` (pruned by L-menu) | no earlier close; for P79781, exactly 1 frame | PROVEN-GIVEN-ASSUMPTIONS (A-STATE, A-TAINT, A-MENU-CLOSURE; A-CORE-EQ for the pads outside the class representatives) | yes, over the classes plus sampled entries over all 256 pads, from the repository layout |
| `cert_walk77811_k4` | the last 4 frames of the capsule walk | PROVEN-GIVEN-ASSUMPTIONS (A-STATE, A-TAINT; A-CORE-EQ for the pads outside the class representatives) | yes, over the classes plus sampled entries over all 256 pads, from the repository layout |
| L-HIT, L-1C-LOCAL | section 4.5 | PROVEN-GIVEN-ASSUMPTIONS | not applicable (ROM only) |

A judge-core check over the classes confirms the class representatives' transitions on the judge core. The other pads
of each class are covered by the taint verdicts, which can only be computed on the working core (FCEUX 2.3.0 has no
memory hooks). For those certificates A-CORE-EQ is therefore discharged for the representatives only; for the other
pads the judge-core claim rests on A-TAINT as computed on the working core plus A-CORE-EQ. Only a check over all 256
pads on every entry on the judge core (as for `cert_menu77716`) discharges both.

## 5. A full optimality proof: what it would take

### 5.1 The statement

L* = 85,004, or the length of the best movie at the time.
* The upper bound is a replay.
* The lower bound says that none of the 256^85,003 possible pad sequences reaches the ending sooner. That includes sequences that use glitches nobody knows.

### 5.2 What it needs

1. **The whole-program code lemmas**: L-CLK, the gate lemmas, the writer and reader sets, the input independence of the fixed loops, and speed bounds. These need a converged sound analysis plus its checker.
2. **Necessity lemmas for the route skeleton.**
   * Every winning run beats the eight robot masters in some order and the Wily stages in order, and reaches the alien fight. This follows from the stage flags `$9A` and `$2A` and their writers.
   * Every route must be covered: all 8! robot-master orders; every item and weapon plan; deaths and death warps; and glitches, known or unknown. Only code lemmas cover the unknown ones.
3. **One budget per rule interval.** For every rule interval k, the largest counted-frame gain any run can make is at most q_k − w_k − 1. Each interval's bound is a composition of segment bounds that hold for every reachable hand-over state (O2), not only for the movie's own state (O1).
4. **The uncounted frames.** Either every true lag frame in the movie is forced, or the movie has the fewest possible. Proving a lag frame forced needs a lower bound on the CPU cycles of that frame's code over all inputs (a best-case execution-time analysis). No such tool exists here yet.
5. **The end of the run.** After the last rule (the alien's health fill), every frame counts. This needs an exact bound for the alien fight, plus L-END.
6. **The judge core.** All of the above must hold on the judge core, through A-CORE-EQ or by re-running every checker there.

### 5.3 Why it is out of reach today

* **Search does not scale.** Gameplay states multiply about 12 times per frame, even after removing the pad bits proven dead, so 4 frames is the practical depth. The run is 85,004 frames long.
* **The state cannot be made small.** RAM alone does not determine the future: 1-3 CPU cycles of difference change it hundreds of frames later (T4). The DelayScroll checks depend on a window of 17-50 cycles.
* **Every hand-over carries hidden state:**
  * the RNG;
  * the `$1C` phase;
  * stale weapon-slot subpixels;
  * Mega Man's offscreen Y byte;
  * the real-time phase of the music;
  * the CPU's phase within the frame.

  A segment bound has to hold for every reachable combination of these, and we cannot yet describe that set.
* **The static analysis does not converge yet.** 1,921 of 2,048 RAM bytes become "any value", so no whole-program lemma exists yet.
* **The route space is large.** Even the robot-master order is settled only as an ESTIMATE, with a margin of at least 140 frames.
* **Lag frames** need cycle-exact lower bounds, which no tool here computes.
* **There is no formal model of the NES**, let alone of FCEUX, in any proof assistant.
  * The "kernel" of our proofs is FCEUX itself plus our checkers.
  * Our transcription of FCEUX's CPU is tested, not proven.
  * A Lean proof of the whole run would first need a formalised 6502, MMC1 and the relevant PPU and APU behaviour, shown to agree with FCEUX.

### 5.4 The realistic path

The run does not need tight bounds everywhere. Section 2.5 turns "optimal up to rule k" into budgets: each rule interval only has to be shown unable to gain q − w frames. Most intervals have q = 4 or q = 8, and the movie already waits very little at them.

So the work is a ledger of obligations, filled in from the end of the run backwards:
1. **Adopt the labels.**
   * Run `tools/proof/label_lint.py` on the docs and fix what it reports.
   * Re-read the audit notes' PROVEN entries under the stricter definition.
2. **Make the whole-program static analysis converge**, using invariants per array for the object tables instead of one flow-insensitive value per byte, and write the fixpoint checker. This discharges L-CLK, the writer lemmas, A-ENTRY-A59D and the input independence of the fixed loops, which every later step uses.
3. **Build the obligations ledger for the current movie.**
   * For every rule k: q_k and w_k re-measured on the current movie (the table in docs/whole-game-analysis.md is for #4410), the budget q_k − w_k − 1, and the segments in the interval with their labels.
   * Every uncounted frame, with a label saying whether it is proven forced.
4. **Close the end first.**
   * After the alien's fill every frame counts, the fight is short, and the alien's path depends only on counted, unpaused frames.
   * A relaxation built on the hit cadence (L-HIT, the `$B4` latch, at most two bubbles, 1 damage per hit), plus L-END, could give "v6.x is optimal from the alien fill to the end, given A-…".
   * Then the Wily 5/6 q4 intervals, where the menus are already certified and the hub walks are short.
5. **Fixed segments.** About 58% of the frames lie in loops whose length does not depend on input (a flow measurement on the movie; ESTIMATE until input independence is proven). Once input independence is a code lemma, those segments have exact lengths and leave no gap.
6. **Fights.** Cadence lemmas (L-HIT, the invincibility timers, the damage tables and the slot parity) give "kill ≥ first hittable frame + (hits − 1) × cadence". Several fights already sit on such bounds; this would make those bounds lemmas.
7. **Movement.** Speed lemmas, plus the level geometry in the ROM, give relaxations. Where a relaxation leaves more than the budget, either sharpen it or search for the saving.
8. **Route.** Necessity lemmas plus the route model can turn the order question from ESTIMATE into PROVEN-IN-MODEL, and later into PROVEN-GIVEN-ASSUMPTIONS.

**Expected outcome.** Steps 1-4 can produce partial theorems of the form "the movie is optimal from frame X to the end, given these named assumptions", starting with the last few thousand frames. A theorem for the whole run is not expected. What is expected is a ledger in which every interval carries a label, so that the weakest labels show where a saving could still hide.

## 6. Assumption register

**Axioms**, which are not to be discharged: AX-ROM, AX-FCEUX, AX-POWERON and AX-TIME (section 1).

**Open assumptions.** Every claim that uses one names it. (The search notes called A-HARNESS, A-STATE, A-TAINT and A-MENU-CLOSURE A1-A4.)

**A-CORE-EQ**
* *Statement:* the working core (master `fa248734`) and the judge core (2.3.0) compute the same T on every state the claim needs.
* *Evidence:* identical per-frame CRC and lag flags on v6.5 plus 3,000 blank frames; the certificates listed in 4.6 as re-checked on the judge core are VALID there from power-on.
* *To discharge:* re-run each claim's checker on the judge core, over all 256 pads. A check over the input classes discharges it only for the class representatives, because the taint verdicts that cover the other pads can be computed only on the working core.

**A-HARNESS**
* *Statement:* the harness's frame loop and FCEUX's movie loader give the same emulation as FCEUX itself, and running with sound output off does not change any CPU-visible state.
* *Evidence:* every movie replays identically both ways. From a reading of the source, the APU's CPU-visible state advances in `FCEU_SoundCPUHook` whatever the sound rate.
* *To discharge:* run one long replay in a stock FCEUX 2.3.0 build and compare.

**A-STATE**
* *Statement:* two states with the same key (the whole savestate minus 8 fields never read after a load) have the same future. Some emulator state is never saved: the old PPU's sprite-0 data, two static variables of the line renderer, and the frame buffer. These affect only the image and bits 5-6 of `$2002`, which the game never uses.
* *Evidence:* saving and reloading before every frame of 85,206 frames gives 0 differences; history independence 0 of 1,500; randomised dropped fields 0 of 300.
* *To discharge:* write out the source argument for each field, and prove the code lemma "the game reads `$2002` only at F:D00C and F:D031 (value discarded) and in the reset code (bit 7 only)".

**A-TAINT**
* *Statement:* the taint tracker (`tools/proof/native/pf_taint.inc`, about 380 lines) is correct for the 151 documented opcodes, and the game runs no undocumented opcode in the searched transitions.
* *Evidence:* negative controls; 21,000 random and 6,000 pad-bit fuzz samples with 0 violations.
* *To avoid it:* check closure over all 256 pads.

**A-MENU-CLOSURE**
* *Statement:* during a menu, only the listed instructions write `$1D`, `$FD`, `$FE` and `$A9`, and at most one NMI runs per frame.
* *Evidence:* a census over 428,656 transitions.
* *To discharge:* a whole-program writer lemma.

**GA-MENU**
* *Statement:* "`$A9` = target and `$FD` = 0" marks the frame on which the menu closes with the target weapon, and the rest of the close has a fixed length.
* *To discharge:* a local code lemma on the close code at bank 13 `$92C9`-`$92D3`.

**A-TRANSCRIBE**
* *Statement:* `tools/proof/static/m6502.py` and `vs.py` match FCEUX's CPU core: all 256 opcodes, the addressing modes, dummy reads, and the double writes of read-modify-write instructions.
* *Evidence:* transcribed from `x6502.cpp` and `ops.inc`; the ALU is exhaustive on single values.
* *To discharge:* an exhaustive differential test of every opcode against the core itself.

**A-NMI** (whole-program static analysis)
* *Statement:*
  * no NMI begins at a mapper-sensitive boundary;
  * NMIs never nest;
  * at most one NMI falls in each bank-switch busy window, and that NMI sees `$67` ≠ `$FF`.
* *Paper argument, from timing:* NMIs are at least 27,897 cycles apart, and the deferred sound path starts at most about 40 cycles after an NMI.
* *REAL evidence:*
  * no nesting;
  * the longest NMI took 12,968 cycles;
  * every interrupt lands in one of the three wait loops, in the busy window C006-C01B, or at one of the listed lag spots.

**A-SND** (whole-program static analysis)
* *Statement:* the sound engine (`JSR $8000` or `$8003` with bank 12 mapped):
  * returns normally;
  * keeps S, the mapped bank, the MMC1 shift state and the I/D flags unchanged;
  * writes RAM only in `$E0`-`$F5` and `$0500`-`$057F`.
* *Evidence:* observed exactly so in both runs.
* *To discharge:* a proof that the music data is well formed.

**A-A406, A-AD, A-WTYPE** (whole-program static analysis)
* *Statement:* three dispatch indices stay in range:
  * at 13:A416, Y ∈ {0, 1};
  * at 14:82DF, Y ∈ 0..8;
  * at 15:DD03, A ∈ 0..15.
* *Evidence:* observed in range.
* *To discharge:* the converged analysis.

**GINV** (whole-program static analysis; an invariant the analysis checks)
* *Statement:* `$29` and `$69` stay in 0..15, and object types in `$0400`-`$041F` are at most `$7E`.
* *Status:* 12 writers may violate the second today; they are listed as OPEN items.

**A-STACK** (whole-program static analysis)
* *Statement:* data writes to page 1 never hit live stack bytes.
* *Evidence:* the observed data writes stay in `$0100`-`$017F`, and the lowest S seen is `$DE`.

**A-ENTRY-A59D**
* *Statement:* control never enters `$A5A6`-`$A5ED` except from `$A59D`.
* *To discharge:* the converged control-flow graph.

**L-CLK**
* *Statement:* `$1C` is written only by F:D088 (+1, in the NMI) and by the reset's RAM clear, and it advances exactly once per counted frame.
* *Status:* REAL evidence only.

**L-GATE(k)**
* *Statement:* for each frame rule k, its routine waits for the counter phase as described in 2.5.
* *Status:* local lemmas exist for the loops around the observed readers (L-1C-LOCAL); completeness over all readers is open.

**L-END**
* *Statement:* under blank input after the last input, the alien dies within K frames, and the ending follows without input. This gives L ≥ D − K from a bound D on the kill frame.
* *Status:* K = 1 in the current movie; the bound over all states is open.

**A-ROUTE**
* *Statement:* the claim covers only runs that follow the current route: the robot-master order, the item and weapon plan, and no extra deaths. A claim with this assumption says nothing about other routes.

## 7. How to re-check from a clean clone

You need a clone of this repository, the FCEUX source at the two revisions of section 1.2, and the ROM (sha256
`deb88223311aca8ca566b99d4063ca29d389d939fee455f83afaec97c6f0a5d1`). The ROM is never in the repository; every tool
takes its path as an argument and refuses a ROM with other hashes. Tools: git, make, g++ with C++17, zlib headers,
Python 3. numpy is needed only by `static/pfrec.py` and `static/local_lemmas.py --recordings`. Tested 2026-11-07 with
Python 3.13, g++ 13.3 and GNU Make 4.3.

```
git clone <this repository> rm2 && cd rm2
git clone https://github.com/TASEmulators/fceux.git ../fceux-master && git -C ../fceux-master checkout fa248734
git clone --depth 1 --branch fceux-2.3.0 https://github.com/TASEmulators/fceux.git ../fceux-2.3.0
ROM="/path/to/Rockman 2 - Dr. Wily no Nazo (Japan).nes"
BUILD="$PWD/../rm2-build"

# 1. build: the working core plus the analysis libraries, then the judge core (a few minutes each)
make -C tools/proof -j4 FCEUX_SRC="$PWD/../fceux-master/src" OUT="$BUILD/master"
make -C tools/proof -j4 FCEUX_SRC="$PWD/../fceux-2.3.0/src" OUT="$BUILD/v230" core

# 2. the certificates are the files that were checked (the checkers also verify this, check E0)
(cd tools/proof/certs && sha256sum -c --ignore-missing SHA256SUMS)

# 3. pure arithmetic and the ROM-only lemmas (seconds)
python3 tools/proof/frule.py
python3 tools/proof/static/selftest_vs.py
python3 tools/proof/static/local_lemmas.py "$ROM" --check tools/proof/data/local_lemmas.expected.json

# 4. one certificate on both cores (about 2 minutes each, most of it the power-on replay to the root)
python3 tools/proof/pfcheck.py tools/proof/certs/cert_menu77716.json.gz --rom "$ROM" --lib "$BUILD/master/librm2.so"
python3 tools/proof/pfcheck.py tools/proof/certs/cert_menu77716.json.gz --rom "$ROM" --lib "$BUILD/v230/librm2.so"

# 5. every certificate with the command its envelope names (working core; about 25 minutes in all)
for e in tools/proof/certs/*.envelope.json; do
  cmd=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["checker"]["command"])' "$e")
  ROM="$ROM" BUILD="$BUILD" sh -c "$cmd" | tail -n 1 | cut -c1-60
done
# the judge core: the same loop with "judge_core_command" in place of "command"

# 6. the labelling lint on the docs (exit code 1 while unlabelled claims remain; section 3 has the baseline)
python3 tools/proof/label_lint.py docs/whole-game-analysis.md README.md --list
```

What to expect:

* `frule.py`: `frule selfcheck OK: 1073988 single-rule cases (P1-P3), 20000 random chains (P4)`.
* `selftest_vs.py`: `selftest_vs: failures = 0`.
* `local_lemmas.py`: the two L-HIT classes (`$1C` even: slots 8, 6, 4, 2; odd: 9, 7, 5, 3; only B:A5E8 writes `$B4`)
  and the L-1C-LOCAL exit conditions of section 4.5, then `result equals local_lemmas.expected.json: True`.
* Each checker: lines `E0`, `C1`, `C0`, `C2`, `C3` (and `C3b`, `C4`, `C5`-`C7` as requested), all `True`, then
  `VERDICT <id>.json: VALID {...}` and exit code 0. Any `FAIL` line, an `INVALID` verdict or a non-zero exit code
  means the certificate is not confirmed. The `{...}` part repeats the counts, the library's md5 and the checker's
  sha256; compare them with the envelope's `checked` entries.
* `C1` also prints whether the rebuilt root is byte-identical to the state the search started from
  ("full-state sha256 also equal"). This is informational and is normally `False`: the search started from a
  pickled savestate and the checkers from power-on, and the two differ only in fields the key drops (for
  `cert_menu77716` on the working core, only `SFMDATA.LRST`).

Layout of `tools/proof/`:

| path | what it is |
|---|---|
| `Makefile` | builds `librm2.so` (through `tools/harness/Makefile`), `librm2pf.so` and `librm2rec.so` from `FCEUX_SRC` into `OUT` |
| `native/driver_pf.cpp`, `native/pf_taint.inc` | the analysis driver: harness driver + taint tracker, read and write watches (observing hooks only) |
| `native/driver_rec.cpp`, `native/pf_rec.inc` | the recorder driver used by `static/pfrec.py` (coverage, read/write sets, value sets, interrupt statistics) |
| `pflib.py`, `pfsearch.py`, `pfrun.py` | the certified search: state identity, BFS engine, command line (`menu`, `menuP`, `walk`) |
| `pfcheck.py`, `pfcheck_stream.py` | the independent checkers (E0, C0-C7); they share no code with the search |
| `certs/` | the 11 pilot certificates (`.json.gz`), one envelope each (`.envelope.json`), `SHA256SUMS` |
| `data/` | `v63_pauses.json` (the v6.3 pauses after frame 76,000), `1c_readers.json` (the `$1C` readers seen in two REAL replays), `local_lemmas.expected.json` |
| `frule.py` | frame-rule arithmetic with its exhaustive self-check |
| `label_lint.py` | the labelling lint of section 3 |
| `static/` | `m6502.py` (FCEUX opcode table), `vs.py` (value-set ALU) and `selftest_vs.py`, `lemmas.py` (loop exit sets), `local_lemmas.py` (L-HIT, L-1C-LOCAL), `pfrec.py` (REAL-replay recorder) |
