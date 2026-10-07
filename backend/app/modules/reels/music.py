"""The Avasetu theme: music we make ourselves in code (so there is no licence question), the same under every reel.

The idea, in plain words:
- Five notes only, those of Raag Bhupali (Sa Re Ga Pa Dha = C D E G A): a calm, warm, "coming home" evening raag that sounds
  Indian without sounding like a film song, and fits under a voice-over.
- The signature is four of those notes, one per syllable of A-va-se-tu: G4 C5 E5 G5 (Pa Sa Ga Pa), rising, the last one held.
  It opens the theme on the santoor and closes it on a bell, so the brand is heard in the first second and again at the end.
- A santoor-like plucked string (two slightly detuned strings per note, like the instrument's paired strings) plays a gentle
  pattern over four chords (C, Am, F, G); a soft pad, a light bass and quiet hand-drum strokes (a low "dha", a high "na" tick)
  keep it moving at 84 beats a minute.
Rendered to a WAV for each reel (cached per length) and mixed quietly under the voice. REEL_BRAND_MUSIC=off turns it off
(compose.encode). scripts/brand_music.py writes the theme and the sound logo as files for anyone making a reel by hand."""
import functools
import wave
from pathlib import Path

import numpy as np

SR = 48000
BPM = 84.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT

# note frequencies (Hz)
G3, A3, C4, D4, E4, G4, A4 = 196.00, 220.00, 261.63, 293.66, 329.63, 392.00, 440.00
C5, D5, E5, G5, A5 = 523.25, 587.33, 659.25, 783.99, 880.00
BHUPALI = (C4, D4, E4, G4, A4, C5, D5, E5, G5, A5)  # Sa Re Ga Pa Dha over two octaves

# four chords, one bar each: pad voicing (Hz) and the bass root
CHORDS = [
    ((130.81, 164.81, 196.00, 293.66), 65.41),   # C (add9)
    ((110.00, 130.81, 164.81, 196.00), 55.00),   # Am7
    ((87.31, 130.81, 174.61, 220.00), 87.31),    # Fmaj7
    ((98.00, 146.83, 196.00, 246.94), 98.00),    # G
]
# the santoor's eighth notes over each chord: Bhupali notes only
PATTERNS = [
    (C5, G4, E5, G4, D5, G4, E5, G5),
    (A4, E5, C5, E5, A5, E5, G5, E5),
    (A4, C5, G5, C5, A5, C5, G5, E5),
    (G4, D5, G5, D5, A5, G5, E5, D5),
]
PLUCK = [n for p in PATTERNS for n in p]

# the signature: A-va-se-tu (seconds from the motif's start, Hz, how long it rings)
SIGNATURE = [(0.00, G4, 0.9), (0.28, C5, 0.9), (0.56, E5, 0.9), (0.84, G5, 2.2)]
SIGNATURE_LEAD = 2.6  # the closing motif starts this many seconds (plus 0.4) before the end, so the held note rings over the fade


def _env(n: int, attack: float, release: float) -> np.ndarray:
    t = np.arange(n) / SR
    a = np.clip(t / attack, 0, 1)
    r = np.clip((n / SR - t) / release, 0, 1)
    return a * r


def _add(out: np.ndarray, at: float, sound: np.ndarray, gain: float) -> None:
    a = int(at * SR)
    if a >= len(out) or a < 0:
        return
    b = min(len(out), a + len(sound))
    out[a:b] += (sound[:b - a] * gain).astype(np.float32)


# ---- instruments --------------------------------------------------------------------------------------------------------------------
def _string(f: float, n: int, seed: int, decay: float = 0.9965) -> np.ndarray:
    """One plucked string (Karplus-Strong), computed a period at a time: y[k] = decay * (y[k-N] + y[k-N-1]) / 2. That sounds at
    SR / (N + 0.5) Hz; N is whole samples, so the result is resampled to land exactly on `f` (in tune with the bell and the pad)."""
    period = max(2, int(SR / f - 0.5))
    ratio = f / (SR / (period + 0.5))  # > 1: read the string a little faster to raise it to f
    m = int(n * ratio) + 2
    raw = _ks(period, m, seed, decay)
    return np.interp(np.arange(n) * ratio, np.arange(m), raw)


def _ks(period: int, n: int, seed: int, decay: float) -> np.ndarray:
    rng = np.random.default_rng(seed)
    burst = rng.uniform(-1, 1, period)
    burst = 0.6 * burst + 0.4 * np.roll(burst, 1)  # a softer strike (a santoor hammer, not a pick)
    burst -= burst.mean()  # no DC: the averaging filter would keep it for ever
    y = np.zeros(n + period + 1, np.float64)  # y[0] is a silent sample before the strike, so y[k-N-1] always exists
    y[1:period + 1] = burst
    for s in range(period + 1, n + period + 1, period):
        e = min(s + period, n + period + 1)
        y[s:e] = decay * 0.5 * (y[s - period:e - period] + y[s - period - 1:e - period - 1])
    return y[1:n + 1]


@functools.lru_cache(maxsize=64)
def santoor(f: float, seconds: float = 1.3, seed: int = 0) -> np.ndarray:
    """Two slightly detuned strings per note, as on a santoor's paired courses, with a gentle fade at the end."""
    n = int(seconds * SR)
    tone = _string(f * 0.99825, n, seed) + 0.9 * _string(f * 1.00175, n, seed + 1)  # 3 cents either side: centred on f, slow beating
    tone *= _env(n, 0.002, 0.25)
    return (tone / max(1e-6, np.abs(tone).max())).astype(np.float32)


@functools.lru_cache(maxsize=16)
def bell(f: float, seconds: float) -> np.ndarray:
    """A soft bell: the note, a quiet octave and a slightly sharp fifth partial, each dying away."""
    tt = np.arange(int(seconds * SR)) / SR
    tone = (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 2.2) + 0.35 * np.sin(2 * np.pi * f * 2 * tt) * np.exp(-tt * 3.5)
            + 0.12 * np.sin(2 * np.pi * f * 3.01 * tt) * np.exp(-tt * 5.0))
    return (tone * _env(len(tt), 0.004, 0.3)).astype(np.float32)


@functools.lru_cache(maxsize=4)
def dha(seconds: float = 0.45) -> np.ndarray:
    """A low hand-drum stroke: a pitch that falls from 150 to 70 Hz, with a soft thump."""
    tt = np.arange(int(seconds * SR)) / SR
    freq = 70 + 80 * np.exp(-tt * 18)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    return (np.sin(phase) * np.exp(-tt * 7.5)).astype(np.float32)


@functools.lru_cache(maxsize=4)
def na(seconds: float = 0.12) -> np.ndarray:
    """A high, dry tick on the drum's rim: a short ringing tone plus a breath of noise."""
    n = int(seconds * SR)
    tt = np.arange(n) / SR
    noise = np.random.default_rng(7).uniform(-1, 1, n)
    noise = noise - np.roll(noise, 1)  # brighter
    return ((0.6 * np.sin(2 * np.pi * 1180 * tt) + 0.25 * noise) * np.exp(-tt * 45)).astype(np.float32)


def signature(n_total: int, at: float) -> np.ndarray:
    """The A-va-se-tu motif on the bell, placed at `at` seconds in a buffer of `n_total` samples."""
    out = np.zeros(n_total, np.float32)
    for start, f, ring in SIGNATURE:
        _add(out, at + start, bell(f, ring), 0.11)
    return out


# ---- the theme ----------------------------------------------------------------------------------------------------------------------
@functools.lru_cache(maxsize=8)
def _render(seconds: float, logo: bool) -> np.ndarray:
    n = int(seconds * SR)
    t_all = np.arange(n) / SR
    pad = np.zeros(n, np.float32)
    bass = np.zeros(n, np.float32)
    strings = np.zeros(n, np.float32)
    drums = np.zeros(n, np.float32)
    i = 0
    while i * BAR < seconds:
        t0 = i * BAR
        voicing, root = CHORDS[i % 4]
        start, length = int(t0 * SR), int(BAR * SR * 1.15)
        seg = slice(start, min(n, start + length))
        tt = t_all[seg] - t0
        p = sum(np.sin(2 * np.pi * f * tt) * 0.5 + np.sin(2 * np.pi * f * 2.002 * tt) * 0.10 for f in voicing)
        pad[seg] += (p * _env(len(tt), 0.9, 1.2) * 0.05).astype(np.float32)
        for beat in (0, 2):  # bass on beats 1 and 3; the second harmonic keeps it audible on a phone speaker
            m = int(BEAT * 1.6 * SR)
            b = np.arange(m) / SR
            tone = np.sin(2 * np.pi * root * b) + 0.45 * np.sin(2 * np.pi * root * 2 * b)
            _add(bass, t0 + beat * BEAT, tone * np.exp(-b * 2.2) * _env(m, 0.01, 0.15), 0.12)
        if i == 0:  # the opening: the signature on the santoor, then the pattern takes over
            for k, (off, f, _) in enumerate(SIGNATURE):
                _add(strings, off + 0.05, santoor(f, 1.6 if k == 3 else 1.1, seed=100 + k), 0.16)
        else:
            for k, f in enumerate(PATTERNS[i % 4]):
                _add(strings, t0 + k * BEAT / 2, santoor(f, 1.3, seed=(i % 4) * 8 + k), 0.11 if k % 2 == 0 else 0.08)
            _add(drums, t0, dha(), 0.16)
            _add(drums, t0 + 2 * BEAT, dha(), 0.11)
            for off in (1.5, 3.5):
                _add(drums, t0 + off * BEAT, na(), 0.05)
            _add(drums, t0 + 3.75 * BEAT, na(), 0.03)
        i += 1
    moving = strings + drums + bass
    out = pad + moving
    if logo and seconds >= SIGNATURE_LEAD + 3:
        at = seconds - SIGNATURE_LEAD - 0.4
        # the pattern and drums step back as the bell motif comes in; the pad holds the chord under it
        a, b = int((at - 0.6) * SR), int(at * SR)
        duck = np.ones(n, np.float32)
        duck[a:b] = np.linspace(1.0, 0.25, b - a)
        duck[b:] = 0.25
        out = pad + moving * duck + signature(n, at)
    echo = int(0.32 * SR)  # a little room
    wet = np.zeros_like(out)
    wet[echo:] = out[:-echo] * 0.28
    out = out + wet
    fade_in, fade_out = int(0.05 * SR), int(1.5 * SR)
    out[:fade_in] *= np.linspace(0, 1, fade_in)
    out[-fade_out:] *= np.linspace(1, 0, fade_out)
    return out / max(1e-6, np.abs(out).max()) * 0.8


def render(seconds: float = 30.0, bpm: float = BPM, logo: bool = True) -> np.ndarray:
    """The theme for `seconds` (mono), closing with the A-va-se-tu bell motif when `logo` (and the reel is long enough to hear it).
    `bpm` is kept for callers; the theme's tempo is fixed (it is part of the brand)."""
    return _render(round(float(seconds), 3), bool(logo)).copy()


def sound_logo() -> np.ndarray:
    """The sound logo on its own (about 3 s): the motif on santoor and bell together over the C chord."""
    n = int(3.2 * SR)
    out = np.zeros(n, np.float32)
    tt = np.arange(n) / SR
    out += (sum(np.sin(2 * np.pi * f * tt) for f in CHORDS[0][0]) * _env(n, 0.3, 1.2) * 0.03).astype(np.float32)
    for k, (off, f, ring) in enumerate(SIGNATURE):
        _add(out, 0.1 + off, santoor(f, 1.6 if k == 3 else 1.1, seed=100 + k), 0.14)
        _add(out, 0.1 + off, bell(f, ring), 0.07)
    return out / max(1e-6, np.abs(out).max()) * 0.8


def _write_wav(path: Path, data: np.ndarray) -> Path:
    stereo = np.stack([data, np.roll(data, int(0.012 * SR))], axis=1)  # a touch of width
    pcm = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path


def write(path: Path, seconds: float = 30.0, logo: bool = True) -> Path:
    return _write_wav(path, render(seconds, logo=logo))


def write_logo(path: Path) -> Path:
    return _write_wav(path, sound_logo())
