"""Center-crop hero images to the exact hero aspect ratio (1920x800, 12:5).

Run this after uploading raw images to static/images/hero/ to remove the
top/bottom cropping caused by background-size: cover:

    python deployment/crop_hero_images.py

It rewrites static/images/hero/hero-*.webp in place, center-cropping to
1920x800 (keeps the middle of the photo, which is what matters).
"""

from pathlib import Path
from PIL import Image

HERO_DIR = Path(__file__).resolve().parent.parent / "static" / "images" / "hero"
TARGET_W = 1920
TARGET_H = 800


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
    files = sorted(HERO_DIR.glob("hero-*.webp"))
    if not files:
        print(f"No hero-*.webp found in {HERO_DIR}")
        return
    for path in files:
        with Image.open(path) as im:
            im = im.convert("RGB")
            im = center_crop_to(im, TARGET_W, TARGET_H)
            if im.width != TARGET_W or im.height != TARGET_H:
                im = im.resize((TARGET_W, TARGET_H), Image.LANCZOS)
            im.save(path, "WEBP", quality=82, method=6)
        print(f"{path.name} -> 1920x800")


if __name__ == "__main__":
    main()