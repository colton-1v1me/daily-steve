"""Draw the day's quote into the blank area of steve.jpg.
Used by post_quote.py."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = Path(__file__).parent
PHOTO = HERE / "steve.jpg"                      # background photo with blank space on the right
FONT = HERE / "fonts" / "Anton-Regular.ttf"     # bold headline font

OUT_W = 1400              # width of the posted image (height follows the photo's shape)
TEXT_LEFT = 0.52          # where the text area starts, as a fraction of the width
MARGIN = 60               # padding on the right and top/bottom of the text area
TEXT_COLOR = "#111111"
NOTE_COLOR = "#444444"


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT), size)


def wrap(draw, text, fnt, max_w):
    """Greedy word-wrap so every line fits within max_w pixels."""
    words, lines, line = text.split(), [], ""
    for w in words:
        trial = f"{line} {w}".strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            line = trial
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def fit(draw, text, max_w, max_h, start=130, floor=36):
    """Largest font size at which the wrapped text fits in the box."""
    for size in range(start, floor, -2):
        fnt = font(size)
        lines = wrap(draw, text, fnt, max_w)
        line_h = int(size * 1.12)
        if all(draw.textlength(l, font=fnt) <= max_w for l in lines) and len(lines) * line_h <= max_h:
            return fnt, lines, line_h
    fnt = font(floor)
    return fnt, wrap(draw, text, fnt, max_w), int(floor * 1.12)


def make_image(text: str, author: str, note: str | None = None, out: Path = HERE / "quote.png") -> Path:
    canvas = ImageOps.exif_transpose(Image.open(PHOTO)).convert("RGB")
    W = OUT_W
    H = round(canvas.height * W / canvas.width)
    canvas = canvas.resize((W, H), Image.LANCZOS)

    draw = ImageDraw.Draw(canvas)
    x0 = int(W * TEXT_LEFT)
    box_w = W - x0 - MARGIN
    author_fnt = font(44)
    note_fnt = font(32)
    reserved = 80 + (60 if note else 0)          # space for author (and note)
    box_h = H - 2 * MARGIN - reserved

    fnt, lines, line_h = fit(draw, f"\u201c{text}\u201d", box_w, box_h)
    total_h = len(lines) * line_h + reserved
    y = (H - total_h) // 2
    for line in lines:
        lw = draw.textlength(line, font=fnt)
        draw.text((x0 + (box_w - lw) / 2, y), line, font=fnt, fill=TEXT_COLOR)
        y += line_h

    if note:
        y += 12
        for line in wrap(draw, f"[{note}]", note_fnt, box_w):
            lw = draw.textlength(line, font=note_fnt)
            draw.text((x0 + (box_w - lw) / 2, y), line, font=note_fnt, fill=NOTE_COLOR)
            y += 38

    y += 24
    sig = f"~ {author}"
    sw = draw.textlength(sig, font=author_fnt)
    draw.text((x0 + box_w - sw, y), sig, font=author_fnt, fill=TEXT_COLOR)

    canvas.save(out, "PNG")
    return out


if __name__ == "__main__":
    make_image("I want to be the hypotenuse", "Stephen R Hyde", "bends over and stretches arms out, straight-faced", HERE / "preview.png")
    print("wrote preview.png")
