"""Background music we make ourselves (so there is no licence question): a soft, warm ambient bed with a slow chord progression,
gentle plucks and a light echo. Rendered once to a WAV and mixed quietly under the voice."""
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


def _env(n: int, attack: float, release: float) -> np.ndarray:
    t = np.arange(n) / SR
    a = np.clip(t / attack, 0, 1)
    r = np.clip((n / SR - t) / release, 0, 1)
    return a * r


def render(seconds: float = 30.0, bpm: float = 76.0) -> np.ndarray:
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
    echo = int(0.32 * SR)
    wet = np.zeros_like(out)
    wet[echo:] = out[:-echo] * 0.35
    out = out + wet
    fade = int(1.5 * SR)
    out[:fade] *= np.linspace(0, 1, fade)
    out[-fade:] *= np.linspace(1, 0, fade)
    return out / max(1e-6, np.abs(out).max()) * 0.8


def write(path: Path, seconds: float = 30.0) -> Path:
    data = render(seconds)
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
