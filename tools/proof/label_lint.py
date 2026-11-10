#!/usr/bin/env python3
"""label_lint.py - enforce the labelling rule of the proof standards (pf_doc, 2026-11-07).

Rule: every statement in the docs that says something is impossible, optimal, minimal, closed, a dead end, or
"cannot" save time must carry one of the claim labels in the same unit of text. A unit is one Markdown bullet
(with its continuation lines), one table row, or one plain paragraph.

usage: label_lint.py FILE.md [FILE.md ...] [--list]
Exit code 0 if every triggering unit carries a label, 1 otherwise. Reads files only; writes nothing.
Text in inline code (`...`) is ignored, so paths such as tools/proof/ do not trigger.
A unit whose trigger word is not a claim (e.g. "a closed room", or history such as "the 2006 exhaustive search
found") is waived by writing the HTML comment <!-- no-claim --> inside it; the waiver is visible in review.

This is a necessary check, not a sufficient one: it cannot tell whether the label is the right one, and the
trigger list can miss a negative claim phrased in other words. Reviewers still read the text.
"""
import re
import sys

LABELS = r'\b(PROVEN-GIVEN-ASSUMPTIONS|PROVEN-IN-MODEL|PROVEN|SEARCH-LIMITED|ESTIMATE|UNSUPPORTED|OVERTAKEN)\b'
TRIGGERS = (r'impossib|\boptimal|\boptimum|provabl|\bproven\b|\bproof\b|\bproves?\b|dead[ -]end|at (its|their|the) limit'
            r'|not improvable|\bminimal\b|frame-perfect|\bclosed\b|exhaustive|earliest possible|fastest possible'
            r'|cannot (gain|save|be (shortened|improved|raised|faster|reached))|can(no|\')t gain|no (time )?saving'
            r'|nothing (earlier|faster|better)|never (works|helps|gains)')
LAB = re.compile(LABELS)          # labels are matched case-sensitively: they are written in capitals
TRIG = re.compile(TRIGGERS, re.I)
CODE = re.compile(r'`[^`]*`')     # inline code (paths such as tools/proof/, commands) never triggers
IGNORE = '<!-- no-claim -->'      # put this in a unit whose trigger word is not a claim ("a closed room", history)


def units(text):
    """Split Markdown into units: bullets with continuation lines, table rows, paragraphs. Code blocks are skipped."""
    out, cur, start, in_code = [], [], 0, False
    lines = text.split('\n')

    def flush():
        if cur:
            out.append((start, ' '.join(s.strip() for s in cur)))
        cur.clear()
    for i, ln in enumerate(lines, 1):
        if ln.strip().startswith('```'):
            flush(); in_code = not in_code; continue
        if in_code:
            continue
        s = ln.strip()
        if not s or s.startswith('#'):
            flush(); continue
        if s.startswith('|'):
            flush(); out.append((i, s)); continue
        if re.match(r'^([*+-]|\d+[.)])\s', s):
            flush(); start = i; cur.append(s); continue
        if not cur:
            start = i
        cur.append(s)
    flush()
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    show = '--list' in sys.argv
    bad_total = 0
    for fn in args:
        us = units(open(fn, encoding='utf-8').read())
        trig = [(ln, u) for ln, u in us if TRIG.search(CODE.sub(' ', u))]
        bad = [(ln, u) for ln, u in trig if not LAB.search(u) and IGNORE not in u]
        bad_total += len(bad)
        print('%s: %d units, %d with a claim trigger, %d of those unlabelled' % (fn, len(us), len(trig), len(bad)))
        if show:
            for ln, u in bad:
                m = TRIG.search(CODE.sub(' ', u))
                print('  l.%d [%s] %s' % (ln, m.group(0), u[:160]))
    sys.exit(1 if bad_total else 0)


if __name__ == '__main__':
    main()
