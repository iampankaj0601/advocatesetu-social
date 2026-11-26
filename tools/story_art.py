"""Drawing helpers for AdvocateSetu story posts: original illustrated characters,
speech bubbles, highlighted text, stickers and bold palettes."""
import os, math, datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "tools", "fonts")
LOGO = os.path.join(ROOT, "brand", "logo_1024.png")
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

NAVY = (11, 27, 61)
GOLD = (244, 168, 30)
WHITE = (255, 255, 255)

# Bold palettes. bg/bg2 stay dark (brand navy family) so the bright accents pop.
PALETTES = {
    "punch":    dict(bg=(11, 27, 61),  bg2=(30, 20, 90),  a1=(255, 61, 127), hl=(255, 230, 0),  a2=(120, 255, 170), soft=(255, 196, 220)),
    "electric": dict(bg=(28, 12, 74),  bg2=(10, 40, 110), a1=(0, 214, 255),  hl=(255, 230, 0),  a2=(255, 110, 80),  soft=(170, 240, 255)),
    "sunset":   dict(bg=(16, 22, 64),  bg2=(70, 18, 80),  a1=(255, 120, 20), hl=(190, 255, 40), a2=(255, 70, 160),  soft=(255, 210, 160)),
    "mint":     dict(bg=(8, 36, 56),   bg2=(16, 24, 80),  a1=(0, 230, 160),  hl=(255, 225, 0),  a2=(255, 90, 120),  soft=(180, 255, 225)),
}

def palette(c):
    name = c.get("story", {}).get("palette")
    if name not in PALETTES:
        d = datetime.date.fromisoformat(c["date"])
        name = list(PALETTES)[d.toordinal() % len(PALETTES)]
    return name, PALETTES[name]

_fc = {}
def F(name, size):
    key = (name, size)
    if key not in _fc:
        p = {"bold": "Poppins-Bold.ttf", "med": "Poppins-Medium.ttf", "semi": "Inter-SemiBold.otf", "imed": "Inter-Medium.otf"}[name]
        kw = {"layout_engine": ImageFont.Layout.RAQM} if p.startswith("Poppins") else {}
        _fc[key] = ImageFont.truetype(os.path.join(FONTS, p), size, **kw)
    return _fc[key]

_emo = {}
def emoji(ch, size):
    key = (ch, size)
    if key not in _emo:
        try:
            f = ImageFont.truetype(EMOJI_FONT, 109, layout_engine=ImageFont.Layout.RAQM)
            im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
            ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
            bb = im.getbbox()
            im = im.crop(bb) if bb else im
            _emo[key] = im.resize((size, int(size * im.height / max(1, im.width))), Image.LANCZOS)
        except Exception:
            _emo[key] = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    return _emo[key]

def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3

def back(t):
    """ease-out-back (overshoot) for pop-ins"""
    t = max(0.0, min(1.0, t))
    c1 = 1.9
    return 1 + (c1 + 1) * (t - 1) ** 3 + c1 * (t - 1) ** 2

# ------------------------------------------------------------------ characters
SKIN = {"light": (241, 198, 164), "medium": (218, 163, 120), "tan": (192, 132, 92), "deep": (146, 96, 64)}
HAIR = {"black": (28, 22, 26), "brown": (84, 52, 32), "grey": (176, 176, 182), "auburn": (120, 46, 30)}

def _shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)

def _hex(v, default):
    if isinstance(v, (list, tuple)):
        return tuple(v)
    if isinstance(v, str) and v.startswith("#") and len(v) == 7:
        return tuple(int(v[i:i + 2], 16) for i in (1, 3, 5))
    return default

_av = {}
def avatar(look, expr="neutral", mouth=0, blink=False, height=600):
    """Original flat-style character. look: {skin, hair, hair_color, outfit, glasses, beard, earrings, bindi}.
    expr: neutral | happy | shocked | worried | thinking | talk.  mouth: 0 closed / 1 open (talking)."""
    key = (repr(sorted(look.items())), expr, mouth, blink, height)
    if key in _av:
        return _av[key]
    S = 3
    W, H = 400 * S, 560 * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    def P(*xy):
        return [v * S for v in xy]
    skin = SKIN.get(look.get("skin"), _hex(look.get("skin"), SKIN["medium"]))
    sk2 = _shade(skin, 0.86)
    hc = HAIR.get(look.get("hair_color"), _hex(look.get("hair_color"), HAIR["black"]))
    out = _hex(look.get("outfit"), (255, 61, 127))
    style = look.get("hair", "short")
    dark = (46, 30, 30)

    # back hair
    if style in ("long", "wavy"):
        d.ellipse(P(88, 72, 312, 330), fill=hc)
        d.rounded_rectangle(P(92, 190, 308, 450), radius=60 * S, fill=hc)
    if style == "bun":
        d.ellipse(P(160, 30, 240, 110), fill=hc)
    # body
    d.rounded_rectangle(P(36, 405, 364, 640), radius=100 * S, fill=out)
    d.rounded_rectangle(P(36, 405, 364, 640), radius=100 * S, outline=_shade(out, 0.82), width=4 * S)
    # neck + collar
    d.rectangle(P(170, 300, 230, 418), fill=sk2)
    d.polygon(P(160, 402, 200, 462, 240, 402), fill=sk2)
    collar = look.get("collar", "white")
    if collar == "white":
        d.polygon(P(150, 404, 200, 470, 176, 488, 130, 420), fill=(250, 250, 250))
        d.polygon(P(250, 404, 200, 470, 224, 488, 270, 420), fill=(250, 250, 250))
    # ears
    d.ellipse(P(92, 192, 126, 246), fill=skin)
    d.ellipse(P(274, 192, 308, 246), fill=skin)
    if look.get("earrings"):
        d.ellipse(P(100, 244, 116, 260), fill=GOLD)
        d.ellipse(P(284, 244, 300, 260), fill=GOLD)
    # head
    d.ellipse(P(104, 92, 296, 338), fill=skin)
    # beard
    if look.get("beard"):
        d.chord(P(110, 170, 290, 350), 0, 180, fill=hc)
        d.ellipse(P(160, 262, 240, 312), fill=skin)
    # front hair: cap ellipse minus a face ellipse -> curved hairline
    def cap(outer, inner):
        m = Image.new("L", im.size, 0)
        md = ImageDraw.Draw(m)
        md.ellipse(P(*outer), fill=255)
        md.ellipse(P(*inner), fill=0)
        im.paste(Image.new("RGBA", im.size, hc + (255,)), (0, 0), m)
    if style in ("long", "wavy", "bun"):
        cap((98, 74, 302, 300), (122, 150, 292, 400))
        d.rectangle(P(98, 190, 116, 270), fill=hc)
        d.rectangle(P(284, 190, 302, 270), fill=hc)
    elif style == "short":
        cap((100, 78, 300, 250), (112, 146, 292, 380))
        d.rectangle(P(103, 168, 115, 214), fill=hc)
        d.rectangle(P(285, 168, 297, 214), fill=hc)
    elif style == "curly":
        for cx, cy in [(124, 162), (150, 120), (190, 102), (232, 106), (268, 128), (288, 166)]:
            d.ellipse(P(cx - 32, cy - 32, cx + 32, cy + 32), fill=hc)
    elif style == "bald":
        d.chord(P(104, 92, 296, 338), 165, 195, fill=hc)
        d.chord(P(104, 92, 296, 338), 345, 15, fill=hc)
    d = ImageDraw.Draw(im)
    if look.get("bindi"):
        d.ellipse(P(194, 176, 206, 188), fill=(200, 20, 50))

    ey = 222
    # brows
    bw = 5 * S
    if expr == "shocked":
        d.arc(P(146, 168, 186, 196), 200, 340, fill=hc, width=bw)
        d.arc(P(214, 168, 254, 196), 200, 340, fill=hc, width=bw)
    elif expr == "worried":
        d.line(P(148, 196, 184, 186), fill=hc, width=bw)
        d.line(P(216, 186, 252, 196), fill=hc, width=bw)
    elif expr == "thinking":
        d.line(P(148, 192, 184, 192), fill=hc, width=bw)
        d.arc(P(214, 178, 254, 204), 200, 340, fill=hc, width=bw)
    else:
        d.arc(P(146, 180, 186, 204), 205, 335, fill=hc, width=bw)
        d.arc(P(214, 180, 254, 204), 205, 335, fill=hc, width=bw)
    # eyes
    for ex in (166, 234):
        if blink:
            d.arc(P(ex - 13, ey - 6, ex + 13, ey + 10), 200, 340, fill=dark, width=4 * S)
        elif expr == "happy":
            d.arc(P(ex - 14, ey - 4, ex + 14, ey + 18), 200, 340, fill=dark, width=5 * S)
        elif expr == "shocked":
            d.ellipse(P(ex - 17, ey - 19, ex + 17, ey + 19), fill=WHITE)
            d.ellipse(P(ex - 9, ey - 10, ex + 9, ey + 10), fill=dark)
        else:
            d.ellipse(P(ex - 11, ey - 14, ex + 11, ey + 14), fill=dark)
            d.ellipse(P(ex - 2, ey - 9, ex + 5, ey - 2), fill=WHITE)
    if look.get("glasses"):
        gc = (30, 30, 40)
        d.ellipse(P(136, 194, 196, 250), outline=gc, width=5 * S)
        d.ellipse(P(204, 194, 264, 250), outline=gc, width=5 * S)
        d.line(P(196, 218, 204, 218), fill=gc, width=5 * S)
    # nose
    d.arc(P(188, 236, 210, 266), 300, 80, fill=_shade(skin, 0.72), width=4 * S)
    # cheeks
    if expr in ("happy", "talk") and not look.get("beard"):
        blush = Image.new("RGBA", im.size, (0, 0, 0, 0))
        bd = ImageDraw.Draw(blush)
        bd.ellipse(P(124, 250, 164, 276), fill=(255, 110, 120, 90))
        bd.ellipse(P(236, 250, 276, 276), fill=(255, 110, 120, 90))
        im.alpha_composite(blush)
        d = ImageDraw.Draw(im)
    # mouth
    mc = (120, 30, 40)
    if mouth:
        d.ellipse(P(180, 274, 220, 304), fill=mc)
        d.ellipse(P(188, 290, 212, 304), fill=(230, 100, 110))
    elif expr == "shocked":
        d.ellipse(P(186, 274, 214, 310), fill=mc)
    elif expr == "happy":
        d.chord(P(170, 262, 230, 310), 0, 180, fill=mc)
        d.chord(P(176, 262, 224, 280), 0, 180, fill=WHITE)
    elif expr == "worried":
        d.arc(P(178, 286, 222, 316), 200, 340, fill=mc, width=5 * S)
    elif expr == "thinking":
        d.line(P(186, 292, 214, 288), fill=mc, width=5 * S)
    else:
        d.arc(P(176, 264, 224, 300), 25, 155, fill=mc, width=5 * S)
    w = int(height * 400 / 560)
    res = im.resize((w, height), Image.LANCZOS)
    if len(_av) > 400:
        _av.clear()
    _av[key] = res
    return res

# ------------------------------------------------------------------ text helpers
def wrap_words(draw, words, font, maxw, space=None):
    space = space if space is not None else draw.textlength(" ", font=font)
    lines, cur, w = [], [], 0
    for wd in words:
        ww = draw.textlength(wd, font=font)
        if cur and w + space + ww > maxw:
            lines.append(cur); cur, w = [wd], ww
        else:
            w = w + (space if cur else 0) + ww; cur.append(wd)
    if cur:
        lines.append(cur)
    return lines

def mark_words(text, highlight):
    """Return [(word, is_highlight)]."""
    words = text.split()
    flags = [False] * len(words)
    if highlight:
        hw = [w.strip(".,!?:;'\"").lower() for w in highlight.split()]
        n = len(hw)
        low = [w.strip(".,!?:;'\"").lower() for w in words]
        for i in range(len(words) - n + 1):
            if low[i:i + n] == hw:
                for j in range(i, i + n):
                    flags[j] = True
                break
    return list(zip(words, flags))

def fit_rich(draw, text, highlight, fname, size, maxw, maxlines, minsize=34):
    while True:
        f = F(fname, size)
        mw = mark_words(text, highlight)
        lines = wrap_words(draw, [w for w, _ in mw], f, maxw)
        if len(lines) <= maxlines or size <= minsize:
            # rebuild with flags
            out, k = [], 0
            for ln in lines:
                out.append(mw[k:k + len(ln)]); k += len(ln)
            return f, out
        size -= 4

def draw_rich(img, x, y, lines, font, color, hl_bg, hl_fg, t=1.0, stagger=0.0, lh=None, center_w=None, sweep=None):
    """Draw word-wrapped lines; highlighted words get a marker box.
    t: seconds since start (words rise in with `stagger` s between them; stagger 0 = all at once).
    sweep: 0..1 progress of the marker sweep (None = full)."""
    d = ImageDraw.Draw(img)
    lh = lh or int(font.size * 1.28)
    sp = d.textlength(" ", font=font)
    idx = 0
    pad = int(font.size * 0.16)
    for li, ln in enumerate(lines):
        widths = [d.textlength(w, font=font) for w, _ in ln]
        total = sum(widths) + sp * (len(ln) - 1)
        cx = x + ((center_w - total) / 2 if center_w else 0)
        yy = y + li * lh
        # highlight boxes first (merged runs)
        runs, i = [], 0
        while i < len(ln):
            if ln[i][1]:
                j = i
                while j + 1 < len(ln) and ln[j + 1][1]:
                    j += 1
                runs.append((i, j)); i = j + 1
            else:
                i += 1
        xs = []
        xx = cx
        for w in widths:
            xs.append(xx); xx += w + sp
        for (i, j) in runs:
            k = ease((t - (idx + i) * stagger) / 0.3) if stagger else 1
            if k <= 0:
                continue
            x0, x1 = xs[i] - pad, xs[j] + widths[j] + pad
            if sweep is not None:
                x1 = x0 + (x1 - x0) * max(0, min(1, sweep))
            if x1 > x0 + 2:
                d.rounded_rectangle([x0, yy + font.size * 0.08, x1, yy + font.size * 1.22], radius=int(font.size * 0.18),
                                    fill=hl_bg + (int(255 * k),))
        for wi, (w, hl) in enumerate(ln):
            k = ease((t - (idx + wi) * stagger) / 0.28) if stagger else 1
            if k <= 0:
                continue
            off = int((1 - k) * font.size * 0.5)
            col = hl_fg if hl and (sweep is None or sweep > 0.5) else color
            d.text((xs[wi], yy + off), w, font=font, fill=col + (int(255 * k),))
        idx += len(ln)
    return y + len(lines) * lh

def text_w(text, font):
    return ImageDraw.Draw(Image.new("RGB", (4, 4))).textlength(text, font=font)

def sticker(text, font, bg, fg, angle=-5, padx=34, pady=16, outline=None):
    w = int(text_w(text, font))
    h = int(font.size * 1.25)
    im = Image.new("RGBA", (w + 2 * padx + 20, h + 2 * pady + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, 10 + w + 2 * padx, 10 + h + 2 * pady], radius=18, fill=bg,
                        outline=outline, width=5 if outline else 0)
    d.text((10 + padx, 10 + pady - font.size * 0.05), text, font=font, fill=fg)
    return im.rotate(angle, resample=Image.BICUBIC, expand=True)

def paste_scaled(img, piece, cx, cy, scale=1.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    p = piece
    if abs(scale - 1) > 0.01:
        p = piece.resize((max(1, int(piece.width * scale)), max(1, int(piece.height * scale))), Image.BILINEAR)
    if alpha < 0.99:
        p = p.copy()
        p.putalpha(p.split()[3].point(lambda v: int(v * alpha)))
    img.alpha_composite(p, (int(cx - p.width / 2), int(cy - p.height / 2)))

def bubble(text, font, maxw, fill, fg, tail="left", name=None, name_font=None, name_col=None):
    probe = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    lines = wrap_words(probe, text.split(), font, maxw - 68)
    lh = int(font.size * 1.32)
    tw = max(probe.textlength(" ".join(l), font=font) for l in lines)
    bw, bh = int(tw + 68), int(len(lines) * lh + 44)
    top = 0
    if name:
        top = int(name_font.size * 1.5)
    im = Image.new("RGBA", (bw + 20, bh + top + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # shadow
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([10, top + 14, bw + 10, top + bh + 14], radius=38, fill=(0, 0, 0, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    im.alpha_composite(sh)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, top, bw, top + bh], radius=38, fill=fill)
    if tail == "left":
        d.polygon([(46, top + bh - 4), (30, top + bh + 34), (96, top + bh - 4)], fill=fill)
    else:
        d.polygon([(bw - 46, top + bh - 4), (bw - 30, top + bh + 34), (bw - 96, top + bh - 4)], fill=fill)
    for i, l in enumerate(lines):
        d.text((34, top + 20 + i * lh), " ".join(l), font=font, fill=fg)
    if name:
        nx = 8 if tail == "left" else bw - probe.textlength(name, font=name_font) - 8
        d.text((nx, 0), name, font=name_font, fill=name_col)
    return im

_shield = None
def shield():
    global _shield
    if _shield is None:
        _shield = Image.open(LOGO).convert("RGBA").crop((260, 200, 790, 730))
    return _shield

def brand_pill(img, x, y, h):
    d = ImageDraw.Draw(img)
    f = F("bold", int(h * 0.42))
    wA = d.textlength("Advocate", font=f); wS = d.textlength("Setu", font=f)
    w = int(h * 0.95 + wA + wS + h * 0.45)
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=WHITE)
    s = shield().resize((int(h * 0.72), int(h * 0.72)), Image.LANCZOS)
    img.alpha_composite(s, (x + int(h * 0.18), y + int(h * 0.14)))
    tx, ty = x + int(h * 0.95), y + int(h * 0.22)
    d.text((tx, ty), "Advocate", font=f, fill=NAVY)
    d.text((tx + wA, ty), "Setu", font=f, fill=GOLD)
    return w

def background(w, h, pal, t=0.0, pattern=True):
    import numpy as np
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    k = np.clip(xx / w * 0.35 + yy / h * 0.65, 0, 1)[..., None]
    a = np.array(pal["bg"], np.float32); b = np.array(pal["bg2"], np.float32)
    base = Image.fromarray((a * (1 - k) + b * k).astype(np.uint8), "RGB").convert("RGBA")
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    r = int(w * 0.5)
    cx, cy = int(w * (0.9 + 0.04 * math.sin(t))), int(h * (0.1 + 0.02 * math.cos(t)))
    g.ellipse([cx - r, cy - r, cx + r, cy + r], fill=pal["a1"] + (70,))
    cx2, cy2 = int(w * 0.05), int(h * 0.92)
    g.ellipse([cx2 - r, cy2 - r, cx2 + r, cy2 + r], fill=pal["a2"] + (45,))
    glow = glow.filter(ImageFilter.GaussianBlur(w // 7))
    base.alpha_composite(glow)
    if pattern:
        dots = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        dd = ImageDraw.Draw(dots)
        for yy_ in range(40, h, 64):
            for xx_ in range(40 + (yy_ // 64 % 2) * 32, w, 64):
                dd.ellipse([xx_ - 3, yy_ - 3, xx_ + 3, yy_ + 3], fill=(255, 255, 255, 16))
        base.alpha_composite(dots)
    return base
