"""Turns a phone photo or scan of a signature / rubber-stamp impression into a
clean, transparent PNG that sits naturally on the letter.

The paper becomes transparent and the ink keeps a single colour (its own
median colour, so a blue-ink signature stays blue and a violet seal stays
violet); the image is then cropped to the mark and scaled down. Works for
photos with uneven, greyish paper because "white" is measured from the image
itself rather than assumed to be pure white.
"""
import base64
import binascii
import hashlib
from io import BytesIO

from fastapi import HTTPException
from PIL import Image, ImageOps, ImageStat, UnidentifiedImageError

from app.models.letter import LetterImageKind

MAX_UPLOAD_BYTES = 6 * 1024 * 1024
_MAX_PIXELS = 40_000_000
_WORK_SIZE = 1600                       # long side while cleaning
_OUTPUT_WIDTH = {LetterImageKind.SIGNATURE: 900, LetterImageKind.SEAL: 700}


def decode_data_url(value: str) -> bytes:
    """`data:image/png;base64,...` (or bare base64) -> bytes."""
    payload = value.split(",", 1)[1] if value.startswith("data:") else value
    if len(payload) > MAX_UPLOAD_BYTES * 4 // 3 + 4:
        raise HTTPException(status_code=413, detail="That image is too large - use one under 6 MB")
    try:
        return base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="The image could not be read")


def _percentile(histogram: list[int], fraction: float) -> int:
    target = sum(histogram) * fraction
    running = 0
    for value, count in enumerate(histogram):
        running += count
        if running >= target:
            return value
    return 255


def clean_mark(raw: bytes, kind: LetterImageKind) -> tuple[bytes, int, int, str]:
    """Returns (png, width, height, sha256) or raises 400 with a reason the admin can act on."""
    try:
        img = Image.open(BytesIO(raw))
        if img.width * img.height > _MAX_PIXELS:
            raise HTTPException(status_code=400, detail="That image is too large - use a smaller photo")
        img = ImageOps.exif_transpose(img)
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise HTTPException(status_code=400, detail="That file is not an image we can read (use JPEG or PNG)")

    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        paper = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(paper, img)
    img = img.convert("RGB")
    img.thumbnail((_WORK_SIZE, _WORK_SIZE))

    grey = img.convert("L")
    hist = grey.histogram()
    paper_level = _percentile(hist, 0.80)  # most of the picture is paper
    ink_level = _percentile(hist, 0.002)   # the darkest strokes
    if paper_level - ink_level < 40:
        raise HTTPException(status_code=400, detail=(
            "No clear mark found - photograph the signature or stamp on plain white paper, in good light"))

    # Ink opacity: 0 at paper (and a little darker, to drop paper texture and
    # shadows), rising to fully opaque at the darkest ink.
    floor = paper_level - max(18, (paper_level - ink_level) // 6)
    span = max(floor - ink_level, 1)
    alpha = grey.point(lambda v: 0 if v >= floor else min(255, int((floor - v) * 255 / (span * 0.75))))

    box = alpha.point(lambda a: 255 if a > 60 else 0).getbbox()
    if not box:
        raise HTTPException(status_code=400, detail="No clear mark found in that image")
    pad = 6
    box = (max(box[0] - pad, 0), max(box[1] - pad, 0), min(box[2] + pad, img.width), min(box[3] + pad, img.height))
    width, height = box[2] - box[0], box[3] - box[1]
    if width < 30 or height < 12:
        raise HTTPException(status_code=400, detail="The mark in that image is too small - crop closer or use a sharper photo")

    strong = alpha.point(lambda a: 255 if a > 180 else 0)
    ink = tuple(int(c) for c in ImageStat.Stat(img, strong).median) if strong.getbbox() else (20, 20, 60)
    if kind == LetterImageKind.SIGNATURE:
        ink = tuple(int(c * 0.8) for c in ink)  # photos lighten ink; keep the hue, deepen it a little

    out = Image.new("RGBA", img.size, ink + (0,))
    out.putalpha(alpha)
    out = out.crop(box)
    target = _OUTPUT_WIDTH[kind]
    if out.width > target:
        out = out.resize((target, max(1, round(out.height * target / out.width))), Image.LANCZOS)

    buffer = BytesIO()
    out.save(buffer, format="PNG", optimize=True)
    png = buffer.getvalue()
    return png, out.width, out.height, hashlib.sha256(png).hexdigest()
