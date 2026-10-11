"""双林寺 · 沉浸探秘 —— 程序化分层地图生成器（正立面殿宇版）

布局依据「建筑布局平面图」（南北中轴，入口在南）。
殿宇改为「正立面」像素建筑：石台基 + 红柱开间 + 门/格窗 + 大屋顶（飞檐翘角、正脊鸱吻）+ 匾额。
地面 / 围墙 / 树木为俯视，构成经典 RPG 的「俯视地面 + 立面建筑」混排。
输出 ground.png / props/*.png / collision.png / data/map.js
"""
import os
import json
import base64
import random
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS = os.path.join(BASE, "assets", "maps")
PROPS = os.path.join(MAPS, "props")
DATA = os.path.join(BASE, "data")
PREVIEW = os.path.join(BASE, "_preview")
FONT_TTF = os.path.join(BASE, "thirdparty", "fonts", "Cubic_11.ttf")

W, H = 700, 1000
AXIS = 349
random.seed(7)

GRASS = (150, 170, 96); GRASS2 = (134, 154, 82); GRASS_D = (114, 134, 72)
STONE = (201, 191, 162); STONE2 = (185, 174, 144); STONE_L = (216, 207, 180)
PATH = (197, 177, 121); PATH_D = (179, 159, 105)
ROOF = (86, 94, 104); ROOF_D = (58, 66, 76); ROOF_L = (112, 120, 132); RIDGE = (40, 45, 54)
WALLB = (190, 136, 76); COPING = (86, 94, 86)
WOOD = (168, 74, 58); WOOD_D = (118, 48, 38); WOOD_L = (196, 106, 84)
OUT = (30, 34, 40)
TREE_D = (44, 72, 42); TREE = (66, 104, 58); TREE_L = (100, 142, 74)
TRUNK = (92, 64, 42); TRUNK_D = (66, 44, 30)
FOREST_BG = (98, 118, 66)
PLAQUE = (150, 60, 48); PLAQUE_T = (238, 226, 178)
DOOR = (34, 26, 26)


def layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


# ---------------- 地面 ----------------
def stone(img, x0, y0, x1, y1, base=STONE, joint=STONE2, step=11):
    d = ImageDraw.Draw(img)
    d.rectangle((x0, y0, x1, y1), fill=base)
    for yy in range(int(y0), int(y1) + 1, step):
        d.line((x0, yy, x1, yy), fill=joint)
    i = 0
    for xx in range(int(x0), int(x1) + 1, step):
        off = step // 2 if i % 2 else 0
        d.line((xx + off, y0, xx + off, y1), fill=joint)
        i += 1
    for _ in range(int((x1 - x0) * (y1 - y0) / 90)):
        d.point((random.randint(x0, x1), random.randint(y0, y1)), fill=STONE_L)


def path(img, pts, width=14):
    d = ImageDraw.Draw(img)
    d.line(pts, fill=PATH_D, width=width + 2, joint="curve")
    d.line(pts, fill=PATH, width=width, joint="curve")


def draw_ground():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, H), fill=GRASS)
    for _ in range(9000):
        d.point((random.randint(0, W - 1), random.randint(0, H - 1)),
                fill=random.choice([GRASS2, GRASS_D, (160, 178, 104)]))
    d.rectangle((0, 0, W, 26), fill=FOREST_BG)
    d.rectangle((0, H - 26, W, H), fill=FOREST_BG)
    d.rectangle((0, 0, 24, H), fill=FOREST_BG)
    d.rectangle((W - 24, 0, W, H), fill=FOREST_BG)
    stone(img, 92, 120, 608, 890)
    path(img, [(AXIS, 940), (AXIS, 130)], 24)
    path(img, [(AXIS, 460), (110, 460)], 15)
    path(img, [(AXIS, 460), (590, 460)], 15)
    path(img, [(AXIS, 700), (110, 700)], 13)
    path(img, [(AXIS, 700), (590, 700)], 13)
    return img


# ---------------- 正立面殿宇 ----------------
def facade(x0, y0, x1, y1, label, kind="hall"):
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    L = layer(); d = ImageDraw.Draw(L)
    w = x1 - x0; cx = (x0 + x1) // 2
    eave_y = y0 + int((y1 - y0) * 0.46)          # 檐口线
    wall_b = y1 - 9
    bays = 3 if w < 150 else 5
    if kind == "gate":
        eave_y = y0 + int((y1 - y0) * 0.42)

    # 台基 + 台阶
    d.rectangle((x0 - 6, y1 - 12, x1 + 6, y1 + 6), fill=STONE, outline=OUT)
    d.line((x0 - 5, y1 + 3, x1 + 5, y1 + 3), fill=STONE2)
    d.rectangle((cx - 13, y1 + 4, cx + 13, y1 + 12), fill=STONE_L, outline=OUT)

    # 墙身
    d.rectangle((x0, eave_y + 8, x1, wall_b), fill=WOOD, outline=OUT)
    d.line((x0 + 2, eave_y + 10, x1 - 2, eave_y + 10), fill=WOOD_L)
    for i in range(1, bays):
        bx = x0 + w * i // bays
        d.line((bx, eave_y + 9, bx, wall_b - 1), fill=WOOD_D, width=2)
    d.line((x0, wall_b, x1, wall_b), fill=WOOD_D)
    # 门
    dh = 34 if w > 150 else 26
    d.rectangle((cx - 12, wall_b - dh, cx + 12, wall_b), fill=DOOR, outline=OUT)
    d.rectangle((cx - 12, wall_b - dh, cx + 12, wall_b - dh + 2), fill=WOOD_D)
    d.line((cx, wall_b - dh + 3, cx, wall_b - 1), fill=(70, 52, 44))
    # 格窗（侧间）
    wy0 = eave_y + 13; wy1 = wall_b - dh - 6
    if w > 120 and wy1 > wy0 + 4:
        for wx in (x0 + w // 4, x1 - w // 4):
            d.rectangle((wx - 11, wy0, wx + 11, wy1), fill=(60, 46, 40), outline=OUT)
            d.line((wx, wy0 + 1, wx, wy1 - 1), fill=STONE_L)
            d.line((wx - 10, (wy0 + wy1) // 2, wx + 10, (wy0 + wy1) // 2), fill=STONE_L)

    # 屋顶（梯形：檐宽 > 脊宽）
    eave_x0, eave_x1 = x0 - 12, x1 + 12
    ridge_x0, ridge_x1 = x0 + int(w * 0.16), x1 - int(w * 0.16)
    ridge_y = y0 + 2
    d.polygon([(eave_x0, eave_y), (ridge_x0, ridge_y), (ridge_x1, ridge_y), (eave_x1, eave_y)],
              fill=ROOF, outline=OUT)
    step = max(4, w // 26)
    for xx in range(int(eave_x0) + 3, int(eave_x1) - 2, step):
        # 沿斜边的竖直瓦垄
        t0 = (xx - eave_x0) / max(1, (eave_x1 - eave_x0))
        rx = eave_x0 + (ridge_x0 - eave_x0) * 0 + (xx - eave_x0)
        d.line((xx, ridge_y + 3, xx, eave_y), fill=ROOF_D)
    d.line((eave_x0 + 2, eave_y - 1, eave_x1 - 2, eave_y - 1), fill=ROOF_L)
    # 正脊 + 鸱吻
    d.rectangle((ridge_x0 - 6, ridge_y - 5, ridge_x1 + 6, ridge_y + 1), fill=RIDGE, outline=OUT)
    d.polygon([(ridge_x0 - 6, ridge_y - 5), (ridge_x0 - 12, ridge_y - 14), (ridge_x0 - 4, ridge_y - 2)],
              fill=RIDGE, outline=OUT)
    d.polygon([(ridge_x1 + 6, ridge_y - 5), (ridge_x1 + 12, ridge_y - 14), (ridge_x1 + 4, ridge_y - 2)],
              fill=RIDGE, outline=OUT)
    # 飞檐翘角
    d.polygon([(eave_x0, eave_y), (eave_x0 - 10, eave_y + 9), (eave_x0 + 4, eave_y - 2)], fill=ROOF, outline=OUT)
    d.polygon([(eave_x1, eave_y), (eave_x1 + 10, eave_y + 9), (eave_x1 - 4, eave_y - 2)], fill=ROOF, outline=OUT)
    # 檐下阴影
    d.rectangle((x0 - 6, eave_y + 1, x1 + 6, eave_y + 6), fill=ROOF_D, outline=OUT)

    # 匾额（檐下居中）
    try:
        f = ImageFont.truetype(FONT_TTF, 15)
        tw = d.textlength(label, font=f)
        px = cx - tw / 2 - 5; py = eave_y + 9
        d.rectangle((px, py, px + tw + 10, py + 20), fill=PLAQUE, outline=OUT)
        d.rectangle((px + 2, py + 2, px + tw + 8, py + 18), outline=PLAQUE_T)
        d.text((px + 5, py + 2), label, font=f, fill=PLAQUE_T)
    except Exception:
        pass
    return L


def wall_rect(x0, y0, x1, y1, t=12):
    L = layer(); d = ImageDraw.Draw(L)
    for pts in [[(x0, y0), (x1, y0)], [(x1, y0), (x1, y1)], [(x1, y1), (x0, y1)], [(x0, y1), (x0, y0)]]:
        d.line(pts, fill=OUT, width=t + 2, joint="curve")
        d.line(pts, fill=WALLB, width=t, joint="curve")
        d.line(pts, fill=COPING, width=t - 5, joint="curve")
    return L


def tree(r, seed=0):
    rnd = random.Random(seed)
    sz = r * 2 + 12
    L = Image.new("RGBA", (sz, sz + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    cx = sz // 2; base = sz + 4
    d.ellipse((cx - r, base - r // 3, cx + r, base + r // 4), fill=(20, 30, 16, 70))
    tw = max(3, r // 4)
    d.polygon([(cx - tw - 1, base), (cx + tw + 1, base), (cx + tw - 1, base - r), (cx - tw + 1, base - r)],
              fill=TRUNK, outline=TRUNK_D)
    blobs = []
    for i in range(7):
        a = i / 7 * 6.283
        rr = r * (0.52 + 0.24 * rnd.random())
        ox = int(math.cos(a) * r * 0.46); oy = int(math.sin(a) * r * 0.36) - r
        blobs.append((cx + ox, base + oy, rr))
    for (x, y, rr) in blobs:
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=TREE_D, outline=OUT)
    for (x, y, rr) in blobs:
        d.ellipse((x - rr * .82, y - rr * .82 - 2, x + rr * .82, y + rr * .82 - 2), fill=TREE, outline=OUT)
    for (x, y, rr) in blobs[::2]:
        d.ellipse((x - rr * .5, y - rr * .8, x + rr * .35, y + rr * .1), fill=TREE_L)
    return L.crop(L.getbbox())


def sprite_at(img, x, y):
    full = layer(); full.alpha_composite(img, (int(x - img.width / 2), int(y - img.height)))
    return full


# (name, x0, y0, x1, y1, 匾额, kind)
HALLS = [
    ("danmu", 279, 176, 419, 284, "佛母殿", "hall"),
    ("daxiong", 249, 320, 449, 438, "大雄宝殿", "main"),
    ("shijia", 259, 478, 439, 586, "释迦殿", "hall"),
    ("tianwang", 264, 632, 434, 740, "天王殿", "hall"),
    ("shanmen", 299, 796, 399, 888, "山门", "gate"),
    ("pusa", 120, 450, 190, 558, "菩萨殿", "side"),
    ("qianfo", 510, 450, 580, 558, "千佛殿", "side"),
    ("gulou", 124, 630, 186, 710, "鼓楼", "side"),
    ("zhonglou", 514, 630, 576, 710, "钟楼", "side"),
    ("yanwang", 112, 740, 180, 834, "阎王殿", "side"),
    ("tudi", 208, 768, 276, 842, "土地殿", "side"),
    ("luohan", 516, 740, 584, 834, "罗汉殿", "side"),
    ("qielan", 418, 768, 486, 842, "伽蓝殿", "side"),
    ("zhenyi", 520, 186, 610, 284, "贞义殿", "side"),
]


def main():
    for p in [MAPS, PROPS, DATA, PREVIEW]:
        os.makedirs(p, exist_ok=True)
    ground = draw_ground().convert("RGB")
    ground.save(os.path.join(MAPS, "ground.png"))
    render = ground.convert("RGBA")
    props = []
    blocked = np.zeros((H, W), dtype=bool)

    def place(img, name, block="alpha", base_w=0, base_h=0, base_cx=0, base_y0=0):
        bbox = img.getbbox()
        if bbox is None:
            return
        x0, y0, x1, y1 = bbox
        crop = img.crop(bbox)
        crop.save(os.path.join(PROPS, f"{name}.png"))
        props.append({"file": f"assets/maps/props/{name}.png", "x": x0, "y": y0,
                      "w": x1 - x0, "h": y1 - y0, "anchorY": float(y1), "cat": name.split("_")[0]})
        render.alpha_composite(crop, (x0, y0))
        if block == "alpha":
            blocked[y0:y1, x0:x1] |= (np.array(crop)[:, :, 3] > 0)
        elif block == "base" and base_w:
            blocked[base_y0:base_y0 + base_h, base_cx - base_w // 2:base_cx + base_w // 2] = True

    # 围墙
    place(wall_rect(58, 112, 640, 900), "wall")
    # 殿宇（碰撞只取台基）
    for (name, x0, y0, x1, y1, label, kind) in HALLS:
        place(facade(x0, y0, x1, y1, label, kind), f"hall_{name}", block="none")
        blocked[y0 - 14:y1 + 10, x0 - 4:x1 + 4] = True   # 建筑整体阻挡

    # 唐槐 + 松柏
    place(sprite_at(tree(30, 1), 200, 452), "tree_tanghuai", block="base", base_w=18, base_h=14, base_cx=200, base_y0=438)
    for i, (x, y, s) in enumerate([(150, 300, .9), (560, 300, .9), (150, 900, .9), (560, 880, .9),
                                   (300, 700, .8), (410, 700, .8)]):
        r = int(14 * s)
        t = tree(r, i + 2)
        place(sprite_at(t, x, y), f"tree_{i:02d}", block="base", base_w=10, base_h=10, base_cx=x, base_y0=y - 10)

    for i in range(90):
        side = random.randint(0, 3)
        if side == 0: x, y = random.randint(8, W - 8), random.randint(8, 24)
        elif side == 1: x, y = random.randint(8, W - 8), random.randint(H - 24, H - 8)
        elif side == 2: x, y = random.randint(8, 22), random.randint(8, H - 8)
        else: x, y = random.randint(W - 22, W - 8), random.randint(8, H - 8)
        place(sprite_at(tree(random.randint(10, 15), i), x, y), f"forest_{i:03d}", block="none")

    play = Image.new("L", (W, H), 0)
    ImageDraw.Draw(play).rectangle((70, 124, 628, 928), fill=255)
    walkable = (np.array(play) > 0) & ~blocked
    # 贴墙回廊 + 门洞：保证全寺连通
    walkable[124:162, 74:624] = True      # 北廊
    walkable[858:898, 74:624] = True      # 南廊
    walkable[124:898, 74:116] = True      # 西廊
    walkable[124:898, 584:624] = True     # 东廊
    walkable[730:930, 302:396] = True     # 山门门洞贯通

    render.convert("RGB").save(os.path.join(PREVIEW, "map_render.png"))
    Image.fromarray((walkable * 255).astype(np.uint8)).save(os.path.join(MAPS, "collision.png"))
    ov = np.array(render.convert("RGB")).copy()
    ov[walkable] = (ov[walkable] * 0.55 + np.array([0, 255, 90]) * 0.45).astype(np.uint8)
    Image.fromarray(ov).resize((560, 800)).save(os.path.join(PREVIEW, "map_walk.png"))
    render.convert("RGB").resize((700, 1000)).save(os.path.join(PREVIEW, "map_big.png"))

    bits = np.packbits(walkable.astype(np.uint8)).tobytes()
    mapdata = {"w": W, "h": H, "ground": "assets/maps/ground.png",
               "collision": "assets/maps/collision.png", "collisionW": W, "collisionH": H,
               "collisionBits": base64.b64encode(bits).decode("ascii"), "props": props}
    with open(os.path.join(DATA, "map.js"), "w", encoding="utf-8") as f:
        f.write("// auto-generated by tools/gen_map.py\nconst MAPDATA = ")
        f.write(json.dumps(mapdata, ensure_ascii=False, indent=1))
        f.write(";\n")
    print("props:", len(props), "walkable frac:", round(float(walkable.mean()), 3))


if __name__ == "__main__":
    main()
