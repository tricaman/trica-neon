"""Trica Neon -- write the UFO masters and the designspace.

There is one master per named weight, each drawn by the generator at its own stroke
width, so the variable font passes exactly through every weight the generator defines.

usage: python sources/generator/make_sources.py [--check] [output folder]
  The output folder defaults to sources/. With --check the sources are built in a
  temporary folder and compared with the output folder; any difference is an error.
"""
import filecmp, os, sys, tempfile
import pathops
import ufoLib2
from ufoLib2.objects import Anchor
from fontTools import agl
from fontTools.designspaceLib import DesignSpaceDocument
from fontTools.misc.roundTools import otRound

import build_font as bf
import kerning
import spacing

FAMILY, PS_FAMILY = "Trica Neon", "TricaNeon"
REPO = "https://github.com/tricaman/trica-neon"
SITE = "https://mariustrica.com"
WEIGHTS = [("Thin", 100), ("ExtraLight", 200), ("Light", 300), ("Regular", 400), ("Medium", 500), ("SemiBold", 600)]
DEFAULT_WEIGHT = 400


def stroke_width(wght):
    """Linear axis: ExtraLight (200) has the H/20 stroke, Regular (400) twice that."""
    return 35 + 0.175 * (wght - 200)


def integer_contours(outline):
    rp = lambda p: (otRound(p[0]), otRound(p[1]))
    return [(rp(s), [(g[0],) + tuple(rp(p) for p in g[1:]) for g in segs]) for s, segs in outline.contours]


def signature(contours):
    return [tuple(g[0] for g in segs) for _, segs in contours]


def simplify(per_master):
    """The stroker gives every vertex a line and a curve so that the masters always match.
    Drop the segments that have zero length in every master, and turn into lines the
    curves whose handles sit on their end points in every master."""
    def prev(contour, si):
        start, segs = contour
        return start if si == 0 else segs[si - 1][-1]

    for ci in range(len(per_master[0])):
        degenerate = lambda c, si: all(p == prev(c[ci], si) for p in c[ci][1][si][1:])
        keep = [si for si in range(len(per_master[0][ci][1])) if not all(degenerate(c, si) for c in per_master)]
        for c in per_master:
            c[ci] = (c[ci][0], [c[ci][1][si] for si in keep])
        for si, g in enumerate(per_master[0][ci][1]):
            if g[0] == "curve" and all(c[ci][1][si][1] == prev(c[ci], si) and c[ci][1][si][2] == c[ci][1][si][3]
                                       for c in per_master):
                for c in per_master:
                    c[ci][1][si] = ("line", c[ci][1][si][3])


def overlaps(contours):
    """Whether the contours overlap: their nonzero union is smaller than the sum of their areas."""
    path = pathops.Path()
    pen = path.getPen()
    for start, segs in contours:
        pen.moveTo(start)
        for g in segs:
            pen.lineTo(g[1]) if g[0] == "line" else pen.curveTo(*g[1:])
        pen.closePath()
    return path.area - pathops.simplify(path).area > 1


def production_names(order, cmap):
    """Adobe Glyph List name (AGLFN) or uniXXXX, from the lowest codepoint of each glyph."""
    first = {}
    for cp in sorted(cmap):
        first.setdefault(cmap[cp], cp)
    names = {n: n if n not in first else agl.UV2AGL.get(first[n], "uni%04X" % first[n]) for n in order}
    assert len(set(names.values())) == len(names), "two glyphs share a production name"
    return names


def draw(glyph, contours):
    pen = glyph.getPointPen()
    for start, segs in contours:
        pen.beginPath()
        pen.addPoint(start, segs[-1][0])
        for g in segs[:-1]:
            for p in g[1:-1]:
                pen.addPoint(p)
            pen.addPoint(g[-1], g[0])
        for p in segs[-1][1:-1]:
            pen.addPoint(p)
        pen.endPath()


FIGURES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
TOP_MARKS = ["gravecomb", "acutecomb", "circumflexcomb", "tildecomb", "macroncomb", "brevecomb",
             "dotaccentcomb", "dieresiscomb", "ringcomb", "hungarumlautcomb", "caroncomb", "commaturnedabovecomb"]
BRACKETS = ["parenleft", "parenright", "bracketleft", "bracketright", "braceleft", "braceright"]


def feature_code(names):
    """features.fea, the same for every master. kern, mark and mkmk are not here: ufo2ft
    writes them from the kerning and the anchors."""
    def cls(glyphs):
        return "[" + " ".join(names[g] for g in glyphs) + "]"
    return "\n".join([
        "# Trica Neon OpenType features, written by sources/generator/make_sources.py.",
        "# kern, mark and mkmk come from the kerning and the anchors of the UFOs.",
        "",
        "languagesystem DFLT dflt;",
        "languagesystem latn dflt;",
        "languagesystem latn ROM;",
        "languagesystem latn MOL;",
        "",
        f"@figures = {cls(FIGURES)};",
        f"@figures_numr = {cls([f + '.numr' for f in FIGURES])};",
        f"@figures_dnom = {cls([f + '.dnom' for f in FIGURES])};",
        f"@figures_sups = {cls([f + 'superior' for f in FIGURES])};",
        f"@figures_tf = {cls([f + '.tf' for f in FIGURES])};",
        f"@marks_top = {cls(TOP_MARKS)};",
        "",
        "# i, j and į lose their dot under a mark above, also with marks below in between (the",
        "# filtering set skips every mark that is not above); I and the dotless i take the narrow",
        "# tilde and breve; d l t L take the vertical caron",
        "lookup soft_dotted {",
        "    lookupflag UseMarkFilteringSet @marks_top;",
        f"    sub {cls(['i', 'j', 'uni012F'])}' @marks_top by {cls(['dotlessi', 'dotlessj', 'iogonek.dotless'])};",
        "} soft_dotted;",
        "lookup narrow_marks {",
        f"    sub {cls(['I', 'dotlessi', 'iogonek.dotless'])} {names['tildecomb']}' by {names['tildecomb.narrow']};",
        f"    sub {cls(['I', 'dotlessi', 'iogonek.dotless'])} {names['brevecomb']}' by {names['brevecomb.narrow']};",
        "} narrow_marks;",
        "lookup vertical_caron {",
        f"    sub {cls(['d', 'l', 't', 'L'])} {names['caroncomb']}' by {names['caroncomb.alt']};",
        "} vertical_caron;",
        "feature ccmp {",
        "    lookup soft_dotted;",
        "    lookup narrow_marks;",
        "    lookup vertical_caron;",
        "} ccmp;",
        "",
        "# Romanian and Moldovan: S and T take a comma below, not a cedilla",
        "lookup romanian {",
        f"    sub {cls(['uni015E', 'uni015F', 'uni0162', 'uni0163'])} by {cls(['uni0218', 'uni0219', 'uni021A', 'uni021B'])};",
        "} romanian;",
        "feature locl {",
        "    script latn;",
        "    language ROM;",
        "    lookup romanian;",
        "    language MOL;",
        "    lookup romanian;",
        "} locl;",
        "",
        "# fractions: figures before the slash become numerators, after it denominators",
        "feature frac {",
        f"    lookup frac_slash {{ sub {names['slash']} by {names['fraction']}; }} frac_slash;",
        "    lookup frac_numr { sub @figures by @figures_numr; } frac_numr;",
        f"    lookup frac_dnom {{ sub [{names['fraction']} @figures_dnom] @figures_numr' by @figures_dnom; }} frac_dnom;",
        "} frac;",
        "feature numr { sub @figures by @figures_numr; } numr;",
        "feature dnom { sub @figures by @figures_dnom; } dnom;",
        "feature sups { sub @figures by @figures_sups; } sups;",
        f"feature ordn {{ sub @figures {cls(['a', 'o'])}' by {cls(['ordfeminine', 'ordmasculine'])}; }} ordn;",
        "feature tnum { sub @figures by @figures_tf; } tnum;",
        f"feature case {{ sub {cls(BRACKETS)} by {cls([b + '.case' for b in BRACKETS])}; }} case;",
        "",
    ])


def style_map_family(style):
    return FAMILY if style == "Regular" else f"{FAMILY} {style}"


def set_info(info, style, wght, win):
    info.familyName, info.styleName = FAMILY, style
    info.styleMapFamilyName, info.styleMapStyleName = style_map_family(style), "regular"
    if style != "Regular":
        info.openTypeNamePreferredFamilyName, info.openTypeNamePreferredSubfamilyName = FAMILY, style
    info.postscriptFontName, info.postscriptFullName = f"{PS_FAMILY}-{style}", f"{FAMILY} {style}"
    info.versionMajor, info.versionMinor, info.year = 1, 0, 2026
    info.copyright = f"Copyright 2026 The {FAMILY} Project Authors ({REPO})"
    info.openTypeNameDesigner = info.openTypeNameManufacturer = "Marius Trica"
    info.openTypeNameDesignerURL = info.openTypeNameManufacturerURL = SITE
    info.openTypeNameLicense = ("This Font Software is licensed under the SIL Open Font License, Version 1.1. "
                                "This license is available with a FAQ at: https://openfontlicense.org")
    info.openTypeNameLicenseURL = "https://openfontlicense.org"
    info.openTypeOS2VendorID = "TRCA"
    info.openTypeOS2WeightClass, info.openTypeOS2WidthClass = wght, 5
    info.openTypeOS2Selection = [7]                   # USE_TYPO_METRICS
    info.openTypeOS2Type = []                         # fsType 0: installable embedding
    info.unitsPerEm, info.capHeight, info.xHeight, info.italicAngle = bf.UPM, bf.H, bf.XH, 0
    info.ascender, info.descender = bf.H, -round(bf.H * 0.28)     # lowercase ascenders reach the cap height
    # line metrics as the Google Fonts guide asks (https://googlefonts.github.io/gf-guide/metrics.html),
    # the same in every master: a 1.3 em line with the capitals centred in it (typoAscender - capHeight
    # = -typoDescender), no line gap, hhea equal to typo; the win metrics cover every glyph
    line = otRound(1.3 * bf.UPM)
    asc = otRound((line + bf.H) / 2)
    info.openTypeOS2TypoAscender, info.openTypeOS2TypoDescender, info.openTypeOS2TypoLineGap = asc, asc - line, 0
    info.openTypeHheaAscender, info.openTypeHheaDescender, info.openTypeHheaLineGap = asc, asc - line, 0
    info.openTypeOS2WinAscent, info.openTypeOS2WinDescent = win
    # one underline for the whole family (Google Fonts wants it consistent): the Regular underscore
    regular = stroke_width(DEFAULT_WEIGHT)
    info.postscriptUnderlineThickness = otRound(regular)
    info.postscriptUnderlinePosition = otRound(-bf.H * 0.12 + regular / 2)  # top of the underscore


def write_designspace(path):
    doc = DesignSpaceDocument()
    doc.addAxisDescriptor(tag="wght", name="Weight", minimum=WEIGHTS[0][1], default=DEFAULT_WEIGHT, maximum=WEIGHTS[-1][1])
    for style, wght in WEIGHTS:
        doc.addSourceDescriptor(filename=f"{PS_FAMILY}-{style}.ufo", familyName=FAMILY, styleName=style,
                                location={"Weight": wght})
    for style, wght in WEIGHTS:
        doc.addInstanceDescriptor(familyName=FAMILY, styleName=style, location={"Weight": wght},
                                  postScriptFontName=f"{PS_FAMILY}-{style}", styleMapFamilyName=style_map_family(style),
                                  styleMapStyleName="regular", filename=f"instance_ufos/{PS_FAMILY}-{style}.ufo")
    doc.write(path)


def flattened(name, data, comps):
    """The contours of a glyph with its components resolved (for areas and extents)."""
    out = list(data[name][1])
    for c, dx, dy in comps.get(name, []):
        move = lambda p: (p[0] + dx, p[1] + dy)
        out += [(move(s), [(g[0],) + tuple(move(p) for p in g[1:]) for g in segs]) for s, segs in flattened(c, data, comps)]
    return out


def write_sources(out):
    builds = {style: bf.build_glyphs(stroke_width(wght)) for style, wght in WEIGHTS}
    first = builds[WEIGHTS[0][0]]
    order, cmap, marks = first["order"], first["cmap"], first["marks"]
    shape = lambda b: (b["order"], b["cmap"], {n: [c[0] for c in v] for n, v in b["components"].items()},
                       {n: [a[0] for a in v] for n, v in b["anchors"].items()})
    for style, b in builds.items():
        if shape(b) != shape(first):
            sys.exit(f"{style}: the glyphs, components or anchors differ from {WEIGHTS[0][0]}")
    spacing.respace(list(builds.values()), bf.XH, bf.H, bf.SB)
    data = {s: {n: (adv, integer_contours(p)) for n, (adv, p) in b["glyphs"].items()} for s, b in builds.items()}
    comps = {s: {n: [(c, otRound(x), otRound(y)) for c, x, y in v] for n, v in b["components"].items()}
             for s, b in builds.items()}
    anchors = {s: {n: [(a, otRound(x), otRound(y)) for a, x, y in v] for n, v in b["anchors"].items()}
               for s, b in builds.items()}
    bad = {n: [len(signature(data[s][n][1])) for s in data] for n in order
           if len({repr(signature(data[s][n][1])) for s in data}) > 1}
    if bad:
        sys.exit("masters not interpolatable (contours per master):\n" + "\n".join(f"  {n}: {v}" for n, v in bad.items()))
    for n in order:
        simplify([data[s][n][1] for s in data])
    flat = {s: {n: flattened(n, data[s], comps[s]) for n in order} for s in data}
    # the variable font keeps the overlaps: flag those glyphs (OVERLAP_SIMPLE/COMPOUND) for the rasterizers
    overlapping = {n for n in order if any(overlaps(flat[s][n]) for s in data)}
    names = production_names(order, cmap)
    unicodes = {}
    for cp, n in cmap.items():
        unicodes.setdefault(n, []).append(cp)
    kern_letters = kerning.letters(cmap, builds[WEIGHTS[0][0]]["components"])
    kern_groups = kerning.groups(builds[WEIGHTS[0][0]]["components"], kern_letters)
    kern_values = {s: kerning.values(flat[s], {n: data[s][n][0] for n in order}, 2 * bf.SB, stroke_width(w), kern_letters)
                   for s, w in WEIGHTS}
    fea = feature_code(names)
    ys = [p[1] for s in flat for cs in flat[s].values() for _, segs in cs for g in segs for p in g[1:]]
    win = (max(ys), max(0, -min(ys)))
    os.makedirs(out, exist_ok=True)
    for style, wght in WEIGHTS:
        font = ufoLib2.Font()
        set_info(font.info, style, wght, win)
        for n in order:
            adv, contours = data[style][n]
            g = font.newGlyph(names[n])
            g.width, g.unicodes = adv, sorted(unicodes.get(n, []))
            if n in overlapping:
                g.lib["public.truetype.overlap"] = True
            draw(g, contours)
            pen = g.getPointPen()
            for c, x, y in comps[style].get(n, []):
                pen.addComponent(names[c], (1, 0, 0, 1, x, y))
            g.anchors = [Anchor(x, y, a) for a, x, y in anchors[style].get(n, [])]
        font.groups = {g: [names[n] for n in members] for g, members in kern_groups.items()}
        font.kerning = kern_values[style]
        font.features.text = fea
        font.lib["public.glyphOrder"] = [names[n] for n in order]
        font.lib["public.openTypeCategories"] = {names[n]: "mark" if n in marks else "base" for n in order}
        font.lib["public.openTypeMeta"] = {"dlng": ["Latn"], "slng": ["Latn"]}   # designed for / supports Latin
        font.save(os.path.join(out, f"{PS_FAMILY}-{style}.ufo"), overwrite=True)
    write_designspace(os.path.join(out, f"{PS_FAMILY}.designspace"))
    return len(order), len(cmap)


def differences(new, old):
    """Paths of the generated files that are missing, extra or different in `old`."""
    out = []
    for item in os.listdir(new):
        for root in (new, old):
            base = os.path.join(root, item)
            files = [base] if os.path.isfile(base) else [os.path.join(d, f) for d, _, fs in os.walk(base) for f in fs]
            for f in files:
                rel = os.path.relpath(f, root)
                a, b = os.path.join(new, rel), os.path.join(old, rel)
                if rel not in out and not (os.path.isfile(a) and os.path.isfile(b) and filecmp.cmp(a, b, shallow=False)):
                    out.append(rel)
    return sorted(out)


def main():
    args = [a for a in sys.argv[1:] if a != "--check"]
    out = args[0] if args else os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
    if "--check" not in sys.argv:
        glyphs, codepoints = write_sources(out)
        print(f"wrote {len(WEIGHTS)} masters ({glyphs} glyphs, {codepoints} codepoints) and the designspace to {os.path.normpath(out)}")
        return
    with tempfile.TemporaryDirectory() as tmp:
        write_sources(tmp)
        diff = differences(tmp, out)
    if diff:
        sys.exit("the sources differ from what the generator produces:\n" + "\n".join("  " + d for d in diff))
    print("the sources match the generator")


if __name__ == "__main__":
    main()
