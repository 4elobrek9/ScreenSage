"""Screen capture encoding tests."""

import base64
from io import BytesIO

import pytest
from PIL import Image

from screensage.capture import capture_region, image_to_base64


def test_png_encoding_round_trip() -> None:
    image = Image.new("RGB", (3, 2), (10, 20, 30))
    decoded = Image.open(BytesIO(base64.b64decode(image_to_base64(image))))
    assert decoded.size == (3, 2)
    assert decoded.getpixel((0, 0)) == (10, 20, 30)


def test_capture_rejects_empty_region() -> None:
    with pytest.raises(ValueError):
        capture_region(0, 0, 0, 10)


def test_capture_passes_global_monitor_coordinates(mocker) -> None:
    shot = mocker.Mock(size=(2, 1), rgb=bytes((1, 2, 3, 4, 5, 6)))
    context = mocker.patch("mss.mss")
    context.return_value.__enter__.return_value.grab.return_value = shot
    image = capture_region(-1920, 50, 2, 1)
    context.return_value.__enter__.return_value.grab.assert_called_once_with(
        {"left": -1920, "top": 50, "width": 2, "height": 1}
    )
    assert image.getpixel((1, 0)) == (4, 5, 6)
