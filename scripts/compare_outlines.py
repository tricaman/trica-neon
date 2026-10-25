"""Compare two fonts glyph by glyph, matched by codepoint (unencoded glyphs by name).
Overlaps are merged first, then the largest distance between the two outlines is measured.
usage: python -I compare_outlines.py <reference font> <font> [<tolerance in units, default 1>]"""
import sys
import pathops
from fontTools.pens.basePen import decomposeQuadraticSegment
from fontTools.ttLib import TTFont

STEPS = 48          # points per curve when flattening: under 0.05 units of error on these curves
CELL = 8            # grid cell for the nearest-segment search, in font units


def polylines(glyphset, name):
    path = pathops.Path()
    glyphset[name].draw(path.getPen(glyphSet=glyphset))        # the glyph set resolves components
    return path_polylines(pathops.simplify(path))


def path_polylines(path):
    """Flatten a pathops path into closed polylines."""
    out, cur = [], None
    for verb, pts in path.segments:
        if verb == "moveTo":
            cur = pts[0]; out.append([cur])
        elif verb == "lineTo":
            cur = pts[0]; out[-1].append(cur)
        elif verb == "curveTo":
            p0, (p1, p2, p3) = cur, pts
            out[-1] += [_cubic(p0, p1, p2, p3, i / STEPS) for i in range(1, STEPS + 1)]; cur = p3
        elif verb == "qCurveTo":
            if pts[-1] is None:                    # TrueType contour made only of off-curve points
                offs = pts[:-1]
                cur = tuple((a + b) / 2 for a, b in zip(offs[-1], offs[0]))
                out.append([cur])
                pts = offs + (cur,)
            for c, p in decomposeQuadraticSegment(pts):
                out[-1] += [_quad(cur, c, p, i / STEPS) for i in range(1, STEPS + 1)]; cur = p
        elif verb == "closePath" and out[-1][-1] != out[-1][0]:
            out[-1].append(out[-1][0])
    return out


def _cubic(p0, p1, p2, p3, t):
    s = 1 - t
    return tuple(s ** 3 * a + 3 * s * s * t * b + 3 * s * t * t * c + t ** 3 * d for a, b, c, d in zip(p0, p1, p2, p3))


def _quad(p0, p1, p2, t):
    s = 1 - t
    return tuple(s * s * a + 2 * s * t * b + t * t * c for a, b, c in zip(p0, p1, p2))


def _seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    ll = dx * dx + dy * dy
    t = 0 if ll == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / ll))
    return ((p[0] - a[0] - t * dx) ** 2 + (p[1] - a[1] - t * dy) ** 2) ** 0.5


def farthest(lines_a, lines_b):
    """Largest distance from a point of outline A to outline B."""
    segs = [(q[i], q[i + 1]) for q in lines_b for i in range(len(q) - 1)]
    grid = {}
    for k, (a, b) in enumerate(segs):
        for i in range(int(min(a[0], b[0]) // CELL), int(max(a[0], b[0]) // CELL) + 1):
            for j in range(int(min(a[1], b[1]) // CELL), int(max(a[1], b[1]) // CELL) + 1):
                grid.setdefault((i, j), []).append(k)
    worst = 0
    for p in (p for q in lines_a for p in q):
        cx, cy, best = int(p[0] // CELL), int(p[1] // CELL), float("inf")
        for ring in range(1000):
            for i in range(cx - ring, cx + ring + 1):
                for j in range(cy - ring, cy + ring + 1):
                    if max(abs(i - cx), abs(j - cy)) == ring:
                        for k in grid.get((i, j), ()):
                            best = min(best, _seg_dist(p, *segs[k]))
            if best <= ring * CELL:      # segments in the outer rings are at least ring * CELL away
                break
        worst = max(worst, best)
    return worst


def main():
    ref, new = TTFont(sys.argv[1]), TTFont(sys.argv[2])
    tolerance = float(sys.argv[3]) if len(sys.argv) > 3 else 1
    rmap, nmap = ref.getBestCmap(), new.getBestCmap()
    pairs = {(rmap[cp], nmap[cp]) for cp in rmap.keys() & nmap.keys()}
    unencoded = (set(ref.getGlyphOrder()) - set(rmap.values())) & (set(new.getGlyphOrder()) - set(nmap.values()))
    pairs |= {(n, n) for n in unencoded}
    missing = sorted(rmap.keys() ^ nmap.keys())
    rgs, ngs = ref.getGlyphSet(), new.getGlyphSet()
    widths = [f"{a}/{b} {rgs[a].width}->{ngs[b].width}" for a, b in sorted(pairs) if rgs[a].width != ngs[b].width]
    dist = {}
    for a, b in sorted(pairs):
        la, lb = polylines(rgs, a), polylines(ngs, b)
        dist[b] = 0 if not la and not lb else float("inf") if not la or not lb else max(farthest(la, lb), farthest(lb, la))
    worst = sorted(dist.items(), key=lambda kv: -kv[1])
    print(f"glyphs compared: {len(pairs)}; codepoints in only one font: {[f'U+{cp:04X}' for cp in missing] or 'none'}")
    print(f"advance differences: {widths or 'none'}")
    print("largest distances:", ", ".join(f"{n} {d:.2f}" for n, d in worst[:8]))
    over = [f"{n} {d:.2f}" for n, d in worst if d > tolerance]
    print(f"over {tolerance} units: {over or 'none'}")
    sys.exit(1 if over or widths or missing else 0)


if __name__ == "__main__":
    main()
