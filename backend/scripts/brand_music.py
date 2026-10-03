"""Write the Avasetu theme and sound logo as audio files, for reels made by hand (in Instagram's or Facebook's editor, CapCut...).

  cd backend && PYTHONPATH=. python scripts/brand_music.py [--out ../docs/brand/avasetu/audio]

Writes avasetu-sound-logo.m4a (about 3 s), avasetu-theme-15s.m4a and avasetu-theme-30s.m4a (both end on the A-va-se-tu motif).
The same music is generated under every reel the system makes (app/modules/reels/music.py); it is ours, so it can be used anywhere.
"""
import argparse
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modules.reels import ffmpeg, music  # noqa: E402


def write_all(out: Path) -> list:
    out.mkdir(parents=True, exist_ok=True)
    done = []
    with tempfile.TemporaryDirectory() as work:
        w = Path(work)
        jobs = [("avasetu-sound-logo", music.write_logo(w / "logo.wav")),
                ("avasetu-theme-15s", music.write(w / "t15.wav", 15.0)),
                ("avasetu-theme-30s", music.write(w / "t30.wav", 30.0))]
        for name, wav in jobs:
            dest = out / f"{name}.m4a"
            ffmpeg.run(["-y", "-i", str(wav), "-c:a", "aac", "-b:a", "160k", str(dest)])
            done.append(dest)
    return done


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=str(BACKEND.parent / "docs" / "brand" / "avasetu" / "audio"))
    for p in write_all(Path(ap.parse_args().out)):
        print("wrote", p)
