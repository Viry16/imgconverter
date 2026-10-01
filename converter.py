"""Image conversion logic, independent of the Streamlit UI."""

import base64
import io
import re
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError


@dataclass(frozen=True)
class OutputFormat:
    label: str
    pil_format: str | None  # None for formats Pillow cannot write (SVG)
    extension: str
    mime: str
    has_quality: bool = False


FORMATS = {
    f.label: f
    for f in [
        OutputFormat("PNG", "PNG", "png", "image/png"),
        OutputFormat("JPG/JPEG", "JPEG", "jpg", "image/jpeg", has_quality=True),
        OutputFormat("WEBP", "WEBP", "webp", "image/webp", has_quality=True),
        OutputFormat("BMP", "BMP", "bmp", "image/bmp"),
        OutputFormat("GIF", "GIF", "gif", "image/gif"),
        OutputFormat("TIFF", "TIFF", "tiff", "image/tiff"),
        OutputFormat("ICO", "ICO", "ico", "image/x-icon"),
        OutputFormat("SVG", None, "svg", "image/svg+xml"),
    ]
}

INPUT_EXTENSIONS = ["png", "jpg", "jpeg", "webp", "bmp", "gif", "tif", "tiff", "ico"]

SVG_TRACE = "Vector trace"
SVG_EMBED = "Embed raster"
SVG_MODES = [SVG_TRACE, SVG_EMBED]

# Tracing large images is slow and memory hungry; trace a downscaled copy instead.
MAX_TRACE_SIDE = 1024


class ConversionError(Exception):
    """A user-facing error explaining why an image could not be converted."""


@dataclass
class ConvertOptions:
    quality: int = 95
    resize: tuple[int, int] | None = None
    svg_mode: str = SVG_TRACE
    svg_colormode: str = "color"
    svg_filter_speckle: int = 4
    svg_color_precision: int = 6


@dataclass
class ConvertResult:
    filename: str
    data: bytes
    mime: str
    preview: Image.Image | str = field(repr=False)


def load_image(file) -> Image.Image:
    """Open an uploaded file, fully decode it and apply EXIF rotation."""
    if hasattr(file, "seek"):
        file.seek(0)
    try:
        image = Image.open(file)
        image.load()
    except UnidentifiedImageError:
        raise ConversionError("This file is not a recognised image.")
    except Image.DecompressionBombError:
        raise ConversionError("This image is too large to process.")
    except (OSError, ValueError) as e:
        raise ConversionError(f"This image could not be read ({e}).")

    source_format = image.format
    image = ImageOps.exif_transpose(image)
    image.format = source_format
    return image


def normalize(image: Image.Image) -> Image.Image:
    """Convert any Pillow mode to one of L, LA, RGB or RGBA."""
    mode = image.mode
    if mode in ("L", "LA", "RGB", "RGBA"):
        return image
    if mode.startswith("I;16"):
        return image.convert("I").point(lambda v: v / 257).convert("L")
    if mode in ("I", "F"):
        lo, hi = image.getextrema()
        scale = 255 / (hi - lo) if hi > lo else 0
        return image.point(lambda v: (v - lo) * scale).convert("L")
    if mode == "1":
        return image.convert("L")
    if mode in ("La", "PA"):
        return image.convert("RGBA")
    if mode == "RGBa":
        return image.convert("RGBA")
    if mode == "P":
        has_alpha = "transparency" in image.info
        return image.convert("RGBA" if has_alpha else "RGB")
    return image.convert("RGB")


def flatten(image: Image.Image, background=(255, 255, 255)) -> Image.Image:
    """Composite a transparent image onto a solid background."""
    if image.mode not in ("LA", "RGBA"):
        return image
    rgba = image.convert("RGBA")
    base = Image.new("RGB", rgba.size, background)
    base.paste(rgba, mask=rgba.getchannel("A"))
    return base


def prepare_for(image: Image.Image, fmt: OutputFormat) -> Image.Image:
    """Return an image in a mode the target format can store."""
    image = normalize(image)
    if fmt.pil_format == "JPEG":
        return flatten(image)
    if image.mode == "LA" and fmt.pil_format not in ("PNG", "TIFF"):
        return image.convert("RGBA")
    return image


def image_to_svg(image: Image.Image, options: ConvertOptions) -> str:
    """Convert an image to SVG markup."""
    image = normalize(image)
    width, height = image.size

    if options.svg_mode == SVG_EMBED:
        png = io.BytesIO()
        image.save(png, format="PNG")
        b64 = base64.b64encode(png.getvalue()).decode("ascii")
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">'
            f'<image width="{width}" height="{height}" href="data:image/png;base64,{b64}"/></svg>'
        )

    try:
        import vtracer
    except ImportError:
        raise ConversionError("Vector tracing is unavailable: the 'vtracer' package is not installed.")

    traced = image.convert("RGBA")
    traced.thumbnail((MAX_TRACE_SIDE, MAX_TRACE_SIDE), Image.Resampling.LANCZOS)
    png = io.BytesIO()
    traced.save(png, format="PNG")

    svg = vtracer.convert_raw_image_to_svg(
        png.getvalue(),
        img_format="png",
        colormode=options.svg_colormode,
        filter_speckle=options.svg_filter_speckle,
        color_precision=options.svg_color_precision,
    )
    # Scale the traced paths back up to the original dimensions.
    tw, th = traced.size
    return re.sub(
        r'<svg ([^>]*?)width="\d+" height="\d+"',
        rf'<svg \1width="{width}" height="{height}" viewBox="0 0 {tw} {th}"',
        svg,
        count=1,
    )


def convert(image: Image.Image, fmt: OutputFormat, options: ConvertOptions, source_name: str) -> ConvertResult:
    """Convert an image to the given format and return the encoded file."""
    if options.resize:
        image = image.resize(options.resize, Image.Resampling.LANCZOS)

    filename = f"{Path(source_name).stem}.{fmt.extension}"

    if fmt.pil_format is None:
        svg = image_to_svg(image, options)
        return ConvertResult(filename, svg.encode("utf-8"), fmt.mime, svg)

    prepared = prepare_for(image, fmt)
    save_kwargs = {"format": fmt.pil_format}
    if fmt.has_quality:
        save_kwargs["quality"] = options.quality

    buffer = io.BytesIO()
    try:
        prepared.save(buffer, **save_kwargs)
    except (OSError, ValueError) as e:
        raise ConversionError(f"Could not save as {fmt.label} ({e}).")
    return ConvertResult(filename, buffer.getvalue(), fmt.mime, prepared)
