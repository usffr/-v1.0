"""双林寺 · 沉浸探秘 —— 原创角色像素素材（6 帧行走 + 2 帧待机呼吸）

精灵表：4 朝向(下/上/左/右) × 8 帧
  帧 0  = 待机（呼吸）
  帧 1  = 待机（下沉）
  帧 2-7 = 六帧行走循环
输出 assets/characters/hero_{male,female}.png, data/characters.js
"""
import os
import math
import json
from PIL import Image, ImageDraw

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "assets", "characters")
DATA = os.path.join(BASE, "data")
PREVIEW = os.path.join(BASE, "_preview")

CW, CH = 32, 40
DIRS = ["down", "up", "left", "right"]
FRAMES = 8
OUTL = (26, 28, 36)
SKIN = (236, 196, 158); SKIN_D = (206, 164, 126)
PANTS = (62, 66, 82); BOOT = (42, 46, 56)


def palette(g):
    if g == "male":
        return {"robe": (72, 116, 178), "robe_d": (50, 86, 142), "trim": (224, 228, 238), "hair": (40, 36, 48), "sash": (196, 84, 64)}
    return {"robe": (206, 122, 150), "robe_d": (168, 92, 120), "trim": (240, 226, 232), "hair": (54, 40, 34), "sash": (110, 170, 150)}


def rect(d, x0, y0, x1, y1, col, out=True):
    if x1 < x0: x0, x1 = x1, x0
    if y1 < y0: y0, y1 = y1, y0
    d.rectangle((x0, y0, x1, y1), fill=col, outline=OUTL if out else None)


def draw_char(g, direction, f):
    p = palette(g); L = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    cx = CW // 2
    side = direction in ("left", "right")
    fx = -1 if direction == "left" else 1
    # 相位
    if f in (0, 1):
        bob = 1 if f == 1 else 0
        legA = legB = 0; armA = armB = 0; liftA = liftB = 0
    else:
        w = f - 2; a = w / 6 * math.pi * 2
        bob = 1 if w in (1, 4) else 0
        legA = round(math.sin(a) * 2); legB = round(math.sin(a + math.pi) * 2)
        armA = -round(math.sin(a) * 2); armB = -round(math.sin(a + math.pi) * 2)
        liftA = 3 if w in (1, 2) else 0; liftB = 3 if w in (4, 5) else 0
    y_head = 8 + bob; y_head_b = y_head + 7; y_sh = y_head_b; y_hip = y_sh + 10; y_feet = CH - 3
    bw = 3 if side else 4

    # 腿
    if not side:
        # 正/背视：支撑腿不动，迈步腿抬起（不左右分开）
        rect(d, cx - 4, y_hip, cx - 1, y_feet - 3 - liftA, PANTS)
        rect(d, cx + 1, y_hip, cx + 4, y_feet - 3 - liftB, PANTS)
        rect(d, cx - 4, y_feet - 3 - liftA, cx - 1, y_feet - liftA, BOOT)
        rect(d, cx + 1, y_feet - 3 - liftB, cx + 4, y_feet - liftB, BOOT)
    else:
        # 侧视：前后摆腿
        lx = cx - 3 + legA
        rect(d, lx, y_hip, lx + 5, y_feet - 3 - liftA, PANTS)
        rect(d, lx, y_feet - 3 - liftA, lx + 5, y_feet - liftA, BOOT)
        bx = cx - 3 + legB
        rect(d, bx, y_hip + 1, bx + 5, y_feet - 4 - liftB, PANTS)
        rect(d, bx, y_feet - 3 - liftB, bx + 5, y_feet - liftB, BOOT)

    # 袍身
    rect(d, cx - bw, y_sh, cx + bw, y_hip, p["robe"])
    d.line((cx - bw, y_hip, cx + bw, y_hip), fill=p["robe_d"])
    if direction != "up":
        d.line((cx, y_sh + 2, cx, y_hip), fill=p["robe_d"])
        d.polygon([(cx - 2, y_sh), (cx, y_sh + 2), (cx + 2, y_sh)], fill=p["trim"], outline=OUTL)
    rect(d, cx - bw, y_hip - 2, cx + bw, y_hip - 1, p["sash"])

    # 手臂
    if not side:
        rect(d, cx - bw - 2, y_sh + 2, cx - bw - 1, y_hip - 3 + armA, p["robe_d"])
        rect(d, cx + bw + 1, y_sh + 2, cx + bw + 2, y_hip - 3 + armB, p["robe_d"])
    else:
        fpos = cx + fx * (bw + 1)
        rect(d, fpos - 1, y_sh + 2, fpos + 1, y_hip - 3 + armA, p["robe_d"])
        bpos = cx - fx * (bw + 1)
        rect(d, min(bpos, bpos + fx), y_sh + 3, max(bpos, bpos + fx), y_hip - 4 + armB, p["robe_d"])

    # 头
    rect(d, cx - 4, y_head, cx + 3, y_head_b, SKIN)
    if direction == "up":
        rect(d, cx - 4, y_head - 1, cx + 3, y_head_b - 1, p["hair"])
        d.line((cx - 2, y_head, cx - 2, y_head_b - 3), fill=tuple(min(255, v + 24) for v in p["hair"]))
        d.line((cx + 1, y_head, cx + 1, y_head_b - 3), fill=tuple(min(255, v + 24) for v in p["hair"]))
    elif direction == "down":
        rect(d, cx - 4, y_head - 1, cx + 3, y_head + 1, p["hair"])
        rect(d, cx - 4, y_head - 1, cx - 3, y_head + 4, p["hair"])
        rect(d, cx + 2, y_head - 1, cx + 3, y_head + 4, p["hair"])
    else:
        rect(d, cx - 4, y_head - 1, cx + 3, y_head + 1, p["hair"])
        if fx < 0:
            rect(d, cx + 1, y_head - 1, cx + 3, y_head_b, p["hair"]); rect(d, cx - 4, y_head, cx + 1, y_head_b, SKIN)
        else:
            rect(d, cx - 4, y_head - 1, cx - 2, y_head_b, p["hair"]); rect(d, cx - 2, y_head, cx + 3, y_head_b, SKIN)
    rect(d, cx - 1, y_head - 3, cx + 1, y_head - 1, p["hair"])
    if g == "female":
        rect(d, cx - 5, y_head, cx - 3, y_head + 5, p["hair"]); rect(d, cx + 2, y_head, cx + 4, y_head + 5, p["hair"])

    ey = y_head + 4
    if direction == "down":
        d.point((cx - 2, ey), fill=OUTL); d.point((cx + 1, ey), fill=OUTL)
    elif direction == "left":
        d.point((cx - 2, ey), fill=OUTL); d.point((cx - 5, ey + 1), fill=SKIN_D)
    elif direction == "right":
        d.point((cx + 1, ey), fill=OUTL); d.point((cx + 4, ey + 1), fill=SKIN_D)
    return L


def build(g):
    sheet = Image.new("RGBA", (CW * FRAMES, CH * len(DIRS)), (0, 0, 0, 0))
    for r, d in enumerate(DIRS):
        for c in range(FRAMES):
            sheet.alpha_composite(draw_char(g, d, c), (c * CW, r * CH))
    return sheet


def main():
    for p in [OUT, DATA, PREVIEW]:
        os.makedirs(p, exist_ok=True)
    for g in ["male", "female"]:
        s = build(g)
        s.save(os.path.join(OUT, f"hero_{g}.png"))
        s.resize((s.width * 4, s.height * 4), Image.NEAREST).save(os.path.join(PREVIEW, f"char_{g}.png"))
    meta = {"cellW": CW, "cellH": CH, "cols": FRAMES, "rows": len(DIRS), "dirs": DIRS,
            "idleSeq": [0, 1], "walkSeq": [2, 3, 4, 5, 6, 7],
            "male": "assets/characters/hero_male.png", "female": "assets/characters/hero_female.png"}
    with open(os.path.join(DATA, "characters.js"), "w", encoding="utf-8") as f:
        f.write("// auto-generated by tools/gen_char.py\nconst CHARDATA = ")
        f.write(json.dumps(meta, ensure_ascii=False, indent=1))
        f.write(";\n")
    print("characters:", CW, "x", CH, FRAMES, "frames x", len(DIRS), "dirs")


if __name__ == "__main__":
    main()
