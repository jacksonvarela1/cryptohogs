#!/usr/bin/env python3
"""Generate the Crypto Hogs shirt artwork and the shirt mockups.

Run from anywhere:  python tools/build-merch.py

What it writes (and nothing else):
  assets/merch/design-a-left-chest.svg   small coin mark, bronze on ink
  assets/merch/design-b-back-full.svg    full back print, three screens
  assets/merch/design-c-back-onecolor-cream.svg  the same back print, one screen
  assets/merch/design-c-back-onecolor-ink.svg     the same, for a light blank
  assets/merch/proof-alphabet.svg        every glyph, for eyeballing the letterforms
  assets/merch/mockup-*.svg              shirt mockups, rendered to PNG separately

Every letter and every shape here is drawn as vector path data in this file. No
raster, no external font, no CDN. Type is a stroked geometric alphabet on a 6 by 10
unit grid, so a printer expands strokes to fills once and the art is press ready.

No University of Arkansas mark appears anywhere. The club's own name is the only
name on the shirt.

Standard library only, Python 3.9+.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "merch")

INK = "#0B0B0D"
CREAM = "#F4EFE4"
BRONZE = "#C9A96A"
CARDINAL = "#9D2235"
CARDINAL_BRIGHT = "#C41230"

# ---------------------------------------------------------------- alphabet
# Each glyph lives in a 6 wide by 10 tall box. y=0 is the cap line, y=10 the
# baseline. Paths are centerlines, stroked with round caps and joins.
GLYPHS = {
    "A": "M0,10 L3,0 L6,10 M0.9,7 L5.1,7",
    "B": "M0,0 L0,10 M0,0 L3.4,0 A2.5,2.5 0 0 1 3.4,5 L0,5 M0,5 L3.7,5 A2.5,2.5 0 0 1 3.7,10 L0,10",
    "C": "M5.6,0.75 A5,5 0 1 0 5.6,9.25",
    "D": "M0,0 L0,10 M0,0 L2.8,0 A3.3,5 0 0 1 2.8,10 L0,10",
    "E": "M6,0 L0,0 L0,10 L6,10 M0,5 L4.4,5",
    "F": "M6,0 L0,0 L0,10 M0,5 L4.4,5",
    "G": "M5.6,0.75 A5,5 0 1 0 5.9,7.6 L5.9,5.4 L3.5,5.4",
    "H": "M0,0 L0,10 M6,0 L6,10 M0,5 L6,5",
    "I": "M3,0 L3,10 M1,0 L5,0 M1,10 L5,10",
    "J": "M5,0 L5,7.2 A2.5,2.5 0 0 1 0.2,7.6",
    "K": "M0,0 L0,10 M6,0 L1,5.4 M2,4.4 L6,10",
    "L": "M0,0 L0,10 L6,10",
    "M": "M0,10 L0,0 L3,5.6 L6,0 L6,10",
    "N": "M0,10 L0,0 L6,10 L6,0",
    "O": "M3,0 A3,5 0 1 0 3,10 A3,5 0 1 0 3,0",
    "P": "M0,10 L0,0 L3.4,0 A2.6,2.6 0 0 1 3.4,5.2 L0,5.2",
    "Q": "M3,0 A3,5 0 1 0 3,10 A3,5 0 1 0 3,0 M3.6,7.2 L6.2,10.4",
    "R": "M0,10 L0,0 L3.4,0 A2.6,2.6 0 0 1 3.4,5.2 L0,5.2 M3,5.2 L6,10",
    "S": "M5.4,1.4 A2.6,2.6 0 1 0 3,5 A2.6,2.6 0 1 1 0.6,8.6",
    "T": "M0,0 L6,0 M3,0 L3,10",
    "U": "M0,0 L0,7 A3,3 0 0 0 6,7 L6,0",
    "V": "M0,0 L3,10 L6,0",
    "W": "M0,0 L1.5,10 L3,3.6 L4.5,10 L6,0",
    "X": "M0,0 L6,10 M6,0 L0,10",
    "Y": "M0,0 L3,5 L6,0 M3,5 L3,10",
    "Z": "M0,0 L6,0 L0,10 L6,10",
    "0": "M3,0 A3,5 0 1 0 3,10 A3,5 0 1 0 3,0 M1.1,8.3 L4.9,1.7",
    "1": "M0.8,2 L3,0 L3,10 M1,10 L5,10",
    "2": "M0.5,2.6 A2.9,2.9 0 1 1 5.3,4.9 L0.4,10 L6,10",
    "3": "M0.5,1.8 A2.7,2.7 0 1 1 3.1,5 A2.8,2.8 0 1 1 0.5,8.4",
    "4": "M4.6,10 L4.6,0 L0,7 L6,7",
    "5": "M5.6,0 L1.2,0 L0.9,4.2 A2.9,2.9 0 1 1 0.5,8.6",
    "6": "M5.2,0.6 C1.8,1.6 0.4,3.6 0.4,6.6 A2.8,2.8 0 1 0 3.2,3.9 C1.6,3.9 0.4,5 0.4,6.6",
    "7": "M0,0 L6,0 L2.4,10",
    "8": "M3,0 A2.4,2.4 0 1 0 3,4.8 A2.7,2.7 0 1 0 3,10 A2.7,2.7 0 1 0 3,4.8 A2.4,2.4 0 1 0 3,0",
    "9": "M0.8,9.4 C4.2,8.4 5.6,6.4 5.6,3.4 A2.8,2.8 0 1 0 2.8,6.1 C4.4,6.1 5.6,5 5.6,3.4",
    ".": "M2.9,9.8 L3.1,9.8",
    ",": "M3.1,9.6 L2.4,11.2",
    "-": "M1,5 L5,5",
    "/": "M5.4,0 L0.6,10",
    "'": "M3,0 L3,2.4",
    "&": "M6,10 L2.4,2.4 A1.7,1.7 0 1 1 2.4,5.8 C0.4,7.2 1.2,10 3.2,10 C4.9,10 5.7,8.6 5.7,7",
    "+": "M3,2.4 L3,7.6 M0.4,5 L5.6,5",
    "$": "M5.2,1.9 A2.4,2.4 0 1 0 3,5 A2.4,2.4 0 1 1 0.8,8.1 M3,-1 L3,11",
    " ": "",
}

ADV = 8.2          # glyph advance in unit space, box is 6 wide
SPACE_ADV = 5.4


def text_width(s, tracking=0.0):
    """Width of a string in unit space, cap height 10."""
    w = 0.0
    for ch in s:
        w += (SPACE_ADV if ch == " " else ADV) + tracking
    return w - tracking if s else 0.0


def text_group(s, x, y, cap, color, weight=1.4, tracking=0.0, anchor="middle",
               opacity=None):
    """A run of drawn type. x,y is the baseline point, cap is the cap height."""
    s = s.upper()
    scale = cap / 10.0
    w = text_width(s, tracking) * scale
    if anchor == "middle":
        left = x - w / 2
    elif anchor == "end":
        left = x - w
    else:
        left = x
    top = y - cap
    parts = []
    cursor = 0.0
    for ch in s:
        d = GLYPHS.get(ch, GLYPHS[" "])
        if d:
            parts.append('<path transform="translate(%.3f 0)" d="%s"/>' % (cursor, d))
        cursor += (SPACE_ADV if ch == " " else ADV) + tracking
    style = ('fill="none" stroke="%s" stroke-width="%.3f" stroke-linecap="round" '
             'stroke-linejoin="round"' % (color, weight))
    if opacity is not None:
        style += ' opacity="%.2f"' % opacity
    return ('<g transform="translate(%.3f %.3f) scale(%.5f)" %s>%s</g>'
            % (left, top, scale, style, "".join(parts)))


# ---------------------------------------------------------------- the boar
# Side profile, facing left, drawn in a 100 by 62 box. Filled, one closed path,
# so it works as a single screen. The bristled back is the tell.
BOAR_BODY = (
    "M3,33 "
    "C6,29 9,25.6 13.5,23.5 L16,22 "
    "L18,11 L25.5,19.5 "
    "L29,10 L32.5,17 L36.5,8.5 L40,15.5 L44.5,7.5 L47.5,14.5 "
    "C57,10.5 67,14.5 75,20.5 "
    "C83,25 87,31 87.5,38 "
    "L94,33.5 L91.5,41.5 L88,42 "
    "L86.4,48 L86,58.4 L79.6,58.4 L81.8,48 L81.4,41.8 "
    "C78.5,43 76,43.4 73.6,43.2 "
    "L73,49 L71.8,58.4 L66.6,58.4 L69,49 L69.4,43 "
    "C61,44.4 53,45.6 46.4,46.4 "
    "L45.6,51 L44.4,58.4 L39.2,58.4 L41.6,51 L42,46.6 "
    "C38.6,46.6 34.6,46.2 31.6,45.4 "
    "L31,50 L29.8,58.4 L24.4,58.4 L26.7,50 L26.3,43.6 "
    "C22,41.4 17.5,39.6 13.4,38.6 "
    "C9,37.6 5.4,35.6 3,33 Z"
)
BOAR_TUSK = ("M2.4,34 C0.2,31 0.6,27 3.6,24.4 "
             "C3.2,27.8 3.8,30.8 5.4,33 Z")
BOAR_EYE = "M16.4,26.6 A1.4,1.4 0 1 0 16.4,29.4 A1.4,1.4 0 1 0 16.4,26.6 Z"


def boar(x, y, w, fill, eye_fill=None, opacity=None):
    """Place the boar with its top left at x,y and total width w."""
    s = w / 100.0
    eye = ""
    if eye_fill:
        eye = '<path d="%s" fill="%s"/>' % (BOAR_EYE, eye_fill)
    op = ' opacity="%.2f"' % opacity if opacity is not None else ""
    return ('<g transform="translate(%.3f %.3f) scale(%.5f)"%s>'
            '<path d="%s" fill="%s"/><path d="%s" fill="%s"/>%s</g>'
            % (x, y, s, op, BOAR_BODY, fill, BOAR_TUSK, fill, eye))


# ---------------------------------------------------------------- the coin
def coin(cx, cy, r, ring, face, teeth=44):
    """The club coin: reeded edge, double ring, boar in the middle."""
    ticks = []
    import math
    for i in range(teeth):
        a = (2 * math.pi * i) / teeth
        x1, y1 = cx + math.cos(a) * (r * 0.895), cy + math.sin(a) * (r * 0.895)
        x2, y2 = cx + math.cos(a) * (r * 0.985), cy + math.sin(a) * (r * 0.985)
        ticks.append("M%.3f,%.3f L%.3f,%.3f" % (x1, y1, x2, y2))
    return (
        '<g>'
        '<circle cx="%.3f" cy="%.3f" r="%.3f" fill="none" stroke="%s" stroke-width="%.3f"/>'
        '<path d="%s" fill="none" stroke="%s" stroke-width="%.3f" stroke-linecap="round"/>'
        '<circle cx="%.3f" cy="%.3f" r="%.3f" fill="none" stroke="%s" stroke-width="%.3f"/>'
        '%s'
        '</g>'
    ) % (
        cx, cy, r * 0.94, ring, r * 0.075,
        " ".join(ticks), ring, r * 0.05,
        cx, cy, r * 0.735, ring, r * 0.035,
        boar(cx - r * 0.64, cy - r * 0.40, r * 1.28, face),
    )


# ---------------------------------------------------------------- documents
def svg(w, h, body, title, bg=None):
    back = '<rect width="%s" height="%s" fill="%s"/>' % (w, h, bg) if bg else ""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" '
        'viewBox="0 0 %s %s" role="img" aria-label="%s">\n'
        '<title>%s</title>\n%s%s\n</svg>\n'
    ) % (w, h, w, h, title, title, back, body)


def design_a(bg=None, mark=BRONZE, sub=BRONZE):
    """Left chest hit. Board is 1050 x 770, artwork centred on 525."""
    W, H = 1050, 770
    body = [
        coin(525, 300, 230, mark, mark),
        text_group("CRYPTO HOGS", 525, 646, 74, mark, weight=2.0, tracking=1.4),
        text_group("FAYETTEVILLE AR", 525, 722, 34, sub, weight=1.15, tracking=3.4,
                   opacity=0.85),
    ]
    return svg(W, H, "\n".join(body), "Crypto Hogs left chest mark", bg)


def back_print(bg=None, wordmark=CREAM, accent=CARDINAL_BRIGHT, mark=BRONZE, mono=CREAM,
               rule=BRONZE, one_color=False):
    """Back print. The inked area is 1800 by 2640 units, which is 11 by 16.1 in."""
    W, H = 2400, 3000
    if one_color:
        accent = wordmark
        mark = wordmark
        mono = wordmark
        rule = wordmark
    body = []
    # Wordmark, two stacked lines so it reads across a back at ten feet.
    body.append(text_group("CRYPTO", 1200, 470, 300, wordmark, weight=2.2, tracking=1.6))
    body.append(text_group("HOGS", 1200, 830, 300, wordmark, weight=2.2, tracking=1.6))
    # Hairline rules flanking the year.
    body.append('<path d="M300,960 L940,960 M1460,960 L2100,960" stroke="%s" '
                'stroke-width="5" stroke-linecap="round" opacity="%s"/>'
                % (rule, "0.9" if not one_color else "0.55"))
    body.append(text_group("EST 2026", 1200, 978, 44, mono, weight=1.2, tracking=5.0,
                           opacity=None if one_color else None))
    # The boar.
    eye = None if one_color else (bg if bg else INK)
    body.append(boar(310, 1040, 1780, mark, eye_fill=eye))
    # The line that keeps the club honest about who it is for.
    body.append(text_group("FOR THE CURIOUS", 1200, 2230, 68, accent, weight=1.4,
                           tracking=3.2))
    body.append(text_group("NOT THE EXPERTS", 1200, 2352, 68, accent, weight=1.4,
                           tracking=3.2))
    # Sponsor zone: a delimited box a printer can drop a logo into, or leave empty.
    body.append('<path d="M760,2470 L1640,2470" stroke="%s" stroke-width="4" '
                'opacity="0.55"/>' % rule)
    body.append(text_group("PRESENTED BY", 1200, 2578, 40, mono, weight=1.15,
                           tracking=4.6, opacity=0.8))
    body.append('<rect x="760" y="2610" width="880" height="200" rx="10" fill="none" '
                'stroke="%s" stroke-width="4" stroke-dasharray="18 16" opacity="0.55"/>'
                % rule)
    body.append(text_group("SPONSOR ZONE", 1200, 2732, 38, mono, weight=1.05,
                           tracking=4.2, opacity=0.45))
    name = "Crypto Hogs back print, one color" if one_color else "Crypto Hogs back print"
    return svg(W, H, "\n".join(body), name, bg)


def proof():
    """Every glyph at a readable size, so the letterforms can be checked by eye."""
    rows = ["ABCDEFGHIJKLM", "NOPQRSTUVWXYZ", "0123456789 &+", "$ . , - / '"]
    body = []
    y = 190
    for r in rows:
        body.append(text_group(r, 1200, y, 130, CREAM, weight=1.35, tracking=2.6))
        y += 250
    body.append(boar(300, 1140, 900, BRONZE, eye_fill=INK))
    body.append(coin(1750, 1420, 330, BRONZE, BRONZE))
    body.append(text_group("CRYPTO HOGS", 1200, 1960, 150, CREAM, weight=2.2,
                           tracking=1.6))
    return svg(2400, 2100, "\n".join(body), "Alphabet and shape proof", INK)


# ---------------------------------------------------------------- mockups
def mockup(shirt_fill, art_svg_body, art_x, art_y, art_scale, label, thread):
    """A shirt drawn as vector, with the artwork placed at print scale.

    The body is 416 px across and stands in for a 20 inch chest, so one printed
    inch is 20.8 px and every placement below is a real measurement.
    """
    W, H = 1200, 1080
    shade = "#000000" if shirt_fill == CREAM else "#FFFFFF"
    tee = (
        "M520,250 L424,272 L246,346 "
        "C228,354 220,376 228,394 L286,486 "
        "C292,500 308,506 322,500 L392,470 L392,852 "
        "C392,868 404,880 420,880 L780,880 "
        "C796,880 808,868 808,852 L808,470 L878,500 "
        "C892,506 908,500 914,486 L972,394 "
        "C980,376 972,354 954,346 L776,272 L680,250 "
        "C664,300 636,322 600,322 C564,322 536,300 520,250 Z"
    )
    collar = ("M520,250 C536,300 564,322 600,322 C636,322 664,300 680,250 "
              "C660,278 632,290 600,290 C568,290 540,278 520,250 Z")
    body = [
        '<rect width="%d" height="%d" fill="#171719"/>' % (W, H),
        '<path d="%s" fill="%s"/>' % (tee, shirt_fill),
        '<path d="%s" fill="%s" opacity="0.16"/>' % (collar, shade),
        # A little cloth shading so the print does not float.
        '<path d="M392,470 L392,852 C392,868 404,880 420,880 L462,880 '
        'C438,730 436,600 462,478 Z" fill="%s" opacity="0.07"/>' % shade,
        '<path d="M808,470 L808,852 C808,868 796,880 780,880 L738,880 '
        'C762,730 764,600 738,478 Z" fill="%s" opacity="0.07"/>' % shade,
        '<g transform="translate(%.2f %.2f) scale(%.5f)">%s</g>'
        % (art_x, art_y, art_scale, art_svg_body),
        text_group(label, 600, 1008, 28, CREAM, weight=1.1, tracking=3.6, opacity=0.75),
        text_group(thread, 600, 118, 28, BRONZE, weight=1.1, tracking=3.6, opacity=0.8),
    ]
    return svg(W, H, "\n".join(body), label)


def inner(doc):
    """Strip the svg wrapper so a design can be dropped into a mockup."""
    start = doc.index(">", doc.index("<title>")) + 1
    start = doc.index("</title>") + len("</title>")
    return doc[start:doc.rindex("</svg>")]


def main():
    os.makedirs(OUT, exist_ok=True)
    files = {
        "design-a-left-chest.svg": design_a(),
        "design-b-back-full.svg": back_print(),
        "design-c-back-onecolor-cream.svg": back_print(one_color=True),
        "design-c-back-onecolor-ink.svg": back_print(wordmark=INK, one_color=True),
        "proof-alphabet.svg": proof(),
    }
    # Mockups. Artwork scale is chosen so the print reads at real proportions:
    # a 3.5 inch chest hit and a 12 inch back hit on a 20 inch wide shirt.
    a_ink = inner(design_a(mark=BRONZE))
    b_ink = inner(back_print())
    c_cream = inner(back_print(wordmark=INK, one_color=True))
    # One printed inch is 20.8 px on the mockup. Design A prints 3.5 in wide and
    # sits on the wearer's left chest, which is the viewer's right. Designs B and
    # C print 11 in wide, starting about 3 in below the collar.
    PPI = 416 / 20.0
    a_scale = (3.5 * PPI) / 728.0          # 728 is the inked width of board A
    b_scale = (11.0 * PPI) / 1800.0        # 1800 is the inked width of board B
    files["mockup-a-left-chest-ink.svg"] = mockup(
        INK, a_ink, 704 - 1050 * a_scale / 2, 404 - 70 * a_scale, a_scale,
        "DESIGN A  LEFT CHEST  3.5 IN", "INK BLANK  BRONZE INK")
    files["mockup-b-back-ink.svg"] = mockup(
        INK, b_ink, 600 - 2400 * b_scale / 2, 396 - 170 * b_scale, b_scale,
        "DESIGN B  FULL BACK  11 BY 16 IN", "INK BLANK  THREE SCREENS")
    files["mockup-c-back-cream.svg"] = mockup(
        CREAM, c_cream, 600 - 2400 * b_scale / 2, 396 - 170 * b_scale, b_scale,
        "DESIGN C  FULL BACK  ONE SCREEN", "CREAM BLANK  INK INK")
    for name, doc in files.items():
        path = os.path.join(OUT, name)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(doc)
        print("wrote", os.path.relpath(path, ROOT).replace("\\", "/"))


if __name__ == "__main__":
    main()
