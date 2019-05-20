import subprocess
from pathlib import Path

import PIL.Image


def generate_thumbnail(
    source: Path, target: Path, width: int = 320, height: int = 240
) -> None:
    if target.exists():
        return

    target.parent.mkdir(exist_ok=True, parents=True)

    try:
        image = PIL.Image.open(str(source))
        image.thumbnail((width, height))
        image.save(target, "JPEG")
    except OSError:
        subprocess.run(
            [
                "ffmpeg",
                "-i",
                str(source),
                "-vframes",
                "1",
                "-s",
                f"{width}x{height}",
                str(target),
            ]
        )
