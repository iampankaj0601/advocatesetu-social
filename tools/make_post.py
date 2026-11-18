#!/usr/bin/env python3
"""Render AdvocateSetu daily banner (1080x1350 JPEG) and reel (1080x1920 MP4) from a content JSON.

Usage: python3 tools/make_post.py daily/YYYY-MM-DD/content.json
Writes banner.jpg, reel.mp4 and cover.jpg next to content.json.
"""
import json, math, os, subprocess, sys, shutil, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "tools", "fonts")
LOGO = os.path.join(ROOT, "brand", "logo_1024.png")

NAVY = (11, 27, 61)
NAVY2 = (24, 52, 110)
GOLD = (244, 168, 30)
GOLD_SOFT = (252, 211, 120)
WHITE = (255, 255, 255)
MUTED = (205, 215, 236)

def F(name, size):
    p = {
        "bold": "Poppins-Bold.ttf",
        "semi": "Inter-SemiBold.otf",
        "med": "Inter-Medium.otf",
        "hi": "Poppins-Bold.ttf",
        "hi6": "Poppins-Medium.ttf",
    }[name]
    kw = {}
    if name.startswith("hi"):
        kw = {"layout_engine": ImageFont.Layout.RAQM}
    return ImageFont.truetype(os.path.join(FONTS, p), size, **kw)

_shield = None
def shield():
    global _shield
    if _shield is None:
        _shield = Image.open(LOGO).convert("RGBA").crop((260, 200, 790, 730))
    return _shield

def gradient(w, h, shift=0.0):
    """Diagonal navy gradient with soft gold glow."""
    import numpy as np
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    t = np.clip((xx / w * 0.45 + yy / h * 0.55), 0, 1)[..., None]
    a = np.array(NAVY, np.float32); b = np.array(NAVY2, np.float32)
    arr = (a * (1 - t) + b * t).astype(np.uint8)
    base = Image.fromarray(arr, "RGB")
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)
    cx = int(w * (0.85 + 0.05 * math.sin(shift)))
    cy = int(h * (0.12 + 0.03 * math.cos(shift)))
    r = int(w * 0.55)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(70, 120, 230, 46))
    r2 = int(w * 0.45)
    d.ellipse([-r2 // 2, h - r2, r2, h + r2 // 2], fill=(60, 110, 220, 40))
    glow = glow.filter(ImageFilter.GaussianBlur(w // 8))
    base = base.convert("RGBA")
    base.alpha_composite(glow)
    return base

def wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines

def fit_lines(draw, text, fname, size, maxw, maxlines, minsize=30):
    while size >= minsize:
        f = F(fname, size)
        ls = wrap(draw, text, f, maxw)
        if len(ls) <= maxlines:
            return f, ls
        size -= 4
    f = F(fname, minsize)
    return f, wrap(draw, text, f, maxw)

def brand_pill(img, x, y, h):
    d = ImageDraw.Draw(img)
    f = F("bold", int(h * 0.48))
    wA = d.textlength("Advocate", font=f)
    wS = d.textlength("Setu", font=f)
    w = int(h * 1.05 + wA + wS + h * 0.45)
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=WHITE)
    s = shield().resize((int(h * 0.8), int(h * 0.8)), Image.LANCZOS)
    img.alpha_composite(s, (x + int(h * 0.18), y + int(h * 0.1)))
    tx = x + int(h * 1.05)
    ty = y + int(h * 0.5) - int(f.size * 0.62)
    d.text((tx, ty), "Advocate", font=f, fill=NAVY)
    d.text((tx + wA, ty), "Setu", font=f, fill=GOLD)
    return w

def check_icon(d, x, y, s):
    d.ellipse([x, y, x + s, y + s], fill=GOLD)
    d.line([(x + s * 0.27, y + s * 0.52), (x + s * 0.44, y + s * 0.68), (x + s * 0.74, y + s * 0.34)],
           fill=NAVY, width=max(3, s // 9), joint="curve")

DISCLAIMER = "For general awareness only. Not legal advice."

# ---------------------------------------------------------------- banner
def banner(c, out):
    W, H = 1080, 1350
    b = c["banner"]
    img = gradient(W, H)
    d = ImageDraw.Draw(img)
    M = 80
    brand_pill(img, M, 70, 92)
    y = 230
    fk = F("semi", 30)
    kick = b["kicker"].upper()
    kw = d.textlength(kick, font=fk)
    d.rounded_rectangle([M, y, M + kw + 44, y + 54], radius=27, outline=GOLD, width=3)
    d.text((M + 22, y + 9), kick, font=fk, fill=GOLD)
    y += 90
    fh, lines = fit_lines(d, b["headline"], "bold", 80, W - 2 * M, 3)
    for ln in lines:
        d.text((M, y), ln, font=fh, fill=WHITE)
        y += int(fh.size * 1.18)
    y += 18
    fhi, hl = fit_lines(d, b["hindi"], "hi", 50, W - 2 * M, 2)
    for ln in hl:
        d.text((M, y), ln, font=fhi, fill=GOLD_SOFT)
        y += int(fhi.size * 1.35)
    y += 24
    fp = F("semi", 36)
    for p in b["points"][:3]:
        pl = wrap(d, p, fp, W - 2 * M - 120)[:2]
        ch = 40 + len(pl) * 46
        card = Image.new("RGBA", (W - 2 * M, ch), (0, 0, 0, 0))
        ImageDraw.Draw(card).rounded_rectangle([0, 0, W - 2 * M - 1, ch - 1], radius=22, fill=(255, 255, 255, 22),
                                                outline=(255, 255, 255, 50), width=2)
        img.alpha_composite(card, (M, y))
        check_icon(d, M + 26, y + ch // 2 - 24, 48)
        ty = y + 20
        for ln in pl:
            d.text((M + 98, ty), ln, font=fp, fill=WHITE)
            ty += 46
        y += ch + 18
    # CTA bar
    cy = H - 210
    fc = F("bold", 38)
    cta = b["cta"]
    cw = d.textlength(cta, font=fc)
    d.rounded_rectangle([M, cy, M + cw + 70, cy + 88], radius=44, fill=GOLD)
    d.text((M + 35, cy + 18), cta, font=fc, fill=NAVY)
    fu = F("semi", 34)
    d.text((M, cy + 112), "advocatesetu.com", font=fu, fill=WHITE)
    fd = F("med", 22)
    dw = d.textlength(DISCLAIMER, font=fd)
    d.text((W - M - dw, cy + 120), DISCLAIMER, font=fd, fill=MUTED)
    img.convert("RGB").save(out, "JPEG", quality=92, optimize=True)

# ---------------------------------------------------------------- reel
FPS = 30
RW, RH = 1080, 1920

def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3

class Layer:
    """Text block that fades and rises in at `start` seconds."""
    def __init__(self, lines, font, color, x, y, lh, start, center=False):
        self.lines, self.font, self.color = lines, font, color
        self.x, self.y, self.lh, self.start, self.center = x, y, lh, start, center

    def draw(self, img, t):
        k = ease((t - self.start) / 0.55)
        if k <= 0:
            return
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        off = int((1 - k) * 50)
        for i, ln in enumerate(self.lines):
            x = self.x
            if self.center:
                x = (RW - d.textlength(ln, font=self.font)) / 2
            d.text((x, self.y + i * self.lh + off), ln, font=self.font, fill=self.color + (int(255 * k),))
        img.alpha_composite(layer)

def scene_frames(c, idx, n_scenes, dur, build):
    bgs = {}
    total = int(dur * FPS)
    for f in range(total):
        t = f / FPS
        key = f // 6  # update background drift every 6 frames
        if key not in bgs:
            bgs.clear()
            bgs[key] = gradient(RW, RH, shift=(idx * dur + t) * 0.6)
        img = bgs[key].copy()
        d = ImageDraw.Draw(img)
        brand_pill(img, 70, 120, 96)
        # progress bar
        prog = (idx + t / dur) / n_scenes
        d.rounded_rectangle([70, 70, RW - 70, 78], radius=4, fill=(255, 255, 255, 60))
        d.rounded_rectangle([70, 70, 70 + int((RW - 140) * prog), 78], radius=4, fill=GOLD)
        build(img, d, t)
        fd = F("med", 26)
        dw = d.textlength(DISCLAIMER, font=fd)
        d.text(((RW - dw) / 2, RH - 110), DISCLAIMER, font=fd, fill=MUTED)
        # fade from black-navy at very start and to it at very end of reel
        a = 0
        if idx == 0 and t < 0.25:
            a = 1 - t / 0.25
        if idx == n_scenes - 1 and t > dur - 0.4:
            a = (t - (dur - 0.4)) / 0.4
        if a > 0:
            ov = Image.new("RGBA", img.size, NAVY + (int(255 * a),))
            img.alpha_composite(ov)
        yield img.convert("RGB")

def encode(frames, out):
    tmp = out[:-4] + ".part.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{RW}x{RH}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                          "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS), tmp], stdin=subprocess.PIPE)
    for fr in frames:
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise SystemExit("ffmpeg failed for " + out)
    os.replace(tmp, out)

def reel(c, outdir):
    r = c["reel"]
    M = 90
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    scenes = []

    # hook
    def hook(img, d, t, _c={}):
        if not _c:
            fh, hl = fit_lines(probe, r["hook"], "bold", 96, RW - 2 * M, 4)
            fhi, hil = fit_lines(probe, r["hook_hi"], "hi", 62, RW - 2 * M, 2)
            y0 = 900 - len(hl) * fh.size * 0.6
            _c["L"] = [Layer(hl, fh, WHITE, M, int(y0), int(fh.size * 1.16), 0.15),
                       Layer(hil, fhi, GOLD_SOFT, M, int(y0 + len(hl) * fh.size * 1.16 + 30), int(fhi.size * 1.35), 0.7)]
            _c["k"] = F("semi", 36)
        k = ease(t / 0.5)
        kick = r.get("kicker", "KNOW YOUR RIGHTS").upper()
        kw = d.textlength(kick, font=_c["k"])
        y = int(_c["L"][0].y) - 110
        d.rounded_rectangle([M, y, M + kw + 50, y + 64], radius=32, outline=GOLD + (int(255 * k),), width=3)
        d.text((M + 25, y + 11), kick, font=_c["k"], fill=GOLD + (int(255 * k),))
        for L in _c["L"]:
            L.draw(img, t)
    scenes.append((4.0, hook))

    for i, s in enumerate(r["slides"][:3]):
        def slide(img, d, t, s=s, i=i, _c={}):
            if not _c:
                ft, tl = fit_lines(probe, s["title"], "bold", 76, RW - 2 * M, 3)
                fb, bl = fit_lines(probe, s["body"], "semi", 48, RW - 2 * M - 40, 6)
                y0 = 760
                _c["L"] = [Layer(tl, ft, WHITE, M, y0, int(ft.size * 1.18), 0.25),
                           Layer(bl, fb, MUTED, M + 40, y0 + len(tl) * int(ft.size * 1.18) + 60, int(fb.size * 1.45), 0.75)]
                _c["n"] = F("bold", 190)
                _c["bar"] = (y0 + len(tl) * int(ft.size * 1.18) + 60, len(bl) * int(fb.size * 1.45))
                hi = s.get("hi")
                if hi:
                    fhi, hil = fit_lines(probe, hi, "hi6", 50, RW - 2 * M, 2)
                    yb = _c["bar"][0] + _c["bar"][1] + 60
                    _c["L"].append(Layer(hil, fhi, GOLD_SOFT, M, yb, int(fhi.size * 1.35), 1.2))
            k = ease(t / 0.45)
            d.text((M - 6, 530), f"0{i + 1}", font=_c["n"], fill=GOLD + (int(200 * k),))
            by, bh = _c["bar"]
            kk = ease((t - 0.7) / 0.5)
            if kk > 0:
                d.rounded_rectangle([M, by + 6, M + 8, by + 6 + int(bh * kk)], radius=4, fill=GOLD)
            for L in _c["L"]:
                L.draw(img, t)
        scenes.append((4.2, slide))

    def cta(img, d, t, _c={}):
        if not _c:
            fc, cl = fit_lines(probe, r["cta"], "bold", 84, RW - 2 * M, 3)
            fhi, hil = fit_lines(probe, r["cta_hi"], "hi", 56, RW - 2 * M, 2)
            _c["L"] = [Layer(cl, fc, WHITE, M, 980, int(fc.size * 1.18), 0.5, center=True),
                       Layer(hil, fhi, GOLD_SOFT, M, 980 + len(cl) * int(fc.size * 1.18) + 30, int(fhi.size * 1.35), 0.9, center=True)]
            _c["yb"] = 980 + len(cl) * int(fc.size * 1.18) + 30 + len(hil) * int(fhi.size * 1.35) + 70
            _c["f"] = F("bold", 46)
        k = ease(t / 0.6)
        sz = int(300 + 40 * k)
        s = shield().resize((sz, sz), Image.LANCZOS)
        a = s.split()[3].point(lambda v: int(v * k))
        s.putalpha(a)
        circle = Image.new("RGBA", (sz + 120, sz + 120), (0, 0, 0, 0))
        ImageDraw.Draw(circle).ellipse([0, 0, sz + 119, sz + 119], fill=(255, 255, 255, int(255 * k)))
        img.alpha_composite(circle, ((RW - sz - 120) // 2, 560 - 60 - (sz - 300) // 2))
        img.alpha_composite(s, ((RW - sz) // 2, 560 - (sz - 300) // 2))
        for L in _c["L"]:
            L.draw(img, t)
        kb = ease((t - 1.3) / 0.5)
        if kb > 0:
            txt = "advocatesetu.com"
            tw = d.textlength(txt, font=_c["f"])
            bw = tw + 100
            x = (RW - bw) / 2
            y = _c["yb"] + int((1 - kb) * 40)
            d.rounded_rectangle([x, y, x + bw, y + 104], radius=52, fill=GOLD + (int(255 * kb),))
            d.text((x + 50, y + 22), txt, font=_c["f"], fill=NAVY + (int(255 * kb),))
    scenes.append((4.6, cta))

    work = tempfile.mkdtemp(prefix="reel_")
    parts = []
    for i, (dur, fn) in enumerate(scenes):
        out = os.path.join(work, f"s{i}.mp4")
        encode(scene_frames(c, i, len(scenes), dur, fn), out)
        parts.append(out)
    lst = os.path.join(work, "list.txt")
    with open(lst, "w") as fh:
        fh.writelines(f"file '{p}'\n" for p in parts)
    silent = os.path.join(work, "v.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    final = os.path.join(outdir, "reel.mp4")
    tmp = final[:-4] + ".part.mp4"
    audio = os.path.join(ROOT, "brand", "reel_bed.m4a")
    if os.path.exists(audio):
        ain = ["-stream_loop", "-1", "-i", audio]
    else:
        ain = ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, *ain, "-map", "0:v", "-map", "1:a",
                    "-c:v", "libx264", "-profile:v", "high", "-level", "4.1", "-preset", "veryfast", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", str(FPS * 2), "-keyint_min", str(FPS * 2), "-sc_threshold", "0",
                    "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "128k", "-shortest", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, final)
    # cover = frame at 2.5s of hook
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "2.5", "-i", final, "-frames:v", "1", "-q:v", "3",
                    os.path.join(outdir, "cover.jpg")], check=True)
    shutil.rmtree(work, ignore_errors=True)

def main():
    path = sys.argv[1]
    c = json.load(open(path, encoding="utf-8"))
    outdir = os.path.dirname(os.path.abspath(path))
    only = sys.argv[2] if len(sys.argv) > 2 else "all"
    if only in ("all", "banner"):
        banner(c, os.path.join(outdir, "banner.jpg"))
    if only in ("all", "reel"):
        reel(c, outdir)
    print("ok", outdir)

if __name__ == "__main__":
    main()
