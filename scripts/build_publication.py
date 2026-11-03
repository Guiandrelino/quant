"""Build a portable public research demo and LinkedIn cover from synthetic data."""

import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from equity_lab.data import synthetic_data
from equity_lab.research import run_research

ROOT = Path(__file__).resolve().parents[1]


def build() -> None:
    output = ROOT / "outputs" / "publication"
    run_research(synthetic_data(), output)
    site = ROOT / "site"
    site.mkdir(exist_ok=True)
    shutil.copyfile(output / "report.html", site / "index.html")
    shutil.copyfile(output / "manifest.json", site / "manifest.json")
    assets = ROOT / "docs" / "assets"
    assets.mkdir(exist_ok=True)
    image = Image.new("RGB", (1200, 627), "#0b1220")
    draw = ImageDraw.Draw(image)

    def font(size: int):
        for name in [
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]:
            if Path(name).exists():
                return ImageFont.truetype(name, size)
        return ImageFont.load_default(size=size)

    draw.rectangle((0, 0, 14, 627), fill="#38bdf8")
    draw.text((65, 65), "QUANTITATIVE INVESTMENT RESEARCH", font=font(24), fill="#38bdf8")
    draw.text((65, 145), "Brazilian Equity Lab", font=font(64), fill="#f8fafc")
    draw.text((65, 245), "Momentum + Low Volatility", font=font(34), fill="#cbd5e1")
    for i, text in enumerate(
        [
            "Delayed execution & trading costs",
            "Portfolio constraints & risk analytics",
            "Reproducible research & automated tests",
        ]
    ):
        draw.text((70, 325 + i * 48), text, font=font(26), fill="#e2e8f0")
    draw.rounded_rectangle((65, 520, 1135, 580), radius=12, fill="#713f12")
    draw.text(
        (90, 535),
        "SYNTHETIC DEMO | No real-market performance claims",
        font=font(24),
        fill="#fef3c7",
    )
    image.save(assets / "linkedin-cover.png")
    print(
        json.dumps(
            {"public_demo": str(site / "index.html"), "cover": str(assets / "linkedin-cover.png")},
            indent=2,
        )
    )


if __name__ == "__main__":
    build()
