"""Trica Neon -- class kerning, measured on the outlines.

Each pair of the brief is kerned so that the space between the two glyphs, averaged over
the height they share, matches the space between two straight stems (twice the
sidebearing). Open areas, such as under the bar of a T or beside the foot of a V, count
only up to a limit, and only part of the difference becomes kerning, so it stays moderate.
Then no two letters or figures, and no letter and punctuation mark, come closer than a share
of the stroke: kerning that would bring them closer is reduced, and pairs that are too close
untouched get kerned apart.
"""
import math, unicodedata

STEPS = 40          # heights sampled in the band the two glyphs share
CLIP = 2.0          # open space counts up to CLIP x the reference gap
FACTOR = 0.75       # share of the measured difference that becomes kerning
MIN_KERN = 15       # smaller values are left out
MIN_GAP = 0.4       # closest two glyphs may come, as a share of the stroke ...
MIN_GAP_UNITS = 20  # ... and in units at least

# group -> glyph measured for it; the members are that glyph and its accented letters
LEFT = {"A": "A", "F": "F", "L": "L", "P": "P", "T": "T", "V": "V", "W": "W", "Y": "Y",
        "r": "r", "v": "v", "y": "y", "quotes": "quotesingle"}
RIGHT = {"A": "A", "T": "T", "V": "V", "W": "W", "Y": "Y", "a": "a", "e": "e", "o": "o",
         "period": "period", "quotes": "quotesingle"}
LISTS = {"quotes": ["quotesingle", "quotedbl", "quoteleft", "quotedblleft", "quoteright", "quotedblright"],
         "period": ["period", "comma", "ellipsis"]}
PAIRS = [("A", "V"), ("A", "W"), ("A", "Y"), ("A", "T"), ("A", "quotes"), ("quotes", "A"),
         ("L", "T"), ("L", "V"), ("L", "Y"), ("P", "A"), ("P", "period"), ("F", "period"),
         ("r", "period"), ("y", "period"), ("v", "period")] + \
        [(left, right) for left in ("T", "V", "W", "Y") for right in ("A", "a", "e", "o", "period")]


def letters(cmap, components):
    """The drawn letters and figures (not the accented ones): each is a kerning class with its accented forms."""
    return sorted({n for cp, n in cmap.items()
                   if unicodedata.category(chr(cp)) in ("Ll", "Lu", "Lt", "Nd") and n not in components})


def punctuation(cmap, components, skip):
    """The drawn punctuation and symbols, kept apart from the letters (as single glyphs, not classes),
    but for those in `skip`, drawn to touch their neighbours (_ ⁄)."""
    return sorted({n for cp, n in cmap.items()
                   if unicodedata.category(chr(cp))[0] in "PS" and unicodedata.category(chr(cp)) != "Sk"
                   and n not in components and n not in skip})


def groups(components, letters):
    """{"public.kern1.X": [...], "public.kern2.X": [...]} with internal glyph names. On the
    left side of a pair, accented letters whose mark sticks out on the right (ogonek,
    vertical caron) stay out of the group."""
    def members(group, key, left):
        if group in LISTS:
            return LISTS[group]
        out = [key]
        for name, comps in components.items():
            marks = {c[0] for c in comps[1:]}
            if comps[0][0] == key and comps[1:] and not (left and marks & {"ogonekcomb", "caroncomb.alt"}):
                out.append(name)
        return out
    left, right = {**LEFT, **{n: n for n in letters}}, {**RIGHT, **{n: n for n in letters}}
    result = {f"public.kern1.{g}": members(g, k, True) for g, k in left.items()}
    result.update({f"public.kern2.{g}": members(g, k, False) for g, k in right.items()})
    return result


def values(contours, advances, gap, stroke, letters, marks):
    """{(kern1 group, kern2 group): value} for one master; contours resolved, in font units."""
    lines = {g: _polylines(contours[g]) for g in set(LEFT.values()) | set(RIGHT.values()) | set(letters) | set(marks)}
    rows = {g: _rows(lines[g]) for g in lines}
    least = max(MIN_GAP * stroke, MIN_GAP_UNITS)

    def closest(a, b, kern):                       # nearest approach of b set after a, over every height
        return min((advances[a] + kern + rows[b][y][0] - rows[a][y][1] for y in rows[a] if y in rows[b]), default=None)

    def apart(a, b, value):                        # the kerning that keeps a and b at least `least` apart
        near = closest(a, b, value)
        return value if near is None or near >= least else value + 5 * math.ceil((least - near) / 5)

    out = {}
    for left, right in PAIRS:
        a, b = LEFT[left], RIGHT[right]
        value = min(0, apart(a, b, _kern(lines[a], advances[a], lines[b], gap)))
        if abs(value) >= MIN_KERN:
            out[(f"public.kern1.{left}", f"public.kern2.{right}")] = value
    for a in letters:
        for b in letters:
            key = (f"public.kern1.{a}", f"public.kern2.{b}")
            if key not in out and not any((LEFT.get(l), RIGHT.get(r)) == (a, b) for l, r in PAIRS):
                value = apart(a, b, 0)
                if value:
                    out[key] = value
    # punctuation next to letters: glyph to class (marks already in a list class stay out)
    listed = {side: {m for g in groups_ if g in LISTS for m in LISTS[g]} for side, groups_ in (("l", LEFT), ("r", RIGHT))}
    for a, b, key in [(p, b, (p, f"public.kern2.{b}")) for p in marks if p not in listed["l"] for b in letters] + \
                     [(a, p, (f"public.kern1.{a}", p)) for a in letters for p in marks if p not in listed["r"]]:
        value = apart(a, b, 0)
        if value:
            out[key] = value
    return out


def _kern(left, advance, right, gap):
    ys_l, ys_r = [p[1] for c in left for p in c], [p[1] for c in right for p in c]
    lo, hi = max(min(ys_l), min(ys_r)), min(max(ys_l), max(ys_r))
    if hi <= lo:
        return 0
    gaps = []
    for k in range(STEPS):
        y = lo + (hi - lo) * (k + 0.5) / STEPS + 0.01      # never exactly on a point
        a, b = _extent(left, y, max), _extent(right, y, min)
        gaps.append(gap * CLIP if a is None or b is None else min(gap * CLIP, advance + b - a))
    value = 5 * round((gap - sum(gaps) / len(gaps)) * FACTOR / 5)
    return value if abs(value) >= MIN_KERN else 0


def _rows(lines):
    """{height: (leftmost x, rightmost x)} every 10 units where the glyph has ink."""
    out = {}
    for y in range(-400, 1100, 10):
        lo, hi = _extent(lines, y + 0.01, min), _extent(lines, y + 0.01, max)
        if lo is not None:
            out[y] = (lo, hi)
    return out


def _extent(lines, y, pick):
    xs = [p[0] + (y - p[1]) * (q[0] - p[0]) / (q[1] - p[1])
          for c in lines for p, q in zip(c, c[1:] + c[:1]) if (p[1] - y) * (q[1] - y) < 0]
    return pick(xs) if xs else None


def _polylines(contours):
    out = []
    for start, segs in contours:
        pts, cur = [start], start
        for g in segs:
            if g[0] == "curve":
                pts += [_cubic(cur, g[1], g[2], g[3], k / 16) for k in range(1, 17)]
            else:
                pts.append(g[1])
            cur = g[-1]
        out.append(pts)
    return out


def _cubic(p0, p1, p2, p3, t):
    s = 1 - t
    return tuple(s ** 3 * a + 3 * s * s * t * b + 3 * s * t * t * c + t ** 3 * d for a, b, c, d in zip(p0, p1, p2, p3))
