#!/usr/bin/env python3
"""Bold promotional banners for AdvocateSetu (feed 1080x1350 and story 1080x1920).

Usage: python3 tools/make_promo.py <outdir>
Writes clients_feed.jpg, clients_story.jpg, advocates_feed.jpg, advocates_story.jpg.
"""
import math, os, sys
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_post import F, gradient, brand_pill, shield, NAVY, NAVY2, GOLD, GOLD_SOFT, WHITE, MUTED

W = 1080
M = 72

# ------------------------------------------------------------ icons
def icon_bg(d, x, y, s):
    d.ellipse([x, y, x + s, y + s], fill=WHITE)

def ic_shield(d, x, y, s):
    icon_bg(d, x, y, s)
    cx = x + s / 2
    pts = [(cx, y + s * .2), (x + s * .74, y + s * .3), (x + s * .72, y + s * .55), (cx, y + s * .82),
           (x + s * .28, y + s * .55), (x + s * .26, y + s * .3)]
    d.polygon(pts, fill=NAVY)
    d.line([(x + s * .38, y + s * .5), (x + s * .47, y + s * .6), (x + s * .63, y + s * .4)], fill=GOLD, width=max(4, s // 14), joint="curve")

def ic_chat(d, x, y, s):
    icon_bg(d, x, y, s)
    d.rounded_rectangle([x + s * .22, y + s * .26, x + s * .78, y + s * .66], radius=s * .1, fill=NAVY)
    d.polygon([(x + s * .32, y + s * .62), (x + s * .3, y + s * .78), (x + s * .46, y + s * .64)], fill=NAVY)
    for i in range(3):
        cx = x + s * (.36 + i * .14); cy = y + s * .46; r = s * .045
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GOLD)

def ic_lock(d, x, y, s):
    icon_bg(d, x, y, s)
    d.arc([x + s * .34, y + s * .2, x + s * .66, y + s * .54], 180, 360, fill=NAVY, width=max(5, s // 12))
    d.line([(x + s * .34 + 2, y + s * .37), (x + s * .34 + 2, y + s * .46)], fill=NAVY, width=max(5, s // 12))
    d.line([(x + s * .66 - 3, y + s * .37), (x + s * .66 - 3, y + s * .46)], fill=NAVY, width=max(5, s // 12))
    d.rounded_rectangle([x + s * .27, y + s * .44, x + s * .73, y + s * .78], radius=s * .06, fill=NAVY)
    d.ellipse([x + s * .46, y + s * .53, x + s * .54, y + s * .61], fill=GOLD)
    d.rectangle([x + s * .485, y + s * .58, x + s * .515, y + s * .68], fill=GOLD)

def ic_clock(d, x, y, s):
    icon_bg(d, x, y, s)
    d.ellipse([x + s * .22, y + s * .22, x + s * .78, y + s * .78], outline=NAVY, width=max(5, s // 12))
    d.pieslice([x + s * .3, y + s * .3, x + s * .7, y + s * .7], -90, 30, fill=GOLD)
    d.line([(x + s / 2, y + s / 2), (x + s / 2, y + s * .32)], fill=NAVY, width=max(4, s // 16))

def ic_calendar(d, x, y, s):
    icon_bg(d, x, y, s)
    d.rounded_rectangle([x + s * .24, y + s * .28, x + s * .76, y + s * .76], radius=s * .06, fill=NAVY)
    d.rectangle([x + s * .24, y + s * .28, x + s * .76, y + s * .4], fill=GOLD)
    for r in range(2):
        for c in range(3):
            xx = x + s * (.32 + c * .14); yy = y + s * (.48 + r * .13)
            d.rectangle([xx, yy, xx + s * .07, yy + s * .07], fill=WHITE)

def ic_rupee(d, x, y, s):
    icon_bg(d, x, y, s)
    f = F("bold", int(s * .52))
    d.text((x + s / 2, y + s / 2 + 2), "₹", font=f, fill=NAVY, anchor="mm")

def ic_chart(d, x, y, s):
    icon_bg(d, x, y, s)
    for i, h in enumerate([.2, .32, .44]):
        xx = x + s * (.28 + i * .16)
        d.rectangle([xx, y + s * (.74 - h), xx + s * .11, y + s * .74], fill=NAVY if i < 2 else GOLD)

ICONS = dict(shield=ic_shield, chat=ic_chat, lock=ic_lock, clock=ic_clock, calendar=ic_calendar, rupee=ic_rupee, chart=ic_chart)

# ------------------------------------------------------------ pieces
def scales(img, cx, top, size, alpha=255):
    """Gold scales of justice line illustration."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    g = GOLD + (alpha,)
    lw = max(6, size // 40)
    d.line([(cx, top + size * .08), (cx, top + size * .86)], fill=g, width=lw)
    d.ellipse([cx - size * .045, top, cx + size * .045, top + size * .09], fill=g)
    d.line([(cx - size * .42, top + size * .2), (cx + size * .42, top + size * .2)], fill=g, width=lw)
    for side in (-1, 1):
        px = cx + side * size * .42
        d.line([(px, top + size * .2), (px - size * .14, top + size * .52)], fill=g, width=lw // 2)
        d.line([(px, top + size * .2), (px + size * .14, top + size * .52)], fill=g, width=lw // 2)
        d.chord([px - size * .17, top + size * .4, px + size * .17, top + size * .64], 0, 180, fill=g)
    d.polygon([(cx - size * .16, top + size * .9), (cx + size * .16, top + size * .9), (cx + size * .08, top + size * .82), (cx - size * .08, top + size * .82)], fill=g)
    d.rounded_rectangle([cx - size * .26, top + size * .9, cx + size * .26, top + size * .97], radius=8, fill=g)
    img.alpha_composite(layer)

def glow_badge(img, cx, cy, r, lines):
    """Round navy badge with gold ring and rays."""
    d = ImageDraw.Draw(img)
    rays = Image.new("RGBA", img.size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(rays)
    for i in range(16):
        a = i * math.pi / 8 + 0.2
        r1, r2 = r * 1.08, r * (1.26 if i % 2 else 1.18)
        rd.line([(cx + r1 * math.cos(a), cy + r1 * math.sin(a)), (cx + r2 * math.cos(a), cy + r2 * math.sin(a))], fill=GOLD + (255,), width=7)
    halo = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([cx - r * 1.15, cy - r * 1.15, cx + r * 1.15, cy + r * 1.15], fill=(255, 200, 80, 90))
    img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(30)))
    img.alpha_composite(rays)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE)
    d.ellipse([cx - r * .9, cy - r * .9, cx + r * .9, cy + r * .9], fill=NAVY)
    d.ellipse([cx - r * .9, cy - r * .9, cx + r * .9, cy + r * .9], outline=GOLD, width=5)
    total = sum(s for _, s, _ in lines) * 1.08
    y = cy - total / 2
    for txt, size, col in lines:
        f = F("bold", size)
        d.text((cx, y + size * .54), txt, font=f, fill=col, anchor="mm")
        y += size * 1.08

def headline(d, x, y, parts, size, maxw):
    """parts: list of (line, colour). Shrinks to fit width."""
    while True:
        f = F("bold", size)
        if all(d.textlength(t, font=f) <= maxw for t, _ in parts):
            break
        size -= 4
    for t, c in parts:
        d.text((x, y), t, font=f, fill=c)
        y += int(size * 1.08)
    return y

def features(img, x, y, items, s, gap, tw):
    d = ImageDraw.Draw(img)
    ft, fs = F("bold", int(s * .36)), F("med", int(s * .29))
    for icon, title, sub in items:
        ICONS[icon](d, x, y, s)
        tx = x + s + 26
        if sub:
            d.text((tx, y + s * .5 - 4), title, font=ft, fill=WHITE, anchor="ls")
            d.text((tx, y + s * .5 + 8), sub, font=fs, fill=MUTED, anchor="lt")
        else:
            d.text((tx, y + s * .5), title, font=ft, fill=WHITE, anchor="lm")
        y += s + gap
    return y

def cta_pill(img, cx, y, text, h=104, w=None):
    d = ImageDraw.Draw(img)
    f = F("bold", int(h * .4))
    tw = d.textlength(text, font=f)
    w = w or int(tw + h * 1.6)
    x = cx - w // 2
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([x, y + 10, x + w, y + h + 10], radius=h // 2, fill=(0, 0, 0, 110))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=GOLD)
    ar = h * .36
    ax = x + w - h * .2 - ar * 2
    d.text((x + (w - ar * 2 - h * .2) / 2 + 6, y + h / 2), text, font=f, fill=NAVY, anchor="mm")
    d.ellipse([ax, y + h / 2 - ar, ax + ar * 2, y + h / 2 + ar], fill=NAVY)
    acx, acy = ax + ar, y + h / 2
    d.line([(acx - ar * .45, acy), (acx + ar * .45, acy)], fill=GOLD, width=6)
    d.line([(acx + ar * .05, acy - ar * .4), (acx + ar * .45, acy), (acx + ar * .05, acy + ar * .4)], fill=GOLD, width=6, joint="curve")
    return y + h

def trust_bar(img, y, h, items):
    d = ImageDraw.Draw(img)
    d.rectangle([0, y, W, img.height], fill=WHITE)
    d.rectangle([0, y, W, y + 8], fill=GOLD)
    n = len(items); cw = W / n
    ft, fs = F("bold", 27), F("med", 22)
    for i, (icon, t, s) in enumerate(items):
        x0 = i * cw
        if i:
            d.line([(x0, y + 34), (x0, y + h - 26)], fill=(210, 216, 230), width=2)
        isz = 58
        ix = x0 + 26
        iy = y + 8 + (h - 8) / 2 - isz / 2
        ICONS[icon](d, ix, iy, isz)
        d.ellipse([ix, iy, ix + isz, iy + isz], outline=NAVY, width=3)
        tx = ix + isz + 14
        d.text((tx, y + 8 + (h - 8) / 2 - 2), t, font=ft, fill=NAVY, anchor="ls")
        d.text((tx, y + 8 + (h - 8) / 2 + 6), s, font=fs, fill=(90, 102, 130), anchor="lt")

def watermark(img, cx, cy, size, alpha=28):
    s = shield().resize((size, size), Image.LANCZOS)
    a = s.split()[3].point(lambda v: v * alpha // 255)
    s.putalpha(a)
    img.alpha_composite(s, (int(cx - size / 2), int(cy - size / 2)))

def phone(img, x, y, w, h, rows):
    d = ImageDraw.Draw(img)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([x + 12, y + 20, x + w + 12, y + h + 20], radius=58, fill=(0, 0, 0, 120))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
    d.rounded_rectangle([x, y, x + w, y + h], radius=58, fill=(18, 22, 34))
    sx, sy, sw, shh = x + 16, y + 16, w - 32, h - 32
    d.rounded_rectangle([sx, sy, sx + sw, sy + shh], radius=44, fill=(246, 247, 251))
    d.rounded_rectangle([x + w / 2 - 60, y + 26, x + w / 2 + 60, y + 52], radius=13, fill=(18, 22, 34))
    f1, f2, f3 = F("bold", 30), F("bold", 23), F("med", 19)
    d.text((sx + 28, sy + 66), "Advocate", font=f1, fill=NAVY)
    d.text((sx + 28 + d.textlength("Advocate", font=f1), sy + 66), "Setu", font=f1, fill=GOLD)
    d.text((sx + 28, sy + 116), "My dashboard", font=f2, fill=NAVY)
    yy = sy + 160
    for title, sub, tag in rows:
        d.rounded_rectangle([sx + 20, yy, sx + sw - 20, yy + 92], radius=16, fill=WHITE, outline=(226, 230, 240), width=2)
        d.text((sx + 40, yy + 18), title, font=f2, fill=NAVY)
        d.text((sx + 40, yy + 54), sub, font=f3, fill=(110, 120, 145))
        tw = d.textlength(tag, font=f3)
        d.rounded_rectangle([sx + sw - 40 - tw - 24, yy + 18, sx + sw - 40, yy + 48], radius=15, fill=(255, 241, 214))
        d.text((sx + sw - 40 - tw - 12, yy + 22), tag, font=f3, fill=(176, 110, 0))
        yy += 108
    d.rounded_rectangle([sx + 20, yy + 6, sx + sw - 20, yy + 66], radius=14, fill=NAVY)
    d.text((sx + sw / 2, yy + 36), "MANAGE SLOTS", font=f2, fill=WHITE, anchor="mm")

DISC = "For general awareness only. Not legal advice."

# ------------------------------------------------------------ designs
def clients(H):
    img = gradient(W, H)
    d = ImageDraw.Draw(img)
    story = H > 1500
    top = 150 if story else 64
    watermark(img, W * .78, H * .58, 760, 22)
    brand_pill(img, M, top, 88)
    y = top + 150 + (40 if story else 0)
    br = 150 if story else 118
    glow_badge(img, W - 60 - br * 1.05, y + 40 + (10 if story else 0), br,
               [(t, int(sz * br / 150), c) for t, sz, c in [("VIDEO", 40, WHITE), ("AUDIO", 40, WHITE), ("CHAT", 40, WHITE), ("consults", 30, GOLD)]])
    y = headline(d, M, y, [("Talk to a", WHITE), ("Verified", WHITE), ("Advocate.", WHITE)], 108 if story else 82, W - 2 * M - 330)
    y = headline(d, M, y + 4, [("Get Clear", GOLD), ("Legal Guidance.", GOLD)], 96 if story else 72, W - 2 * M)
    fh = F("hi", 40 if story else 34)
    d.text((M, y + 10), "सत्यापित वकील से ऑनलाइन बात करें", font=fh, fill=GOLD_SOFT)
    y += 100 if story else 80
    y += 50 if story else 0
    s = 108 if story else 76
    y = features(img, M, y, [
        ("shield", "Bar Council-verified advocates", "Every profile checked"),
        ("chat", "Consult from anywhere", "Video, audio or chat"),
        ("clock", "Book in minutes", "50+ cities, 10 practice areas"),
    ], s, 34 if story else 16, W - 2 * M)
    bar_h = 150 if story else 128
    disc_h = 46
    cta_y = H - bar_h - disc_h - (220 if story else 172)
    if story:
        scales(img, int(W * .8), int(cta_y - 330), 300, 210)
    else:
        scales(img, int(W * .84), int(cta_y - 330), 230, 200)
    cta_pill(img, W // 2, cta_y, "Consult an Advocate Online", h=112 if story else 96)
    d.text((W // 2, cta_y + (112 if story else 96) + 22), "advocatesetu.com", font=F("semi", 34), fill=WHITE, anchor="mt")
    trust_bar(img, H - bar_h - disc_h, bar_h, [("shield", "Verified", "Advocates"), ("lock", "Secure", "& confidential"), ("chat", "Online", "Anywhere in India")])
    d = ImageDraw.Draw(img)
    d.rectangle([0, H - disc_h, W, H], fill=(240, 242, 248))
    d.text((W // 2, H - disc_h / 2), DISC, font=F("med", 21), fill=(90, 102, 130), anchor="mm")
    return img

def advocates(H):
    img = gradient(W, H, shift=1.5)
    d = ImageDraw.Draw(img)
    story = H > 1500
    top = 150 if story else 64
    brand_pill(img, M, top, 88)
    # "For advocates" tab
    ft = F("bold", 30)
    tab = "FOR ADVOCATES"
    tw = d.textlength(tab, font=ft)
    d.rounded_rectangle([W - M - tw - 50, top + 16, W - M, top + 72], radius=28, fill=GOLD)
    d.text((W - M - tw / 2 - 25, top + 44), tab, font=ft, fill=NAVY, anchor="mm")
    y = top + 150 + (40 if story else 0)
    y = headline(d, M, y, [("YOUR PRACTICE.", WHITE), ("YOUR SLOTS.", GOLD), ("FASTER PAYOUTS.", WHITE)], 104 if story else 76, W - 2 * M)
    d.rectangle([M, y + 14, M + 120, y + 20], fill=GOLD)
    y += 44
    if story:
        d.text((M, y), "The new AdvocateSetu is live.", font=F("semi", 36), fill=WHITE)
        y += 48
    d.text((M, y), "नया डैशबोर्ड, आसान स्लॉट, तेज़ भुगतान", font=F("hi", 38 if story else 34), fill=GOLD_SOFT)
    y += 120 if story else 80
    s = 96 if story else 80
    ph_w, ph_h = (400, 640) if story else (350, 440)
    ph_x = W - ph_w - 40
    items = [
        ("chart", "Refreshed dashboard", "Everything in one place"),
        ("calendar", "Simpler slot management", "Set your availability"),
        ("rupee", "Faster payouts", "Get paid sooner"),
        ("chat", "Video, audio & chat", "Consult clients online"),
    ]
    items[1] = ("calendar", "Simpler slots", "Set your availability")
    if not story:
        items[3] = ("chat", "Video, audio & chat", "Consult online")
    features(img, M, y, items, s, 30 if story else 14, ph_x - M - 20)
    phone(img, ph_x, y - (10 if story else 70), ph_w, ph_h, [
        ("Today, 11:00", "Video consultation", "Booked"),
        ("Today, 4:30", "Audio consultation", "Booked"),
    ] + ([("Tomorrow, 10:00", "Chat consultation", "Open")] if story else []))
    bar_h = 150 if story else 128
    disc_h = 46
    cta_y = H - bar_h - disc_h - (220 if story else 172)
    cta_pill(img, W // 2, cta_y, "Log in to Your Dashboard", h=112 if story else 96)
    d = ImageDraw.Draw(img)
    d.text((W // 2, cta_y + (112 if story else 96) + 22), "advocatesetu.com", font=F("semi", 34), fill=WHITE, anchor="mt")
    trust_bar(img, H - bar_h - disc_h, bar_h, [("calendar", "Your schedule", "You set slots"), ("rupee", "Quick payouts", "Faster than before"), ("lock", "Secure", "Online consults")])
    d = ImageDraw.Draw(img)
    d.rectangle([0, H - disc_h, W, H], fill=(240, 242, 248))
    d.text((W // 2, H - disc_h / 2), "AdvocateSetu is a technology platform. Not legal advice.", font=F("med", 21), fill=(90, 102, 130), anchor="mm")
    return img

def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for name, fn in (("clients", clients), ("advocates", advocates)):
        for kind, H in (("feed", 1350), ("story", 1920)):
            fn(H).convert("RGB").save(os.path.join(out, f"{name}_{kind}.jpg"), "JPEG", quality=92, optimize=True)
    print("ok", out)

if __name__ == "__main__":
    main()
