"""A reel's voice-over: the lines spoken in one take, each placed at its beat, over music that steps back while the voice speaks.

One take: the whole script is synthesised in one request with a long pause between lines (voice.take_ssml), so the voice
carries its intonation from line to line instead of starting afresh each time. The take is cut at those pauses (found in the
decoded audio). When the request fails, or the cut does not give exactly one piece per line, each line is synthesised on its
own as before; only when that fails too is there no voice (voice.VoiceError).

Ducking: the music is a little louder than before between lines and at the end, and a compressor keyed by the voice lowers it
while a line is spoken (ffmpeg sidechaincompress)."""
import logging
import re
import wave
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import numpy as np

from . import ffmpeg, voice

log = logging.getLogger(__name__)

SR = 48000
FRAME = SR // 100                 # 10 ms
SILENT_DB = -40.0                 # quieter than this, against the loudest 10 ms, is a pause
MIN_GAP_S = 0.85                  # a pause this long is a line break (voice.LINE_BREAK_MS); a comma or a '?' is shorter
MIN_PIECE_S = 0.3
HEAD_S, TAIL_S = 0.04, 0.15       # kept before and after each spoken line
VOICE_GAIN = 1.35
BED_GAIN = 0.30                   # the music between lines and at the end; under a voice line the compressor lowers it by about 10 to 14 dB
DUCK = "threshold=0.025:ratio=3:attack=20:release=450:makeup=1"


def split(pcm: np.ndarray, n: int) -> Optional[List[np.ndarray]]:
    """Cut a take (mono 16-bit samples at SR) into `n` lines at its long pauses. None unless there are exactly n - 1 of them
    and every piece is long enough to be a spoken line."""
    if n < 2 or pcm.size < SR // 2:
        return None
    frames = pcm[: pcm.size // FRAME * FRAME].astype(np.float64).reshape(-1, FRAME)
    rms = np.sqrt((frames ** 2).mean(axis=1))
    peak = float(rms.max()) if rms.size else 0.0
    if peak <= 0:
        return None
    idx = np.flatnonzero(rms > peak * 10 ** (SILENT_DB / 20))
    if idx.size == 0:
        return None
    gaps = [(int(idx[b]) + 1, int(idx[b + 1])) for b in np.flatnonzero(np.diff(idx) > 1)]   # silent frames [start, end)
    breaks = [(s, e) for s, e in gaps if (e - s) * FRAME >= MIN_GAP_S * SR]
    if len(breaks) != n - 1:
        return None
    head, tail = int(HEAD_S * 100), int(TAIL_S * 100)
    starts = [max(0, int(idx[0]) - head)] + [max(s, e - head) for s, e in breaks]
    ends = [min(e, s + tail) for s, e in breaks] + [min(len(rms), int(idx[-1]) + 1 + tail)]
    pieces = [pcm[a * FRAME:b * FRAME] for a, b in zip(starts, ends)]
    if any(p.size < MIN_PIECE_S * SR for p in pieces):
        return None
    return pieces


def _write_wav(path: Path, pcm: np.ndarray) -> Path:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.astype("<i2").tobytes())
    return path


def _decode(mp3: Path) -> np.ndarray:
    raw = mp3.with_suffix(".pcm")
    ffmpeg.run(["-i", str(mp3), "-ac", "1", "-ar", str(SR), "-f", "s16le", str(raw), "-y"])
    return np.frombuffer(raw.read_bytes()[: raw.stat().st_size // 2 * 2], dtype="<i2")


def one_take(lines: Sequence[str], lang: str, work: Path) -> Optional[List[Path]]:
    """The lines from one request, one WAV each, or None (the caller then synthesises each line on its own)."""
    if len(lines) < 2:
        return None
    try:
        mp3 = work / "take.mp3"
        mp3.write_bytes(voice.synth(voice.take_ssml(lines), lang, ssml=True))
        pieces = split(_decode(mp3), len(lines))
    except Exception as e:  # the service refused the script, ffmpeg could not decode it...: the lines one by one instead
        reason = str(e) if isinstance(e, voice.VoiceError) else type(e).__name__   # a VoiceError's message is already redacted
        log.warning("voice-over: one take not used (%s); trying line by line", reason)
        return None
    if pieces is None:
        log.info("voice-over: one take did not cut into %d lines; trying line by line", len(lines))
        return None
    return [_write_wav(work / f"take{i}.wav", p) for i, p in enumerate(pieces)]


def per_line(lines: Sequence[str], lang: str, work: Path) -> List[Path]:
    clips = []
    for i, text in enumerate(lines):
        mp3 = work / f"b{i}.mp3"
        mp3.write_bytes(voice.synth(text, lang))
        clips.append(mp3)
    return clips


GREETING = re.compile(r"^\s*«([^»]+)»\s*(.*)$", re.S)
GREETING_GAP_S = 0.35   # after the drawn-out greeting, before the voice goes on


def spoken_lines(lines, lang: str, gender: str, work: Path) -> List[Path]:
    """The voice-over step's lines (pause tags in them), one request each: a line is a person's sentence over one picture,
    its pauses its own. A line opening with «greeting» has it said slower and warmer (voice.synth_greeting), then a breath,
    then the rest. Raises voice.VoiceError."""
    clips = []
    for i, text in enumerate(lines):
        if not text.strip():   # a scene with no words: a breath of silence, its music plays
            quiet = work / f"q{i}.wav"
            ffmpeg.run(["-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=mono", "-t", "0.2", str(quiet), "-y"])
            clips.append(quiet)
            continue
        m = GREETING.match(text)
        mp3 = work / f"s{i}.mp3"
        mp3.write_bytes(voice.synth_spoken(m.group(2) if m else text, lang, gender))
        if m:
            hello = work / f"g{i}.mp3"
            hello.write_bytes(voice.synth_greeting(m.group(1), lang, gender))
            joined = work / f"s{i}.wav"
            ffmpeg.run(["-i", str(hello), "-i", str(mp3), "-filter_complex",
                        f"[0:a]aresample={SR},apad=pad_dur={GREETING_GAP_S}[g];[1:a]aresample={SR}[r];[g][r]concat=n=2:v=0:a=1[o]",
                        "-map", "[o]", "-ac", "1", str(joined), "-y"])
            mp3 = joined
        clips.append(mp3)
    return clips


def voice_lines(lines: Sequence[str], lang: str, work: Path) -> Tuple[List[Path], str]:
    """(one audio file per line, how: 'take' or 'lines'). Raises voice.VoiceError when no voice could be made."""
    clips = one_take(lines, lang, work)
    if clips is not None:
        return clips, "take"
    return per_line(lines, lang, work), "lines"


def delays_ms(starts: Sequence[float]) -> List[int]:
    """Each line starts just after its scene appears (the hook a little later, as the reel opens)."""
    return [int((t + (0.35 if i == 0 else 0.25)) * 1000) for i, t in enumerate(starts)]


def graph(n: int, starts: Sequence[float], total: float, music: bool = True) -> str:
    """The ffmpeg filter graph: inputs 0..n-1 are the lines, input n the music bed (when `music`); the output is [out]."""
    filters = [f"[{i}:a]adelay={ms}|{ms},aresample={SR}[a{i}]" for i, ms in enumerate(delays_ms(starts[:n]))]
    mix = "".join(f"[a{i}]" for i in range(n))
    voice_out = "[voice][key]" if music else "[out]"
    filters.append(f"{mix}amix=inputs={n}:normalize=0,apad=whole_dur={total:.2f},volume={VOICE_GAIN}"
                   + (",asplit=2" if music else "") + voice_out)
    if music:
        filters.append(f"[{n}:a]aresample={SR},volume={BED_GAIN:.2f}[bed]")
        filters.append(f"[bed][key]sidechaincompress={DUCK}[ducked]")
        filters.append("[voice][ducked]amix=inputs=2:normalize=0:duration=first[out]")
    return ";".join(filters)


def mix(work: Path, clips: Sequence[Path], starts: Sequence[float], total: float, bed: Optional[Path]) -> Path:
    """The voice lines, each at its start, over the music bed (ducked under the voice); without a bed, the voice alone."""
    inputs: List[str] = []
    for c in clips:
        inputs += ["-i", str(c)]
    if bed is not None:
        inputs += ["-i", str(bed)]
    audio = work / "narration.m4a"
    ffmpeg.run([*inputs, "-filter_complex", graph(len(clips), starts, total, music=bed is not None), "-map", "[out]",
                "-t", f"{total:.2f}", "-c:a", "aac", "-b:a", "160k", str(audio), "-y"])
    return audio
