from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import List, Tuple, TypedDict

import qrcode
from PIL import Image, ImageDraw, ImageFont

CARD_WIDTH: int = 1000
CARD_HEIGHT: int = 600

BG_COLOR: Tuple[int, int, int] = (245, 245, 245)
TEXT_COLOR: Tuple[int, int, int] = (20, 20, 20)
ACCENT: Tuple[int, int, int] = (0, 90, 160)

FONT_PATH: str = "assets/arial.ttf"

FONT_TITLE: ImageFont.FreeTypeFont = ImageFont.truetype(FONT_PATH, 70)
FONT_LABEL: ImageFont.FreeTypeFont = ImageFont.truetype(FONT_PATH, 32)
FONT_VALUE: ImageFont.FreeTypeFont = ImageFont.truetype(FONT_PATH, 36)


class CardData(TypedDict):
    company: str
    name: str
    gender: str
    dob: str
    mobile: str
    address: str


def draw_label(draw: ImageDraw.ImageDraw, text: str, xy: Tuple[int, int]) -> None:
    draw.text(xy, text, font=FONT_LABEL, fill=ACCENT)


def draw_value(draw: ImageDraw.ImageDraw, text: str, xy: Tuple[int, int]) -> None:
    draw.text(xy, text, font=FONT_VALUE, fill=TEXT_COLOR)


def render_card(data: CardData, outdir: str | Path) -> Path:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    card: Image.Image = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), BG_COLOR)
    draw: ImageDraw.ImageDraw = ImageDraw.Draw(card)

    panel_w: int = 260
    draw.rectangle([(0, 0), (panel_w, CARD_HEIGHT)], fill=ACCENT)

    brand_y: int = 40
    draw.text((40, brand_y), data["company"].upper(), font=FONT_TITLE, fill=(0, 0, 0))

    x_offset: int = panel_w + 40
    y_start: int = 60

    y: int = y_start + 120
    row_gap: int = 55

    fields: List[Tuple[str, str]] = [
        ("Name", data["name"]),
        ("Gender", data["gender"]),
        ("D.O.B.", data["dob"]),
        ("Mobile", data["mobile"]),
        ("Address", data["address"]),
    ]

    for label, value in fields:
        draw_label(draw, label.upper(), (x_offset, y))
        draw_value(draw, value, (x_offset + 250, y))
        y += row_gap

    qr = qrcode.make(f"{data['company']}|{data['name']}|")
    qr_image: Image.Image = qr.get_image()
    qr_resized: Image.Image = qr_image.resize((200, 200))
    card.paste(qr_resized, (CARD_WIDTH - 250, CARD_HEIGHT - 250))

    draw.line(
        [(panel_w, CARD_HEIGHT - 40), (CARD_WIDTH - 40, CARD_HEIGHT - 40)],
        fill=ACCENT,
        width=4,
    )

    card_path: Path = outdir / f"{data['name'].replace(' ', '_')}.png"
    card.save(card_path)

    return card_path


def process_csv(path: str | Path, outdir: str | Path) -> None:
    with open(path, newline="", encoding="utf-8") as f:
        reader: csv.DictReader = csv.DictReader(f)

        for row in reader:
            clean: CardData = CardData(
                company=row["company"].strip(),
                name=row["name"].strip(),
                gender=row["gender"].strip(),
                dob=row["dob"].strip(),
                mobile=row["mobile"].strip(),
                address=row["address"].strip(),
            )

            render_card(clean, outdir)


def cli() -> None:
    ap = argparse.ArgumentParser(description="ID Card Generator")

    ap.add_argument("--input", help="CSV file path")
    ap.add_argument("--out", help="Output directory", default="output")
    ap.add_argument("--single", action="store_true", help="Single mode")

    ap.add_argument("--company")
    ap.add_argument("--name")
    ap.add_argument("--gender")
    ap.add_argument("--dob")
    ap.add_argument("--mobile")
    ap.add_argument("--address")

    args = ap.parse_args()

    # Interactive mode
    if not any([args.input, args.single]):
        print("Interactive mode activated. Leave blank to re-prompt.")
        fields: List[str] = ["company", "name", "gender", "dob", "mobile", "address"]

        data: CardData = CardData(
            company="",
            name="",
            gender="",
            dob="",
            mobile="",
            address="",
        )

        for f in fields:
            while True:
                v = input(f"Enter {f.upper()}: ").strip()
                if v:
                    data[f] = v
                    break

        render_card(data, args.out)
        return

    # Single mode
    if args.single:
        required = ["company", "name", "gender", "dob", "mobile", "address"]
        missing = [r for r in required if getattr(args, r) is None]

        if missing:
            raise SystemExit(f"Missing fields: {missing}")

        data: CardData = CardData(
            company=args.company,
            name=args.name,
            gender=args.gender,
            dob=args.dob,
            mobile=args.mobile,
            address=args.address,
        )

        render_card(data, args.out)
        return

    # CSV mode
    if args.input:
        process_csv(args.input, args.out)
        return

    raise SystemExit("Provide --input csv or --single mode.")


if __name__ == "__main__":
    cli()
