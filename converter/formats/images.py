"""Image conversions via Pillow."""
from pathlib import Path
from typing import Optional, Tuple

try:
    from PIL import Image, ImageOps
except ImportError as exc:
    raise ImportError("Pillow is required for image conversion. Run: pip install Pillow") from exc


# Formats that do not support alpha (transparency)
_NEEDS_RGB = {"jpg", "jpeg", "bmp"}


def parse_resize(resize_str: str, original_size: Tuple[int, int]) -> Tuple[int, int]:
    """Parse resize string into (width, height).

    Supports:
      - "800x600" -> (800, 600)
      - "50%" -> half of original dimensions
    """
    orig_w, orig_h = original_size
    resize_str = resize_str.strip().lower()
    if resize_str.endswith("%"):
        try:
            percent = float(resize_str[:-1]) / 100.0
            if percent <= 0:
                raise ValueError
            new_w = max(1, int(orig_w * percent))
            new_h = max(1, int(orig_h * percent))
            return (new_w, new_h)
        except ValueError as exc:
            raise ValueError(f"Invalid resize percentage: {resize_str}") from exc

    if "x" in resize_str:
        parts = resize_str.split("x")
        if len(parts) == 2:
            try:
                new_w = int(parts[0])
                new_h = int(parts[1])
                if new_w > 0 and new_h > 0:
                    return (new_w, new_h)
            except ValueError:
                pass
    raise ValueError(f"Invalid resize format: '{resize_str}'. Expected WIDTHxHEIGHT (e.g. 800x600) or PERCENT% (e.g. 50%)")


def convert_image(
    input_path: Path,
    output_path: Path,
    *,
    quality: int = 90,
    resize: Optional[str] = None,
    rotate: Optional[int] = None,
    grayscale: bool = False,
) -> None:
    """
    Convert an image to the format inferred from *output_path* suffix.

    Parameters
    ----------
    input_path  : source image file
    output_path : destination file (format determined by suffix)
    quality     : compression quality 1–100, used for JPEG/WebP
    resize      : optional resize string like "800x600" or "50%"
    rotate      : optional rotation angle in degrees (90, 180, 270)
    grayscale   : whether to convert image to grayscale
    """
    dst_ext = output_path.suffix.lstrip(".").lower()

    with Image.open(input_path) as img:
        # Preserve animated GIF / WebP frames where possible if not transforming
        if getattr(img, "is_animated", False) and dst_ext in ("webp", "gif") and not resize and not rotate and not grayscale:
            frames = []
            try:
                while True:
                    frames.append(img.copy().convert("RGBA"))
                    img.seek(img.tell() + 1)
            except EOFError:
                pass
            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                quality=quality,
            )
            return

        # Apply transformations
        if rotate:
            img = img.rotate(-rotate, expand=True)

        if resize:
            new_size = parse_resize(resize, img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        if grayscale:
            img = ImageOps.grayscale(img)

        # Handle format specific requirements
        if dst_ext == "ico":
            # Windows icon format supports RGBA
            if img.mode not in ("RGBA", "RGB"):
                img = img.convert("RGBA")
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            # Filter sizes to not exceed image size if small
            target_sizes = [s for s in sizes if s[0] <= max(img.size)] or [(img.width, img.height)]
            img.save(output_path, format="ICO", sizes=target_sizes)
            return

        # Flatten alpha for formats without alpha channel (JPEG, BMP)
        if dst_ext in _NEEDS_RGB:
            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                mask = img.split()[-1] if img.mode == "RGBA" else None
                background.paste(img, mask=mask)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            if dst_ext in ("jpg", "jpeg"):
                img.save(output_path, format="JPEG", quality=quality, optimize=True)
            elif dst_ext == "bmp":
                img.save(output_path, format="BMP")
            return

        if dst_ext == "webp":
            img.save(output_path, format="WEBP", quality=quality, method=6)
        elif dst_ext == "png":
            img.save(output_path, format="PNG", optimize=True)
        elif dst_ext == "tiff":
            img.save(output_path, format="TIFF")
        elif dst_ext == "gif":
            img.save(output_path, format="GIF")
        else:
            img.save(output_path)
