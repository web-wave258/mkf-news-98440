#!/usr/bin/env python3
# make.fun competition entry: news-image-20261119
# Renders a 1024x768 newspaper-style front page summarising world news of
# Thursday 19 November 2026, written as a deterministic PNG using only the
# Python standard library (zlib + struct). No network, no randomness.
import hashlib
import os
import struct
import zlib

SEED = 'web-wave258'
W, H = 1024, 768
M = 24  # page margin in pixels

# ---------------------------------------------------------------------------
# 5x7 bitmap font: each character maps to 7 row values; bit 4 (0b10000) is
# the leftmost pixel of the row. Scaled by an integer factor when drawn.
# ---------------------------------------------------------------------------
FONT = {
    'A': (0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    'B': (0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110),
    'C': (0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110),
    'D': (0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110),
    'E': (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111),
    'F': (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000),
    'G': (0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111),
    'H': (0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    'I': (0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    'J': (0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100),
    'K': (0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001),
    'L': (0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111),
    'M': (0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001),
    'N': (0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001),
    'O': (0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    'P': (0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000),
    'Q': (0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101),
    'R': (0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001),
    'S': (0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110),
    'T': (0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    'U': (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    'V': (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    'W': (0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001),
    'X': (0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001),
    'Y': (0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100),
    'Z': (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111),
    '0': (0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110),
    '1': (0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    '2': (0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b01000, 0b11111),
    '3': (0b11111, 0b00010, 0b00100, 0b00010, 0b00001, 0b10001, 0b01110),
    '4': (0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010),
    '5': (0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110),
    '6': (0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110),
    '7': (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000),
    '8': (0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110),
    '9': (0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100),
    ' ': (0, 0, 0, 0, 0, 0, 0),
    '-': (0, 0, 0, 0b11111, 0, 0, 0),
    ':': (0, 0b00100, 0b00100, 0, 0b00100, 0b00100, 0),
    ',': (0, 0, 0, 0, 0, 0b00100, 0b01000),
    '.': (0, 0, 0, 0, 0, 0b00100, 0b00100),
    "'": (0b00100, 0b00100, 0, 0, 0, 0, 0),
    '!': (0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0, 0b00100),
    '?': (0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0, 0b00100),
    '/': (0b00001, 0b00010, 0b00010, 0b00100, 0b01000, 0b01000, 0b10000),
    '$': (0b00100, 0b01111, 0b10100, 0b01110, 0b00101, 0b11110, 0b00100),
    '%': (0b11001, 0b11010, 0b00010, 0b00100, 0b01000, 0b01011, 0b10011),
    '&': (0b01100, 0b10010, 0b10100, 0b01000, 0b10101, 0b10010, 0b01101),
    '(': (0b00010, 0b00100, 0b01000, 0b01000, 0b01000, 0b00100, 0b00010),
    ')': (0b01000, 0b00100, 0b00010, 0b00010, 0b00010, 0b00100, 0b01000),
    '+': (0, 0b00100, 0b00100, 0b11111, 0b00100, 0b00100, 0),
    '#': (0b01010, 0b01010, 0b11111, 0b01010, 0b11111, 0b01010, 0b01010),
    '|': (0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    # pound sign: top loop, two crossbars, stem
    chr(0xA3): (0b00110, 0b01001, 0b00100, 0b11110, 0b00100, 0b11110, 0b00100),
    chr(0xB7): (0, 0, 0, 0b01100, 0b01100, 0, 0),  # middle dot
    'a': (0, 0, 0b01110, 0b00001, 0b01111, 0b10001, 0b01111),
    'b': (0b10000, 0b10000, 0b11110, 0b10001, 0b10001, 0b10001, 0b11110),
    'c': (0, 0, 0b01110, 0b10000, 0b10000, 0b10001, 0b01110),
    'd': (0b00001, 0b00001, 0b01111, 0b10001, 0b10001, 0b10001, 0b01111),
    'e': (0, 0, 0b01110, 0b10001, 0b11111, 0b10000, 0b01110),
    'f': (0b00110, 0b01001, 0b01000, 0b11100, 0b01000, 0b01000, 0b01000),
    'g': (0, 0b01111, 0b10001, 0b10001, 0b01111, 0b00001, 0b01110),
    'h': (0b10000, 0b10000, 0b11110, 0b10001, 0b10001, 0b10001, 0b10001),
    'i': (0b00100, 0, 0b01100, 0b00100, 0b00100, 0b00100, 0b01110),
    'j': (0b00010, 0, 0b00110, 0b00010, 0b00010, 0b10010, 0b01100),
    'k': (0b10000, 0b10000, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010),
    'l': (0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    'm': (0, 0, 0b11010, 0b10101, 0b10101, 0b10101, 0b10101),
    'n': (0, 0, 0b11110, 0b10001, 0b10001, 0b10001, 0b10001),
    'o': (0, 0, 0b01110, 0b10001, 0b10001, 0b10001, 0b01110),
    'p': (0, 0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000),
    'q': (0, 0b01111, 0b10001, 0b10001, 0b01111, 0b00001, 0b00001),
    'r': (0, 0, 0b10110, 0b11001, 0b10000, 0b10000, 0b10000),
    's': (0, 0, 0b01111, 0b10000, 0b01110, 0b00001, 0b11110),
    't': (0b01000, 0b01000, 0b11100, 0b01000, 0b01000, 0b01001, 0b00110),
    'u': (0, 0, 0b10001, 0b10001, 0b10001, 0b10011, 0b01101),
    # half-height row for scale-1 small print (struck on the baseline)
    '~': (0, 0, 0, 0b10001, 0b10001, 0b10001, 0b01110),
    'v': (0, 0, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    'w': (0, 0, 0b10101, 0b10101, 0b10101, 0b10101, 0b01010),
    'x': (0, 0, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001),
    'y': (0, 0b10001, 0b10001, 0b01111, 0b00001, 0b00001, 0b01110),
    'z': (0, 0, 0b11111, 0b00010, 0b00100, 0b01000, 0b11111),
}

# ---------------------------------------------------------------------------
# Palette. The two accent colours are picked deterministically from the
# entrant seed so this entry's bytes are unique to web-wave258.
# ---------------------------------------------------------------------------
_PALETTES = (
    (142, 28, 28),   # oxblood red
    (18, 48, 88),    # midnight navy
    (16, 84, 58),    # forest green
    (96, 26, 84),    # plum
    (0, 96, 104),    # deep teal
    (122, 52, 24),   # rust
)
_d = hashlib.sha256(SEED.encode()).digest()
PRIMARY = _PALETTES[_d[0] % len(_PALETTES)]
SECONDARY = _PALETTES[(_d[0] + 1 + _d[1]) % len(_PALETTES)]
if SECONDARY == PRIMARY:
    SECONDARY = _PALETTES[(_d[0] + 2) % len(_PALETTES)]
PAPER = (246, 240, 227)
PAPER2 = (238, 230, 212)
INK = (26, 24, 20)
INK2 = (78, 72, 62)


class Canvas(object):
    # Simple RGB raster with clipping; pixels live in one bytearray.

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(bytes(bg) * (w * h))

    def rect(self, x, y, w, h, col):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(col) * (x1 - x0)
        for yy in range(y0, y1):
            off = (yy * self.w + x0) * 3
            self.buf[off:off + len(row)] = row

    def width(self, s, sc=1):
        return max(0, len(s) * 6 * sc - sc)

    def text(self, s, x, y, col, sc=1):
        cx = x
        for ch in s:
            g = FONT.get(ch)
            if g:
                for r in range(7):
                    bi = g[r]
                    if bi:
                        for c in range(5):
                            if bi & (1 << (4 - c)):
                                self.rect(cx + c * sc, y + r * sc, sc, sc, col)
            cx += 6 * sc
        return cx

    def center(self, s, y, col, sc=1, x0=0, x1=None):
        if x1 is None:
            x1 = self.w
        self.text(s, x0 + (x1 - x0 - self.width(s, sc)) // 2, y, col, sc)

    def right(self, s, y, col, sc=1, x1=None):
        if x1 is None:
            x1 = self.w
        self.text(s, x1 - self.width(s, sc), y, col, sc)

    def wrap(self, s, maxw, sc=1):
        maxch = maxw // (6 * sc)
        lines = []
        cur = ''
        for word in s.split():
            cand = (cur + ' ' + word).strip()
            if len(cand) <= maxch or not cur:
                cur = cand
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


LEAD = {
    'kicker': 'GAMES ' + chr(0xB7) + ' THE BIG RELEASE',
    'headline': 'GTA VI LAUNCH DAY: THE WAIT IS OVER',
    'body': ('MIDNIGHT QUEUES as the twelve-year wait ends: the console '
             'release sweeps stores worldwide at launch, with bundles sold '
             'out within hours and retailers reporting the biggest software '
             'launch day ever recorded.'),
    'dateline': 'LOS ANGELES, FRIDAY',
}

STORIES = (
    {
        'kicker': 'MARKETS & MONEY',
        'headline': 'GLOBAL MARKETS MIXED AS TECH SHARES RALLY',
        'body': ('Wall Street futures climb as European indices waver; bond '
                 'yields ease and the AI chip rally powers tech shares to '
                 'fresh highs.'),
        'page': 2,
    },
    {
        'kicker': 'CLIMATE ' + chr(0xB7) + ' COP31',
        'headline': 'CLIMATE SUMMIT: DEAL IN SIGHT AS TALKS RUN LONG',
        'body': ('Ministers in Antalya work through the night on adaptation '
                 'finance, hoping to land a COP31 deal before the final '
                 'gavel falls.'),
        'page': 3,
    },
    {
        'kicker': 'TECHNOLOGY & AI',
        'headline': 'AI SAFETY PLEDGE SIGNED BY FORTY NATIONS',
        'body': ('Forty nations sign a frontier-model safety accord on testing '
                 'and incident reporting as data-center buildoustrain '
                 'power grids.'),
        'page': 4,
    },
    {
        'kicker': 'SPORT ' + chr(0xB7) + ' CHAMPIONS LEAGUE',
        'headline': 'GOALS GALORE ON A WILD EUROPEAN NIGHT',
        'body': ('Stoppage-time winners flip the group table on a wild '
                 'European night of goals watched by record crowds across '
                 'the continent.'),
        'page': 5,
    },
)

SIDE = {
    'kicker': 'THE DAY IN BRIEF',
    'headline': 'ALSO MAKING NEWS TODAY',
    'body': ('COP31 extra time ' + chr(0xB7) + ' AI chip rally '
             '+ record euro night ' + chr(0xB7) + ' markemixed '
             '+ GTA VI launch live coverage and reaction, pages 2-5.'),
}

PULL = ('A LAUNCH DAY', 'LIKE NO OTHER')


def draw_pull(c, x, y, w, h, fill, bar):
    # Pull-quote box between the brief and the ticker.
    c.rect(x, y, w, h, fill)
    c.rect(x, y, w, 2, INK)
    c.rect(x + w - 2, y, 2, h, INK)
    c.rect(x, y + h - 2, w, 2, INK)
    c.rect(x, y, 2, h, INK)
    c.text(chr(0xB7) * (w // 16), x + 14, y + 12, bar, 2)
    yy = y + 34
    for line in PULL:
        c.center(line, yy, bar, 3, x, x + w)
        yy += 26
    c.rect(x + 14, yy + 2, w - 28, 1, INK2)
    c.center('THE WORLD, IN ONE PAGE', yy + 12, INK2, 1, x, x + w)


def draw_box(c, x, y, w, h, story, head_sc, body_w, top, fill, bar):
    # One headline box: border, accent bar, kicker, wrapped headline, body.
    c.rect(x, y, w, h, fill)
    c.rect(x, y, w, 2, INK)
    c.rect(x, y + h - 2, w, 2, INK)
    c.rect(x, y, 2, h, INK)
    c.rect(x + w - 2, y, 2, h, INK)
    c.rect(x, y, w, top, bar)
    c.rect(x + w - 26, y, 10, top, SECONDARY if bar is PRIMARY else PRIMARY)
    px = x + 14
    ky = y + top + 8
    c.rect(px, ky + 4, 8, 8, bar)
    c.text(story['kicker'], px + 14, ky, bar, 2)
    if story.get('dateline'):
        c.right(story['dateline'], ky, bar, 1, x + w - 12)
    hy = ky + 14 + 6
    for line in c.wrap(story['headline'], w - 28, head_sc):
        c.text(line, px, hy, INK, head_sc)
        hy += 7 * head_sc + 5
    hy += 4
    room = max(1, (y + h - 10 - hy) // 18)
    for line in c.wrap(story['body'], body_w, 2)[:room]:
        c.text(line, px, hy, INK2, 2)
        hy += 18
    if story.get('page'):
        c.right('Full story, page %d' % story['page'], y + h - 13, INK2, 1,
                x + w - 12)


def build_page():
    c = Canvas(W, H, PAPER)
    # top accent bands
    c.rect(0, 0, W, 10, PRIMARY)
    c.rect(0, 10, W, 2, SECONDARY)
    # masthead
    c.center('WORLD NEWS', 22, INK, 10, M, W - M)
    c.center('- Thursday 19 November 2026', 98, INK, 3, M, W - M)
    c.text('LATE EDITION', M, 101, PRIMARY, 2)
    c.right(chr(0xA3) + '2.50', 101, PRIMARY, 2, W - M)
    # masthead rules
    c.rect(M, 128, W - 2 * M, 3, INK)
    c.rect(M, 133, W - 2 * M, 1, PRIMARY)
    # lead story
    draw_box(c, M, 144, W - 2 * M, 178, LEAD, 4, W - 2 * M - 28, 8,
             PAPER2, PRIMARY)
    # double rule
    c.rect(M, 332, W - 2 * M, 2, INK)
    c.rect(M, 336, W - 2 * M, 1, PRIMARY)
    # five-story grid: lead, four stories, brief + pull-quote
    gx = (M, M, M + 496, M, M + 496)
    gy = (346, 454, 346, 562, 454)
    bw, bh = 480, 96
    for i, story in enumerate(STORIES):
        draw_box(c, gx[i], gy[i], bw, bh, story, 2, bw - 28, 5,
                 PAPER if i % 2 == 0 else PAPER2,
                 PRIMARY if i % 2 == 0 else SECONDARY)
    draw_box(c, M, 562, 232, 106, SIDE, 1, 204, 4, PAPER, SECONDARY)
    draw_pull(c, M + 244, 562, 236, 106, PAPER2, SECONDARY)
    # inside ticker
    c.rect(0, 714, W, 38, PRIMARY)
    c.center('INSIDE: GTA VI LAUNCH LIVE ' + chr(0xB7) + ' COP31 EXTRA TIME '
             + chr(0xB7) + ' AI CHIP RALLY ' + chr(0xB7) + ' EURO GOAL FEST',
             727, PAPER2, 2, 0, W)
    # footer with the literal masthead line
    c.text('WORLD NEWS - Thursday 19 November 2026', M, 758, INK2, 1)
    c.right('PAGE 1', 758, INK2, 1, W - M)
    return c


def encode_png(c):
    stride = c.w * 3
    raw = bytearray()
    for y in range(c.h):
        raw.append(0)  # filter type 0 per scanline
        raw += c.buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        return (struct.pack('>I', len(data)) + tag + data +
                struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack('>IIBBBBB', c.w, c.h, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) +
            chunk(b'IDAT', comp) + chunk(b'IEND', b''))


def main():
    out_dir = os.environ.get('MAKEFUN_OUTPUT_DIR') or 'out'
    os.makedirs(out_dir, exist_ok=True)
    page = build_page()
    data = encode_png(page)
    path = os.path.join(out_dir, 'entry.png')
    with open(path, 'wb') as f:
        f.write(data)
    print('wrote %s (%d bytes, %dx%d)' % (path, len(data), W, H))


if __name__ == '__main__':
    main()
