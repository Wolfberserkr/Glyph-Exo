#!/usr/bin/env python3
"""
Pikachu Glyph Generator for Nothing Phone 3
Outputs a .ogg file importable directly in the Glyph Composer app.

Usage:  python3 generate.py [output.ogg]
"""

import math
import zlib
import base64
import os
import subprocess
import sys
import tempfile

from mutagen.oggvorbis import OggVorbis

# ── Phone 3 constants ────────────────────────────────────────────────────────

MATRIX   = 25
COLS     = MATRIX * MATRIX   # 625
MAX_BR   = 4095
FPS      = 60
DURATION = 10                # seconds of audio

# ── Visible pixel mask (circular 489-LED layout) ─────────────────────────────

_VISIBLE_RANGES = [
    (9,   15),  # row 0
    (32,  42),  # row 1
    (55,  69),  # row 2
    (79,  95),  # row 3
    (103, 121), # row 4
    (127, 147), # row 5
    (152, 172), # row 6
    (176, 198), # row 7
    (201, 223), # row 8
    (225, 399), # rows 9-15 (fully filled)
    (401, 423), # row 16
    (426, 448), # row 17
    (452, 472), # row 18
    (477, 497), # row 19
    (503, 521), # row 20
    (529, 545), # row 21
    (555, 569), # row 22
    (582, 592), # row 23
    (609, 615), # row 24
]

VISIBLE: set[int] = set()
for _s, _e in _VISIBLE_RANGES:
    VISIBLE.update(range(_s, _e + 1))


def idx(row: int, col: int) -> int:
    return row * MATRIX + col


def in_circle(row: int, col: int, cr: int, cc: int, r: float) -> bool:
    return math.hypot(row - cr, col - cc) <= r


# ── Pikachu static layers ─────────────────────────────────────────────────────

def build_layers() -> dict[str, dict[int, int]]:
    layers: dict[str, dict[int, int]] = {
        'face': {}, 'ears': {}, 'eyes': {},
        'nose': {}, 'mouth': {}, 'cheek_l': {}, 'cheek_r': {},
    }

    for r in range(MATRIX):
        for c in range(MATRIX):
            i = idx(r, c)
            if i not in VISIBLE:
                continue

            # Main face (filled circle)
            if in_circle(r, c, 12, 12, 11):
                layers['face'][i] = 2200

            # Ears — two lobes at the top overlapping the face circle
            if in_circle(r, c, 4, 8, 4.5):
                layers['ears'][i] = 1700
            if in_circle(r, c, 4, 16, 4.5):
                layers['ears'][i] = 1700

            # Eyes (bright filled dots)
            if in_circle(r, c, 9, 8, 1.4):
                layers['eyes'][i] = MAX_BR
            if in_circle(r, c, 9, 16, 1.4):
                layers['eyes'][i] = MAX_BR

            # Nose (single bright dot)
            if r == 11 and c == 12:
                layers['nose'][i] = 3200

            # Mouth — a smile: two downward-angled dots each side + lower centre
            if (r == 13 and c in (10, 11)) or (r == 13 and c in (13, 14)):
                layers['mouth'][i] = MAX_BR
            if r == 14 and c in (11, 12, 13):
                layers['mouth'][i] = MAX_BR

            # Cheek pouches (circles on each side of the face)
            if in_circle(r, c, 13, 5, 2.8):
                layers['cheek_l'][i] = MAX_BR
            if in_circle(r, c, 13, 19, 2.8):
                layers['cheek_r'][i] = MAX_BR

    return layers


# ── Frame composer ────────────────────────────────────────────────────────────

def compose(
    layers: dict[str, dict[int, int]],
    *,
    face_scale: float = 1.0,
    cl: float = 1.0,   # cheek-left brightness multiplier
    cr: float = 1.0,   # cheek-right brightness multiplier
    bolt: list[tuple[int, int]] | None = None,
    flash: int = 0,
) -> list[int]:
    frame = [0] * COLS

    for i, v in layers['face'].items():
        frame[i] = int(v * face_scale)
    for i, v in layers['ears'].items():
        # ears only if face is building in
        frame[i] = max(frame[i], int(v * face_scale))
    for layer in ('eyes', 'nose', 'mouth'):
        scale = max(0.25, face_scale)
        for i, v in layers[layer].items():
            frame[i] = int(v * scale)

    for i in layers['cheek_l']:
        frame[i] = int(MAX_BR * cl * face_scale)
    for i in layers['cheek_r']:
        frame[i] = int(MAX_BR * cr * face_scale)

    if bolt:
        for i, v in bolt:
            if i in VISIBLE:
                frame[i] = v

    if flash:
        for i in VISIBLE:
            frame[i] = min(MAX_BR, frame[i] + flash)

    return frame


# ── Thunderbolt path ──────────────────────────────────────────────────────────

# Classic ⚡ zigzag traced from cheeks outward
_BOLT_PATH: list[tuple[int, int]] = [
    # Left bolt shoots left-downward from left cheek
    (13, 4), (13, 3), (14, 3), (14, 2), (15, 2), (15, 1),
    (16, 2), (17, 2), (18, 3), (19, 4), (20, 5), (21, 5),
    # Right bolt shoots right-downward from right cheek
    (13, 20), (13, 21), (14, 21), (14, 22), (15, 22), (15, 23),
    (16, 22), (17, 22), (18, 21), (19, 20), (20, 19), (21, 19),
]
_BOLT_VISIBLE = [(r, c) for r, c in _BOLT_PATH if idx(r, c) in VISIBLE]


def bolt_pixels(progress: float) -> list[tuple[int, int]]:
    """Active bolt pixels with trailing fade for progress in [0, 1]."""
    n = int(len(_BOLT_VISIBLE) * progress)
    result = []
    for k, (r, c) in enumerate(_BOLT_VISIBLE[:n]):
        age = n - k
        brightness = max(0, MAX_BR - age * 300)
        result.append((idx(r, c), brightness))
    return result


# ── Animation timeline (5-second loop) ───────────────────────────────────────

CYCLE = 300   # frames per loop (5 s)

def generate_frames(total: int, layers: dict) -> list[list[int]]:
    frames = []
    for f in range(total):
        t = f % CYCLE

        if t < 45:
            # ── Fade in ──────────────────────────────────────────────────────
            scale = t / 45.0
            frame = compose(layers, face_scale=scale, cl=0.0, cr=0.0)

        elif t < 90:
            # ── Left cheek sparks ─────────────────────────────────────────
            phase = (t - 45) / 45.0
            cl = abs(math.sin(phase * math.pi * 3))
            frame = compose(layers, cl=cl, cr=0.1)

        elif t < 135:
            # ── Right cheek sparks ────────────────────────────────────────
            phase = (t - 90) / 45.0
            cr = abs(math.sin(phase * math.pi * 3))
            frame = compose(layers, cl=0.1, cr=cr)

        elif t < 195:
            # ── Both cheeks charge, thunderbolts extend ───────────────────
            progress = (t - 135) / 60.0
            bpx = bolt_pixels(progress)
            cl_br = 0.5 + 0.5 * abs(math.sin((t - 135) / 8.0))
            cr_br = cl_br
            frame = compose(layers, cl=cl_br, cr=cr_br, bolt=bpx)

        elif t < 225:
            # ── Thunderflash ──────────────────────────────────────────────
            ft = (t - 195) / 30.0
            fl = int(MAX_BR * 0.6 * math.sin(ft * math.pi))
            frame = compose(layers, cl=1.0, cr=1.0,
                            bolt=bolt_pixels(1.0), flash=fl)

        elif t < 270:
            # ── Bolts fade out ────────────────────────────────────────────
            progress = 1.0 - (t - 225) / 45.0
            bpx = bolt_pixels(progress)
            frame = compose(layers, cl=progress, cr=progress, bolt=bpx)

        else:
            # ── Hold base pose then fade into next cycle ──────────────────
            hold_t = (t - 270) / 30.0
            scale = 1.0 - 0.3 * hold_t   # gentle dim, not full off
            frame = compose(layers, face_scale=scale, cl=0.1, cr=0.1)

        frames.append(frame)
    return frames


# ── Encoding ──────────────────────────────────────────────────────────────────

def encode_author(frames: list[list[int]]) -> str:
    rows = [','.join(str(v) for v in row) + ',' for row in frames]
    csv_bytes = ('\r\n'.join(rows) + '\r\n').encode('utf-8')
    compressed = zlib.compress(csv_bytes, zlib.Z_BEST_COMPRESSION)
    b64 = base64.b64encode(compressed).decode('utf-8').rstrip('=')
    return '\n'.join(b64[i:i+76] for i in range(0, len(b64), 76)) + '\n'


def encode_custom1() -> str:
    compressed = zlib.compress(b'', zlib.Z_BEST_COMPRESSION)
    b64 = base64.b64encode(compressed).decode('utf-8').rstrip('=')
    return '\n'.join(b64[i:i+76] for i in range(0, len(b64), 76)) + '\n'


# ── OGG builder ───────────────────────────────────────────────────────────────

def build_ogg(output: str, author_tag: str, custom1_tag: str) -> None:
    fd, silent = tempfile.mkstemp(suffix='.ogg')
    os.close(fd)
    try:
        # Create a silent OGG Vorbis carrier
        result = subprocess.run([
            'ffmpeg', '-y',
            '-f', 'lavfi', '-i', f'anullsrc=r=44100:cl=mono',
            '-t', str(DURATION),
            '-c:a', 'libvorbis', '-q:a', '0',
            silent,
        ], capture_output=True)
        if result.returncode != 0:
            sys.exit(f'ffmpeg failed: {result.stderr.decode()}')

        import shutil
        shutil.copy2(silent, output)

        # Inject glyph metadata via mutagen (supports multiline values)
        ogg = OggVorbis(output)
        ogg['TITLE']    = ['Pikachu Thunderbolt']
        ogg['ALBUM']    = ['custom']
        ogg['COMPOSER'] = ['v1-Metroid Glyph Composer']
        ogg['CUSTOM2']  = ['625cols']
        ogg['AUTHOR']   = [author_tag]
        ogg['CUSTOM1']  = [custom1_tag]
        ogg.save()
    finally:
        os.unlink(silent)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    output = sys.argv[1] if len(sys.argv) > 1 else 'pikachu.ogg'
    total_frames = DURATION * FPS  # 600

    print('Building Pikachu layers...')
    layers = build_layers()
    for name, pxs in layers.items():
        print(f'  {name}: {len(pxs)} pixels')

    print(f'Generating {total_frames} frames ({DURATION}s @ {FPS}fps)...')
    frames = generate_frames(total_frames, layers)

    print('Encoding glyph data...')
    author_tag = encode_author(frames)
    custom1_tag = encode_custom1()
    print(f'  AUTHOR tag: {len(author_tag):,} chars')

    print(f'Building OGG → {output}')
    build_ogg(output, author_tag, custom1_tag)

    size_kb = os.path.getsize(output) / 1024
    print(f'\nDone!  {output}  ({size_kb:.1f} KB)')
    print()
    print('How to use:')
    print('  1. Transfer pikachu.ogg to your Nothing Phone 3')
    print('  2. Open the Glyph Composer app')
    print('  3. Tap Import and select the file')
    print('  4. Assign it to a contact via Phone > Contacts > [name] > Glyph')


if __name__ == '__main__':
    main()
