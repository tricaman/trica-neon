"""Trica Neon -- optical spacing, measured on the outlines.

The letters are drawn in boxes with the same sidebearing on both sides, which leaves letters
with open or slanted sides (v x T L ...) looking further apart than the others. This sets the
sidebearings of the letters and figures so that the white beside each of them, averaged over
the x-height (lowercase) or the cap height (capitals and figures), matches the white beside n
or H. As in HT Letterspacer, open areas count only up to a depth, a share of the x-height.
A side where a part outside the zone reaches into that depth (the hook of j, the bar of ł)
keeps its sidebearing. Accented letters take the sidebearings of their base letter.
"""
import unicodedata

STEPS = 60          # heights sampled in the zone
DEPTH = 0.15        # open areas count up to this share of the x-height


def respace(builds, xheight, cap):
    """Change the sidebearings of the letters and figures of every master, in place. Whether a side
    keeps its sidebearing is decided once for all the masters, so that the weights progress evenly."""
    first = builds[0]
    kinds = {}                                                 # glyph -> "lc" or "uc"
    for cp, name in first["cmap"].items():
        cat = unicodedata.category(chr(cp))
        if cat in ("Ll", "Lu", "Lt", "Nd"):
            kinds[name] = "lc" if cat == "Ll" else "uc"
    drawn = [n for n in kinds if n not in first["components"]]
    depth = DEPTH * xheight
    zones = {"lc": (0, xheight), "uc": (0, cap)}

    def white(glyphs, name):
        """Optical space on the left and right of a drawn glyph (sidebearing plus the white inside it), and
        whether a part outside the zone (the hook of j or ſ, the bar of ł đ ħ ...) reaches the measured depth."""
        lines = _polylines(glyphs[name][1].contours)
        lo, hi = zones[kinds[name]]
        rows = [_extent(lines, lo + (hi - lo) * (k + 0.5) / STEPS) for k in range(STEPS)]
        ink = [r for r in rows if r]
        x0, x1 = min(r[0] for r in ink), max(r[1] for r in ink)
        wl = sum(min(r[0] - x0, depth) if r else depth for r in rows) / STEPS
        wr = sum(min(x1 - r[1], depth) if r else depth for r in rows) / STEPS
        out = [r for y in range(-400, 1100, 10) if not lo <= y <= hi for r in [_extent(lines, y)] if r]
        return (x0 + wl, glyphs[name][0] - x1 + wr,
                any(r[0] < x0 + depth for r in out), any(r[1] > x1 - depth for r in out))

    measured = [{n: white(b["glyphs"], n) for n in drawn + ["n", "H"]} for b in builds]
    # a side with a part outside the zone near its edge, in any master, keeps its sidebearing: it was drawn
    # with that part in mind
    keep = {n: (any(m[n][2] for m in measured), any(m[n][3] for m in measured)) for n in drawn}
    for build, m in zip(builds, measured):
        glyphs, comps, anchors = build["glyphs"], build["components"], build["anchors"]
        ref = {"lc": m["n"], "uc": m["H"]}
        shift = {}                                             # glyph -> (change on the left, on the right)
        for name in drawn:
            (l, r, _, _), (rl, rr, _, _) = m[name], ref[kinds[name]]
            shift[name] = (0 if keep[name][0] else rl - l, 0 if keep[name][1] else rr - r)
        for name in kinds:
            if name in comps and comps[name][0][0] in shift:  # accented letters follow their base
                shift[name] = shift[comps[name][0][0]]
        shift["iogonek.dotless"] = shift["dotlessi"]
        for name, (dl, dr) in shift.items():
            adv, outline = glyphs[name]
            glyphs[name] = (round(adv + dl + dr), outline.transform(1, 0, 0, 1, dl, 0))
            if name in anchors:
                anchors[name] = [(a, x + dl, y) for a, x, y in anchors[name]]
        # components keep their place in their composite: a moved base moves back, marks follow the composite
        for name, cs in comps.items():
            own = shift.get(name, (0, 0))[0]
            comps[name] = [(c, x + own - shift.get(c, (0, 0))[0], y) for c, x, y in cs]


def _extent(lines, y):
    y += 0.01                                                  # never exactly on a point
    xs = [p[0] + (y - p[1]) * (q[0] - p[0]) / (q[1] - p[1])
          for c in lines for p, q in zip(c, c[1:] + c[:1]) if (p[1] - y) * (q[1] - y) < 0]
    return (min(xs), max(xs)) if xs else None


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
