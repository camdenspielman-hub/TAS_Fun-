"""Value sets of bytes as 256-bit Python ints (bit v set <=> value v possible) + concrete FCEUX ALU semantics.

Soundness contract of every abstract op here: for all concrete inputs drawn from the argument sets, the concrete
FCEUX result (see the c_* functions, transcribed from x6502.cpp's macros) is in the returned set.  Checked by
selftest_vs.py (exhaustive over small sets + random fuzz)."""
from functools import lru_cache

TOP = (1 << 256) - 1
EMPTY = 0
LOW = (1 << 128) - 1          # values 0..127
HIGH = TOP ^ LOW              # values 128..255
F0, F1, FB = 1, 2, 3          # flag masks: can be 0 / can be 1 / both


def c(v):
    return 1 << (v & 0xFF)


def from_iter(it):
    s = 0
    for v in it:
        s |= 1 << (v & 0xFF)
    return s


def rng(lo, hi):
    """values lo..hi inclusive"""
    if hi < lo:
        return 0
    return ((1 << (hi - lo + 1)) - 1) << lo


def elems(s):
    out = []
    while s:
        low = s & -s
        out.append(low.bit_length() - 1)
        s ^= low
    return out


def count(s):
    return s.bit_count()


def single(s):
    """the value if s is a singleton else None"""
    if s and not (s & (s - 1)):
        return s.bit_length() - 1
    return None


def vmin(s):
    return (s & -s).bit_length() - 1


def vmax(s):
    return s.bit_length() - 1


def fmt(s, maxn=12):
    if s == TOP:
        return 'TOP'
    if s == 0:
        return '{}'
    e = elems(s)
    if len(e) <= maxn:
        return '{' + ','.join('%02X' % v for v in e) + '}'
    # compress into ranges
    rs = []
    st = pv = e[0]
    for v in e[1:]:
        if v == pv + 1:
            pv = v
            continue
        rs.append((st, pv)); st = pv = v
    rs.append((st, pv))
    txt = ','.join(('%02X' % a) if a == b else ('%02X-%02X' % (a, b)) for a, b in rs)
    if len(txt) > 80:
        txt = txt[:77] + '...'
    return '{%s}(%d)' % (txt, len(e))


def add_const(s, k):
    """{(x + k) & 255}"""
    k &= 0xFF
    if k == 0 or s == TOP:
        return s
    return ((s << k) | (s >> (256 - k))) & TOP


def flagset_of_bool_iter(it):
    m = 0
    for b in it:
        m |= F1 if b else F0
        if m == FB:
            break
    return m


# ---------------- concrete FCEUX semantics (x6502.cpp macros) ----------------
def c_adc(a, x, cin):
    l = a + x + cin
    v = 1 if ((((a ^ x) & 0x80) ^ 0x80) & ((a ^ l) & 0x80)) else 0
    return l & 0xFF, (l >> 8) & 1, v


def c_sbc(a, x, cin):
    l = (a - x - (cin ^ 1)) & 0xFFFFFFFF   # uint32 arithmetic in FCEUX
    v = 1 if ((a ^ l) & (a ^ x) & 0x80) else 0
    cout = ((l >> 8) & 1) ^ 1
    return l & 0xFF, cout, v


def c_cmp(r, x):
    t = (r - x) & 0xFFFFFFFF
    return t & 0xFF, ((t >> 8) & 1) ^ 1      # (result for N/Z, carry)


def c_asl(x):
    return (x << 1) & 0xFF, x >> 7


def c_lsr(x):
    return x >> 1, x & 1


def c_rol(x, cin):
    return ((x << 1) | cin) & 0xFF, x >> 7


def c_ror(x, cin):
    return (x >> 1) | (cin << 7), x & 1


# ---------------- abstract ops ----------------
PAIR_LIMIT = 4096


@lru_cache(maxsize=200000)
def a_binop(op, a, m, cin):
    """op in ADC SBC AND ORA EOR; a, m value sets; cin flag mask.  returns (result set, carry mask, overflow mask)."""
    if op in ('AND', 'ORA', 'EOR'):
        if count(a) * count(m) > PAIR_LIMIT:
            if op == 'AND':
                # bitwise bound: result bits subset of (OR of a) & (OR of m)
                ora = 0
                for v in (elems(a) if count(a) <= 256 else range(256)):
                    ora |= v
                return TOP, cin, FB  # flags C,V untouched by logic ops (caller keeps them); result TOP is sound
            return TOP, cin, FB
        r = 0
        ea, em = elems(a), elems(m)
        for x in ea:
            for y in em:
                r |= 1 << ((x & y) if op == 'AND' else (x | y) if op == 'ORA' else (x ^ y))
        return r, cin, FB
    cins = [v for v in (0, 1) if cin & (1 << v)]
    if count(a) * count(m) * len(cins) > PAIR_LIMIT:
        return TOP, FB, FB
    r = 0; cm = 0; vm = 0
    ea, em = elems(a), elems(m)
    f = c_adc if op == 'ADC' else c_sbc
    for x in ea:
        for y in em:
            for ci in cins:
                res, co, ov = f(x, y, ci)
                r |= 1 << res
                cm |= F1 if co else F0
                vm |= F1 if ov else F0
    return r, cm, vm


@lru_cache(maxsize=200000)
def a_cmp(r, m):
    """returns (difference set (for N/Z), carry mask)"""
    if count(r) * count(m) > PAIR_LIMIT:
        return TOP, FB
    d = 0; cm = 0
    for x in elems(r):
        for y in elems(m):
            t, co = c_cmp(x, y)
            d |= 1 << t
            cm |= F1 if co else F0
    return d, cm


@lru_cache(maxsize=200000)
def a_shift(op, s, cin):
    """op in ASL LSR ROL ROR. returns (result set, carry mask)"""
    r = 0; cm = 0
    cins = [v for v in (0, 1) if cin & (1 << v)]
    for x in (elems(s) if s != TOP else range(256)):
        if op == 'ASL':
            res, co = c_asl(x); r |= 1 << res; cm |= F1 if co else F0
        elif op == 'LSR':
            res, co = c_lsr(x); r |= 1 << res; cm |= F1 if co else F0
        else:
            for ci in (cins if op in ('ROL', 'ROR') else [0]):
                res, co = (c_rol if op == 'ROL' else c_ror)(x, ci)
                r |= 1 << res; cm |= F1 if co else F0
    return r, cm


@lru_cache(maxsize=200000)
def a_map(name, s, k=0):
    """unary maps with an immediate: AND#k, ORA#k, EOR#k"""
    r = 0
    for x in (elems(s) if s != TOP else range(256)):
        if name == 'AND':
            r |= 1 << (x & k)
        elif name == 'ORA':
            r |= 1 << (x | k)
        elif name == 'EOR':
            r |= 1 << (x ^ k)
        else:
            raise ValueError(name)
    return r


def z_mask(s):
    """possible Z flag values for result set s"""
    m = 0
    if s & 1:
        m |= F1
    if s & ~1 & TOP:
        m |= F0
    return m


def n_mask(s):
    m = 0
    if s & LOW:
        m |= F0
    if s & HIGH:
        m |= F1
    return m


def keep_n(s, n):
    """subset of s whose bit7 == n"""
    return s & (HIGH if n else LOW)
