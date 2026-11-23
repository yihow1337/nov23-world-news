#!/usr/bin/env python3
"""Local renderer for entry.png (Pillow). Not used by main.py.

Draws a 1024x1024 picture of Monday 23 November 2026 world news with the
Monday afternoon figures: the Dymer toll of 11, the Air Force's 153/134
overnight tally, Zelenskyy's Merkury claim, the Delhi MoUs and package, the
North Atlantic Council that met, and the Shuri Castle hall that opened.

Design rules: 300px-first (one-line date banner near 72px, headlines >= 40px,
kickers >= 32px on the 1024 canvas), one original pictogram per story, one
colour per story, bone paper with floating panels, nothing microscopic.

Usage:  python3 tools/render.py [out_path]
Also writes preview_300.png beside the output for the legibility check.
"""

import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

GOOGLE = "/usr/share/fonts/truetype/sand-box/google"
DISPLAY = f"{GOOGLE}/Archivo Black/ArchivoBlack-Regular.ttf"
TEXT = f"{GOOGLE}/Source Sans 3/SourceSans3-VariableFont_wght.ttf"

SIZE = 1024
SS = 2  # supersample: draw at 2048, downscale once with LANCZOS

# Palette: bone paper, six story colours, an ink date-check band.
BONE = (243, 238, 228)
INK = (18, 17, 22)
WHITE = (255, 255, 255)
VERMILION = (203, 46, 38)
DEEPSEA = (10, 66, 88)
SEA = (22, 108, 134)
MAROON = (98, 20, 38)
INDIGO = (44, 48, 142)
MOSS = (24, 104, 64)
BRONZE = (154, 100, 16)
LACQUER = (198, 58, 34)
AMBER = (247, 190, 40)
SAND = (250, 220, 160)
MIST = (190, 214, 226)
ROSE = (244, 200, 198)
LEAF = (196, 228, 200)
CREAM = (255, 240, 198)

WARN = []


# ------------------------------------------------------------------ type ----

_fonts = {}


def face(px, display=True, weight=700):
    """Font at a size given in 1024-canvas units (built at supersample size)."""
    key = (display, round(px, 1), weight)
    if key not in _fonts:
        if display:
            _fonts[key] = ImageFont.truetype(DISPLAY, max(1, int(px * SS)))
        else:
            f = ImageFont.truetype(TEXT, max(1, int(px * SS)))
            f.set_variation_by_axes([float(weight)])
            _fonts[key] = f
    return _fonts[key]


def gap(font, extra):
    """Word advance: the space glyph plus extra tracking, so words breathe."""
    return (font.getlength(" ") / SS) + extra


def measure(words, font, extra):
    if not words:
        return 0.0
    return (sum(font.getlength(w) for w in words) / SS
            + gap(font, extra) * (len(words) - 1))


def wrap(s, font, max_w, extra):
    lines, cur = [], []
    for w in s.split(" "):
        if cur and measure(cur + [w], font, extra) > max_w:
            lines.append(cur)
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(cur)
    return lines


def fit(s, box_w, box_h, hi, lo, lead, extra, display=True, weight=700):
    """Biggest size <= hi whose wrapped block fits the box; never below lo."""
    px = hi
    while px >= lo:
        f = face(px, display, weight)
        ls = wrap(s, f, box_w, extra)
        if len(ls) * px * lead <= box_h and all(
                measure(l, f, extra) <= box_w for l in ls):
            return f, ls, px
        px -= 1
    f = face(lo, display, weight)
    WARN.append("tight at %dpx: %r" % (lo, s))
    return f, wrap(s, f, box_w, extra), lo


class Pen:
    """Draws in 1024-canvas units onto the supersampled bitmap."""

    def __init__(self, draw):
        self.d = draw

    def _b(self, box):
        return [box[0] * SS, box[1] * SS, box[2] * SS, box[3] * SS]

    def _p(self, pts):
        return [(x * SS, y * SS) for x, y in pts]

    def rect(self, box, fill):
        self.d.rectangle(self._b(box), fill=fill)

    def poly(self, pts, fill):
        self.d.polygon(self._p(pts), fill=fill)

    def ell(self, box, fill=None, outline=None, width=0):
        self.d.ellipse(self._b(box), fill=fill, outline=outline,
                       width=int(width * SS))

    def pie(self, box, a0, a1, fill):
        self.d.pieslice(self._b(box), a0, a1, fill=fill)

    def arc(self, box, a0, a1, fill, width):
        self.d.arc(self._b(box), a0, a1, fill=fill,
                   width=max(1, int(width * SS)))

    def line(self, pts, fill, width, joint=None):
        self.d.line(self._p(pts), fill=fill, width=max(1, int(width * SS)),
                    joint=joint)

    # -- text ---------------------------------------------------------------

    def words(self, x, y, words, font, fill, extra, align="left", box_w=None):
        if align != "left" and box_w:
            slack = box_w - measure(words, font, extra)
            x += slack / 2 if align == "center" else slack
        step = gap(font, extra)
        for w in words:
            self.d.text((x * SS, y * SS), w, font=font, fill=fill, anchor="la")
            x += font.getlength(w) / SS + step

    def block(self, s, x, y, w, h, hi, lo, fill, lead=1.05, extra=3.0,
              align="left", display=True, weight=700):
        """Wrapped shrink-to-fit block. Returns the y after the last line."""
        f, ls, px = fit(s, w, h, hi, lo, lead, extra, display, weight)
        for i, line in enumerate(ls):
            self.words(x, y + i * px * lead, line, f, fill, extra, align, w)
        return y + len(ls) * px * lead


# ------------------------------------------------------------ pictograms ----
# Every mark below is drawn from primitives here: no traced or imported art.
# `bg` is the panel colour, used to knock shapes back out of a filled mass.


def ico_capsized(p, x, y, w, h, bg, fg, acc, bleed=0):
    """A warship rolled over: hull up, bilge strake and screws out of the
    water, bow to the right, with sea drones running in from astern. The
    water runs `bleed` px past the box on each side, out to the panel edge."""
    def P(pts):
        return [(x + w * a, y + h * b) for a, b in pts]

    sea_y = y + h * 0.70
    # the upturned hull, stern settling to the left, bow lifted at the right
    p.poly(P([(0.07, 0.56), (0.12, 0.34), (0.32, 0.24), (0.60, 0.18),
              (0.80, 0.21), (0.93, 0.40), (0.92, 0.94), (0.08, 0.94)]),
           fill=fg)
    # bilge strake: a thin line following the keel, so it reads as a hull
    p.line(P([(0.13, 0.52), (0.34, 0.37), (0.60, 0.31), (0.80, 0.34),
              (0.90, 0.48)]), fill=bg, width=h * 0.05, joint="curve")
    # screws and rudder standing clear of the water at the stern
    cx, cy, r = x + w * 0.105, y + h * 0.28, h * 0.075
    for k in range(3):
        a = math.radians(-60 + k * 120)
        p.poly([(cx, cy),
                (cx + math.cos(a) * r * 2.4, cy + math.sin(a) * r * 2.4),
                (cx + math.cos(a + 0.75) * r * 2.1,
                 cy + math.sin(a + 0.75) * r * 2.1)], fill=fg)
    p.ell([cx - r, cy - r, cx + r, cy + r], fill=fg)
    p.poly(P([(0.025, 0.46), (0.075, 0.42), (0.085, 0.72), (0.025, 0.72)]),
           fill=fg)
    # the sea closes over her, running out to the panel edges
    p.rect([x - bleed, sea_y, x + w + bleed, y + h], fill=SEA)
    for x0, x1, yf in ((-0.06, 0.54, 0.02), (0.62, 1.06, 0.10),
                       (0.40, 1.06, 0.19)):
        yy = sea_y + h * yf
        p.rect([x + w * x0, yy, x + w * x1, yy + h * 0.055], fill=fg)
    # two sea drones running in, wakes behind them
    for i in range(2):
        dx = x + w * (0.015 + i * 0.13)
        dy = sea_y + h * (0.10 + i * 0.12)
        p.poly([(dx + w * 0.075, dy + h * 0.035), (dx, dy),
                (dx + w * 0.016, dy + h * 0.038), (dx, dy + h * 0.076)],
               fill=acc)
        p.rect([dx - w * 0.045, dy + h * 0.026, dx - w * 0.006,
                dy + h * 0.050], fill=acc)


def ico_mourning(p, x, y, w, h, bg, fg, acc):
    """A memorial candle beside the block of flats with its stairwell gone."""
    cw = w * 0.16
    cx = x + w * 0.03
    base = y + h
    p.rect([cx, y + h * 0.44, cx + cw, base], fill=fg)
    p.rect([cx - w * 0.03, base - h * 0.07, cx + cw + w * 0.03, base], fill=fg)
    p.rect([cx + cw * 0.40, y + h * 0.34, cx + cw * 0.60, y + h * 0.45],
           fill=fg)
    fx = cx + cw * 0.5
    fr = cw * 0.46
    p.ell([fx - fr, y + h * 0.22, fx + fr, y + h * 0.38], fill=acc)
    p.poly([(fx, y + h * 0.04), (fx + fr, y + h * 0.31),
            (fx - fr, y + h * 0.31)], fill=acc)
    # the five-storey block: one entrance section gone, ground to roof
    bx, bw = x + w * 0.32, w * 0.68
    by, bh = y + h * 0.15, h * 0.78
    p.rect([bx, by, bx + bw, by + bh], fill=fg)
    p.rect([x + w * 0.26, by + bh, x + w, by + bh + h * 0.06], fill=fg)
    gx0, gx1 = bx + bw * 0.455, bx + bw * 0.555
    p.rect([gx0, by - h * 0.03, gx1, by + bh], fill=bg)
    step = bh / 10.0
    for i in range(10):
        nub = bw * (0.038 if i % 2 else 0.014)
        p.rect([gx0, by + i * step, gx0 + nub, by + (i + 1) * step], fill=fg)
        p.rect([gx1 - nub, by + i * step, gx1, by + (i + 1) * step], fill=fg)
    # the torn roofline either side of the missing section
    p.poly([(gx0 - bw * 0.07, by), (gx0, by + step * 0.5),
            (gx0, by - h * 0.02)], fill=fg)
    p.poly([(gx1 + bw * 0.07, by), (gx1, by + step * 0.5),
            (gx1, by - h * 0.02)], fill=fg)
    ch = bh / 5.0
    for r in range(5):
        for c in (0.08, 0.25, 0.65, 0.82):
            wx = bx + bw * c
            wy = by + r * ch + ch * 0.28
            p.rect([wx, wy, wx + bw * 0.11, wy + ch * 0.40], fill=bg)
    # rubble heaped where the entrance section came down
    p.poly([(gx0 - bw * 0.30, by + bh + h * 0.04),
            (gx1 + bw * 0.28, by + bh + h * 0.04),
            (gx1 + bw * 0.06, by + bh - ch * 1.05),
            (gx0 + bw * 0.02, by + bh - ch * 1.35),
            (gx0 - bw * 0.14, by + bh - ch * 0.45)], fill=acc)


def ico_tally(p, x, y, w, h, bg, fg, acc):
    """A drone wave coming in over an air-defence arc; most of it breaking up."""
    for k, inset in ((1.0, 0.0), (0.74, 0.13)):
        p.arc([x + w * inset, y + h * (1.58 - 0.98 * k),
               x + w * (1 - inset), y + h * 1.58], 200, 340,
              fill=acc, width=h * 0.055)
    darts = ((0.02, 0.00, 1.2), (0.44, 0.08, 1.2), (0.06, 0.30, 1.05))
    for i, (fx, fy, sc) in enumerate(darts):
        dx, dy = x + w * fx, y + h * fy
        L = w * 0.30 * sc
        p.poly([(dx + L, dy + L * 0.30), (dx, dy),
                (dx + L * 0.28, dy + L * 0.33), (dx, dy + L * 0.60)], fill=fg)
        if i >= 1:  # the ones that were stopped carry a burst at the nose
            bx, by = dx + L * 1.02, dy + L * 0.30
            for ang in range(0, 360, 45):
                ra = math.radians(ang)
                p.line([(bx, by), (bx + math.cos(ra) * L * 0.46,
                                   by + math.sin(ra) * L * 0.46)],
                       fill=acc, width=h * 0.05)


def ico_accord(p, x, y, w, h, bg, fg, acc):
    """A signed sheet, ruled and initialled, with a ribbon seal on its foot."""
    sx, sw = x + w * 0.03, w * 0.80
    sy, sh = y, h * 0.92
    p.rect([sx, sy, sx + sw, sy + sh], fill=fg)
    for r in range(4):
        p.rect([sx + sw * 0.14, sy + sh * (0.10 + r * 0.145),
                sx + sw * (0.86 if r < 3 else 0.60),
                sy + sh * (0.165 + r * 0.145)], fill=bg)
    # a signature run along the last rule
    p.line([(sx + sw * 0.16, sy + sh * 0.78), (sx + sw * 0.30, sy + sh * 0.68),
            (sx + sw * 0.40, sy + sh * 0.80), (sx + sw * 0.54, sy + sh * 0.66),
            (sx + sw * 0.66, sy + sh * 0.80)],
           fill=bg, width=h * 0.045, joint="curve")
    r0 = w * 0.19
    scx, scy = sx + sw * 0.94, sy + sh * 0.80
    p.poly([(scx - r0 * 0.7, scy), (scx - r0 * 0.25, scy + h * 0.20),
            (scx + r0 * 0.1, scy + h * 0.10), (scx + r0 * 0.45, scy + h * 0.20),
            (scx + r0 * 0.7, scy)], fill=acc)
    p.ell([scx - r0, scy - r0, scx + r0, scy + r0], fill=acc)
    p.ell([scx - r0 * 0.36, scy - r0 * 0.36, scx + r0 * 0.36, scy + r0 * 0.36],
          fill=bg)


def ico_umbrella(p, x, y, w, h, bg, fg, acc):
    """A radar aircraft flying above an air-defence dome over a border line."""
    # dome: a thick arc standing on the flank it is meant to cover
    p.arc([x + w * 0.01, y + h * 0.44, x + w * 0.99, y + h * 1.42], 180, 360,
          fill=fg, width=h * 0.12)
    p.rect([x, y + h * 0.90, x + w, y + h * 0.975], fill=fg)
    for c in (0.06, 0.40, 0.74):
        p.rect([x + w * c, y + h * 0.78, x + w * (c + 0.20), y + h * 0.855],
               fill=acc)
    # allied aircraft holding above it: fuselage, swept wings, tailplane
    p.poly([(x + w * 0.98, y + h * 0.16), (x + w * 0.30, y + h * 0.10),
            (x + w * 0.12, y + h * 0.17), (x + w * 0.30, y + h * 0.24),
            (x + w * 0.96, y + h * 0.22)], fill=fg)
    p.poly([(x + w * 0.62, y + h * 0.15), (x + w * 0.80, y + h * 0.15),
            (x + w * 0.56, y + h * 0.40), (x + w * 0.38, y + h * 0.40)],
           fill=fg)
    p.poly([(x + w * 0.20, y + h * 0.13), (x + w * 0.30, y + h * 0.13),
            (x + w * 0.22, y + h * 0.00), (x + w * 0.12, y + h * 0.00)],
           fill=fg)


def ico_hall(p, x, y, w, h, bg, fg, acc):
    """The rebuilt main hall with its doors standing open at last."""
    ry, rh = y + h * 0.05, h * 0.34
    # deep hipped roof, eaves sweeping well past the body
    p.poly([(x + w * 0.36, ry), (x + w * 0.64, ry),
            (x + w * 0.94, ry + rh * 0.66), (x + w, ry + rh * 0.98),
            (x + w * 0.88, ry + rh * 0.80), (x + w * 0.12, ry + rh * 0.80),
            (x, ry + rh * 0.98), (x + w * 0.06, ry + rh * 0.66)], fill=fg)
    p.pie([x + w * 0.32, ry - h * 0.10, x + w * 0.68, ry + rh * 0.86], 180, 360,
          fill=fg)
    p.rect([x + w * 0.46, ry - h * 0.13, x + w * 0.54, ry - h * 0.02],
           fill=acc)
    by = ry + rh * 0.80
    bh = h * 0.42
    p.rect([x + w * 0.20, by, x + w * 0.80, by + bh], fill=fg)
    # the doorway standing open, light falling out of it
    p.rect([x + w * 0.38, by + bh * 0.10, x + w * 0.62, by + bh], fill=acc)
    p.poly([(x + w * 0.38, by + bh * 0.10), (x + w * 0.28, by + bh * 0.24),
            (x + w * 0.28, by + bh), (x + w * 0.38, by + bh)], fill=fg)
    p.poly([(x + w * 0.62, by + bh * 0.10), (x + w * 0.72, by + bh * 0.24),
            (x + w * 0.72, by + bh), (x + w * 0.62, by + bh)], fill=fg)
    sy = by + bh
    for i in range(2):
        p.rect([x + w * (0.26 - i * 0.13), sy + i * h * 0.07,
                x + w * (0.74 + i * 0.13), sy + (i + 1) * h * 0.07], fill=fg)


# --------------------------------------------------------------- compose ----


def render(path):
    img = Image.new("RGB", (SIZE * SS, SIZE * SS), BONE)
    p = Pen(ImageDraw.Draw(img))

    M, G = 16, 14
    FULL = SIZE - 2 * M
    HALF = (FULL - G) / 2.0

    # --- date banner: one huge line across the whole width -------------------
    ban_y, ban_h = M, 104
    p.rect([M, ban_y, M + FULL, ban_y + ban_h], fill=WHITE)
    p.rect([M, ban_y, M + 14, ban_y + ban_h], fill=VERMILION)
    date = ["MONDAY", "23", "NOVEMBER", "2026"]
    dpx, df = 80, None
    while dpx > 44:
        df = face(dpx)
        if measure(date, df, 9) <= FULL - 52:
            break
        dpx -= 1
    dx = M + 34
    dy = ban_y + (ban_h - dpx * 1.16) / 2
    p.words(dx, dy, date[:1], df, VERMILION, 9)
    p.words(dx + measure(date[:1], df, 9) + gap(df, 9), dy, date[1:], df, INK, 9)

    # --- two leads of equal weight -------------------------------------------
    ly, lh = ban_y + ban_h + G, 340

    # lead 1: Zelenskyy's Monday claim about the corvette Merkury
    p.rect([M, ly, M + HALF, ly + lh], fill=DEEPSEA)
    p.rect([M, ly, M + HALF, ly + 10], fill=AMBER)
    ico_capsized(p, M + 26, ly + 22, HALF - 52, 112, DEEPSEA, WHITE, AMBER,
                 bleed=26)
    yy = p.block("MERKURY SUNK AT BENGHAZI", M + 24, ly + 148, HALF - 48, 112,
                 52, 42, WHITE, lead=1.03, extra=4)
    p.block("ZELENSKYY: SEVEN SEA DRONES SANK RUSSIAN SHIP",
            M + 24, yy + 10, HALF - 48, 74, 34, 32, MIST, lead=1.08, extra=2.5,
            display=False, weight=800)

    # lead 2: Kyiv region day of mourning, Dymer toll
    x2 = M + HALF + G
    p.rect([x2, ly, x2 + HALF, ly + lh], fill=MAROON)
    p.rect([x2, ly, x2 + HALF, ly + 10], fill=INK)
    ico_mourning(p, x2 + 24, ly + 22, 222, 114, MAROON, WHITE, AMBER)
    pw = 182
    px0 = x2 + HALF - 24 - pw
    p.rect([px0, ly + 24, px0 + pw, ly + 138], fill=AMBER)
    p.block("11", px0, ly + 18, pw, 94, 92, 70, INK, align="center", extra=4)
    p.block("DEAD", px0, ly + 102, pw, 36, 32, 28, INK, align="center",
            extra=6)
    yy = p.block("DYMER: KYIV REGION MOURNS", x2 + 24, ly + 148, HALF - 48, 112,
                 52, 42, WHITE, lead=1.03, extra=4)
    p.block("WOMAN, 79, PULLED OUT ALIVE AT 03:28",
            x2 + 24, yy + 10, HALF - 48, 74, 34, 32, ROSE, lead=1.08, extra=2.5,
            display=False, weight=800)

    # --- four story tiles -----------------------------------------------------
    tiles = [
        (INDIGO, ico_tally, "153 DRONES, 134 DOWNED",
         "AIR FORCE, 08:00", AMBER, MIST),
        (MOSS, ico_accord, "MODI, SHAH SIGN 8 MoUs",
         "24,000 CRORE NPR", AMBER, LEAF),
        (BRONZE, ico_umbrella, "NATO COUNCIL MET",
         "POLAND ASKS AIR COVER", INK, CREAM),
        (LACQUER, ico_hall, "SHURI CASTLE OPENED",
         "NAHA, OKINAWA, NOON", AMBER, SAND),
    ]
    ty0 = ly + lh + G
    th = 186
    for i, (col, ico, head, kick, acc, kcol) in enumerate(tiles):
        tx = M + (i % 2) * (HALF + G)
        ty = ty0 + (i // 2) * (th + G)
        p.rect([tx, ty, tx + HALF, ty + th], fill=col)
        ico(p, tx + 18, ty + 30, 82, 92, col, WHITE, acc)
        cx0 = tx + 18 + 82 + 12
        cw = HALF - (cx0 - tx) - 16
        yy = p.block(head, cx0, ty + 16, cw, 93, 44, 40, WHITE, lead=1.04,
                     extra=3)
        p.block(kick, cx0, yy + 8, cw, 44, 34, 32, kcol, lead=1.06, extra=1.5,
                display=False, weight=800)

    # --- date check -----------------------------------------------------------
    dy2 = ty0 + 2 * (th + G)
    dh = SIZE - M - dy2
    p.rect([M, dy2, M + FULL, dy2 + dh], fill=INK)
    cw_ = 176
    p.rect([M + 20, dy2 + 22, M + 20 + cw_, dy2 + 22 + 84], fill=AMBER)
    p.block("NOT MONDAY", M + 20, dy2 + 28, cw_, 76, 34, 28, INK, lead=1.02,
            align="center", extra=3)
    lx = M + 20 + cw_ + 20
    lw = M + FULL - 22 - lx
    yy = dy2 + 24
    for line in ("COP31 ENDED SUNDAY WITH NO TEXT ADOPTED",
                 "POLAND MISSILES FRIDAY; CIKANDE FIRE SATURDAY"):
        yy = p.block(line, lx, yy, lw, 44, 36, 32, WHITE, extra=3,
                     display=False, weight=800) + 8

    out = img.resize((SIZE, SIZE), Image.LANCZOS)
    out.save(path, "PNG", optimize=True)
    here = os.path.dirname(os.path.abspath(path))
    out.resize((300, 300), Image.LANCZOS).save(
        os.path.join(here, "preview_300.png"), "PNG", optimize=True)
    return path


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "entry.png")
    render(target)
    for w in WARN:
        print("WARN", w)
    print(target, os.path.getsize(target), "bytes")
