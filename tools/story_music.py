"""Original, royalty-free background music + sound effects for AdvocateSetu reels,
synthesised from scratch (no samples, no copyrighted audio). Varies by seed."""
import wave, random
import numpy as np
from scipy.signal import butter, lfilter

SR = 48000

def _bp(x, lo, hi):
    b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], btype="band")
    return lfilter(b, a, x)

def _lp(x, f):
    b, a = butter(2, f / (SR / 2))
    return lfilter(b, a, x)

def _hp(x, f):
    b, a = butter(2, f / (SR / 2), btype="high")
    return lfilter(b, a, x)

def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)

def _env(n, a, d):
    t = np.arange(n) / SR
    e = np.exp(-t / d)
    na = max(1, int(a * SR))
    e[:na] *= np.linspace(0, 1, na)
    return e

def kick(rng):
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t / 0.035)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16)

def clap(rng):
    n = int(0.25 * SR)
    x = _bp(rng.standard_normal(n), 900, 5000) * _env(n, 0.002, 0.07)
    return x * 1.6

def hat(rng, open_=False):
    n = int((0.18 if open_ else 0.05) * SR)
    return _hp(rng.standard_normal(n), 7000) * _env(n, 0.001, 0.06 if open_ else 0.015)

def pluck(freqs, dur, bright=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n)
    for f in freqs:
        ph = 2 * np.pi * f * t
        x += np.sin(ph) + 0.35 * np.sin(2 * ph) * bright + 0.15 * np.sin(3 * ph) * bright
    return x / max(1, len(freqs)) * _env(n, 0.004, 0.22)

def bass(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sign(np.sin(2 * np.pi * f * t)) * 0.4
    e = np.minimum(1, np.arange(n) / (0.005 * SR)) * np.exp(-t / (dur * 0.9))
    return _lp(x * e, 600)

def bell(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t + 1.5 * np.sin(2 * np.pi * f * 3.5 * t) * np.exp(-t / 0.15))
    return x * _env(n, 0.003, 0.35)

def pop():
    n = int(0.09 * SR); t = np.arange(n) / SR
    f = 520 + 900 * (t / t[-1])
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.002, 0.03)

def whoosh(rng, dur=0.45):
    n = int(dur * SR)
    x = rng.standard_normal(n)
    out = np.zeros(n)
    seg = n // 12
    for i in range(12):
        lo = 300 + 3500 * (i / 11)
        out[i * seg:(i + 1) * seg] = _bp(x[i * seg:(i + 1) * seg], lo, lo * 1.8)
    w = np.sin(np.linspace(0, np.pi, n)) ** 2
    return out * w * 0.9

def ding():
    return 0.6 * bell(midi(88), 0.6) + 0.4 * bell(midi(95), 0.6)

PROGS = [
    [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [48, 52, 55]), (55, [55, 59, 62])],   # Am F C G
    [(48, [48, 52, 55]), (55, [55, 59, 62]), (57, [57, 60, 64]), (53, [53, 57, 60])],   # C G Am F
    [(50, [50, 53, 57]), (55, [55, 59, 62]), (48, [48, 52, 55]), (57, [57, 60, 64])],   # Dm G C Am
]

def make(dur, seed, events, out_path):
    """events: list of (time_s, kind) with kind in pop|whoosh|ding."""
    rng = np.random.default_rng(seed)
    R = random.Random(seed)
    bpm = R.choice([96, 100, 104, 108])
    shift = R.choice([0, 2, -3, 5])
    prog = R.choice(PROGS)
    beat = 60 / bpm
    n = int((dur + 1) * SR)
    L = np.zeros(n); Rr = np.zeros(n)
    def add(buf, x, t, g=1.0):
        i = int(t * SR)
        if i >= n:
            return
        j = min(n, i + len(x))
        buf[i:j] += g * x[:j - i]
    K, C = kick(rng), clap(rng)
    bars = int(dur / (4 * beat)) + 2
    for b in range(bars):
        root, chord = prog[b % 4]
        root += shift; chord = [c + shift for c in chord]
        t0 = b * 4 * beat
        intro = t0 < 4 * beat * 0.999 and False
        for q in range(4):
            tq = t0 + q * beat
            if b > 0 or q >= 2:
                add(L, K, tq, 0.9); add(Rr, K, tq, 0.9)
            if q in (1, 3):
                add(L, C, tq, 0.32); add(Rr, C, tq + 0.004, 0.32)
            for e in range(2):
                h = hat(rng, open_=(e == 1 and q == 3))
                add(L, h, tq + e * beat / 2, 0.16); add(Rr, h, tq + e * beat / 2 + 0.006, 0.12)
        # bass: eighths with a skip
        for e in range(8):
            if e in (3,):
                continue
            add(L, bass(midi(root - 12), beat * 0.45), t0 + e * beat / 2, 0.42)
            add(Rr, bass(midi(root - 12), beat * 0.45), t0 + e * beat / 2, 0.42)
        # off-beat chord stabs
        for e in (1, 3, 5, 6):
            pl = pluck([midi(c + 12) for c in chord], beat * 0.9)
            add(L, pl, t0 + e * beat / 2, 0.22); add(Rr, pl, t0 + e * beat / 2 + 0.012, 0.18)
        # sparkle arpeggio on 16ths every other bar
        if b % 2 == 1:
            arp = [chord[0] + 24, chord[1] + 24, chord[2] + 24, chord[1] + 24]
            for s16 in range(16):
                if s16 % 3 == 2:
                    continue
                add(Rr, bell(midi(arp[s16 % 4]), 0.3), t0 + s16 * beat / 4, 0.07)
                add(L, bell(midi(arp[s16 % 4]), 0.3), t0 + s16 * beat / 4 + 0.03, 0.04)
    # master: gentle compression via tanh, fades
    mix = np.stack([L, Rr], 1)[: int(dur * SR)]
    mix = np.tanh(mix * 0.9) * 0.55
    fi, fo = int(0.15 * SR), int(1.4 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    # duck music slightly under SFX and add them
    sfx = np.zeros_like(mix)
    for t, kind in events:
        x = {"pop": lambda: 0.5 * pop(), "whoosh": lambda: 0.45 * whoosh(rng), "ding": lambda: 0.35 * ding()}[kind]()
        i = int(t * SR)
        j = min(len(sfx), i + len(x))
        if i < len(sfx):
            sfx[i:j, 0] += x[:j - i]; sfx[i:j, 1] += x[:j - i]
    mix = mix + sfx
    peak = np.max(np.abs(mix)) or 1
    mix = mix / peak * 0.89
    data = (mix * 32767).astype("<i2")
    with wave.open(out_path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(data.tobytes())
    return dict(bpm=bpm, key_shift=shift)
