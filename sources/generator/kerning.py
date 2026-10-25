"""Trica Neon -- class kerning, measured on the outlines.

Each pair of the brief is kerned so that the space between the two glyphs, averaged over
the height they share, matches the space between two straight stems (twice the
sidebearing). Open areas, such as under the bar of a T or beside the foot of a V, count
only up to a limit, and only part of the difference becomes kerning, so it stays moderate.
"""

STEPS = 40          # heights sampled in the band the two glyphs share
CLIP = 2.0          # open space counts up to CLIP x the reference gap
FACTOR = 0.75       # share of the measured difference that becomes kerning
MIN_KERN = 15       # smaller values are left out

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


def groups(components):
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
    result = {f"public.kern1.{g}": members(g, k, True) for g, k in LEFT.items()}
    result.update({f"public.kern2.{g}": members(g, k, False) for g, k in RIGHT.items()})
    return result


def values(contours, advances, gap):
    """{(kern1 group, kern2 group): value} for one master; contours resolved, in font units."""
    lines = {g: _polylines(contours[g]) for g in set(LEFT.values()) | set(RIGHT.values())}
    out = {}
    for left, right in PAIRS:
        a, b = LEFT[left], RIGHT[right]
        value = _kern(lines[a], advances[a], lines[b], gap)
        if value:
            out[(f"public.kern1.{left}", f"public.kern2.{right}")] = value
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
