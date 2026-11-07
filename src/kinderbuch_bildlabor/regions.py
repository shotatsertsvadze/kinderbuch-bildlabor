"""Bildregionen: Grenzprüfung, Ausschnitte und Markierung auf dem Vollbild.

Koordinaten sind immer Pixel [x, y, Breite, Höhe] im Ausgangsbild (wie der
IIIF-Regionsparameter), nie Bildschirmpixel. Gezeichnet und ausgeschnitten wird
deshalb am Bild in Originalgröße; erst die Anzeige skaliert.
"""

from PIL import Image, ImageDraw, ImageFont

COLORS = ["#d62728", "#1f77b4", "#2ca02c", "#9467bd", "#ff7f0e"]


def bounds_problems(xywh, width: int, height: int) -> list[str]:
    if len(xywh) != 4 or not all(type(v) is int for v in xywh):
        return ["Koordinaten müssen vier ganze Pixelwerte [x, y, Breite, Höhe] sein."]
    x, y, w, h = xywh
    problems = []
    if w <= 0 or h <= 0:
        problems.append("Breite und Höhe müssen größer als 0 sein.")
    if x < 0 or y < 0:
        problems.append("x und y dürfen nicht negativ sein.")
    if x + w > width:
        problems.append(f"Rechter Rand {x + w} liegt außerhalb der Bildbreite {width}.")
    if y + h > height:
        problems.append(f"Unterer Rand {y + h} liegt außerhalb der Bildhöhe {height}.")
    return problems


def crop(image: Image.Image, xywh) -> Image.Image:
    x, y, w, h = xywh
    return image.crop((x, y, x + w, y + h))


def draw_regions(image: Image.Image, regions: list[dict]) -> Image.Image:
    """Farbiger Rahmen mit weißem Rand außen und dunklem innen, damit er auf hellem wie dunklem Papier sichtbar bleibt."""
    marked = image.convert("RGB")
    draw = ImageDraw.Draw(marked)
    font = ImageFont.load_default(size=40)
    for number, region in enumerate(regions, start=1):
        x, y, w, h = region["xywh"]
        color = COLORS[(number - 1) % len(COLORS)]
        draw.rectangle((x - 4, y - 4, x + w + 3, y + h + 3), outline="white", width=4)
        draw.rectangle((x, y, x + w - 1, y + h - 1), outline=color, width=6)
        if w > 18 and h > 18:
            draw.rectangle(
                (x + 6, y + 6, x + w - 7, y + h - 7), outline="black", width=3
            )
        # Nummer links außerhalb, damit sie keinen Text in der Region verdeckt
        draw.text(
            (max(x - 34, 0), y),
            str(number),
            fill="white",
            font=font,
            stroke_width=4,
            stroke_fill="black",
        )
    return marked
