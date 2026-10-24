"""Screen-region capture utilities."""

from __future__ import annotations

import base64
from io import BytesIO

from PIL import Image


def capture_region(left: int, top: int, width: int, height: int) -> Image.Image:
    """Capture a global desktop rectangle, including negative monitor origins."""
    if width <= 0 or height <= 0:
        raise ValueError("Capture region must have positive width and height")
    import mss

    with mss.mss() as screen:
        shot = screen.grab({"left": left, "top": top, "width": width, "height": height})
        return Image.frombytes("RGB", shot.size, shot.rgb)


def image_to_base64(image: Image.Image) -> str:
    """Encode an image as a base64 PNG string."""
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")
