"""Background music we make ourselves (so there is no licence question): a soft, warm ambient bed with a slow chord progression,
gentle plucks and a light echo. Rendered once to a WAV and mixed quietly under the voice.

The Avasetu signature: the same key, tempo and chords on every reel, and near the end a four-note bell motif, one note per
syllable of A-va-se-tu (G4, C5, E5, then a held G5), so the brand is recognisable by ear before the name is read. It is the
default under every reel (compose.make_reel); REEL_BRAND_MUSIC=off turns it off."""
import wave
from pathlib import Path

import numpy as np

SR = 48000
# I - vi - IV - V in C, voiced warm and low (Hz)
CHORDS = [
    (130.81, 164.81, 196.00, 246.94),   # Cmaj7
    (110.00, 130.81, 164.81, 196.00),   # Am7
    (87.31, 130.81, 174.61, 220.00),    # Fmaj7 (F, C, F, A)
    (98.00, 146.83, 196.00, 246.94),    # G (G, D, G, B)
]
PLUCK = [523.25, 659.25, 783.99, 659.25, 587.33, 659.25, 523.25, 493.88]
# the signature: A-va-se-tu (seconds from the motif's start, Hz, how long it rings)
SIGNATURE = [(0.00, 392.00, 0.9), (0.28, 523.25, 0.9), (0.56, 659.25, 0.9), (0.84, 783.99, 2.2)]
SIGNATURE_LEAD = 2.6  # the motif starts this many seconds before the end, so the held note rings out over the fade


def _env(n: int, attack: float, release: float) -> np.ndarray:
    t = np.arange(n) / SR
    a = np.clip(t / attack, 0, 1)
    r = np.clip((n / SR - t) / release, 0, 1)
    return a * r


def _bell(f: float, n: int) -> np.ndarray:
    """A soft bell: the note, a quiet octave and a slightly sharp fifth partial, each dying away."""
    tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 2.2) + 0.35 * np.sin(2 * np.pi * f * 2 * tt) * np.exp(-tt * 3.5)
            + 0.12 * np.sin(2 * np.pi * f * 3.01 * tt) * np.exp(-tt * 5.0))


def signature(n_total: int, at: float) -> np.ndarray:
    """The A-va-se-tu motif placed at `at` seconds in a buffer of `n_total` samples."""
    out = np.zeros(n_total, np.float32)
    for start, f, ring in SIGNATURE:
        a = int((at + start) * SR)
        if a >= n_total or a < 0:
            continue
        b = min(n_total, a + int(ring * SR))
        out[a:b] += (_bell(f, b - a) * 0.11).astype(np.float32)
    return out


def render(seconds: float = 30.0, bpm: float = 76.0, logo: bool = True) -> np.ndarray:
    """The bed for `seconds`, with the A-va-se-tu signature near the end when `logo` (and the reel is long enough to hear it)."""
    n = int(seconds * SR)
    out = np.zeros(n, np.float32)
    bar = 4 * 60.0 / bpm
    t_all = np.arange(n) / SR
    i = 0
    while i * bar < seconds:
        start, length = int(i * bar * SR), int(bar * SR * 1.15)
        seg = slice(start, min(n, start + length))
        tt = t_all[seg] - i * bar
        pad = sum(np.sin(2 * np.pi * f * tt) * 0.5 + np.sin(2 * np.pi * f * 2.001 * tt) * 0.12 for f in CHORDS[i % 4])
        out[seg] += (pad * _env(len(tt), 0.9, 1.2) * 0.06).astype(np.float32)
        i += 1
    step = 60.0 / bpm / 2  # eighth notes
    k = 0
    while k * step < seconds:
        if k % 2 == 0:
            start, length = int(k * step * SR), int(0.9 * SR)
            seg = slice(start, min(n, start + length))
            tt = t_all[seg] - k * step
            f = PLUCK[(k // 2) % len(PLUCK)]
            tone = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 5.5) + 0.3 * np.sin(2 * np.pi * f * 2 * tt) * np.exp(-tt * 8)
            out[seg] += (tone * 0.05).astype(np.float32)
        k += 1
    if logo and seconds >= SIGNATURE_LEAD + 3:
        out = out * 0.85 + signature(n, seconds - SIGNATURE_LEAD - 0.4)  # the bed steps back a little under the motif
    echo = int(0.32 * SR)
    wet = np.zeros_like(out)
    wet[echo:] = out[:-echo] * 0.35
    out = out + wet
    fade = int(1.5 * SR)
    out[:fade] *= np.linspace(0, 1, fade)
    out[-fade:] *= np.linspace(1, 0, fade)
    return out / max(1e-6, np.abs(out).max()) * 0.8


def write(path: Path, seconds: float = 30.0, logo: bool = True) -> Path:
    data = render(seconds, logo=logo)
    stereo = np.stack([data, np.roll(data, int(0.012 * SR))], axis=1)
    pcm = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path
