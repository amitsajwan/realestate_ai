"""ffmpeg access. The binary comes from the `imageio-ffmpeg` package (a static build bundled in its wheel), so no apt package or
system install is needed on Windows or in a python:slim container. Errors are sanitised: they never contain paths or tokens."""
import re
import subprocess
import tempfile
import threading
from dataclasses import dataclass
from typing import Iterable, List, Optional

from app.platform.meta_graph.publisher import sanitize

DEFAULT_TIMEOUT_S = 600.0


class FfmpegError(Exception):
    """ffmpeg is unavailable or failed; the message is safe to show."""


def binary() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        raise FfmpegError("ffmpeg is not available (pip install imageio-ffmpeg)")


def available() -> bool:
    try:
        r = subprocess.run([binary(), "-version"], capture_output=True, timeout=30)
        return r.returncode == 0
    except Exception:
        return False


def _clean(stderr: bytes, exe: str, args=()) -> str:
    text = stderr.decode("utf8", "replace")
    text = text.replace(exe, "ffmpeg")
    for a in sorted((str(x) for x in args), key=len, reverse=True):   # file arguments (may contain spaces) never appear in messages
        if "/" in a or "\\" in a:
            text = text.replace(a, "<file>").replace(a.replace("\\", "/"), "<file>")
    text = re.sub(r"[A-Za-z]:[\/][^\s:\"']+|/(?:[\w.\-]+/)+[\w.\-]+", "<path>", text)
    return sanitize(text[-600:])


def run(args: List[str], timeout: float = DEFAULT_TIMEOUT_S, check: bool = True) -> str:
    """Run ffmpeg with `args` (without the binary). Returns stderr text (ffmpeg writes its log and `-i` probe output there)."""
    exe = binary()
    try:
        r = subprocess.run([exe, "-hide_banner", "-nostdin", *args], capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise FfmpegError(f"ffmpeg timed out after {int(timeout)} s")
    except OSError as e:
        raise FfmpegError(f"ffmpeg could not start ({type(e).__name__})")
    if check and r.returncode != 0:
        raise FfmpegError("ffmpeg failed: " + _clean(r.stderr, exe, args))
    return r.stderr.decode("utf8", "replace")


def run_with_frames(args: List[str], frames: Iterable[bytes], timeout: float = DEFAULT_TIMEOUT_S) -> None:
    """Run ffmpeg reading raw frames (the caller's `-i -` input) from `frames`; the whole job is bounded by `timeout`."""
    exe = binary()
    with tempfile.TemporaryFile() as err:
        try:
            proc = subprocess.Popen([exe, "-hide_banner", "-nostdin", "-y", *args], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=err)
        except OSError as e:
            raise FfmpegError(f"ffmpeg could not start ({type(e).__name__})")
        timer = threading.Timer(timeout, proc.kill)
        timer.start()
        broken = False
        try:
            for fr in frames:
                try:
                    proc.stdin.write(fr)
                except (BrokenPipeError, OSError):
                    broken = True
                    break
            try:
                proc.stdin.close()
            except OSError:
                pass
            code = proc.wait()
        finally:
            timer.cancel()
            if proc.poll() is None:
                proc.kill()
        if code != 0 or broken:
            err.seek(0)
            raise FfmpegError(("ffmpeg failed: " if code else "ffmpeg stopped early: ") + _clean(err.read(), exe, args))


@dataclass
class Probe:
    duration: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    video_codec: str = ""
    pix_fmt: str = ""
    audio_codec: str = ""
    has_audio: bool = False
    size_bytes: int = 0


def probe(path) -> Probe:
    """ffprobe-equivalent using `ffmpeg -i` (the bundled build ships no ffprobe)."""
    import os

    text = run(["-i", str(path)], check=False)
    p = Probe(size_bytes=os.path.getsize(path))
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text)
    if m:
        p.duration = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    v = re.search(r"Stream #\S+.*?Video:\s*(\w+)[^,]*?(?:\(([^)]*)\))?[^,]*,\s*(\w+)[^,]*,\s*(\d+)x(\d+)", text)
    if v:
        p.video_codec, p.pix_fmt, p.width, p.height = v.group(1), v.group(3), int(v.group(4)), int(v.group(5))
    f = re.search(r"([\d.]+)\s*fps", text)
    if f:
        p.fps = float(f.group(1))
    a = re.search(r"Stream #\S+.*?Audio:\s*(\w+)", text)
    if a:
        p.has_audio, p.audio_codec = True, a.group(1)
    return p
