#!/usr/bin/env python3
"""frule.py - frame-rule arithmetic with an exhaustive self-check (pf_doc, 2026-11-07). Pure arithmetic; no emulator.

Model (the GATE lemma, which is a code lemma to be proven separately for each rule): an event that becomes ready
when the frame counter (unwrapped $1C, i.e. the number of COUNTED frames) has value R happens at the first counter
value E >= R with E = phi (mod q).  Reference run: ready at R0, event at E0 = R0 + w with 0 <= w < q.

  gain(c)  = E0 - E(R0 - c)                 for a lead of c >= 0 counted frames before the rule
  loss(d)  = E(R0 + d) - E0                 for a delay of d >= 0 counted frames
  P1: gain(c) = q * floor((w + c) / q)
  P2: gain(c) = 0 for every 0 <= c <= cmax  <=>  cmax <= q - w - 1        (the per-rule OBLIGATION)
  P3: loss(d) = q * ceil(max(0, d - w) / q)
  P4: chain: lead entering rule k = (lead carried out of rule k-1) + (gain made in interval k); if every interval's
      maximum possible gain g_k satisfies g_k <= q_k - w_k - 1, then every carried lead is 0 and the counter value
      at every rule event, including the last, equals the reference run's.

Paper proof of P1: E(R) = R + ((phi - R) mod q). With R = R0 - c: (phi - R0 + c) mod q = (w + c) mod q, so
E0 - E = w + c - ((w + c) mod q) = q * floor((w + c) / q). P2 follows since 0 <= w < q. P3 likewise.
The self-check below compares the formulas with a brute-force simulation of the definition (scan counter values
upward until the phase matches) on a finite range; it is a certificate for that range only.

usage: frule.py            (runs the self-check and prints the counts)
"""


def event(R, q, phi):
    """Definition: first counter value >= R that is = phi mod q (brute force)."""
    E = R
    while E % q != phi % q:
        E += 1
    return E


def gain(c, q, w):
    return q * ((w + c) // q)


def loss(d, q, w):
    return q * (-(-max(0, d - w) // q))


def obligation(q, w):
    """Largest lead (counted frames) that a rule with period q and reference wait w absorbs completely."""
    return q - w - 1


def chain(rules, gains):
    """rules: [(q, w)], gains: max counted-frame gain inside each interval (before rule k). Returns leads out of rules."""
    out, carried = [], 0
    for (q, w), g in zip(rules, gains):
        carried = gain(carried + g, q, w)
        out.append(carried)
    return out


def selfcheck():
    n = 0
    for q in (1, 2, 4, 8, 16, 32):
        for phi in range(q):
            for R0 in range(0, 3 * q + 5):
                E0 = event(R0, q, phi); w = E0 - R0
                assert 0 <= w < q
                for c in range(0, min(R0, 200) + 1):
                    assert E0 - event(R0 - c, q, phi) == gain(c, q, w); n += 1
                for d in range(0, 200):
                    assert event(R0 + d, q, phi) - E0 == loss(d, q, w); n += 1
                # P2 in both directions
                cm = obligation(q, w)
                assert all(gain(c, q, w) == 0 for c in range(cm + 1)) and gain(cm + 1, q, w) == q
    # P4 on random chains, against the same composition done with brute force event times
    import random
    rnd = random.Random(1)
    m = 0
    for _ in range(20000):
        k = rnd.randint(1, 6)
        rules = []
        for _ in range(k):
            q = rnd.choice((4, 8, 16)); rules.append((q, rnd.randrange(q)))
        gains = [rnd.randrange(0, 20) for _ in range(k)]
        leads = chain(rules, gains)
        # brute force: reference event counters; candidate run makes the extra gains
        R = 100; ref, cand, Rc = [], [], 100
        for (q, w), g in zip(rules, gains):
            phi = (R + w) % q
            Er = event(R, q, phi); Ec = event(Rc - g, q, phi)
            ref.append(Er); cand.append(Ec)
            R = Er + 37; Rc = Ec + 37          # same fixed-length stretch after each rule in both runs
        assert [a - b for a, b in zip(ref, cand)] == leads
        if all(g <= obligation(q, w) for (q, w), g in zip(rules, gains)):
            assert all(x == 0 for x in leads)
        m += 1
    return n, m


if __name__ == '__main__':
    n, m = selfcheck()
    print('frule selfcheck OK: %d single-rule cases (P1-P3), %d random chains (P4)' % (n, m))
    print('example: Wily 1 fade in #4410: q=16, w=0 -> the fade absorbs any counted lead up to %d frames' % obligation(16, 0))
    print('example: chain q4 w3 then q8 w3 with gains 1 and 4 -> leads out', chain([(4, 3), (8, 3)], [1, 4]))
