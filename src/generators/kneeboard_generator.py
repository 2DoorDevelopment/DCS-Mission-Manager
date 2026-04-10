"""
Kneeboard PNG Generator
Produces DCS-compatible kneeboard card images from briefing text.
Pure stdlib — no Pillow or external packages required.
Uses zlib compression and a built-in 8x13 bitmap font to render text onto PNG.
"""

import zlib
import struct
import math

# ---------------------------------------------------------------------------
# Minimal 8×13 bitmap font (printable ASCII 32-126)
# Each character is 13 rows of 8-bit scanlines stored as integers.
# This is a compact public-domain proportional terminal font.
# ---------------------------------------------------------------------------
_FONT_W = 8
_FONT_H = 13

# Encoded as tuples of 13 bytes (row 0 = top).  Only the subset we actually
# need for briefing text is included; anything outside 0x20-0x7E falls back
# to a blank glyph.
_GLYPHS: dict[int, tuple] = {
    0x20: (0,0,0,0,0,0,0,0,0,0,0,0,0),                          # space
    0x21: (0,24,24,24,24,24,24,0,24,24,0,0,0),                  # !
    0x22: (0,54,54,54,0,0,0,0,0,0,0,0,0),                       # "
    0x23: (0,36,36,126,36,36,36,126,36,36,0,0,0),               # #
    0x24: (0,24,62,72,72,60,12,12,124,24,0,0,0),                # $
    0x25: (0,0,70,38,16,16,8,8,100,98,0,0,0),                   # %
    0x26: (0,56,108,108,56,110,219,219,110,59,0,0,0),           # &
    0x27: (0,24,24,24,0,0,0,0,0,0,0,0,0),                       # '
    0x28: (0,6,12,24,24,24,24,24,12,6,0,0,0),                   # (
    0x29: (0,96,48,24,24,24,24,24,48,96,0,0,0),                 # )
    0x2A: (0,0,0,54,28,127,28,54,0,0,0,0,0),                    # *
    0x2B: (0,0,0,24,24,126,24,24,0,0,0,0,0),                    # +
    0x2C: (0,0,0,0,0,0,0,0,24,24,48,0,0),                       # ,
    0x2D: (0,0,0,0,0,126,0,0,0,0,0,0,0),                        # -
    0x2E: (0,0,0,0,0,0,0,0,24,24,0,0,0),                        # .
    0x2F: (0,0,3,6,12,24,48,96,0,0,0,0,0),                      # /
    0x30: (0,60,102,110,118,102,102,102,60,0,0,0,0),            # 0
    0x31: (0,24,56,24,24,24,24,24,126,0,0,0,0),                 # 1
    0x32: (0,60,102,6,12,24,48,96,126,0,0,0,0),                 # 2
    0x33: (0,60,102,6,28,6,6,102,60,0,0,0,0),                   # 3
    0x34: (0,12,28,60,108,126,12,12,12,0,0,0,0),                # 4
    0x35: (0,126,96,96,124,6,6,102,60,0,0,0,0),                 # 5
    0x36: (0,28,48,96,124,102,102,102,60,0,0,0,0),              # 6
    0x37: (0,126,6,6,12,24,48,48,48,0,0,0,0),                   # 7
    0x38: (0,60,102,102,60,102,102,102,60,0,0,0,0),             # 8
    0x39: (0,60,102,102,62,6,6,12,56,0,0,0,0),                  # 9
    0x3A: (0,0,0,24,24,0,0,24,24,0,0,0,0),                      # :
    0x3B: (0,0,0,24,24,0,0,24,24,48,0,0,0),                     # ;
    0x3C: (0,0,6,12,24,48,24,12,6,0,0,0,0),                     # <
    0x3D: (0,0,0,0,126,0,126,0,0,0,0,0,0),                      # =
    0x3E: (0,0,96,48,24,12,24,48,96,0,0,0,0),                   # >
    0x3F: (0,60,102,6,12,24,0,24,24,0,0,0,0),                   # ?
    0x40: (0,60,102,110,110,110,96,96,60,0,0,0,0),              # @
    0x41: (0,24,60,102,102,126,102,102,102,0,0,0,0),            # A
    0x42: (0,124,102,102,124,102,102,102,124,0,0,0,0),          # B
    0x43: (0,60,102,96,96,96,96,102,60,0,0,0,0),                # C
    0x44: (0,120,108,102,102,102,102,108,120,0,0,0,0),          # D
    0x45: (0,126,96,96,120,96,96,96,126,0,0,0,0),               # E
    0x46: (0,126,96,96,120,96,96,96,96,0,0,0,0),                # F
    0x47: (0,60,102,96,96,110,102,102,60,0,0,0,0),              # G
    0x48: (0,102,102,102,126,102,102,102,102,0,0,0,0),          # H
    0x49: (0,60,24,24,24,24,24,24,60,0,0,0,0),                  # I
    0x4A: (0,30,12,12,12,12,12,108,56,0,0,0,0),                 # J
    0x4B: (0,102,108,120,112,120,108,102,102,0,0,0,0),          # K
    0x4C: (0,96,96,96,96,96,96,96,126,0,0,0,0),                 # L
    0x4D: (0,99,119,127,107,99,99,99,99,0,0,0,0),               # M
    0x4E: (0,102,118,126,126,110,102,102,102,0,0,0,0),          # N
    0x4F: (0,60,102,102,102,102,102,102,60,0,0,0,0),            # O
    0x50: (0,124,102,102,124,96,96,96,96,0,0,0,0),              # P
    0x51: (0,60,102,102,102,102,102,60,14,0,0,0,0),             # Q
    0x52: (0,124,102,102,124,120,108,102,102,0,0,0,0),          # R
    0x53: (0,60,102,96,60,6,6,102,60,0,0,0,0),                  # S
    0x54: (0,126,24,24,24,24,24,24,24,0,0,0,0),                 # T
    0x55: (0,102,102,102,102,102,102,102,60,0,0,0,0),           # U
    0x56: (0,102,102,102,102,102,60,60,24,0,0,0,0),             # V
    0x57: (0,99,99,99,99,107,127,119,99,0,0,0,0),               # W
    0x58: (0,102,102,60,24,24,60,102,102,0,0,0,0),              # X
    0x59: (0,102,102,102,60,24,24,24,24,0,0,0,0),               # Y
    0x5A: (0,126,6,12,24,48,96,96,126,0,0,0,0),                 # Z
    0x5B: (0,60,48,48,48,48,48,48,60,0,0,0,0),                  # [
    0x5C: (0,0,96,48,24,12,6,3,0,0,0,0,0),                      # backslash
    0x5D: (0,60,12,12,12,12,12,12,60,0,0,0,0),                  # ]
    0x5E: (0,24,60,102,0,0,0,0,0,0,0,0,0),                      # ^
    0x5F: (0,0,0,0,0,0,0,0,0,126,0,0,0),                        # _
    0x60: (0,48,24,12,0,0,0,0,0,0,0,0,0),                       # `
    0x61: (0,0,0,60,6,62,102,102,62,0,0,0,0),                   # a
    0x62: (0,96,96,124,102,102,102,102,124,0,0,0,0),            # b
    0x63: (0,0,0,60,102,96,96,102,60,0,0,0,0),                  # c
    0x64: (0,6,6,62,102,102,102,102,62,0,0,0,0),                # d
    0x65: (0,0,0,60,102,126,96,102,60,0,0,0,0),                 # e
    0x66: (0,28,54,48,120,48,48,48,48,0,0,0,0),                 # f
    0x67: (0,0,0,62,102,102,62,6,102,60,0,0,0),                 # g
    0x68: (0,96,96,124,102,102,102,102,102,0,0,0,0),            # h
    0x69: (0,24,0,24,24,24,24,24,24,0,0,0,0),                   # i
    0x6A: (0,6,0,6,6,6,6,6,102,60,0,0,0),                       # j
    0x6B: (0,96,96,102,108,120,120,108,102,0,0,0,0),            # k
    0x6C: (0,56,24,24,24,24,24,24,60,0,0,0,0),                  # l
    0x6D: (0,0,0,110,127,107,107,99,99,0,0,0,0),                # m
    0x6E: (0,0,0,124,102,102,102,102,102,0,0,0,0),              # n
    0x6F: (0,0,0,60,102,102,102,102,60,0,0,0,0),                # o
    0x70: (0,0,0,124,102,102,102,124,96,96,0,0,0),              # p
    0x71: (0,0,0,62,102,102,102,62,6,6,0,0,0),                  # q
    0x72: (0,0,0,108,118,102,96,96,96,0,0,0,0),                 # r
    0x73: (0,0,0,62,96,60,6,6,124,0,0,0,0),                     # s
    0x74: (0,48,48,126,48,48,48,54,28,0,0,0,0),                 # t
    0x75: (0,0,0,102,102,102,102,102,62,0,0,0,0),               # u
    0x76: (0,0,0,102,102,102,102,60,24,0,0,0,0),                # v
    0x77: (0,0,0,99,99,107,107,127,54,0,0,0,0),                 # w
    0x78: (0,0,0,102,60,24,24,60,102,0,0,0,0),                  # x
    0x79: (0,0,0,102,102,102,62,6,12,120,0,0,0),                # y
    0x7A: (0,0,0,126,12,24,48,96,126,0,0,0,0),                  # z
    0x7B: (0,14,24,24,48,96,48,24,24,14,0,0,0),                 # {
    0x7C: (0,24,24,24,24,0,24,24,24,24,0,0,0),                  # |
    0x7D: (0,112,24,24,12,6,12,24,24,112,0,0,0),                # }
    0x7E: (0,118,220,0,0,0,0,0,0,0,0,0,0),                      # ~
}
_BLANK = (0,) * _FONT_H


# ---------------------------------------------------------------------------
# PNG writer (pure stdlib)
# ---------------------------------------------------------------------------

def _png_chunk(name: bytes, data: bytes) -> bytes:
    chunk = name + data
    return struct.pack(">I", len(data)) + chunk + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)


def _write_png(width: int, height: int, pixels: list[list[tuple]]) -> bytes:
    """Encode an RGB pixel grid as a PNG bytestring."""
    header = b"\x89PNG\r\n\x1a\n"

    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # 8-bit RGB
    ihdr = _png_chunk(b"IHDR", ihdr_data)

    raw_rows = []
    for row in pixels:
        row_bytes = b"\x00"  # filter type None
        for r, g, b in row:
            row_bytes += bytes([r, g, b])
        raw_rows.append(row_bytes)

    compressed = zlib.compress(b"".join(raw_rows), 9)
    idat = _png_chunk(b"IDAT", compressed)
    iend = _png_chunk(b"IEND", b"")

    return header + ihdr + idat + iend


# ---------------------------------------------------------------------------
# Text renderer
# ---------------------------------------------------------------------------

# Palette
_BG   = (18, 24, 32)      # Dark panel background  (#121820)
_FG   = (200, 214, 229)   # Main text              (#c8d6e5)
_HDR  = (78, 205, 196)    # Section header accent  (#4ecdc4)
_DIM  = (107, 123, 141)   # Dim separator          (#6b7b8d)

_SCALE = 2                  # Render at 2× for crisp high-DPI kneeboard
_PAD_X = 12
_PAD_Y = 10
_LINE_H = (_FONT_H + 3) * _SCALE


def _draw_char(pixels: list[list], x: int, y: int, ch: str, color: tuple):
    code = ord(ch) if len(ch) == 1 else 0x20
    glyph = _GLYPHS.get(code, _BLANK)
    for row_i, row_bits in enumerate(glyph):
        for col_i in range(_FONT_W):
            if row_bits & (0x80 >> col_i):
                px = x + col_i * _SCALE
                py = y + row_i * _SCALE
                for dy in range(_SCALE):
                    for dx in range(_SCALE):
                        ry, rx = py + dy, px + dx
                        if 0 <= ry < len(pixels) and 0 <= rx < len(pixels[0]):
                            pixels[ry][rx] = color


def _pick_color(line: str) -> tuple:
    stripped = line.strip()
    if stripped.startswith("═") or stripped.startswith("─"):
        return _DIM
    if line.startswith("  ") and stripped.isupper():
        return _HDR
    return _FG


def generate_kneeboard_png(briefing_text: str, aircraft_type: str) -> bytes:
    """
    Render a briefing string into a PNG kneeboard card.
    Returns raw PNG bytes suitable for embedding in a .miz archive.
    """
    lines = briefing_text.splitlines()

    # Measure canvas
    max_chars = max((len(ln) for ln in lines), default=80)
    width  = max(640, _PAD_X * 2 + max_chars * _FONT_W * _SCALE)
    height = _PAD_Y * 2 + len(lines) * _LINE_H

    # Cap at a reasonable kneeboard size (~2048 wide)
    if width > 2048:
        width = 2048
    chars_per_row = (width - _PAD_X * 2) // (_FONT_W * _SCALE)

    # Allocate pixel grid (fill with background)
    pixels: list[list[tuple]] = [[_BG] * width for _ in range(height)]

    cy = _PAD_Y
    for raw_line in lines:
        # Wrap long lines
        wrapped = [raw_line[i:i + chars_per_row]
                   for i in range(0, max(1, len(raw_line)), chars_per_row)] if raw_line else [""]
        for segment in wrapped:
            color = _pick_color(segment)
            cx = _PAD_X
            for ch in segment:
                if ch == "\t":
                    cx += _FONT_W * _SCALE * 4
                    continue
                _draw_char(pixels, cx, cy, ch, color)
                cx += _FONT_W * _SCALE
            cy += _LINE_H
            if cy >= height:
                break
        if cy >= height:
            break

    return _write_png(width, height, pixels)


def get_dcs_aircraft_folder(aircraft_type: str) -> str:
    """Map DCS unit type string to the kneeboard folder name DCS expects."""
    mapping = {
        "F-16C_50":      "F-16C_50",
        "FA-18C_hornet": "FA-18C_hornet",
        "A-10C_2":       "A-10C_2",
        "JF-17":         "JF-17",
        "F-15C":         "F-15C",
        "F-15ESE":       "F-15ESE",
        "AV8BNA":        "AV8BNA",
        "M-2000C":       "M-2000C",
        "AH-64D_BLK_II": "AH-64D_BLK_II",
    }
    return mapping.get(aircraft_type, aircraft_type)
