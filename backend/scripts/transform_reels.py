"""Transformation reels (app/modules/reels/transform_reels.py): check them, preview them. Nothing is added to the calendar.

  PYTHONPATH=. python scripts/transform_reels.py check
        the script checks (claims, hook length, phone numbers in the chat mock); no rendering
  PYTHONPATH=. python scripts/transform_reels.py preview [--codes E1 E2] [--out uploads/transformreels]
        render the MP4s and a contact sheet per reel: for review, or to share by hand
"""
import argparse
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modules.reels import transform_reels as tr  # noqa: E402


def cmd_check(_) -> int:
    bad = [p for s in tr.SCRIPTS for p in tr.check_script(s)]
    print("\n".join(bad) if bad else f"all {len(tr.SCRIPTS)} scripts pass")
    return 1 if bad else 0


def cmd_preview(a) -> int:
    from app.modules.reels import compose, ffmpeg
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for code in a.codes or tr.ORDER:
        mp4 = tr.render(code, out / f"transform-{code.lower()}.mp4")
        compose.contact_sheet(mp4, out / f"transform-{code.lower()}-sheet.png")
        p = ffmpeg.probe(mp4)
        print(f"{code}: {mp4} {p.duration:.1f}s {p.size_bytes / 1e6:.1f} MB  hook: {tr.BY_CODE[code].hook.replace('*', '')}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    p = sub.add_parser("preview")
    p.add_argument("--codes", nargs="*", choices=list(tr.ORDER))
    p.add_argument("--out", default="uploads/transformreels")
    a = ap.parse_args()
    if a.cmd == "check":
        return cmd_check(a)
    return cmd_preview(a)


if __name__ == "__main__":
    sys.exit(main())
