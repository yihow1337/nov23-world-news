#!/usr/bin/env python3
"""Local renderer for entry.png (Pillow). Not used by main.py.

Draws a 1024x1024 editorial summary of Monday 23 November 2026 world news.
Design rules it follows: 300px-first (huge date, headlines >= 40px, kickers
>= 32px on the 1024 canvas), one original pictogram per story, one distinct
colour per tile, generous whitespace, no micro caption strips.

Usage:  python3 tools/render.py [out_path]
Writes the PNG and a preview_300.png beside it for the 300px legibility check.
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

GOOGLE = "/usr/share/fonts/truetype/sand-box/google"
ANTON = f"{GOOGLE}/Anton/Anton-Regular.ttf"
INTER = f"{GOOGLE}/Inter/Inter-VariableFont_opsz,wght.ttf"

SIZE = 1024
SS = 2  # supersample factor: draw big, downscale once with LANCZOS

INK = (12, 14, 17)
PAPER = (255, 255, 255)
CRIMSON = (176, 16, 48)
NAVY = (30, 48, 80)
BLUE = (23, 87, 200)
TEAL = (14, 122, 107)
ORANGE = (200, 81, 26)
VIOLET = (107, 63, 181)
YELLOW = (245, 196, 0)
WHITE = (255, 255, 255)
FOG = (206, 216, 230)
WARN = []


# ---------------------------------------------------------------- type system

_cache = {}


def anton(px):
    key = ("anton", px)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(ANTON, int(px))
    return _cache[key]


def inter(px, weight=700):
    key = ("inter", px, weight)
    if key not in _cache:
        f = ImageFont.truetype(INTER, int(px))
        f.set_variation_by_axes([32.0, float(weight)])
        _cache[key] = f
    return _cache[key]


def word_gap(font, extra):
    """Space advance plus extra tracking: Source Sans 3 and friends run words
    together when set tight, so every string is drawn word by word."""
    return font.getlength(" ") + extra


def text_width(s, font, extra=0.0):
    words = s.split(" ")
    gap = word_gap(font, extra)
    return sum(font.getlength(w) for w in words) + gap * (len(words) - 1)


def draw_words(d, xy, s, font, fill, extra=0.0, align="left", box_w=None):
    """Draw one line word by word so word spacing stays generous."""
    x, y = xy
    if align != "left" and box_w:
        slack = box_w - text_width(s, font, extra)
        x += slack / 2 if align == "center" else slack
    gap = word_gap(font, extra)
    for w in s.split(" "):
        d.text((x, y), w, font=font, fill=fill, anchor="la")
        x += font.getlength(w) + gap
    return x - gap


def wrap(s, font, max_w, extra=0.0):
    lines, cur = [], ""
    for w in s.split(" "):
        trial = w if not cur else cur + " " + w
        if text_width(trial, font, extra) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_lines(s, max_px, min_px, max_w, max_h, lead=1.06, extra=0.0, maker=anton):
    """Largest size at or under max_px whose wrapped block fits the box."""
    px = max_px
    while px >= min_px:
        f = maker(px * SS)
        ls = wrap(s, f, max_w * SS, extra * SS)
        h = len(ls) * px * lead
        if h <= max_h and max(text_width(l, f, extra * SS) for l in ls) <= max_w * SS:
            return f, ls, px
        px -= 1
    f = maker(min_px * SS)
    WARN.append(f"overflow at min size {min_px}px: {s!r}")
    return f, wrap(s, f, max_w * SS, extra * SS), min_px


def block(d, s, x, y, w, max_px, min_px, max_h, fill, lead=1.06, extra=0.0,
          align="left", maker=anton):
    """Draw a wrapped, shrink-to-fit text block. Returns the y after it."""
    f, ls, px = fit_lines(s, max_px, min_px, w, max_h, lead, extra, maker)
    for i, line in enumerate(ls):
        draw_words(d, (x * SS, (y + i * px * lead) * SS), line, f, fill,
                   extra * SS, align, w * SS)
    return y + len(ls) * px * lead


def chip(d, s, x, y, px, bg, fg, pad=(10, 5)):
    """Small solid label chip; px is the type size on the 1024 canvas."""
    f = anton(px * SS)
    w = text_width(s, f, 2 * SS) / SS + pad[0] * 2
    h = px * 1.18 + pad[1] * 2
    d.rectangle([x * SS, y * SS, (x + w) * SS, (y + h) * SS], fill=bg)
    draw_words(d, ((x + pad[0]) * SS, (y + pad[1] - px * 0.1) * SS), s, f, fg, 2 * SS)
    return w, h


# ----------------------------------------------------------------- pictograms
# All original: built from rectangles, polygons, arcs and lines.


ICON_BG = [NAVY]  # tile colour behind the current pictogram, for knockouts


def ico_mourning(d, x, y, w, h, fg, accent):
    """Half-mast flag beside a block of flats with its entrance section gone."""
    bg = ICON_BG[0]
    lw = max(2, int(h * 0.030))
    # flagpole, left, with the flag lowered to half-mast
    px_ = x + w * 0.07
    d.rectangle([px_ - lw, y + h * 0.03, px_ + lw, y + h], fill=fg)
    d.ellipse([px_ - lw * 2, y, px_ + lw * 2, y + h * 0.045], fill=fg)
    fy = y + h * 0.48
    d.rectangle([px_, fy, px_ + w * 0.22, fy + h * 0.19], fill=fg)
    d.polygon([(px_ + w * 0.22, fy), (px_ + w * 0.16, fy + h * 0.095),
               (px_ + w * 0.22, fy + h * 0.19)], fill=bg)
    # the block of flats, one solid mass standing on a ground line
    bx, bw = x + w * 0.34, w * 0.66
    by, bh = y + h * 0.14, h * 0.82
    d.rectangle([bx, by, bx + bw, by + bh], fill=fg)
    d.rectangle([x, y + h * 0.955, x + w, y + h], fill=fg)
    # the destroyed entrance section, top floor to ground
    gx0, gx1 = bx + bw * 0.38, bx + bw * 0.54
    d.rectangle([gx0, by - lw, gx1, by + bh], fill=bg)
    step = bh / 9.0
    for i in range(9):
        off = bw * (0.05 if i % 2 else 0.018)
        d.rectangle([gx0, by + i * step, gx0 + off, by + (i + 1) * step], fill=fg)
        d.rectangle([gx1 - off, by + i * step, gx1, by + (i + 1) * step], fill=fg)
    # windows, skipping the void
    rows = 4
    ch = bh / rows
    for r in range(rows):
        for c in (0.06, 0.21, 0.62, 0.79):
            wx = bx + bw * c
            wy = by + r * ch + ch * 0.26
            d.rectangle([wx, wy, wx + bw * 0.14, wy + ch * 0.46], fill=bg)
    # rubble heaped at its foot
    d.polygon([(gx0 - bw * 0.26, y + h * 0.955), (gx1 + bw * 0.22, y + h * 0.955),
               (gx1 + bw * 0.04, by + bh - ch * 0.85),
               (gx0 + bw * 0.06, by + bh - ch * 0.45)], fill=accent)


def ico_drones(d, x, y, w, h, fg, accent):
    """Three strike drones in echelon with alert waves behind them."""
    lw = max(2, int(h * 0.055))
    for i in range(3):
        L = h * (0.52 + 0.10 * i)
        ax = x + w * (0.26 + 0.27 * i)
        ay = y + h * (0.70 - 0.26 * i)
        # fuselage: long nose to the right
        d.polygon([(ax + L, ay), (ax + L * 0.18, ay + L * 0.18),
                   (ax, ay + L * 0.10)], fill=fg)
        # straight wing crossing the body
        d.polygon([(ax + L * 0.46, ay + L * 0.02), (ax + L * 0.56, ay + L * 0.06),
                   (ax + L * 0.30, ay + L * 0.40), (ax + L * 0.20, ay + L * 0.34)],
                  fill=fg)
        # V tail
        d.polygon([(ax + L * 0.02, ay + L * 0.08), (ax + L * 0.12, ay + L * 0.12),
                   (ax - L * 0.06, ay + L * 0.30), (ax - L * 0.13, ay + L * 0.24)],
                  fill=accent)
    # alert waves, lower left
    cx, cy = x + w * 0.02, y + h * 1.02
    for k in (1, 2, 3):
        r = h * 0.26 * k
        d.arc([cx - r, cy - r, cx + r, cy + r], 268, 352, fill=accent, width=lw)


def ico_council(d, x, y, w, h, fg, accent):
    """Round table seen from above, eight seats, a star knocked out of it."""
    import math
    bg = ICON_BG[0]
    cx, cy = x + w / 2, y + h / 2
    rx, ry = w * 0.30, h * 0.30
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fg)
    k = ry * 0.74
    d.polygon([(cx, cy - k), (cx + k * 0.30, cy - k * 0.26),
               (cx + k * 1.25, cy), (cx + k * 0.30, cy + k * 0.26),
               (cx, cy + k), (cx - k * 0.30, cy + k * 0.26),
               (cx - k * 1.25, cy), (cx - k * 0.30, cy - k * 0.26)], fill=bg)
    for i in range(8):
        a = math.radians(i * 45 + 22.5)
        sx = cx + math.cos(a) * rx * 1.62
        sy = cy + math.sin(a) * ry * 1.62
        sr = min(w, h) * 0.075
        d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=accent)


def ico_handshake(d, x, y, w, h, fg, accent):
    """Two flags on poles: Nepal's double pennant meeting a wheel flag."""
    lw = max(2, int(h * 0.05))
    # Nepal: twin pennants
    p1 = x + w * 0.10
    d.rectangle([p1 - lw * 0.8, y + h * 0.04, p1 + lw * 0.8, y + h], fill=fg)
    d.polygon([(p1, y + h * 0.06), (p1 + w * 0.30, y + h * 0.26),
               (p1, y + h * 0.30)], fill=fg)
    d.polygon([(p1, y + h * 0.26), (p1 + w * 0.32, y + h * 0.50),
               (p1, y + h * 0.56)], fill=fg)
    # India: flag with a wheel
    p2 = x + w * 0.58
    d.rectangle([p2 - lw * 0.8, y + h * 0.04, p2 + lw * 0.8, y + h], fill=fg)
    d.rectangle([p2, y + h * 0.10, p2 + w * 0.40, y + h * 0.46], fill=fg)
    cx = p2 + w * 0.20
    cy = y + h * 0.28
    r = h * 0.11
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=accent)
    d.ellipse([cx - r * 0.34, cy - r * 0.34, cx + r * 0.34, cy + r * 0.34],
              fill=fg)
    # ground line the two poles stand on
    d.rectangle([x, y + h * 0.96, x + w, y + h], fill=accent)


def ico_castle(d, x, y, w, h, fg, accent):
    """Shuri-style hall: deep hipped roof with upturned eaves, bays, stairs."""
    lw = max(2, int(h * 0.05))
    ry = y + h * 0.14
    rh = h * 0.34
    d.polygon([(x + w * 0.30, ry), (x + w * 0.70, ry),
               (x + w * 0.98, ry + rh * 0.78), (x + w * 1.0, ry + rh),
               (x + w * 0.86, ry + rh * 0.92), (x + w * 0.14, ry + rh * 0.92),
               (x, ry + rh), (x + w * 0.02, ry + rh * 0.78)], fill=fg)
    # the curved central gable over the entrance
    d.pieslice([x + w * 0.28, ry - h * 0.09, x + w * 0.72, ry + rh * 0.95],
               180, 360, fill=fg)
    d.rectangle([x + w * 0.47, ry - h * 0.15, x + w * 0.53, ry - h * 0.05],
                fill=accent)
    # body with three bays
    by = ry + rh
    bh = h * 0.36
    d.rectangle([x + w * 0.10, by, x + w * 0.90, by + bh], fill=fg)
    for c in range(3):
        bx = x + w * (0.20 + c * 0.235)
        d.rectangle([bx, by + bh * 0.22, bx + w * 0.125, by + bh], fill=accent)
    # stairs
    sy = by + bh
    for i in range(3):
        d.rectangle([x + w * (0.22 - i * 0.07), sy + i * h * 0.06,
                     x + w * (0.78 + i * 0.07), sy + (i + 1) * h * 0.06], fill=fg)


def ico_dna(d, x, y, w, h, fg, accent):
    """Double helix with rungs beside an identification tag."""
    import math
    lw = max(3, int(h * 0.075))
    hx, hw = x + w * 0.06, w * 0.46
    pts_a, pts_b = [], []
    for i in range(41):
        t = i / 40.0
        yy = y + t * h
        off = math.sin(t * math.pi * 2.0) * hw * 0.42
        pts_a.append((hx + hw * 0.5 + off, yy))
        pts_b.append((hx + hw * 0.5 - off, yy))
    d.line(pts_a, fill=fg, width=lw, joint="curve")
    d.line(pts_b, fill=fg, width=lw, joint="curve")
    for i in (6, 14, 26, 34):
        d.line([pts_a[i], pts_b[i]], fill=accent, width=lw)
    # tag
    tx = x + w * 0.60
    d.rectangle([tx, y + h * 0.26, x + w, y + h * 0.78], outline=fg, width=lw)
    d.ellipse([tx + w * 0.05, y + h * 0.36, tx + w * 0.12, y + h * 0.46], fill=fg)
    for r in range(2):
        d.rectangle([tx + w * 0.16, y + h * (0.38 + r * 0.14),
                     x + w * 0.92, y + h * (0.44 + r * 0.14)], fill=accent)


# -------------------------------------------------------------------- compose

def tile(d, box, colour, radius=0):
    x, y, w, h = box
    d.rectangle([x * SS, y * SS, (x + w) * SS, (y + h) * SS], fill=colour)


def render(path):
    img = Image.new("RGB", (SIZE * SS, SIZE * SS), INK)
    d = ImageDraw.Draw(img)
    M, G = 16, 14  # margin, gutter
    FULL = SIZE - 2 * M

    # --- row A: date block + continuing drone attacks -----------------------
    ay, ah = M, 258
    dw = 520
    tile(d, (M, ay, dw, ah), PAPER)
    d.rectangle([M * SS, ay * SS, (M + dw) * SS, (ay + 10) * SS], fill=CRIMSON)
    block(d, "MONDAY", M + 26, ay + 22, dw - 52, 72, 56, 80, CRIMSON, extra=6)
    block(d, "23 NOVEMBER", M + 26, ay + 96, dw - 52, 72, 56, 80, INK, extra=6)
    block(d, "2026", M + 26, ay + 170, dw - 52, 72, 56, 80, INK, extra=6)
    chip(d, "WORLD NEWS", M + 250, ay + 178, 40, CRIMSON, PAPER, pad=(16, 9))

    kx = M + dw + G
    kw = FULL - dw - G
    tile(d, (kx, ay, kw, ah), CRIMSON)
    ICON_BG[0] = CRIMSON
    ico_drones(d, (kx + 30) * SS, (ay + 22) * SS, (kw - 76) * SS, 70 * SS,
               WHITE, (255, 214, 102))
    yy = block(d, "DRONES OVER UKRAINE ALL NIGHT", kx + 26, ay + 108,
               kw - 52, 46, 40, 104, WHITE, extra=4)
    block(d, "NO MORNING TALLY YET", kx + 26, yy + 10, kw - 52, 34, 32, 40,
          (255, 214, 102), extra=3, maker=lambda p: inter(p, 800))

    # --- row B: lead ---------------------------------------------------------
    by, bh = ay + ah + G, 252
    tile(d, (M, by, FULL, bh), NAVY)
    d.rectangle([M * SS, by * SS, (M + FULL) * SS, (by + 10) * SS], fill=CRIMSON)
    ICON_BG[0] = NAVY
    ico_mourning(d, (M + 26) * SS, (by + 48) * SS, 176 * SS, 156 * SS,
                 WHITE, CRIMSON)
    tx = M + 230
    # stat plate: the Monday toll
    sw = 170
    sx = M + FULL - 26 - sw
    d.rectangle([sx * SS, (by + 44) * SS, (sx + sw) * SS, (by + 212) * SS],
                fill=CRIMSON)
    block(d, "7", sx, by + 40, sw, 112, 90, 120, WHITE, align="center")
    block(d, "DEAD", sx, by + 162, sw, 36, 32, 42, WHITE, align="center", extra=6)
    tw = sx - G - tx
    block(d, "UKRAINE: KYIV REGION IN MOURNING", tx, by + 26, tw, 36, 32, 42,
          FOG, extra=5)
    yy = block(d, "DYMER TOLL RISES TO SEVEN", tx, by + 72, tw, 58, 50, 126,
               WHITE, extra=5)
    block(d, "SEVENTH BODY FOUND AT 00:53", tx, yy + 12, tw, 34, 32,
          40, FOG, extra=3, maker=lambda p: inter(p, 800))

    # --- rows C and D: four story cards --------------------------------------
    stories = [
        (BLUE, ico_council, "NATO COUNCIL MEETS IN BRUSSELS",
         "POLISH AIRSPACE", (255, 221, 85)),
        (TEAL, ico_handshake, "NEPAL PM MEETS MODI IN DELHI",
         "FIRST MEETING", (255, 226, 120)),
        (ORANGE, ico_castle, "SHURI CASTLE HALL OPENS AT NOON",
         "OKINAWA, JAPAN", (255, 232, 160)),
        (VIOLET, ico_dna, "INDONESIA: DNA SEARCH AFTER FIRE",
         "~50 UNACCOUNTED", (255, 226, 140)),
    ]
    cw = (FULL - G) / 2.0
    chh = 156
    for i, (col, ico, head, kick, acc) in enumerate(stories):
        x = M + (i % 2) * (cw + G)
        y = by + bh + G + (i // 2) * (chh + G)
        tile(d, (x, y, cw, chh), col)
        ICON_BG[0] = col
        ico(d, (x + 22) * SS, (y + 34) * SS, 94 * SS, 88 * SS, WHITE, acc)
        txx = x + 22 + 94 + 18
        tww = cw - (txx - x) - 18
        yy = block(d, head, txx, y + 14, tww, 43, 40, 92, WHITE, extra=3)
        block(d, kick, txx, yy + 8, tww, 34, 32, 40, acc, extra=2,
              maker=lambda p: inter(p, 800))

    # --- row E: date check ---------------------------------------------------
    dy = by + bh + G + 2 * (chh + G)
    dh = SIZE - M - dy
    tile(d, (M, dy, FULL, dh), YELLOW)
    block(d, "NOT MONDAY", M + 22, dy + 12, 230, 42, 38, 88, INK, lead=1.02,
          extra=4)
    lx = M + 272
    lw_ = FULL - 272 - 24
    ly = dy + 20
    for line in ("COP31 ENDED SUNDAY WITH NO TEXT ADOPTED",
                 "POLAND MISSILES FRIDAY; BENGHAZI + HK POLLS SUNDAY"):
        ly = block(d, line, lx, ly, lw_, 36, 32, 42, INK, extra=3) + 6

    out = img.resize((SIZE, SIZE), Image.LANCZOS)
    out.save(path, "PNG", optimize=True)
    prev = out.resize((300, 300), Image.LANCZOS)
    prev.save(os.path.join(os.path.dirname(os.path.abspath(path)),
                           "preview_300.png"), "PNG", optimize=True)
    return path


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "entry.png")
    render(target)
    for w in WARN:
        print("WARN", w)
    print(target, os.path.getsize(target), "bytes")
