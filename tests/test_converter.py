import io

import pytest
import converter
from PIL import Image

from converter import (
    FORMATS,
    SVG_EMBED,
    SVG_TRACE,
    ConversionError,
    ConvertOptions,
    convert,
    load_image,
    normalize,
)

SOURCE_MODES = ["RGBA", "RGB", "L", "LA", "P", "1", "CMYK", "I", "I;16", "F", "PA", "YCbCr"]


def make_image(mode, size=(64, 48)):
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    w, h = size
    for x in range(w // 4, 3 * w // 4):
        for y in range(h // 6, 5 * h // 6):
            image.putpixel((x, y), (20, 120, 220, 255))
    if mode == "P":
        return image.convert("P")
    if mode == "I;16":
        return image.convert("L").convert("I").point(lambda v: v * 257).convert("I;16")
    return image.convert(mode)


@pytest.mark.parametrize("mode", SOURCE_MODES)
def test_normalize_gives_displayable_mode(mode):
    assert normalize(make_image(mode)).mode in ("L", "LA", "RGB", "RGBA")


def test_16bit_image_keeps_brightness():
    image = Image.new("I;16", (4, 4), 65535)
    assert normalize(image).getpixel((0, 0)) == 255


@pytest.mark.parametrize("mode", SOURCE_MODES)
@pytest.mark.parametrize("label", [label for label in FORMATS if label != "SVG"])
def test_every_mode_converts_to_every_raster_format(mode, label):
    fmt = FORMATS[label]
    result = convert(make_image(mode), fmt, ConvertOptions(), "photo.png")

    assert result.filename == f"photo.{fmt.extension}"
    reopened = Image.open(io.BytesIO(result.data))
    assert reopened.format == fmt.pil_format


def test_jpeg_flattens_transparency_onto_white():
    result = convert(make_image("RGBA"), FORMATS["JPG/JPEG"], ConvertOptions(), "a.png")
    reopened = Image.open(io.BytesIO(result.data))
    assert reopened.mode == "RGB"
    r, g, b = reopened.getpixel((0, 0))
    assert min(r, g, b) > 240


def test_resize():
    result = convert(make_image("RGB"), FORMATS["PNG"], ConvertOptions(resize=(10, 20)), "a.png")
    assert Image.open(io.BytesIO(result.data)).size == (10, 20)


@pytest.mark.parametrize("mode", ["RGBA", "RGB", "L", "CMYK", "I;16"])
@pytest.mark.parametrize(
    "options",
    [
        ConvertOptions(svg_mode=SVG_TRACE),
        ConvertOptions(svg_mode=SVG_TRACE, svg_colormode="binary"),
        ConvertOptions(svg_mode=SVG_EMBED),
    ],
)
def test_svg(mode, options):
    result = convert(make_image(mode), FORMATS["SVG"], options, "logo.png")
    svg = result.data.decode("utf-8")
    assert result.filename == "logo.svg"
    assert "<svg" in svg and 'width="64" height="48"' in svg


def test_svg_trace_downscales_large_images_but_keeps_size():
    result = convert(make_image("RGB", size=(3000, 1500)), FORMATS["SVG"], ConvertOptions(), "big.png")
    svg = result.data.decode("utf-8")
    assert 'width="3000" height="1500" viewBox="0 0 1024 512"' in svg


def test_svg_previews():
    traced = convert(make_image("RGBA"), FORMATS["SVG"], ConvertOptions(), "logo.png")
    assert traced.preview == traced.data.decode("utf-8")
    embedded = convert(make_image("RGBA"), FORMATS["SVG"], ConvertOptions(svg_mode=SVG_EMBED), "logo.png")
    assert isinstance(embedded.preview, Image.Image)


def test_svg_trace_skips_preview_when_large(monkeypatch):
    monkeypatch.setattr(converter, "MAX_SVG_PREVIEW_BYTES", 10)
    result = convert(make_image("RGBA"), FORMATS["SVG"], ConvertOptions(), "logo.png")
    assert result.preview is None and result.data


def test_svg_trace_rejects_huge_output(monkeypatch):
    monkeypatch.setattr(converter, "MAX_SVG_BYTES", 10)
    with pytest.raises(ConversionError, match="too large"):
        convert(make_image("RGBA"), FORMATS["SVG"], ConvertOptions(), "logo.png")


def test_svg_trace_panic_becomes_conversion_error(monkeypatch):
    import vtracer

    class PanicException(BaseException):
        pass

    def panic(*args, **kwargs):
        raise PanicException("overflow")

    monkeypatch.setattr(vtracer, "convert_raw_image_to_svg", panic)
    with pytest.raises(ConversionError, match="overflow"):
        convert(make_image("RGBA"), FORMATS["SVG"], ConvertOptions(), "logo.png")


def test_load_image_rejects_non_images():
    with pytest.raises(ConversionError):
        load_image(io.BytesIO(b"not an image"))


def test_load_image_rejects_truncated_files():
    buffer = io.BytesIO()
    make_image("RGB", size=(200, 200)).save(buffer, format="JPEG")
    with pytest.raises(ConversionError):
        load_image(io.BytesIO(buffer.getvalue()[:300]))


def test_load_image_applies_exif_rotation():
    exif = Image.Exif()
    exif[0x0112] = 6  # rotate 90° clockwise
    buffer = io.BytesIO()
    make_image("RGB", size=(40, 20)).save(buffer, format="JPEG", exif=exif)
    image = load_image(buffer)
    assert image.size == (20, 40)
    assert image.format == "JPEG"
