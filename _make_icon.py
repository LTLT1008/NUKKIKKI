"""NUKKIKKI 아이콘 생성: 🐵 + 베레모 + 🎨 → nukkikki.png / nukkikki.ico"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).parent
S = 512
EMOJI_FONT = r"C:\Windows\Fonts\seguiemj.ttf"


def emoji_layer(char: str, size: int) -> Image.Image:
    font = ImageFont.truetype(EMOJI_FONT, size)
    img = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((size, size), char, font=font, embedded_color=True, anchor="mm")
    return img.crop(img.getbbox())


def make_beret(w: int, h: int, color=(35, 40, 60, 255)) -> Image.Image:
    # 베레모: 납작 타원 + 윗꼭지, 살짝 기울임
    layer = Image.new("RGBA", (w * 2, h * 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = w, h * 2
    d.ellipse((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2), fill=color)
    d.ellipse((cx - w // 8, cy - h // 2 - h // 4, cx + w // 8, cy - h // 2 + h // 8),
              fill=color)  # 꼭지
    return layer.rotate(-12, expand=True, resample=Image.BICUBIC)


canvas = Image.new("RGBA", (S, S), (0, 0, 0, 0))

monkey = emoji_layer("\U0001F435", 400)  # 🐵
mw, mh = monkey.size
mx, my = (S - mw) // 2, (S - mh) // 2 + 30
canvas.alpha_composite(monkey, (mx, my))

palette = emoji_layer("\U0001F3A8", 190)  # 🎨
canvas.alpha_composite(palette, (S - palette.width - 8, S - palette.height - 4))

canvas.save(BASE / "nukkikki.png")
canvas.resize((256, 256), Image.LANCZOS).save(
    BASE / "nukkikki.ico", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
)
print("생성 완료:", BASE / "nukkikki.png")
