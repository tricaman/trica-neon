"""Trica Neon -- outline geometry.

Glyphs are drawn as centerline skeletons and stroked here. The stroker is analytic:
straight segments are offset as straight lines and every rounded vertex as the same
cubic construction around the offset corner. Each vertex gives one line and one curve
on each side whatever happens there (fillet, miter, bevel, inner corner), so a glyph
has the same points, in the same order, at every stroke width and the weights
interpolate; make_sources.py then drops the curves that are degenerate or straight in
every weight. Strokes are not merged: overlapping contours stay separate (the nonzero
fill rule draws their union) and the overlaps are removed when the static fonts are built.

Only + - * / and sqrt are used, so the output is identical on every platform.
"""
import math

K = 0.5523                      # cubic approximation of a quarter circle
SQUARE, BUTT = "square", "butt"
MITER_LIMIT = 4                 # sharper corners get a bevel, as with the Skia stroker used before
_BEVEL_BELOW = 2 / MITER_LIMIT ** 2 - 1      # cosine of the turn angle where the limit is reached


class Outline:
    """Closed contours, each a (start, segments) pair. A segment is ("line", p) or
    ("curve", c1, c2, p); the last segment of a contour ends at its start point."""

    def __init__(self, contours=()):
        self.contours = list(contours)

    def transform(self, a=1, b=0, c=0, d=1, e=0, f=0):
        """Same arguments as pathops.Path.transform: x' = a*x + c*y + e, y' = b*x + d*y + f."""
        def tp(p):
            return (a * p[0] + c * p[1] + e, b * p[0] + d * p[1] + f)
        out = [(tp(s), [(g[0],) + tuple(tp(p) for p in g[1:]) for g in segs]) for s, segs in self.contours]
        return Outline(out if a * d - b * c > 0 else [_reverse(*k) for k in out])   # a mirror flips direction


class Centerline:
    """A skeleton polyline: its points, the fillet radius used at each vertex, closed or not."""

    def __init__(self, points, fillets, closed):
        self.points, self.fillets, self.closed = points, fillets, closed


def union(*outlines):
    """Overlapping contours are kept: the nonzero fill rule already draws their union."""
    return Outline([k for o in outlines for k in o.contours])


def circle(cx, cy, rad):
    k = K * rad
    s = (cx + rad, cy)
    return Outline([(s, [("curve", (cx + rad, cy + k), (cx + k, cy + rad), (cx, cy + rad)),
                         ("curve", (cx - k, cy + rad), (cx - rad, cy + k), (cx - rad, cy)),
                         ("curve", (cx - rad, cy - k), (cx - k, cy - rad), (cx, cy - rad)),
                         ("curve", (cx + k, cy - rad), (cx + rad, cy - k), s)])])


def rounded(points, radii=None, closed=False):
    """Polyline -> centerline; radii[i] rounds vertex i with a quarter-circle-like arc.
    A radius may use the whole segment when the neighbour is a free end, half otherwise."""
    n = len(points)
    radii = radii or [0] * n
    fillets = []
    for i, P in enumerate(points):
        rr = 0
        if radii[i] and (closed or 0 < i < n - 1):
            A, C = points[i - 1], points[(i + 1) % n]
            da, dc = _dist(P, A), _dist(P, C)
            lim_a = da if (not closed and i - 1 == 0) else da / 2
            lim_c = dc if (not closed and i + 1 == n - 1) else dc / 2
            rr = min(radii[i], lim_a, lim_c)
        fillets.append(rr)
    return Centerline(list(points), fillets, closed)


def stroke(center, cap, width):
    """Outline of a centerline stroked at `width`, with miter joins (bevels past MITER_LIMIT)
    and square or butt caps: one contour for an open line, outer and inner for a closed one."""
    pts, fil, closed = center.points, center.fillets, center.closed
    n = len(pts)
    dirs = [_unit(pts[j], pts[(j + 1) % n]) for j in range(n if closed else n - 1)]
    lens = [_dist(pts[j], pts[(j + 1) % n]) for j in range(len(dirs))]
    vertices = range(n) if closed else range(1, n - 1)
    hw = width / 2

    def side(dl):
        """Segments along the side at signed distance dl (left positive): a line and a curve per vertex."""
        turn = {}
        for i in vertices:
            u, v = dirs[i - 1], dirs[i]
            cr, dt = u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1]
            turn[i] = (dt, dl * cr / (1 + dt))     # q: distance of the offset corner from the vertex along
                                                   # both segments, positive on the inner side of the turn

        def room(i):
            """Length of each neighbouring segment this side uses up at vertex i."""
            if i not in turn:
                return 0                           # free end
            q = turn[i][1]
            return fil[i] if fil[i] > q else max(q, 0)

        segs = []
        for i in vertices:
            P, rr, u, v = pts[i], fil[i], dirs[i - 1], dirs[i]
            dt, q = turn[i]
            m = dl / (1 + dt)
            Q = (P[0] - m * (u[1] + v[1]), P[1] + m * (u[0] + v[0]))      # where the two offset sides meet
            A, B = (P[0] - u[1] * dl, P[1] + u[0] * dl), (P[0] - v[1] * dl, P[1] + v[0] * dl)
            if rr and rr > q:                                              # fillet: offset arc of radius rr - q
                ro = rr - q
                a, b, k = (Q[0] - u[0] * ro, Q[1] - u[1] * ro), (Q[0] + v[0] * ro, Q[1] + v[1] * ro), K * ro
                segs += [("line", a), ("curve", (a[0] + u[0] * k, a[1] + u[1] * k), (b[0] - v[0] * k, b[1] - v[1] * k), b)]
            elif q > 0 and (q + room((i - 1) % n) > lens[i - 1] or q + room((i + 1) % n) > lens[i]):
                segs += [("line", A), ("curve", P, P, B)]                  # no room for the inner corner: turn
                                                                           # through the vertex, like Skia
            elif q < 0 and not rr and dt < _BEVEL_BELOW:                   # outer corner past the miter limit
                segs += [("line", A), ("curve", A, B, B)]
            else:                                                          # miter, or sharp inner corner
                segs += [("line", Q), ("curve", Q, Q, Q)]
        return segs

    def ends(P, d, ext):
        """Left and right corners of a cap at P, pushed `ext` along the direction d."""
        b = (P[0] + d[0] * ext, P[1] + d[1] * ext)
        return (b[0] - d[1] * hw, b[1] + d[0] * hw), (b[0] + d[1] * hw, b[1] - d[0] * hw)

    if closed:
        loops = sorted(((s[-1][-1], s) for s in (side(hw), side(-hw))), key=lambda k: -abs(_area(*k)))
        return Outline([k if (_area(*k) > 0) == (j == 0) else _reverse(*k) for j, k in enumerate(loops)])
    ext = hw if cap == SQUARE else 0
    sl, sr = ends(pts[0], dirs[0], -ext)
    el, er = ends(pts[-1], dirs[-1], ext)
    _, back = _reverse(sr, side(-hw) + [("line", er)])
    k = (sl, side(hw) + [("line", el), ("line", er)] + back + [("line", sl)])
    return Outline([k if _area(*k) > 0 else _reverse(*k)])


def clip(outline, x0, y0, x1, y1):
    """Polygonal contours cut to the box x0..x1, y0..y1 (Sutherland-Hodgman)."""
    out = []
    for start, segs in outline.contours:
        poly, cur = [], start
        for g in segs:                     # lines, and curves with their handles on their end points
            assert g[0] == "line" or (g[1] == cur and g[2] == g[3]), "clip() takes straight segments only"
            poly.append(g[-1])
            cur = g[-1]
        for axis, lim, sgn in ((0, x0, 1), (0, x1, -1), (1, y0, 1), (1, y1, -1)):
            res = []
            for p, q in zip(poly[-1:] + poly[:-1], poly):                   # edge p -> q
                pin, qin = (p[axis] - lim) * sgn >= 0, (q[axis] - lim) * sgn >= 0
                if pin != qin:
                    t = (lim - p[axis]) / (q[axis] - p[axis])
                    x, y = p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])
                    res.append((lim, y) if axis == 0 else (x, lim))
                if qin:
                    res.append(q)
            poly = res
        out.append((poly[-1], [("line", p) for p in poly]))
    return Outline(out)


def _dist(a, b):
    return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)


def _unit(a, b):
    d = _dist(a, b)
    return ((b[0] - a[0]) / d, (b[1] - a[1]) / d)


def _reverse(start, segs):
    """The same path walked backwards: (its end point, the reversed segments)."""
    pts = [start] + [g[-1] for g in segs]
    return pts[-1], [("line", pts[i]) if g[0] == "line" else ("curve", g[2], g[1], pts[i])
                     for i, g in reversed(list(enumerate(segs)))]


def _area(start, segs):
    """Signed area, positive when counter-clockwise (curves flattened)."""
    pts, cur = [], start
    for g in segs:
        if g[0] == "curve":
            pts += [_bezier(cur, g[1], g[2], g[3], t) for t in (0.25, 0.5, 0.75)]
        pts.append(g[-1])
        cur = g[-1]
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1])) / 2


def _bezier(p0, p1, p2, p3, t):
    s = 1 - t
    return tuple(s ** 3 * a + 3 * s * s * t * b + 3 * s * t * t * c + t ** 3 * d for a, b, c, d in zip(p0, p1, p2, p3))
