import sys; import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_promo import *
from PIL import ImageDraw
H = 1350
img = gradient(W, H, shift=0.8)
d = ImageDraw.Draw(img)
watermark(img, W * .8, H * .42, 820, 20)
brand_pill(img, M, 70, 96)
y = 250
d.rounded_rectangle([M, y, M + 400, y + 56], radius=28, outline=GOLD, width=3)
d.text((M + 200, y + 28), "INDIA'S LEGAL BRIDGE", font=F("semi", 28), fill=GOLD, anchor="mm")
y = headline(d, M, y + 96, [("Legal help,", WHITE), ("made simple.", GOLD)], 112, W - 2 * M)
d.text((M, y + 16), "आपका कानूनी सेतु — सरल, सुरक्षित, भरोसेमंद", font=F("hi", 38), fill=GOLD_SOFT)
y += 110
features(img, M, y, [
    ("shield", "Bar Council-verified advocates", "Every profile checked"),
    ("chat", "Video, audio & chat consultations", "From anywhere in India"),
    ("clock", "50+ cities · 10 practice areas", "Book in minutes"),
], 84, 30, W - 2 * M)
bar_h, disc_h = 128, 46
cta_y = H - bar_h - disc_h - 172
cta_pill(img, W // 2, cta_y, "Visit advocatesetu.com", h=96)
d = ImageDraw.Draw(img)
d.text((W // 2, cta_y + 96 + 22), "Follow @advocatesetu for daily legal awareness", font=F("semi", 30), fill=WHITE, anchor="mt")
trust_bar(img, H - bar_h - disc_h, bar_h, [("shield", "Verified", "Advocates"), ("chat", "Daily tips", "Know your rights"), ("lock", "Secure", "& confidential")])
d = ImageDraw.Draw(img)
d.rectangle([0, H - disc_h, W, H], fill=(240, 242, 248))
d.text((W // 2, H - disc_h / 2), "For general awareness only. Not legal advice.", font=F("med", 21), fill=(90, 102, 130), anchor="mm")
img.convert("RGB").save(sys.argv[1], "JPEG", quality=93)
