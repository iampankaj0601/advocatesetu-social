#!/usr/bin/env python3
"""AdvocateSetu story-format renderer (bold colours, illustrated characters, chat story, original music).

Usage: python3 tools/make_story.py daily/YYYY-MM-DD/content.json [all|reel|carousel|banner]
Reads content["story"] (+ content["banner"] for the banner) and writes next to content.json:
  reel.mp4 (1080x1920, H.264 High + AAC 48 kHz, ~22-26 s), cover.jpg,
  carousel_1.jpg ... carousel_N.jpg (1080x1350), banner.jpg (1080x1350)

story = {
  "palette": "punch|electric|sunset|mint" (optional, else rotates by date),
  "characters": {"A": {"name","skin","hair","hair_color","outfit","glasses","beard","earrings","bindi"}, "B": {...}},
  "kicker": "STORY TIME", "hook": "...", "hook_highlight": "...", "hook_hi": "...", "hook_emoji": "😳",
  "dialogue": [{"who": "B", "text": "...", "react": "worried", "emoji": "😟"}, ...]   (3-4 lines, <=16 words),
  "reveal": "Here's what the law says",
  "facts": [{"text": "...", "highlight": "...", "hi": "..."}] x3,
  "ending": {"who": "A", "text": "...", "emoji": "🙌"},
  "cta": "...", "cta_highlight": "...", "cta_hi": "..."
}
A is the main character (never an advocate). Stories are illustrative.
"""
import json, os, sys, math, random, subprocess, shutil, tempfile, zlib
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from story_art import (F, emoji, ease, back, avatar, wrap_words, fit_rich, draw_rich, text_w, sticker,
                       paste_scaled, bubble, brand_pill, background, palette, NAVY, GOLD, WHITE)
import story_music

FPS = 30
RW, RH = 1080, 1920
DISC = "Illustrative story · For general awareness only. Not legal advice."
DISC_B = "For general awareness only. Not legal advice."
probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))

def clamp(v, a, b):
    return max(a, min(b, v))

# ============================================================== reel
class Reel:
    def __init__(self, c):
        self.c = c
        self.s = c["story"]
        self.pname, self.p = palette(c)
        ch = self.s["characters"]
        self.A, self.B = ch["A"], ch.get("B", ch["A"])
        self.events = []
        self.build_timeline()
        self.bgs = {}

    def look(self, who):
        return {k: v for k, v in (self.A if who == "A" else self.B).items() if k != "name"}

    def build_timeline(self):
        s = self.s
        t = 0.0
        self.scenes = []
        self.scenes.append(("hook", t, t + 3.4)); t += 3.4
        self.lines = []
        st = t
        for ln in s["dialogue"]:
            d = clamp(1.3 + 0.085 * len(ln["text"].split()), 2.0, 3.0)
            self.lines.append((t, d, ln)); t += d
        t += 0.3
        self.scenes.append(("chat", st, t))
        st = t
        self.fact_t = []
        t += 0.9
        for f in s["facts"]:
            self.fact_t.append(t); t += 2.6
        t += 0.3
        self.scenes.append(("facts", st, t))
        st = t
        self.end_bubble_t = t + 0.25
        self.cta_t = t + 2.4
        t += 2.4 + 3.4
        self.scenes.append(("end", st, t))
        self.dur = t
        # sfx
        for i, (nm_, a, b) in enumerate(self.scenes):
            if i > 0:
                self.events.append((max(0, a - 0.22), "whoosh"))
        self.events.append((0.3, "pop"))
        for (t0, d, ln) in self.lines:
            self.events.append((t0, "pop"))
        for ft in self.fact_t:
            self.events.append((ft, "ding"))
        self.events.append((self.end_bubble_t, "pop"))
        self.events.append((self.cta_t + 0.5, "ding"))

    def bg(self, name, t):
        key = (name, int(t * 5))
        if key not in self.bgs:
            if len(self.bgs) > 6:
                self.bgs.clear()
            self.bgs[key] = background(RW, RH, self.p, t=t * 0.5, pattern=(name != "hook"))
        return self.bgs[key].copy()

    # ---------------------------------------------------------- chrome
    def chrome(self, img, t):
        d = ImageDraw.Draw(img)
        brand_pill(img, 60, 112, 84)
        prog = t / self.dur
        rr(img, [60, 60, RW - 60, 70], 5, (255, 255, 255, 70))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([60, 60, 60 + int((RW - 120) * prog), 70], radius=5, fill=self.p["hl"])
        f = F("imed", 25)
        w = d.textlength(DISC, font=f)
        rr(img, [(RW - w) / 2 - 18, RH - 96, (RW + w) / 2 + 18, RH - 52], 22, (0, 0, 0, 110))
        d = ImageDraw.Draw(img)
        d.text(((RW - w) / 2, RH - 90), DISC, font=f, fill=(235, 238, 248))

    def wipe(self, img, t):
        for i, (name, a, b) in enumerate(self.scenes):
            if i == 0:
                continue
            k = (t - (a - 0.22)) / 0.44
            if 0 <= k <= 1:
                d = ImageDraw.Draw(img)
                x = -1700 + k * (RW + 2400)
                d.polygon([(x, 0), (x + 900, 0), (x + 900 - 500, RH), (x - 500, RH)], fill=self.p["a1"] + (255,))
                d.polygon([(x + 900, 0), (x + 1040, 0), (x + 540, RH), (x + 400, RH)], fill=self.p["hl"] + (255,))

    # ---------------------------------------------------------- scenes
    def hook(self, img, t):
        s, p = self.s, self.p
        d = ImageDraw.Draw(img)
        # diagonal accent band
        band = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(band).polygon([(0, 1180), (RW, 980), (RW, 1500), (0, 1700)], fill=p["a1"] + (235,))
        img.alpha_composite(band)
        k = back(t / 0.45)
        st = sticker(s.get("kicker", "STORY TIME").upper(), F("bold", 44), p["hl"], NAVY, angle=-5)
        paste_scaled(img, st, 90 + st.width / 2, 300, scale=k)
        fh, lines = fit_rich(probe, s["hook"], s.get("hook_highlight"), "bold", 88, RW - 170, 4, 56)
        y = draw_rich(img, 85, 400, lines, fh, WHITE, p["hl"], NAVY, t=t - 0.3, stagger=0.085)
        nwords = sum(len(l) for l in lines)
        if s.get("hook_hi"):
            fhi, hil = fit_rich(probe, s["hook_hi"], None, "bold", 54, RW - 170, 2, 40)
            kk = ease((t - 0.45 - nwords * 0.085) / 0.4)
            if kk > 0:
                layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
                draw_rich(layer, 85, y + 24 + int((1 - kk) * 30), hil, fhi, p["soft"], p["hl"], NAVY)
                layer.putalpha(layer.split()[3].point(lambda v: int(v * kk)))
                img.alpha_composite(layer)
        # main character pops up from the band
        ka = back((t - 0.15) / 0.55)
        blink = (int(t * 10) % 31) == 0
        av = avatar(self.look("A"), s.get("hook_expr", "shocked"), blink=blink, height=700)
        y0 = 1110 + int((1 - ka) * 500) + int(6 * math.sin(t * 6))
        img.alpha_composite(av, ((RW - av.width) // 2, y0))
        if s.get("hook_emoji"):
            ke = back((t - 1.0) / 0.35)
            paste_scaled(img, emoji(s["hook_emoji"], 150), RW / 2 + 250, 1210 + int(8 * math.sin(t * 5)), scale=ke)

    def chat(self, img, t):
        p = self.p
        d = ImageDraw.Draw(img)
        top, bottom = 300, 1150
        # current line
        cur = None
        for i, (t0, du, ln) in enumerate(self.lines):
            if t >= t0:
                cur = i
        # characters
        exprA, exprB = "neutral", "neutral"
        for i, (t0, du, ln) in enumerate(self.lines[: (cur or 0) + 1]):
            if ln["who"] == "A":
                exprA = ln.get("expr", "talk")
                exprB = ln.get("react", exprB if exprB != "talk" else "neutral")
            else:
                exprB = ln.get("expr", "talk")
                exprA = ln.get("react", "worried")
        for who, cx in (("A", 285), ("B", 795)):
            speaking = cur is not None and self.lines[cur][2]["who"] == who and t - self.lines[cur][0] < self.lines[cur][1] - 0.3
            ex = exprA if who == "A" else exprB
            mouth = 0
            if speaking:
                mouth = 1 if int(t * 8) % 2 == 0 else 0
                if ex == "talk":
                    ex = "neutral"
            elif ex == "talk":
                ex = "neutral"
            blink = (int(t * 10 + (7 if who == "B" else 0)) % 37) == 0
            h = 560 if speaking else 530
            av = avatar(self.look(who), ex, mouth=mouth, blink=blink, height=h)
            bob = int(10 * math.sin(t * 9)) if speaking else int(3 * math.sin(t * 2))
            ka = ease((t - self.scenes[1][1] - (0.0 if who == "A" else 0.12)) / 0.45)
            y = RH - 170 - h + bob + int((1 - ka) * 400)
            img.alpha_composite(av, (int(cx - av.width / 2), y))
            # name tag
            ch = self.A if who == "A" else self.B
            nm = ch.get("name", who)
            fn = F("bold", 36)
            tw = text_w(nm, fn)
            col = p["a1"] if who == "A" else WHITE
            fg = WHITE if who == "A" else NAVY
            ny = RH - 170 - h + int(h * 0.1) - 40 + int((1 - ka) * 400)
            d.rounded_rectangle([cx - tw / 2 - 22, ny, cx + tw / 2 + 22, ny + 56], radius=28, fill=col)
            d.text((cx - tw / 2, ny + 6), nm, font=fn, fill=fg)
            if speaking and self.lines[cur][2].get("emoji"):
                ke = back((t - self.lines[cur][0] - 0.4) / 0.35)
                paste_scaled(img, emoji(self.lines[cur][2]["emoji"], 110), cx + 170, ny + 40, scale=ke)
        # bubbles
        if cur is None:
            return
        fb = F("med", 44)
        fnm = F("bold", 28)
        items = []
        for i, (t0, du, ln) in enumerate(self.lines[: cur + 1]):
            key = ("bub", i)
            if key not in self.__dict__.setdefault("_bc", {}):
                isA = ln["who"] == "A"
                self._bc[key] = bubble(ln["text"], fb, 780, p["a1"] if isA else WHITE, WHITE if isA else NAVY,
                                       tail="left" if isA else "right")
            items.append((t0, ln, self._bc[key]))
        gap = 26
        heights = [b.height + gap for _, _, b in items]
        total = sum(heights)
        prev_total = sum(heights[:-1])
        area = bottom - top
        ov_new, ov_old = max(0, total - area), max(0, prev_total - area)
        k = ease((t - items[-1][0]) / 0.3)
        ov = ov_old + (ov_new - ov_old) * k
        y = top - ov
        for i, (t0, ln, b) in enumerate(items):
            isA = ln["who"] == "A"
            kk = back((t - t0) / 0.32)
            sc = 0.55 + 0.45 * kk if t - t0 < 0.32 else 1.0
            al = clamp((y + b.height - top + 40) / (b.height * 0.6), 0, 1)
            x = 70 if isA else RW - 70 - b.width
            cx, cy = x + b.width / 2, y + b.height / 2
            # scale around the tail corner
            ax = x if isA else x + b.width
            ay = y + b.height
            if sc != 1.0:
                bw, bh = b.width * sc, b.height * sc
                cx = ax + (bw / 2 if isA else -bw / 2)
                cy = ay - bh / 2
            paste_scaled(img, b, cx, cy, scale=sc, alpha=al * min(1, ease((t - t0) / 0.15) + 0.01))
            y += heights[i]

    def facts(self, img, t):
        s, p = self.s, self.p
        a = self.scenes[2][1]
        lt = t - a
        k = back(lt / 0.4)
        st = sticker(s.get("reveal", "Here's what the law says").upper(), F("bold", 46), p["hl"], NAVY, angle=-4)
        paste_scaled(img, st, 80 + st.width / 2, 330, scale=k)
        ke = back((lt - 0.3) / 0.35)
        paste_scaled(img, emoji("👇", 90), 80 + st.width + 40, 330, scale=ke)
        y = 450
        fnum = F("bold", 52)
        for i, f in enumerate(s["facts"]):
            t0 = self.fact_t[i]
            kc = ease((t - t0) / 0.4)
            if kc <= 0:
                break
            ff, lines = fit_rich(probe, f["text"], f.get("highlight"), "bold", 50, RW - 300, 3, 38)
            lh = int(ff.size * 1.28)
            hih = 0
            if f.get("hi"):
                fhi, hil = fit_rich(probe, f["hi"], None, "med", 38, RW - 300, 1, 30)
                hih = int(fhi.size * 1.5)
            ch = len(lines) * lh + hih + 56
            card = Image.new("RGBA", (RW - 120, ch), (0, 0, 0, 0))
            cd = ImageDraw.Draw(card)
            cd.rounded_rectangle([0, 0, card.width - 1, ch - 1], radius=34, fill=(255, 255, 255, 28),
                                 outline=(255, 255, 255, 60), width=2)
            cd.ellipse([26, 28, 26 + 96, 28 + 96], fill=p["a1"])
            nt = str(i + 1)
            cd.text((26 + 48 - text_w(nt, fnum) / 2, 28 + 12), nt, font=fnum, fill=WHITE)
            sweep = clamp((t - t0 - 0.45) / 0.45, 0, 1)
            draw_rich(card, 150, 26, lines, ff, WHITE, p["hl"], NAVY, sweep=sweep)
            if f.get("hi"):
                cd.text((150, 26 + len(lines) * lh + 6), f["hi"], font=fhi, fill=p["soft"])
            off = int((1 - back((t - t0) / 0.45)) * 700)
            card.putalpha(card.split()[3].point(lambda v: int(v * kc)))
            img.alpha_composite(card, (60 + off, y))
            y += ch + 30
        # main character reacts in the corner
        ka = back((lt - 0.5) / 0.5)
        expr = "thinking" if lt < self.fact_t[-1] - a + 1.0 else "happy"
        av = avatar(self.look("A"), expr, blink=(int(t * 10) % 29 == 0), height=420)
        img.alpha_composite(av, (RW - av.width - 20, RH - 150 - av.height + int((1 - ka) * 450)))

    def end(self, img, t):
        s, p = self.s, self.p
        a = self.scenes[3][1]
        lt = t - a
        # confetti
        rnd = random.Random(7)
        cd = ImageDraw.Draw(img)
        if lt > 0.2:
            for i in range(70):
                x0 = rnd.uniform(0, RW); sp = rnd.uniform(260, 520); ph = rnd.uniform(0, 6.28)
                col = rnd.choice([p["a1"], p["hl"], p["a2"], WHITE])
                yy = -60 + (lt - 0.2) * sp + rnd.uniform(-400, 0)
                if yy < -40 or yy > RH:
                    continue
                xx = x0 + 30 * math.sin(lt * 3 + ph)
                w = 10 + 6 * abs(math.sin(lt * 5 + ph))
                cd.rectangle([xx, yy, xx + w, yy + 22], fill=col + (230,))
        e = s["ending"]
        speaking = self.end_bubble_t <= t < self.cta_t - 0.2
        mouth = (1 if int(t * 8) % 2 == 0 else 0) if speaking else 0
        ka = back(lt / 0.5)
        h = 620
        av = avatar(self.look(e.get("who", "A")), "happy" if not speaking else "neutral", mouth=mouth,
                    blink=(int(t * 10) % 33 == 0), height=h)
        bob = int(8 * math.sin(t * 7))
        y_av = 600 + bob + int((1 - ka) * 300)
        sc = 1.0
        # after the CTA arrives, shrink the character up a bit
        kc = ease((t - self.cta_t) / 0.5)
        if kc > 0:
            sc = 1 - 0.28 * kc
            av = av.resize((int(av.width * sc), int(av.height * sc)), Image.LANCZOS)
            y_av = int(600 - 40 * kc + bob)
        img.alpha_composite(av, ((RW - av.width) // 2, y_av))
        # ending bubble
        if t >= self.end_bubble_t:
            key = "endbub"
            if key not in self.__dict__.setdefault("_bc", {}):
                self._bc[key] = bubble(e["text"], F("med", 46), 860, WHITE, NAVY, tail="left")
            b = self._bc[key]
            kb = back((t - self.end_bubble_t) / 0.32)
            paste_scaled(img, b, RW / 2 + 40, 300 + b.height / 2 + 20, scale=0.6 + 0.4 * kb if kb < 1 else 1)
            if e.get("emoji"):
                ke = back((t - self.end_bubble_t - 0.5) / 0.35)
                paste_scaled(img, emoji(e["emoji"], 110), RW - 110, 250 + int(6 * math.sin(t * 5)), scale=ke)
        # CTA
        if kc > 0:
            yb = y_av + int(h * sc) + 30
            layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            fc, cl = fit_rich(probe, s["cta"], s.get("cta_highlight"), "bold", 74, RW - 160, 2, 48)
            yy = draw_rich(layer, 80, yb, cl, fc, WHITE, p["hl"], NAVY, center_w=RW - 160)
            if s.get("cta_hi"):
                fhi, hil = fit_rich(probe, s["cta_hi"], None, "bold", 50, RW - 160, 2, 36)
                yy = draw_rich(layer, 80, yy + 12, hil, fhi, p["soft"], p["hl"], NAVY, center_w=RW - 160)
            layer.putalpha(layer.split()[3].point(lambda v: int(v * kc)))
            img.alpha_composite(layer, (0, int((1 - kc) * 40)))
            kp = back((t - self.cta_t - 0.45) / 0.4)
            if kp > 0:
                fu = F("bold", 48)
                txt = "advocatesetu.com"
                tw = text_w(txt, fu)
                pill = Image.new("RGBA", (int(tw + 110), 110), (0, 0, 0, 0))
                pd = ImageDraw.Draw(pill)
                pd.rounded_rectangle([0, 0, pill.width - 1, 104], radius=52, fill=p["hl"])
                pd.text((55, 20), txt, font=fu, fill=NAVY)
                paste_scaled(img, pill, RW / 2, yy + 100, scale=kp)

    def frame(self, t):
        name = [n for n, a, b in self.scenes if a <= t < b]
        name = name[0] if name else self.scenes[-1][0]
        img = self.bg(name, t)
        getattr(self, name)(img, t)
        self.chrome(img, t)
        self.wipe(img, t)
        if t < 0.2:
            img.alpha_composite(Image.new("RGBA", img.size, self.p["bg"] + (int(255 * (1 - t / 0.2)),)))
        if t > self.dur - 0.35:
            img.alpha_composite(Image.new("RGBA", img.size, self.p["bg"] + (int(255 * clamp((t - self.dur + 0.35) / 0.35, 0, 1)),)))
        return img.convert("RGB")

    def render(self, outdir):
        work = tempfile.mkdtemp(prefix="story_")
        vid = os.path.join(work, "v.mp4")
        pr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{RW}x{RH}",
                               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                               "-pix_fmt", "yuv420p", vid], stdin=subprocess.PIPE)
        n = int(self.dur * FPS)
        for i in range(n):
            pr.stdin.write(self.frame(i / FPS).tobytes())
        pr.stdin.close()
        if pr.wait() != 0:
            raise SystemExit("ffmpeg video failed")
        wav = os.path.join(work, "a.wav")
        seed = zlib.crc32(self.c["date"].encode())
        info = story_music.make(self.dur, seed, self.events, wav)
        final = os.path.join(outdir, "reel.mp4")
        tmp = final[:-4] + ".part.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", vid, "-i", wav, "-map", "0:v", "-map", "1:a",
                        "-c:v", "libx264", "-profile:v", "high", "-level", "4.1", "-preset", "veryfast", "-crf", "19",
                        "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", str(FPS * 2), "-keyint_min", str(FPS * 2),
                        "-sc_threshold", "0", "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "160k", "-shortest",
                        "-movflags", "+faststart", tmp], check=True)
        os.replace(tmp, final)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "2.6", "-i", final, "-frames:v", "1", "-q:v", "3",
                        os.path.join(outdir, "cover.jpg")], check=True)
        shutil.rmtree(work, ignore_errors=True)
        return dict(duration=round(self.dur, 1), palette=self.pname, **info)

# ============================================================== stills (carousel + banner)
CW, CH = 1080, 1350

def rr(img, box, radius, fill, outline=None, width=0):
    """Translucent rounded rect blended onto img."""
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
    img.alpha_composite(ov)

def still_chrome(img, p, idx=None, total=None, disc=DISC):
    d = ImageDraw.Draw(img)
    brand_pill(img, 60, 56, 80)
    if idx is not None:
        txt = f"{idx}/{total}"
        f = F("bold", 32)
        tw = text_w(txt, f)
        rr(img, [CW - 60 - tw - 44, 68, CW - 60, 124], 28, (255, 255, 255, 40))
        d = ImageDraw.Draw(img)
        d.text((CW - 60 - tw - 22, 74), txt, font=f, fill=WHITE)
    f = F("imed", 24)
    w = d.textlength(disc, font=f)
    d.text(((CW - w) / 2, CH - 56), disc, font=f, fill=(225, 230, 245))

def swipe_tag(img, p, x, y):
    f = F("bold", 38)
    st = Image.new("RGBA", (330, 96), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    d.rounded_rectangle([0, 0, 320, 88], radius=44, fill=WHITE)
    d.text((34, 16), "Swipe", font=f, fill=NAVY)
    ax = 34 + text_w("Swipe", f) + 24
    d.polygon([(ax, 26), (ax + 34, 44), (ax, 62)], fill=p["a1"])
    d.polygon([(ax + 30, 26), (ax + 64, 44), (ax + 30, 62)], fill=p["a1"])
    img.alpha_composite(st, (x, y))

def carousel(c, outdir):
    s = c["story"]; pname, p = palette(c)
    A = {k: v for k, v in s["characters"]["A"].items() if k != "name"}
    Bc = s["characters"].get("B", s["characters"]["A"])
    B = {k: v for k, v in Bc.items() if k != "name"}
    n = 2 + len(s["facts"]) + 1
    paths = []
    # 1 cover
    img = background(CW, CH, p, pattern=False)
    d = ImageDraw.Draw(img)
    d.polygon([(0, 930), (CW, 760), (CW, 1150), (0, 1350)], fill=p["a1"] + (235,))
    st = sticker(s.get("kicker", "STORY TIME").upper(), F("bold", 40), p["hl"], NAVY, angle=-5)
    img.alpha_composite(st, (60, 170))
    fh, lines = fit_rich(probe, s["hook"], s.get("hook_highlight"), "bold", 84, CW - 140, 4, 54)
    y = draw_rich(img, 70, 290, lines, fh, WHITE, p["hl"], NAVY)
    if s.get("hook_hi"):
        fhi, hil = fit_rich(probe, s["hook_hi"], None, "bold", 50, CW - 140, 2, 36)
        draw_rich(img, 70, y + 18, hil, fhi, p["soft"], p["hl"], NAVY)
    av = avatar(A, s.get("hook_expr", "shocked"), height=560)
    img.alpha_composite(av, (CW - av.width - 30, CH - 90 - av.height))
    if s.get("hook_emoji"):
        e = emoji(s["hook_emoji"], 130)
        img.alpha_composite(e, (CW - av.width - 90, CH - 90 - av.height + 40))
    swipe_tag(img, p, 70, CH - 220)
    still_chrome(img, p, 1, n)
    paths.append(img)
    # 2 the story (first two lines of dialogue)
    img = background(CW, CH, p)
    fb = F("med", 42)
    y = 190
    for ln in s["dialogue"][:3]:
        isA = ln["who"] == "A"
        b = bubble(ln["text"], fb, 760, p["a1"] if isA else WHITE, WHITE if isA else NAVY, tail="left" if isA else "right")
        if y + b.height > 800:
            break
        img.alpha_composite(b, (60 if isA else CW - 60 - b.width, y))
        y += b.height + 18
    first = s["dialogue"][0]
    exA = first.get("react", "worried") if first["who"] == "B" else first.get("expr", "worried")
    a_av = avatar(A, exA if exA != "talk" else "worried", height=440)
    b_av = avatar(B, "neutral", height=440)
    img.alpha_composite(a_av, (150, CH - 100 - a_av.height))
    img.alpha_composite(b_av, (CW - 150 - b_av.width, CH - 100 - b_av.height))
    for who, ch, cx, col, fg in (("A", s["characters"]["A"], 150 + a_av.width // 2, p["a1"], WHITE),
                                 ("B", Bc, CW - 150 - b_av.width // 2, WHITE, NAVY)):
        nm = ch.get("name", who); fn = F("bold", 32); tw = text_w(nm, fn)
        ny = CH - 100 - 440 + 10
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([cx - tw / 2 - 20, ny, cx + tw / 2 + 20, ny + 50], radius=25, fill=col)
        d.text((cx - tw / 2, ny + 5), nm, font=fn, fill=fg)
    still_chrome(img, p, 2, n)
    paths.append(img)
    # facts
    for i, f in enumerate(s["facts"]):
        img = background(CW, CH, p)
        d = ImageDraw.Draw(img)
        st = sticker(s.get("reveal", "Here's what the law says").upper(), F("bold", 36), p["hl"], NAVY, angle=-4)
        img.alpha_composite(st, (60, 170))
        fnum = F("bold", 210)
        d.text((60, 270), f"0{i + 1}", font=fnum, fill=p["a1"])
        ff, lines = fit_rich(probe, f["text"], f.get("highlight"), "bold", 72, CW - 140, 5, 44)
        y = draw_rich(img, 70, 540, lines, ff, WHITE, p["hl"], NAVY)
        if f.get("hi"):
            fhi, hil = fit_rich(probe, f["hi"], None, "bold", 48, CW - 140, 2, 34)
            draw_rich(img, 70, y + 20, hil, fhi, p["soft"], p["hl"], NAVY)
        av = avatar(A, "happy" if i == len(s["facts"]) - 1 else "thinking", height=360)
        img.alpha_composite(av, (CW - av.width - 30, CH - 90 - av.height))
        still_chrome(img, p, 3 + i, n)
        paths.append(img)
    # CTA
    img = background(CW, CH, p, pattern=False)
    d = ImageDraw.Draw(img)
    rnd = random.Random(3)
    for _ in range(60):
        x, y = rnd.uniform(0, CW), rnd.choice([rnd.uniform(140, 660), rnd.uniform(1180, CH - 90)])
        d.rectangle([x, y, x + rnd.uniform(8, 16), y + 22], fill=rnd.choice([p["a1"], p["hl"], p["a2"], WHITE]) + (200,))
    av = avatar(A, "happy", height=480)
    img.alpha_composite(av, ((CW - av.width) // 2, 170))
    fc, cl = fit_rich(probe, s["cta"], s.get("cta_highlight"), "bold", 74, CW - 140, 3, 48)
    y = draw_rich(img, 70, 690, cl, fc, WHITE, p["hl"], NAVY, center_w=CW - 140)
    if s.get("cta_hi"):
        fhi, hil = fit_rich(probe, s["cta_hi"], None, "bold", 50, CW - 140, 2, 36)
        y = draw_rich(img, 70, y + 14, hil, fhi, p["soft"], p["hl"], NAVY, center_w=CW - 140)
    fu = F("bold", 46); txt = "advocatesetu.com"; tw = text_w(txt, fu)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([(CW - tw) / 2 - 55, y + 40, (CW + tw) / 2 + 55, y + 140], radius=50, fill=p["hl"])
    d.text(((CW - tw) / 2, y + 58), txt, font=fu, fill=NAVY)
    still_chrome(img, p, n, n)
    paths.append(img)
    out = []
    for i, im in enumerate(paths, 1):
        fp = os.path.join(outdir, f"carousel_{i}.jpg")
        im.convert("RGB").save(fp, quality=90)
        out.append(fp)
    return out

def banner(c, outdir):
    s = c["story"]; bn = c["banner"]; pname, p = palette(c)
    A = {k: v for k, v in s["characters"]["A"].items() if k != "name"}
    img = background(CW, CH, p)
    d = ImageDraw.Draw(img)
    st = sticker(bn.get("kicker", "Know your rights").upper(), F("bold", 38), p["hl"], NAVY, angle=-4)
    img.alpha_composite(st, (60, 170))
    fh, lines = fit_rich(probe, bn["headline"], bn.get("highlight"), "bold", 70, CW - 140, 3, 48)
    y = draw_rich(img, 70, 285, lines, fh, WHITE, p["hl"], NAVY)
    if bn.get("hindi"):
        fhi, hil = fit_rich(probe, bn["hindi"], None, "bold", 48, CW - 140, 2, 34)
        y = draw_rich(img, 70, y + 10, hil, fhi, p["soft"], p["hl"], NAVY)
    y += 34
    av = avatar(A, "happy", height=330)
    fp = F("bold", 40)
    for i, pt in enumerate(bn["points"][:3]):
        right = CW - 60 - (av.width - 30 if i == 2 else 0)
        lines = wrap_words(probe, pt.split(), fp, right - 200)
        h = len(lines) * 52 + 44
        rr(img, [60, y, right, y + h], 28, (255, 255, 255, 30), outline=(255, 255, 255, 70), width=2)
        d = ImageDraw.Draw(img)
        d.ellipse([84, y + h / 2 - 34, 152, y + h / 2 + 34], fill=p["a1"])
        nt = str(i + 1); fn = F("bold", 40)
        d.text((118 - text_w(nt, fn) / 2, y + h / 2 - 28), nt, font=fn, fill=WHITE)
        for j, ln in enumerate(lines):
            d.text((180, y + 22 + j * 52), " ".join(ln), font=fp, fill=WHITE)
        y += h + 18
    # CTA + character
    fc = F("bold", 42); cta = bn.get("cta", "Learn more on AdvocateSetu"); cw = text_w(cta, fc)
    cy = CH - 190
    d.rounded_rectangle([60, cy, 60 + cw + 70, cy + 86], radius=43, fill=p["hl"])
    d.text((95, cy + 15), cta, font=fc, fill=NAVY)
    img.alpha_composite(av, (CW - av.width - 20, CH - 80 - av.height))
    still_chrome(img, p, disc=DISC_B)
    img.convert("RGB").save(os.path.join(outdir, "banner.jpg"), quality=92)

def main():
    path = sys.argv[1]
    only = sys.argv[2] if len(sys.argv) > 2 else "all"
    c = json.load(open(path, encoding="utf-8"))
    outdir = os.path.dirname(os.path.abspath(path))
    res = {}
    if only in ("all", "banner"):
        banner(c, outdir)
    if only in ("all", "carousel"):
        res["carousel"] = len(carousel(c, outdir))
    if only in ("all", "reel"):
        res["reel"] = Reel(c).render(outdir)
    print("ok", outdir, json.dumps(res))

if __name__ == "__main__":
    main()
