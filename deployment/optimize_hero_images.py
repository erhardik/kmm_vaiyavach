"""Optimize hero carousel images for the KMM landing page.

Place your original images as src/hero-1.jpg ... src/hero-6.jpg
(next to this script), then run:

    python deployment/optimize_hero_images.py

It center-crops each to the hero's exact aspect ratio (1920x800, 12:5),
resizes to 1920px wide, converts to WebP (quality 82) and writes
static/images/hero/hero-N.webp, keeping visual quality while shrinking
file size dramatically and avoiding any top/bottom cropping on the page.

Then deploy:

    python manage.py collectstatic --noinput
    # and Reload the web app
"""

from pathlib import Path
from PIL import Image

SRC_DIR = Path(__file__).resolve().parent / "src"
OUT_DIR = Path(__file__).resolve().parent.parent / "static" / "images" / "hero"
TARGET_W = 1920
TARGET_H = 800
QUALITY = 82


def center_crop_to(im: Image.Image, w: int, h: int) -> Image.Image:
    src_w, src_h = im.size
    target_ratio = w / h
    src_ratio = src_w / src_h
    if src_ratio > target_ratio:
        new_w = round(src_h * target_ratio)
        new_h = src_h
    else:
        new_w = src_w
        new_h = round(src_w / target_ratio)
    left = (src_w - new_w) // 2
    top = (src_h - new_h) // 2
    return im.crop((left, top, left + new_w, top + new_h))


def main() -> None:
    if not SRC_DIR.exists():
        print(f"Create {SRC_DIR} and put hero-1.jpg .. hero-6.jpg in it.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    images = sorted(SRC_DIR.glob("hero-*.jp*g")) + sorted(SRC_DIR.glob("hero-*.png"))
    if not images:
        print(f"No images found in {SRC_DIR} (hero-1.jpg .. hero-6.jpg).")
        return

    for path in images:
        num = path.stem.split("-")[-1]
        with Image.open(path) as im:
            im = im.convert("RGB")
            im = center_crop_to(im, TARGET_W, TARGET_H)
            im = im.resize((TARGET_W, TARGET_H), Image.LANCZOS)
            out = OUT_DIR / f"hero-{num}.webp"
            im.save(out, "WEBP", quality=QUALITY, method=6)
        kb = round(out.stat().st_size / 1024, 1)
        print(f"{path.name} -> {out.name}  ({im.width}x{im.height}px, {kb} KB)")


if __name__ == "__main__":
    main()