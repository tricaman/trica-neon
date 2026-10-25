"""Trica Neon — modular font generator.

Design rules:
  * every wide letter lives in an l x l square (l = cap height)
  * stroke = l/20 in the Light weight, letter spacing = l/4
  * the base module is the "pill" of the P: width l, height l/2, fully round ends
  * curves are always semicircles of the pill, or quarters of it:
    centerline radius r = (l/2 - stroke/2) / 2

Every glyph is a set of centerline skeletons (polylines with rounded vertices)
stroked at one weight, so changing the stroke regenerates a coherent family.
make_sources.py calls build_glyphs() once per weight and writes the UFO masters.
"""
import math
import geometry
from geometry import BUTT, SQUARE, Outline, circle, clip, rounded, union

UPM = 1000
H = 700                       # cap height = module side l
SB = H / 8                    # sidebearing -> gap between letters = l/4
XH = round(H * 0.72)          # x-height

GLYPHS = {}         # glyph name -> (width, outline)
SKEL = {}           # glyph name -> (width, parts): skeletons, reused to build small figures
CHARS = {}          # glyph name -> characters it serves (filled by the builders below)
COMPONENTS = {}     # composite glyph name -> [(component glyph, x offset, y offset)]
ANCHORS = {}        # glyph name -> [(anchor name, x, y)]
MARKS = set()       # combining marks (zero-width glyphs)


def setup(stroke):
    """Set the stroke width S and everything derived from it, and empty the glyph tables."""
    global S, h, r, T, MI, BT, XT, XM, DB
    S = stroke
    h = S / 2
    r = (H / 2 - h) / 2           # radius of the pill ends (half-height semicircle)
    T, MI, BT = H - h, H / 2, h   # centerline top / middle / bottom
    XT = XH - h                   # centerline top of lowercase
    XM = XH / 2                   # centerline middle of lowercase
    DB = -round(H * 0.28) + h     # centerline bottom of descenders
    for table in (GLYPHS, SKEL, CHARS, COMPONENTS, ANCHORS, MARKS):
        table.clear()


def stroke(path, cap=SQUARE, width=None):
    return geometry.stroke(path, cap, width or S)


def glyph(name, width, parts=(), extra=()):
    SKEL[name] = (width, list(parts))
    strokes = []
    for part in parts:
        pts, rad, closed = (part + (None, False))[:3] if len(part) < 3 else part
        strokes.append(stroke(rounded(pts, rad, closed)))
    GLYPHS[name] = (width, union(*strokes, *extra))


def pill(L, R, y0, y1):            # stadium between two horizontal centerlines
    return ([(L, y1), (R, y1), (R, y0), (L, y0)], [r, r, r, r], True)


def build():
    W = H; L, R, C = h, W - h, W / 2
    q = 2 * r                          # big radius: semicircle spanning the full width

    # -------- letters --------------------------------------------------------------
    top = pill(L, R, MI, T); bot = pill(L, R, BT, MI)
    # A, B: outer corners rounded with r, inner joints sharp (as in the ABEF sketch)
    glyph("A", W, [([(L, BT), (L, T), (R, T), (R, BT)], [0, r, r, 0]), ([(L, MI), (R, MI)],)])
    glyph("B", W, [([(L, BT), (L, T)],),
                   ([(L, T), (R, T), (R, MI), (L, MI)], [0, r, r, 0], True),
                   ([(L, MI), (R, MI), (R, BT), (L, BT)], [0, r, r, 0], True)])
    glyph("C", W, [([(R, T), (L, T), (L, BT), (R, BT)], [0, r, r, 0])])
    glyph("D", W, [([(L, T), (R, T), (R, BT), (L, BT)], [0, r, r, 0], True)])
    glyph("E", W, [([(R, T), (L, T), (L, BT), (R, BT)], [0, r, r, 0]), ([(L, MI), (R, MI)],)])
    glyph("F", W, [([(R, T), (L, T), (L, BT)], [0, r, 0]), ([(L, MI), (R, MI)],)])
    glyph("G", W, [([(R, T), (L, T), (L, BT), (R, BT), (R, MI), (C, MI)], [0, r, r, r, 0, 0])])
    glyph("H", W, [([(L, BT), (L, T)],), ([(R, BT), (R, T)],), ([(L, MI), (R, MI)],)])  # plain, no fillets
    glyph("I", S, [([(h, BT), (h, T)],)])
    glyph("J", W, [([(R, T), (R, BT), (L, BT), (L, MI)], [0, r, r, 0])])
    # strokes that would run along the same edge start inside the stroke already drawn
    # there (same outline, no duplicated path segments in the variable font)
    glyph("K", W, [([(L, BT), (L, T)],),
                   ([(L, MI), (R, MI), (R, T)], [0, r, 0]),
                   ([(R - r, MI), (R, MI), (R, BT)], [0, r, 0])])
    glyph("L", W, [([(L, T), (L, BT), (R, BT)], [0, r, 0])])
    glyph("M", W, [([(L, BT), (L, T), (C, T), (C, BT)], [0, r, r, 0]),
                   ([(C, T - r), (C, T), (R, T), (R, BT)], [0, r, r, 0])])
    glyph("N", W, [([(L, BT), (L, T), (R, T), (R, BT)], [0, r, r, 0])])
    glyph("O", W, [([(L, T), (R, T), (R, BT), (L, BT)], [r, r, r, r], True)])
    glyph("P", W, [([(L, BT), (L, T)],), ([(L, T), (R, T), (R, MI), (L, MI)], [0, r, r, 0], True)])      # sharp where the bowl meets the stem
    # Q: the O with a short diagonal mark crossing the bottom stroke
    qtail = stroke(rounded([(W * 0.60, H * 0.20), (W * 0.84, -H * 0.13)]), BUTT)
    glyph("Q", W, [([(L, T), (R, T), (R, BT), (L, BT)], [r, r, r, r], True)], extra=[qtail])
    glyph("R", W, [([(L, BT), (L, T)],), ([(L, T), (R, T), (R, MI), (L, MI)], [0, r, r, 0], True), ([(R - r, MI), (R, MI), (R, BT)], [0, r, 0])])
    glyph("S", W, [([(R, T), (L, T), (L, MI), (R, MI), (R, BT), (L, BT)], [0, r, r, r, r, 0])])
    glyph("T", W, [([(L, T), (R, T)],), ([(C, T), (C, BT)],)])
    glyph("U", W, [([(L, T), (L, BT), (R, BT), (R, T)], [0, r, r, 0])])
    # V: hard straight diagonals like the Z (temporary), clipped flush to the module box
    vpath = stroke(rounded([(L, T + 2 * S), (C, BT - S * 0.6), (R, T + 2 * S)]))
    glyph("V", W, extra=[clip(vpath, 0, 0, W, H)])
    glyph("W", W, [([(L, T), (L, BT), (C, BT), (C, T)], [0, r, r, 0]),
                   ([(C, BT + r), (C, BT), (R, BT), (R, T)], [0, r, r, 0])])
    xpath = union(stroke(rounded([(L, T + 2 * S), (R, BT - 2 * S)])), stroke(rounded([(L, BT - 2 * S), (R, T + 2 * S)])))
    glyph("X", W, extra=[clip(xpath, 0, 0, W, H)])   # standard X
    glyph("Y", W, [([(L, T), (L, MI), (R, MI), (R, T)], [0, r, r, 0]), ([(C, MI), (C, BT)],)])
    glyph("Z", W, [([(L, T), (R, T), (L, BT), (R, BT)],)])                           # standard Z

    # -------- digits (narrower box, same radii) -------------------------------------
    Wd = H * 0.8; L2, R2, C2 = h, Wd - h, Wd / 2
    glyph("zero", Wd, [([(L2, T), (R2, T), (R2, BT), (L2, BT)], [r, r, r, r], True)])
    # 1 and 7 are open on the left: the flag of the 1 reaches o1 units into the left sidebearing,
    # the bar of the 7 all of it
    Wone, o1, o7 = H * 0.4, 50, SB
    glyph("one", Wone - o1, [([(h - o1, T), (Wone - h - o1, T), (Wone - h - o1, BT)],)])
    glyph("two", Wd, [([(L2, T), (R2, T), (R2, MI), (L2, MI), (L2, BT), (R2, BT)], [0, r, r, r, 0, 0])])
    glyph("three", Wd, [([(L2, T), (R2, T), (R2, MI), (L2, MI)], [0, r, r, 0]),
                        ([(R2 - r, MI), (R2, MI), (R2, BT), (L2, BT)], [0, r, r, 0])])
    glyph("four", Wd, [([(L2, T), (L2, MI), (R2, MI)], [0, r, 0]), ([(R2, T), (R2, BT)],)])
    glyph("five", Wd, [([(R2, T), (L2, T), (L2, MI), (R2, MI), (R2, BT), (L2, BT)], [0, 0, 0, r, r, 0])])
    glyph("six", Wd, [([(R2, T), (L2, T), (L2, BT), (R2, BT), (R2, MI), (L2, MI)], [0, r, r, r, r, 0])])
    glyph("seven", Wd - o7, [([(L2 - o7, T), (R2 - o7, T), (R2 - o7, BT)], [0, r, 0])])
    glyph("eight", Wd, [pill(L2, R2, MI, T), pill(L2, R2, BT, MI)])
    glyph("nine", Wd, [([(L2, BT), (R2, BT), (R2, T), (L2, T), (L2, MI), (R2, MI)], [0, r, r, r, r, 0])])

    # -------- punctuation ---------------------------------------------------------------
    d = max(min(S * 1.6, S + 42), 48)  # dot diameter: 1.6 times the stroke up to the Regular, then it grows with it
    dot = lambda cx, cy: circle(cx, cy, d / 2)
    glyph("period", d, extra=[dot(d / 2, d / 2)])
    glyph("comma", d, [([(d / 2, d / 2), (d / 2, -d * 1.6)],)], extra=[dot(d / 2, d / 2)])
    y_colon = XH - d / 2                       # upper dot of : and ; at the x-height
    glyph("colon", d, extra=[dot(d / 2, d / 2), dot(d / 2, y_colon)])
    glyph("exclam", S, [([(h, d * 2.2), (h, T)],)], extra=[dot(h, d / 2)])     # spaced on the stem, as the i
    glyph("quotesingle", S, [([(h, T - 2 * r), (h, T)],)])
    glyph("hyphen", W / 2, [([(h, MI), (W / 2 - h, MI)],)])
    Wq = Wd
    glyph("question", Wq, [([(L2, MI), (L2, T), (R2, T), (R2, MI), (C2, MI), (C2, min(d * 2.2, MI - h))],
                            [0, r, r, r, 0, 0])], extra=[dot(C2, d / 2)])
    glyph("slash", W / 2, [([(h, BT), (W / 2 - h, T)],)])
    GLYPHS["space"] = (350 - 2 * SB, Outline())     # word space: 350 units

    build_symbols(d, dot)
    build_lowercase(d, dot)
    build_accents(d)
    build_extended(d, dot)


def reg(name, chars):
    CHARS[name] = CHARS.get(name, "") + chars


def ln(*pts, cap=SQUARE, radii=None, closed=False):
    """stroked polyline (helper for symbols)"""
    return stroke(rounded(list(pts), radii, closed), cap)


def put(name, width, *paths, chars=""):
    GLYPHS[name] = (width, union(*paths))
    if chars:
        reg(name, chars)


def build_symbols(d, dot):
    W = H; Wn = H * 0.4                   # narrow box for brackets
    rs = r * 0.5                           # small radius for small shapes
    top_q, bot_q = T, T - 2 * r            # vertical span used by quote marks

    # fix: shorter comma tail
    put("comma", d, dot(d / 2, d / 2), ln((d / 2, d / 2), (d / 2, -d * 1.1), cap=BUTT))
    y_colon = XH - d / 2                       # upper dot, as in the colon
    put("semicolon", d, dot(d / 2, y_colon), dot(d / 2, d / 2), ln((d / 2, d / 2), (d / 2, -d * 1.1), cap=BUTT))
    put("quotedbl", S * 3, ln((h, bot_q), (h, top_q)), ln((S * 3 - h, bot_q), (S * 3 - h, top_q)))
    # typographic quotes: the comma (a dot with a tail), raised to the cap height; ' and " stay straight
    qr = lambda x: union(dot(x + d / 2, H - d / 2), ln((x + d / 2, H - d / 2), (x + d / 2, H - d * 2.1), cap=BUTT))
    ql = lambda x: union(dot(x + d / 2, H - d * 1.6), ln((x + d / 2, H - d * 1.6), (x + d / 2, H), cap=BUTT))
    put("quoteright", d, qr(0))
    put("quoteleft", d, ql(0))
    put("quotedblright", d * 2.5, qr(0), qr(d * 1.5))
    put("quotedblleft", d * 2.5, ql(0), ql(d * 1.5))
    put("grave", 200, ln((40, H + 200), (160, H + 90), cap=BUTT))

    # brackets: same rule as the rest -- outer corners rounded for (), sharp for []
    yb, yt = -H * 0.12 + h, H * 1.0 - h
    put("parenleft", Wn, ln((Wn - h, yt), (h, yt), (h, yb), (Wn - h, yb), radii=[0, Wn, Wn, 0]))
    put("parenright", Wn, ln((h, yt), (Wn - h, yt), (Wn - h, yb), (h, yb), radii=[0, Wn, Wn, 0]))
    put("bracketleft", Wn, ln((Wn - h, yt), (h, yt), (h, yb), (Wn - h, yb)))
    put("bracketright", Wn, ln((h, yt), (Wn - h, yt), (Wn - h, yb), (h, yb)))
    cy = (yt + yb) / 2; nib = Wn * 0.35
    put("braceleft", Wn, ln((Wn - h, yt), (nib, yt), (nib, yb), (Wn - h, yb), radii=[0, rs, rs, 0]),
        ln((h, cy), (nib, cy)))
    put("braceright", Wn, ln((h, yt), (Wn - nib, yt), (Wn - nib, yb), (h, yb), radii=[0, rs, rs, 0]),
        ln((Wn - nib, cy), (Wn - h, cy)))
    put("bar", S, ln((h, yb), (h, yt)))
    put("backslash", W / 2, ln((h, T), (W / 2 - h, BT)))
    put("underscore", W * 0.8, ln((h, -H * 0.12), (W * 0.8 - h, -H * 0.12)))

    # math, same width as the digits
    Wm = H * 0.8; cx = Wm / 2; a = Wm * 0.36; my = MI
    put("plus", Wm, ln((cx - a, my), (cx + a, my)), ln((cx, my - a), (cx, my + a)))
    put("minus", Wm, ln((cx - a, my), (cx + a, my)))
    put("equal", Wm, ln((cx - a, my + a * 0.45), (cx + a, my + a * 0.45)), ln((cx - a, my - a * 0.45), (cx + a, my - a * 0.45)))
    put("less", Wm, ln((cx + a, my + a), (cx - a, my), (cx + a, my - a)))
    put("greater", Wm, ln((cx - a, my + a), (cx + a, my), (cx - a, my - a)))
    k = a * 0.75
    put("multiply", Wm, ln((cx - k, my - k), (cx + k, my + k)), ln((cx - k, my + k), (cx + k, my - k)))
    dy = max(a * 0.75, h + d / 2 + H * 0.066)          # the dots never touch the bar
    put("divide", Wm, ln((cx - a, my), (cx + a, my)), dot(cx, my + dy), dot(cx, my - dy))
    put("asciicircum", Wm, ln((cx - a, T - a * 1.1), (cx, T), (cx + a, T - a * 1.1)))
    tw = a * 0.66
    put("asciitilde", Wm, ln((cx - a, my - tw / 2), (cx - a, my + tw / 2), (cx, my + tw / 2), (cx, my - tw / 2),
                             (cx + a, my - tw / 2), (cx + a, my + tw / 2), radii=[0, rs * 0.6, rs * 0.6, rs * 0.6, rs * 0.6, 0]))
    ay = T - a * 0.9
    put("asterisk", Wm, ln((cx, ay - a * 0.8), (cx, ay + a * 0.8)),
        ln((cx - a * 0.7, ay - a * 0.4), (cx + a * 0.7, ay + a * 0.4)),
        ln((cx - a * 0.7, ay + a * 0.4), (cx + a * 0.7, ay - a * 0.4)))

    # dashes and dots
    put("endash", W * 0.6, ln((h, MI), (W * 0.6 - h, MI)))
    put("emdash", W * 1.1, ln((h, MI), (W * 1.1 - h, MI)))
    put("periodcentered", d, dot(d / 2, MI))
    put("bullet", d * 2, circle(d, MI, d))
    put("ellipsis", d * 5, dot(d / 2, d / 2), dot(d * 2.5, d / 2), dot(d * 4.5, d / 2))
    put("exclamdown", S, ln((h, H - d * 2.2), (h, BT)), dot(h, H - d / 2))

    # degree, guillemets
    ds = H * 0.32
    put("degree", ds, ln((h, T), (ds - h, T), (ds - h, T - ds + S), (h, T - ds + S), radii=[rs * 0.6] * 4, closed=True))
    g = a * 0.6; gx = g * 1.1
    put("guilsinglleft", gx * 1.2, ln((gx, my + g), (h, my), (gx, my - g)))
    put("guilsinglright", gx * 1.2, ln((h, my + g), (gx, my), (h, my - g)))
    # the second chevron keeps a clear gap of at least 0.3 S from the first
    tip = max(gx * 1.1, h + S * math.hypot(g, gx - h) / g + S * 0.3)
    put("guillemotleft", tip + gx * 1.3, ln((gx, my + g), (h, my), (gx, my - g)), ln((tip + gx, my + g), (tip, my), (tip + gx, my - g)))
    put("guillemotright", tip + gx * 1.3, ln((h, my + g), (gx, my), (h, my - g)), ln((tip, my + g), (tip + gx, my), (tip, my - g)))

    # # % & @ $ euro
    put("numbersign", Wm, ln((Wm * 0.33, BT + 60), (Wm * 0.33, T - 60), cap=BUTT), ln((Wm * 0.67, BT + 60), (Wm * 0.67, T - 60), cap=BUTT),
        ln((h, H * 0.34), (Wm - h, H * 0.34)), ln((h, H * 0.66), (Wm - h, H * 0.66)))
    pc = H * 0.3
    put("percent", W, ln((h, T), (pc, T), (pc, T - pc), (h, T - pc), radii=[rs * 0.6] * 4, closed=True),
        ln((W - pc, BT + pc), (W - h, BT + pc), (W - h, BT), (W - pc, BT), radii=[rs * 0.6] * 4, closed=True),
        ln((W * 0.2, BT), (W * 0.8, T)))
    Sw = GLYPHS["S"][1]
    put("dollar", W, Sw, ln((W / 2, -H * 0.1), (W / 2, H * 1.1), cap=BUTT))
    ew = W
    put("Euro", ew, ln((ew - h, T), (h + 80, T), (h + 80, BT), (ew - h, BT), radii=[0, r, r, 0]),
        ln((h, MI + 90), (ew * 0.7, MI + 90)), ln((h, MI - 90), (ew * 0.7, MI - 90)))
    # & : the top pill of the 8; below it a bowl whose right side rises into a short tail, crossed by
    # a straight leg that runs from the pill to the bottom right, trimmed flush with the baseline as in V
    bw = H * 0.8; Rb = bw - h; e = r * 0.6
    put("ampersand", bw + e,
        stroke(rounded([(h, MI), (Rb, MI), (Rb, T), (h, T)], [r, r, r, r], True)),      # top pill
        ln((h + r, MI), (h, MI), (h, BT), (Rb, BT), (Rb, MI * 0.62), radii=[0, r, r, r, 0]),   # bowl and tail
        clip(ln((Rb - r, MI + S), (bw + e * 0.75, BT - S * 0.6)), -H, 0, 2 * H, MI))           # leg
    # @ : the O with a smaller rounded square inside, open at the right
    i0, i1 = W * 0.3, W * 0.7
    put("at", W, ln((W - h, BT + r), (W - h, T), (h, T), (h, BT), (W - h, BT), radii=[0, r, r, r, 0]),
        ln((i1, H * 0.28), (i1, H * 0.66), (i0, H * 0.66), (i0, H * 0.28), (W - h, H * 0.28), radii=[0, rs, rs, rs, 0]))
    put("sterling", W * 0.8, ln((W * 0.8 - h, T), (W * 0.25 + h, T), (W * 0.25 + h, BT), radii=[0, r, 0]),
        ln((h, MI), (W * 0.6, MI)), ln((h, BT), (W * 0.8 - h, BT)))

    # inverted question mark: the ? rotated 180 degrees
    qw, qp = GLYPHS["question"]
    q = qp.transform(-1, 0, 0, -1, qw, H)
    GLYPHS["questiondown"] = (qw, q)

    for n, c in {"semicolon": ";", "quotedbl": '"', "quoteleft": "\u2018", "quotedblleft": "\u201c", "quoteright": "\u2019", "quotedblright": "\u201d",
                 "grave": "`", "parenleft": "(", "parenright": ")", "bracketleft": "[", "bracketright": "]",
                 "braceleft": "{", "braceright": "}", "bar": "|\u00a6", "backslash": "\\", "underscore": "_",
                 "plus": "+", "minus": "\u2212", "equal": "=", "less": "<", "greater": ">", "multiply": "\u00d7",
                 "divide": "\u00f7", "asciicircum": "^", "asciitilde": "~", "asterisk": "*", "endash": "\u2013",
                 "emdash": "\u2014", "periodcentered": "\u00b7", "bullet": "\u2022", "ellipsis": "\u2026", "exclamdown": "\u00a1",
                 "questiondown": "\u00bf", "degree": "\u00b0", "guilsinglleft": "\u2039", "guilsinglright": "\u203a",
                 "guillemotleft": "\u00ab", "guillemotright": "\u00bb", "numbersign": "#", "percent": "%",
                 "dollar": "$", "Euro": "\u20ac", "ampersand": "&", "at": "@", "sterling": "\u00a3"}.items():
        reg(n, c)


def CHARS_ALL():
    return set("".join(CHARS.values()))


def build_extended(d, dot):
    """Latin-1 + Latin Extended-A + punctuation, currency, arrows, math (see extended.py)."""
    import importlib, os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    ext = importlib.import_module("extended")
    ext.install(sys.modules[__name__], d, dot)


def build_accents(d):
    """Ø ø: the O with a slash. The accented letters are composed in extended.py."""
    ow, op_ = GLYPHS["O"]
    GLYPHS["Oslash"] = (ow, union(op_, ln((h, BT - 40), (ow - h, T + 40), cap=BUTT))); reg("Oslash", "\u00d8")
    lw, lp = GLYPHS["o"]
    GLYPHS["oslash"] = (lw, union(lp, ln((h, BT - 40), (lw - h, XT + 40), cap=BUTT))); reg("oslash", "\u00f8")


def build_lowercase(d, dot):
    """Lowercase on the same rules as the caps: stroke S, radius r, outer corners rounded,
    inner joints sharp. x-height 0.72 l, ascenders at cap height, descenders 0.28 l."""
    w = H * 0.8; L, R, C = h, w - h, w / 2
    AT = T
    idot = lambda cx: dot(cx, XH + min(d * 0.6, H * 0.12) + d / 2)

    bowl_r = ([(L, XT), (R, XT), (R, BT), (L, BT)], [0, r, r, 0], True)     # stem on the left
    bowl_l = ([(L, XT), (R, XT), (R, BT), (L, BT)], [r, 0, 0, r], True)     # stem on the right
    glyph("a", w, [([(R, XT), (L, XT), (L, BT), (R, BT)], [0, r, r, 0]), ([(R, XT), (R, BT)],)])
    glyph("b", w, [([(L, BT), (L, AT)],), bowl_r])
    glyph("c", w, [([(R, XT), (L, XT), (L, BT), (R, BT)], [0, r, r, 0])])
    glyph("d", w, [([(R, BT), (R, AT)],), bowl_l])
    glyph("e", w, [([(R, XM), (R, XT), (L, XT), (L, BT), (R, BT)], [0, r, r, r, 0]), ([(L, XM), (R, XM)],)])
    # f and t: the crossbar reaches fl units into the left sidebearing and fr into the right one
    fl, fr = 50, SB / 2
    wf = w * 0.6; sf = wf * 0.38 - fl
    glyph("f", wf - fl - fr, [([(wf - h - fl, AT), (sf, AT), (sf, BT)], [0, r, 0]), ([(h - fl, XT), (wf - h - fl, XT)],)])
    glyph("g", w, [([(R, XT), (L, XT), (L, BT), (R, BT)], [0, r, r, 0]),
                   ([(R, XT), (R, DB), (L, DB)], [0, r, 0])])
    glyph("h", w, [([(L, BT), (L, AT)],), ([(L, XT), (R, XT), (R, BT)], [0, r, 0])])
    # i is spaced on the stem, as the l: the dot sticks out into the sidebearings
    glyph("dotlessi", S, [([(h, BT), (h, XT)],)])          # base for the accented i
    glyph("i", S, [([(h, BT), (h, XT)],)], extra=[idot(h)])
    # the hook of the j reaches 130 units under the previous letter
    wj = w * 0.45 - 130
    glyph("j", wj, [([(wj - h, XT), (wj - h, DB), (h - 130, DB)], [0, r, 0])], extra=[idot(wj - h)])
    glyph("k", w, [([(L, BT), (L, AT)],), ([(L, XM), (R, XM), (R, XT)], [0, r, 0]),
                   ([(R - r, XM), (R, XM), (R, BT)], [0, r, 0])])
    wl = w * 0.42
    glyph("l", wl, [([(h, AT), (h, BT), (wl - h, BT)], [0, r * 0.6, 0])])
    wm = w * 1.45; Cm = wm / 2
    glyph("m", wm, [([(L, BT), (L, XT), (Cm, XT), (Cm, BT)], [0, r, r, 0]),
                    ([(Cm, XT - r), (Cm, XT), (wm - h, XT), (wm - h, BT)], [0, r, r, 0])])
    glyph("n", w, [([(L, BT), (L, XT), (R, XT), (R, BT)], [0, r, r, 0])])
    glyph("o", w, [([(L, XT), (R, XT), (R, BT), (L, BT)], [r, r, r, r], True)])
    glyph("p", w, [([(L, DB), (L, XT)],), bowl_r])
    glyph("q", w, [([(R, DB), (R, XT)],), bowl_l])
    wr = w * 0.72
    glyph("r", wr - 70, [([(L, BT), (L, XT), (wr - h, XT)], [0, r, 0])])     # the arm reaches 70 units into the right sidebearing
    glyph("s", w, [([(R, XT), (L, XT), (L, XM), (R, XM), (R, BT), (L, BT)], [0, r, r, r, r, 0])])
    wt = w * 0.6; st = wt * 0.38 - fl
    glyph("t", wt - fl - fr, [([(st, XT + (AT - XT) * 0.6), (st, BT), (wt - h - fl, BT)], [0, r * 0.6, 0]), ([(h - fl, XT), (wt - h - fl, XT)],)])
    glyph("u", w, [([(L, XT), (L, BT), (R, BT), (R, XT)], [0, r, r, 0])])
    vp = stroke(rounded([(L, XT + 2 * S), (C, BT - S * 0.6), (R, XT + 2 * S)]))
    glyph("v", w, extra=[clip(vp, 0, 0, w, XH)])
    glyph("w", wm, [([(L, XT), (L, BT), (Cm, BT), (Cm, XT)], [0, r, r, 0]),
                    ([(Cm, BT + r), (Cm, BT), (wm - h, BT), (wm - h, XT)], [0, r, r, 0])])
    xp = union(stroke(rounded([(L, XT + 2 * S), (R, BT - 2 * S)])), stroke(rounded([(L, BT - 2 * S), (R, XT + 2 * S)])))
    glyph("x", w, extra=[clip(xp, 0, 0, w, XH)])
    glyph("y", w, [([(L, XT), (L, BT), (R, BT)], [0, r, 0]), ([(R, XT), (R, DB), (L, DB)], [0, r, 0])])
    glyph("z", w, [([(L, XT), (R, XT), (L, BT), (R, BT)],)])


def build_glyphs(stroke):
    """Every glyph at one stroke width, in font units with the sidebearings applied: a dict
    with the glyph order, {name: (advance, outline)}, {codepoint: name}, the components of
    the composite glyphs, the anchors and the set of combining marks."""
    setup(stroke)
    build()
    order = [".notdef"] + list(GLYPHS)
    cmap = {}
    for n in GLYPHS:
        if len(n) == 1:
            cmap[ord(n)] = n                                   # caps and lowercase each map to themselves
    chars = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
             "six": "6", "seven": "7", "eight": "8", "nine": "9", "period": ".", "comma": ",",
             "colon": ":", "exclam": "!", "quotesingle": "'", "hyphen": "-", "question": "?",
             "slash": "/", "space": " \u00a0",
             }
    for n, cs in CHARS.items():
        chars[n] = chars.get(n, "") + cs
    chars["dotlessi"] = chars.get("dotlessi", "") + "\u0131"
    for n, cs in chars.items():
        for ch in cs:
            cmap[ord(ch)] = n

    notdef = Outline([((50, 0), [("line", (450, 0)), ("line", (450, H)), ("line", (50, H)), ("line", (50, 0))])])
    glyphs = {".notdef": (500, notdef)}
    for n, (w, p) in GLYPHS.items():
        glyphs[n] = (int(round(w + 2 * SB)), p.transform(1, 0, 0, 1, SB, 0))
    anchors = {n: [(a, x + SB, y) for a, x, y in v] for n, v in ANCHORS.items()}
    return {"order": order, "glyphs": glyphs, "cmap": cmap, "components": dict(COMPONENTS),
            "anchors": anchors, "marks": set(MARKS)}
