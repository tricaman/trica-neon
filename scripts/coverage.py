"""Coverage of a font against the GF Latin glyphsets.
usage: python -I coverage.py <font>"""
import sys, unicodedata
from fontTools.ttLib import TTFont
import glyphsets

cmap = set(TTFont(sys.argv[1]).getBestCmap())
print("defined Latin glyphsets:", [g for g in glyphsets.defined_glyphsets() if "Latin" in g])
for gs in ["GF_Latin_Kernel", "GF_Latin_Core", "GF_Latin_Plus"]:
    need = set(glyphsets.unicodes_per_glyphset(gs))
    miss = sorted(need - cmap)
    print(f"\n{gs}: {len(need)} codepoints, present {len(need) - len(miss)}, missing {len(miss)}")
    for cp in miss[:80]:
        print(f"  U+{cp:04X} {chr(cp) if unicodedata.category(chr(cp))[0] not in 'MZC' else ' '} {unicodedata.name(chr(cp), '?')}")
    if len(miss) > 80:
        print(f"  ... and {len(miss) - 80} more")
