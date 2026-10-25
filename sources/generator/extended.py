"""Trica Neon -- extended character set.

Latin-1 Supplement (complete), Latin Extended-A (complete), general punctuation,
currency, arrows and common math. Accented letters are composed from the existing
base glyphs plus marks, using Unicode decomposition data, so they always follow
whatever the base letters look like.
"""
import math, unicodedata


def install(bf, d, dot):
    H, S, h, r, T, MI, BT = bf.H, bf.S, bf.h, bf.r, bf.T, bf.MI, bf.BT
    XH, XT, XM, DB = bf.XH, bf.XT, bf.XM, bf.DB
    G = bf.GLYPHS
    ln, union, put, reg, circle = bf.ln, bf.union, bf.put, bf.reg, bf.circle
    stroke, rounded = bf.stroke, bf.rounded
    BUTT = bf.BUTT
    W = H                      # caps box
    w = H * 0.8                # lowercase / figures box

    def shift(p, dx, dy=0):
        return p.transform(1, 0, 0, 1, dx, dy)

    def glyph_of(name):
        return G[name]

    # ------------------------------------------------------------------ marks
    def m_grave(cx, y): return ln((cx - 60, y + 200), (cx + 60, y + 90), cap=BUTT)
    def m_acute(cx, y): return ln((cx - 60, y + 90), (cx + 60, y + 200), cap=BUTT)
    def m_circ(cx, y): return ln((cx - 90, y + 90), (cx, y + 190), (cx + 90, y + 90), cap=BUTT)
    def m_caron(cx, y): return ln((cx - 90, y + 190), (cx, y + 90), (cx + 90, y + 190), cap=BUTT)
    def m_tilde(cx, y):
        a, y0, y1, rr = 100, y + 105, y + 185, 30
        return ln((cx - a, y0), (cx - a, y1), (cx, y1), (cx, y0), (cx + a, y0), (cx + a, y1),
                  radii=[0, rr, rr, rr, rr, 0], cap=BUTT)
    def m_macron(cx, y): return ln((cx - 100, y + 140), (cx + 100, y + 140), cap=BUTT)
    def m_breve(cx, y): return ln((cx - 90, y + 200), (cx - 90, y + 100), (cx + 90, y + 100), (cx + 90, y + 200),
                                  radii=[0, 45, 45, 0], cap=BUTT)
    def m_dot(cx, y): return circle(cx, y + 140, d / 2)
    def m_dier(cx, y): return union(circle(cx - 90, y + 140, d / 2), circle(cx + 90, y + 140, d / 2))
    def m_ring(cx, y):
        a = 70
        return ln((cx - a, y + 230), (cx + a, y + 230), (cx + a, y + 90), (cx - a, y + 90), radii=[35] * 4, closed=True)
    def m_dblacute(cx, y): return union(m_acute(cx - 75, y), m_acute(cx + 75, y))
    def m_cedilla(cx, y): return ln((cx, BT), (cx, -110), (cx - 90, -110), radii=[0, 35, 0], cap=BUTT)
    def m_ogonek(cx, y): return ln((cx, BT), (cx, -110), (cx + 90, -110), radii=[0, 35, 0], cap=BUTT)
    def m_commabelow(cx, y): return ln((cx, -50), (cx, -170), cap=BUTT)
    def m_caronalt(cx, y): return ln((cx, y - 170), (cx, y), cap=BUTT)       # vertical caron of ď ľ ť Ľ

    # Combining marks: zero-width glyphs drawn left of the origin, over the centre of the
    # previous lowercase letter (where renderers without mark positioning leave them).
    # Accented letters use them as components; their anchors drive the mark features.
    mx = -(w + 2 * bf.SB) / 2 - bf.SB          # centre of the marks, before the sidebearing shift
    ABOVE, BELOW = {}, {}
    for name, cp, fn, attach in [
            ("gravecomb", 0x300, m_grave, "top"), ("acutecomb", 0x301, m_acute, "top"),
            ("circumflexcomb", 0x302, m_circ, "top"), ("tildecomb", 0x303, m_tilde, "top"),
            ("macroncomb", 0x304, m_macron, "top"), ("brevecomb", 0x306, m_breve, "top"),
            ("dotaccentcomb", 0x307, m_dot, "top"), ("dieresiscomb", 0x308, m_dier, "top"),
            ("ringcomb", 0x30A, m_ring, "top"), ("hungarumlautcomb", 0x30B, m_dblacute, "top"),
            ("caroncomb", 0x30C, m_caron, "top"), ("commaaccentcomb", 0x326, m_commabelow, "bottom"),
            ("cedillacomb", 0x327, m_cedilla, "bottom"), ("ogonekcomb", 0x328, m_ogonek, "ogonek")]:
        outline = fn(mx, 0)
        ys = [p[1] for _, segs in outline.contours for g in segs for p in g[1:]]
        G[name] = (-2 * bf.SB, outline)                                       # zero advance
        reg(name, chr(cp))
        bf.MARKS.add(name)
        (ABOVE if attach == "top" else BELOW)[cp] = name
        bf.ANCHORS[name] = ([("_top", mx, 0), ("top", mx, max(ys))] if attach == "top" else
                            [("_bottom", mx, 0), ("bottom", mx, min(ys))] if attach == "bottom" else [("_ogonek", mx, 0)])
    G["caroncomb.alt"] = (-2 * bf.SB, m_caronalt(mx, 0))
    bf.MARKS.add("caroncomb.alt")

    # dotted circle: shapers show it under a combining mark that has no letter to sit on.
    # Twelve dots every 30 degrees (sqrt only, so the points are the same on every platform).
    rc, s3 = XH * 0.4, math.sqrt(3) / 2
    put("dottedcircle", w, *[circle(w / 2 + rc * cx, XH / 2 + rc * cy, S * 0.4)
                             for cx, cy in [(1, 0), (s3, 0.5), (0.5, s3), (0, 1), (-0.5, s3), (-s3, 0.5),
                                            (-1, 0), (-s3, -0.5), (-0.5, -s3), (0, -1), (0.5, -s3), (s3, -0.5)]],
        chars="◌")
    bf.ANCHORS["dottedcircle"] = [("top", w / 2, XH), ("bottom", w / 2, 0), ("ogonek", w * 0.78, 0)]

    ASCENDERS = set("bdfhklt")

    # dotless j, needed under marks: the skeleton of the j without the dot
    jw, (jpart,) = bf.SKEL["j"]
    G["dotlessj"] = (jw, union(stroke(rounded(*jpart))))
    reg("dotlessj", "ȷ")

    def base_name(ch):
        return {"i": "dotlessi", "j": "dotlessj"}.get(ch, ch)

    def compose(ch):
        dec = unicodedata.decomposition(ch).split()
        if not dec or dec[0].startswith("<"):
            return False
        base = chr(int(dec[0], 16))
        marks = [int(x, 16) for x in dec[1:]]
        if base not in G and base_name(base) not in G:
            return False
        # caron on d, l, t (and capital L) is drawn as a small vertical apostrophe on the right
        vertical_caron = 0x30C in marks and base in "dltL"
        above = any(m in ABOVE for m in marks)
        bname = base_name(base) if (above and not vertical_caron) else base
        if bname not in G:
            return False
        bw = G[bname][0]                               # as wide as the base: wider marks stick out
        top = H if base.isupper() else (T + h if base in ASCENDERS else XH)
        comps = [(bname, 0, 0)]                        # (glyph, x offset, y offset)
        for m in marks:
            if m == 0x30C and vertical_caron:
                ytop = T + h if base in "dlL" else XT + (T - XT) * 0.6 + h
                if base == "L":
                    ytop = T + h
                comps.append(("caroncomb.alt", bw + 40 - mx, ytop))
                bw = bw + 80
            elif m in ABOVE:
                comps.append((ABOVE[m], bw / 2 - mx, top))
            elif m in BELOW:
                cx = bw * 0.78 if m == 0x328 else bw / 2
                comps.append((BELOW[m], cx - mx, 0))
            else:
                return False
        name = "uni%04X" % ord(ch)
        G[name] = (bw, bf.Outline())
        bf.COMPONENTS[name] = comps
        reg(name, ch)
        return True

    # every precomposed letter of Latin-1 Supplement and Latin Extended-A, Romanian S/T with
    # comma below, and the W and Y accents of GF Latin Core
    for cp in [*range(0xC0, 0x180), *range(0x218, 0x21C), *range(0x1E80, 0x1E86), 0x1EF2, 0x1EF3]:
        ch = chr(cp)
        if unicodedata.category(ch).startswith("L") and ch not in bf.CHARS_ALL():
            compose(ch)

    # anchors where the marks attach to the base letters (the positions compose() uses)
    for b in [*"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz", "dotlessi", "dotlessj"]:
        bw = G[b][0]
        top = H if b.isupper() else (T + h if b in ASCENDERS else XH)
        bf.ANCHORS[b] = [("top", bw / 2, top), ("bottom", bw / 2, 0), ("ogonek", bw * 0.78, 0)]
    # d l t L take the vertical caron on their right, where ď ľ ť Ľ have it (ccmp swaps the mark)
    for b in "dltL":
        ytop = XT + (T - XT) * 0.6 + h if b == "t" else T + h
        bf.ANCHORS[b].append(("caron", G[b][0] + 40, ytop))
    bf.ANCHORS["caroncomb.alt"] = [("_caron", mx, 0)]

    # ------------------------------------------------------- special letters
    def put1(name, width, *paths, ch=""):
        put(name, width, *paths, chars=ch)

    Dw, Dp = G["D"]
    put1("Eth", Dw + 80, shift(Dp, 80), ln((h, MI), (80 + h + 160, MI)), ch="ÐĐ")
    dw, dp = G["d"]
    yb = XH + (T - XH) * 0.55
    put1("dcroat", dw + 60, dp, ln((dw - h - 170, yb), (dw - h + 60, yb)), ch="đ")
    Hw, Hp = G["H"]
    yh = MI + (T - MI) * 0.55
    put1("Hbar", Hw + 120, shift(Hp, 60), ln((h, yh), (Hw + 120 - h, yh)), ch="Ħ")
    hw, hp = G["h"]
    put1("hbar", hw + 70, shift(hp, 70), ln((h, yb), (70 + h + 170, yb)), ch="ħ")
    Iw, Ip = G["I"]; Jw, Jp = G["J"]
    put1("IJ", Iw + Jw + H / 8, Ip, shift(Jp, Iw + H / 8), ch="Ĳ")
    iw, ip = G["i"]; jw2, jp = G["j"]
    put1("ij", iw + jw2 + 2 * bf.SB, ip, shift(jp, iw + 2 * bf.SB), ch="ĳ")     # spaced as i followed by j
    kw = w
    put1("kgreenlandic", kw, ln((h, BT), (h, XT)), ln((h, XM), (kw - h, XM), (kw - h, XT), radii=[0, r, 0]),
         ln((kw - h - r, XM), (kw - h, XM), (kw - h, BT), radii=[0, r, 0]), ch="ĸ")
    Lw, Lp = G["L"]
    put1("Ldot", Lw, Lp, circle(Lw * 0.55, MI, d / 2), ch="Ŀ")
    lw, lp = G["l"]
    put1("ldot", lw + 100, lp, circle(lw + 50, XM, d / 2), ch="ŀ")
    put1("Lslash", Lw + 80, shift(Lp, 80), ln((h, MI - 90), (80 + h + 160, MI + 90)), ch="Ł")
    put1("lslash", lw + 80, shift(lp, 80), ln((h, yb - 90), (80 + h + 160, yb + 90)), ch="ł")
    nw, np_ = G["n"]; qw, _ = G["quotesingle"]
    put1("napostrophe", nw + qw + 60, ln((h, T - 2 * r), (h, T)), shift(np_, qw + 60), ch="ŉ")
    L, R = h, W - h
    DBc = -round(H * 0.22) + h
    put1("Eng", W, ln((L, BT), (L, T), (R, T), (R, DBc), (W / 2, DBc), radii=[0, r, r, r, 0]), ch="Ŋ")
    lR = w - h
    put1("eng", w, ln((h, BT), (h, XT), (lR, XT), (lR, DB), (w / 2, DB), radii=[0, r, r, r, 0]), ch="ŋ")
    Tw, Tp = G["T"]
    put1("Tbar", Tw, Tp, ln((W * 0.3, MI), (W * 0.7, MI)), ch="Ŧ")
    tw, tp = G["t"]
    put1("tbar", tw, tp, ln((h, XM), (tw - h, XM)), ch="ŧ")
    fw = w * 0.6; sf = fw * 0.38
    put1("longs", fw, ln((fw - h, T), (sf, T), (sf, BT), radii=[0, r, 0]), ch="ſ")

    # ligatures and Nordic letters
    Wa = W * 0.62; W2 = W * 1.32
    put1("AE", W2, ln((L, BT), (L, T), (W2 - h, T), radii=[0, r, 0]), ln((Wa, T), (Wa, BT)),
         ln((L, MI), (W2 - h - 40, MI)), ln((Wa, BT), (W2 - h, BT)), ch="Æ")
    put1("OE", W2, ln((Wa, T), (L, T), (L, BT), (Wa, BT), radii=[0, r, r, 0]), ln((Wa, T), (Wa, BT)),
         ln((Wa, T), (W2 - h, T)), ln((Wa, MI), (W2 - h - 40, MI)), ln((Wa, BT), (W2 - h, BT)), ch="Œ")
    aw, ap = G["a"]; ew, ep = G["e"]; ow, op_ = G["o"]
    put1("ae", aw + ew - S, ap, shift(ep, aw - S), ch="æ")
    put1("oe", ow + ew - S, op_, shift(ep, ow - S), ch="œ")
    put1("Thorn", W, ln((L, BT), (L, T)), ln((L, H * 0.8), (R, H * 0.8), (R, H * 0.25), (L, H * 0.25), radii=[0, r, r, 0], closed=True), ch="Þ")
    put1("thorn", w, ln((h, DB), (h, T)), ln((h, XT), (lR, XT), (lR, BT), (h, BT), radii=[0, r, r, 0], closed=True), ch="þ")
    put1("eth", w, ln((h, XT), (lR, XT), (lR, BT), (h, BT), radii=[r, r, r, r], closed=True),
         ln((lR, XM), (lR, T), (w * 0.35, T), radii=[0, r * 0.6, 0]), ln((w * 0.45, yb), (w + 20 - h, yb)), ch="ð")
    ym = (T + BT) * 0.55
    put1("germandbls", w, ln((h, BT), (h, T), (lR, T), (lR, ym), (w / 2, ym), radii=[0, r, r, r, 0]),
         ln((lR - r, ym), (lR, ym), (lR, BT), (w * 0.45, BT), radii=[0, r, r, 0]), ch="ß")
    # capital sharp s: the construction of the ß in the caps box
    put1("Germandbls", W, ln((L, BT), (L, T), (R, T), (R, ym), (W / 2, ym), radii=[0, r, r, r, 0]),
         ln((R - r, ym), (R, ym), (R, BT), (W * 0.45, BT), radii=[0, r, r, 0]), ch="ẞ")
    # anchors on these letters too, so that a combining mark typed after them sits in place (ǽ, ǿ ...)
    for b in ["AE", "Eth", "Oslash", "Thorn", "Germandbls", "Hbar", "Lslash", "Eng", "OE", "Tbar", "ae", "eth",
              "oslash", "thorn", "germandbls", "dcroat", "hbar", "kgreenlandic", "lslash", "eng", "oe", "tbar", "longs"]:
        bw = G[b][0]
        tall = b in ("eth", "thorn", "germandbls", "dcroat", "hbar", "lslash", "tbar", "longs")
        top = H if b[0].isupper() else (T + h if tall else XH)
        bf.ANCHORS[b] = [("top", bw / 2, top), ("bottom", bw / 2, 0), ("ogonek", bw * 0.78, 0)]

    # ------------------------------------------------- small figures (superscripts, fractions)
    def small(name, scale, dx, dy, sw):
        width, parts = bf.SKEL[name]
        res = []
        for part in parts:
            pts, rad, closed = (tuple(part) + (None, False))[:3] if len(part) < 3 else part
            pts2 = [(x * scale + dx, y * scale + dy) for x, y in pts]
            rad2 = [x * scale for x in rad] if rad else None
            res.append(stroke(rounded(pts2, rad2, closed), width=sw))
        return width * scale, union(*res)

    sc, sw = 0.5, S * 0.85
    sup_y = H - H * sc
    for nm, ch in [("one", "¹"), ("two", "²"), ("three", "³")]:
        wd, p = small(nm, sc, 0, sup_y, sw)
        put1(nm + "superior", wd, p, ch=ch)
    for nm in ["zero", "four", "five", "six", "seven", "eight", "nine"]:
        wd, p = small(nm, sc, 0, sup_y, sw)
        put1(nm + "superior", wd, p, ch={"zero": "⁰", "four": "⁴", "five": "⁵", "six": "⁶",
                                            "seven": "⁷", "eight": "⁸", "nine": "⁹"}[nm])
    fw2 = W * 1.0
    for num, den, ch in [("one", "four", "¼"), ("one", "two", "½"), ("three", "four", "¾")]:
        nw_, npth = small(num, sc, 0, sup_y, sw)
        dw_, dpth = small(den, sc, fw2 - G[den][0] * sc, 0, sw)
        put1(num + "_" + den, fw2, npth, dpth, ln((fw2 * 0.28, BT), (fw2 * 0.72, T), cap=BUTT), ch=ch)
    put1("fraction", W * 0.4, ln((h, BT), (W * 0.4 - h, T), cap=BUTT), ch="⁄")
    # ordinals
    aw2, ap2 = small("a", 0.55, 0, H * 0.42, sw)
    put1("ordfeminine", aw2, ap2, ln((h, H * 0.3), (aw2 - h, H * 0.3)), ch="ª")
    ow2, op2 = small("o", 0.55, 0, H * 0.42, sw)
    put1("ordmasculine", ow2, op2, ln((h, H * 0.3), (ow2 - h, H * 0.3)), ch="º")

    # figures for the OpenType features: numerators (the superiors) and denominators (the same
    # small figures on the baseline, as in ½ ¼ ¾) with a 40 unit sidebearing; tabular figures
    # all as wide as the zero
    tight = 40 - bf.SB
    for nm in ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]:
        wd, p = small(nm, sc, 0, 0, sw)
        G[nm + ".dnom"] = (wd + 2 * tight, shift(p, tight))
        G[nm + ".numr"] = (wd + 2 * tight, bf.Outline())
        bf.COMPONENTS[nm + ".numr"] = [(nm + "superior", tight, 0)]
        G[nm + ".tf"] = (G["zero"][0], bf.Outline())
        bf.COMPONENTS[nm + ".tf"] = [(nm, (G["zero"][0] - G[nm][0]) / 2, 0)]

    # brackets for all-capital text (case): they reach below the baseline, so raise them
    # to sit centred on the capitals
    for nm in ["parenleft", "parenright", "bracketleft", "bracketright", "braceleft", "braceright"]:
        G[nm + ".case"] = (G[nm][0], bf.Outline())
        bf.COMPONENTS[nm + ".case"] = [(nm, 0, H * 0.06)]

    # i with ogonek and no dot, for a mark above it (ccmp)
    iw = G["dotlessi"][0]
    G["iogonek.dotless"] = (iw, bf.Outline())
    bf.COMPONENTS["iogonek.dotless"] = [("dotlessi", 0, 0), ("ogonekcomb", iw * 0.78 - mx, 0)]

    # ------------------------------------------------------- Latin-1 symbols
    cw, cp_ = G["c"]
    put1("cent", cw, cp_, ln((cw / 2, -80), (cw / 2, XH + 80), cap=BUTT), ch="¢")
    cx, cy, a = w / 2, MI, w * 0.22
    put1("currency", w, ln((cx - a, cy + a), (cx + a, cy + a), (cx + a, cy - a), (cx - a, cy - a), radii=[a * 0.5] * 4, closed=True),
         ln((cx - a * 1.7, cy + a * 1.7), (cx - a, cy + a), cap=BUTT), ln((cx + a * 1.7, cy + a * 1.7), (cx + a, cy + a), cap=BUTT),
         ln((cx - a * 1.7, cy - a * 1.7), (cx - a, cy - a), cap=BUTT), ln((cx + a * 1.7, cy - a * 1.7), (cx + a, cy - a), cap=BUTT), ch="¤")
    Yw, Yp = G["Y"]
    put1("yen", Yw, Yp, ln((W * 0.25, MI * 0.62), (W * 0.75, MI * 0.62)), ln((W * 0.25, MI * 0.3), (W * 0.75, MI * 0.3)), ch="¥")
    sw_ = W * 0.6; rs = r * 0.55; L1, R1 = h, sw_ - h
    y1, y2, y3, y4 = T, H * 0.62, H * 0.38, BT
    put1("section", sw_, ln((R1, y1), (L1, y1), (L1, y2), (R1, y2), (R1, y3 - 40), radii=[0, rs, rs, rs, 0]),
         ln((L1, y2 + 40), (L1, y3), (R1, y3), (R1, y4), (L1, y4), radii=[0, rs, rs, rs, 0]), ch="§")
    # spacing accents: the combining mark, centred in a 300 wide glyph
    for nm, mark, ch in [("dieresis", "dieresiscomb", "¨"), ("macron", "macroncomb", "¯"), ("acute", "acutecomb", "´"),
                         ("cedilla", "cedillacomb", "¸"), ("breve", "brevecomb", "˘"), ("dotaccent", "dotaccentcomb", "˙"),
                         ("ring", "ringcomb", "˚"), ("ogonek", "ogonekcomb", "˛"), ("tilde", "tildecomb", "˜"),
                         ("hungarumlaut", "hungarumlautcomb", "˝"), ("caron", "caroncomb", "ˇ"),
                         ("circumflex", "circumflexcomb", "ˆ")]:
        G[nm] = (300, bf.Outline())
        bf.COMPONENTS[nm] = [(mark, 150 - mx, 0 if mark in BELOW.values() else H - 90)]
        reg(nm, ch)

    def framed(letter, name, ch):
        bw0, bp0 = G[letter]
        k = 0.5; inner = bp0.transform(k, 0, 0, k, (W - bw0 * k) / 2, H * 0.25)
        put1(name, W, ln((L, T), (R, T), (R, BT), (L, BT), radii=[r] * 4, closed=True), inner, ch=ch)
    framed("C", "copyright", "©")
    framed("R", "registered", "®")
    put1("logicalnot", w, ln((h, MI + 60), (w - h, MI + 60), (w - h, MI - 100)), ch="¬")
    pw = w; pc = pw / 2; pa = pw * 0.34
    put1("plusminus", pw, ln((pc - pa, MI + 60), (pc + pa, MI + 60)), ln((pc, MI + 60 - pa), (pc, MI + 60 + pa)),
         ln((pc - pa, BT), (pc + pa, BT)), ch="±")
    uw, up = G["u"]
    put1("mu", uw, up, ln((h, DB), (h, BT + r)), ch="µμ")       # the descender ends inside the stem of the u
    put1("paragraph", W * 0.7, ln((W * 0.45, BT), (W * 0.45, T)), ln((W * 0.7 - h, BT), (W * 0.7 - h, T)),
         ln((W * 0.45, T), (h, T), (h, MI), (W * 0.45, MI), radii=[0, r * 0.7, r * 0.7, 0]), ch="¶")
    reg("hyphen", "‐‑")             # hyphen, non-breaking hyphen; no soft hyphen (U+00AD)

    # --------------------------------------------------- general punctuation
    put1("quotesinglbase", S, ln((h, -2 * r + 120), (h, 120 - 40), cap=BUTT), ch="‚")
    put1("quotedblbase", S * 3, ln((h, -2 * r + 120), (h, 80), cap=BUTT), ln((S * 3 - h, -2 * r + 120), (S * 3 - h, 80), cap=BUTT), ch="„")
    dg = W * 0.5
    put1("dagger", dg, ln((dg / 2, -80), (dg / 2, T)), ln((h, T - 200), (dg - h, T - 200)), ch="†")
    put1("daggerdbl", dg, ln((dg / 2, -80), (dg / 2, T)), ln((h, T - 200), (dg - h, T - 200)), ln((h, 180), (dg - h, 180)), ch="‡")
    pcw, pcp = G["percent"]
    sq = H * 0.3
    put1("perthousand", pcw + sq + 40, pcp, ln((pcw + 40, BT + sq), (pcw + 40 + sq - h, BT + sq), (pcw + 40 + sq - h, BT), (pcw + 40, BT),
                                              radii=[r * 0.3] * 4, closed=True), ch="‰")
    put1("minute", 120, ln((90, T), (40, T - 200), cap=BUTT), ch="′")
    put1("second", 220, ln((90, T), (40, T - 200), cap=BUTT), ln((190, T), (140, T - 200), cap=BUTT), ch="″")
    tm = W * 1.0; s2 = 0.42
    tT = stroke(rounded([(h, T), (tm * 0.4, T)]), width=S * 0.85)
    tS = stroke(rounded([(tm * 0.2, T), (tm * 0.2, T - H * s2)]), width=S * 0.85)
    mw_, mp = small("M", s2, tm * 0.48, T - H * s2 + h, S * 0.85)
    put1("trademark", tm, tT, tS, mp, ch="™")

    # spaces
    for nm, width, chs in [("enspace", 500, "  "), ("emspace", 1000, "  "), ("thinspace", 200, "  "),
                           ("hairspace", 100, " "), ("figurespace", w + 2 * bf.SB, " "), ("punctspace", d, " ")]:
        G[nm] = (width - 2 * bf.SB, bf.Outline()); reg(nm, chs)

    # ------------------------------------------------------------ arrows
    aw_ = W; ac = aw_ / 2; hd = W * 0.22
    put1("arrowright", aw_, ln((h, MI), (aw_ - h, MI)), ln((aw_ - h - hd, MI + hd), (aw_ - h, MI), (aw_ - h - hd, MI - hd)), ch="→")
    put1("arrowleft", aw_, ln((h, MI), (aw_ - h, MI)), ln((h + hd, MI + hd), (h, MI), (h + hd, MI - hd)), ch="←")
    put1("arrowup", W * 0.6, ln((W * 0.3, BT), (W * 0.3, T)), ln((W * 0.3 - hd, T - hd), (W * 0.3, T), (W * 0.3 + hd, T - hd)), ch="↑")
    put1("arrowdown", W * 0.6, ln((W * 0.3, BT), (W * 0.3, T)), ln((W * 0.3 - hd, BT + hd), (W * 0.3, BT), (W * 0.3 + hd, BT + hd)), ch="↓")
    put1("arrowboth", aw_, ln((h, MI), (aw_ - h, MI)), ln((aw_ - h - hd, MI + hd), (aw_ - h, MI), (aw_ - h - hd, MI - hd)),
         ln((h + hd, MI + hd), (h, MI), (h + hd, MI - hd)), ch="↔")

    # ------------------------------------------------------------ math
    mw = w; mc = mw / 2; ma = mw * 0.36
    eqw, eqp = G["equal"]
    put1("notequal", eqw, eqp, ln((mc - ma * 0.5, MI - ma), (mc + ma * 0.5, MI + ma), cap=BUTT), ch="≠")
    lsw, lsp = G["less"]; gtw, gtp = G["greater"]
    put1("lessequal", lsw, lsp.transform(1, 0, 0, 1, 0, 70), ln((mc - ma, MI - ma - 40), (mc + ma, MI - ma - 40)), ch="≤")
    put1("greaterequal", gtw, gtp.transform(1, 0, 0, 1, 0, 70), ln((mc - ma, MI - ma - 40), (mc + ma, MI - ma - 40)), ch="≥")
    tlw, tlp = G["asciitilde"]
    put1("approxequal", tlw, tlp.transform(1, 0, 0, 1, 0, 70), tlp.transform(1, 0, 0, 1, 0, -70), ch="≈")
    iq = W * 0.28
    put1("infinity", W * 1.0, ln((h, MI + iq / 2), (W / 2, MI + iq / 2), (W / 2, MI - iq / 2), (h, MI - iq / 2), radii=[iq * 0.45] * 4, closed=True),
         ln((W / 2, MI), (W / 2, MI + iq / 2), (W - h, MI + iq / 2), (W - h, MI - iq / 2), (W / 2, MI - iq / 2), (W / 2, MI),
            radii=[0] + [iq * 0.45] * 4 + [0]), ch="∞")           # right loop left open on the shared side
    put1("radical", W * 0.8, ln((h, MI), (W * 0.22, MI), (W * 0.38, BT), (W * 0.52, T), (W * 0.8 - h, T)), ch="√")
    put1("partialdiff", w, ln((h, XT), (lR, XT), (lR, BT), (h, BT), radii=[r] * 4, closed=True),
         ln((lR, XM), (lR, T), (h + 40, T), radii=[0, r, 0]), ch="∂")
    put1("summation", W * 0.8, ln((W * 0.8 - h, T), (h, T), (W * 0.45, MI), (h, BT), (W * 0.8 - h, BT)), ch="∑")
    put1("product", W, ln((L, BT), (L, T), (R, T), (R, BT)), ch="∏")
    put1("increment", W, ln((W / 2, T), (L, BT), (R, BT), (W / 2, T)), ch="∆")
    put1("Omega", W, ln((L, BT), (W * 0.3, BT), (W * 0.3, H * 0.3), (L, H * 0.3), (L, T), (R, T), (R, H * 0.3), (W * 0.7, H * 0.3), (W * 0.7, BT), (R, BT),
                        radii=[0, 0, 0, r * 0.5, r, r, r * 0.5, 0, 0, 0]), ch="ΩΩ")
    put1("pi", w, ln((h, XT), (lR, XT)), ln((w * 0.28, XT), (w * 0.28, BT)), ln((w * 0.72, XT), (w * 0.72, BT)), ch="π")
    put1("lozenge", W * 0.8, ln((W * 0.4, T), (h, MI), (W * 0.4, BT), (W * 0.8 - h, MI), closed=True), ch="◊")
    put1("estimated", W, ln((L, MI), (R, MI), (R, T), (L, T), (L, BT), (R, BT), radii=[0, 0, r, r, r, 0]), ch="℮")
    put1("numero", W * 1.5, G["N"][1], small("o", 0.6, W + 20, H * 0.32, S * 0.85)[1],
         ln((W + 20 + h, H * 0.2), (W * 1.5 - h - 30, H * 0.2)), ch="№")
    # more currency: rupee, ruble, bitcoin, lira
    put1("lira", W * 0.8, *[G["sterling"][1]], ch="₤")
    put1("won", W, G["W"][1], ln((0 + h, MI + 80), (W - h, MI + 80)), ch="₩")
    Pw, Pp = G["P"]
    put1("ruble", Pw + 60, shift(Pp, 60), ln((h, H * 0.25), (60 + h + 300, H * 0.25)), ch="₽")
    Bw, Bp = G["B"]
    put1("bitcoin", Bw, Bp, ln((W * 0.3, -80), (W * 0.3, H + 80), cap=BUTT), ln((W * 0.55, -80), (W * 0.55, H + 80), cap=BUTT), ch="₿")
    rw = W * 0.75
    put1("rupee", rw, ln((h, T), (rw - h, T)), ln((h, MI + 120), (rw - h, MI + 120)),
         ln((rw * 0.55 - r * 0.6, T), (rw * 0.55, T), (rw * 0.55, MI - 40), (h, MI - 40), (rw - h, BT),
            radii=[0, r * 0.6, r * 0.6, 0, 0]), ch="₹")               # starts inside the top bar
