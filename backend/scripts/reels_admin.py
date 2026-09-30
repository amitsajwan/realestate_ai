"""Reels admin: make a short vertical video from our own images and publish it.

  python scripts/reels_admin.py preview --template tip|tour|pitch [--out DIR] [--photos a.jpg b.jpg ...]
        render <template>.mp4 and <template>.png (a contact sheet of 8 frames) into DIR and print the file checks (no network)
  python scripts/reels_admin.py post --file reel.mp4 --channel instagram|facebook --caption "..." [--dry-run | --live]
        stage the file under <uploads>/reels/, then publish it as a Reel. SOCIAL_DRY_RUN is honoured (default: dry run, fake ids);
        --live forces a real post (needs META_* env vars and PUBLIC_MEDIA_BASE_URL; the file must be reachable at
        PUBLIC_MEDIA_BASE_URL/uploads/reels/<name>.mp4, so on the server this must run where <uploads> is served).
        Facebook can also upload the bytes directly: add --upload-bytes (no public URL needed).
Run on the server:  docker compose exec -T -e PYTHONPATH=. backend python scripts/reels_admin.py post --file ... --channel instagram --caption "..." --live
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.modules.reels import compose, ffmpeg, publish, templates  # noqa: E402
from app.modules.social.config import load as load_config  # noqa: E402
from app.modules.social.publisher import PublishError  # noqa: E402

CHANNEL_MAP = {"instagram": "instagram", "facebook": "facebook_page"}


def report(path: Path) -> None:
    p = ffmpeg.probe(path)
    print(f"{path.name}: {p.duration:.1f}s {p.width}x{p.height} {p.video_codec}/{p.pix_fmt} {p.fps:g}fps audio={p.audio_codec or 'NONE'} {p.size_bytes / 1e6:.1f} MB")


def build(template: str, photos):
    if template == "tip":
        return templates.tip_reel(templates.TIP_LINES, images=photos or None)
    if template == "tour":
        if not photos:
            sys.exit("the tour template needs --photos (your own listing photos)")
        return templates.listing_tour(photos, templates.SAMPLE_FACTS["kharadi"], sample=True)
    return templates.agent_pitch(images=photos or None)


def cmd_preview(a) -> int:
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    scenes, opts = build(a.template, a.photos)
    mp4 = compose.make_reel(scenes, out / f"{a.template}.mp4", music=a.music, **opts)
    sheet = compose.contact_sheet(mp4, out / f"{a.template}.png")
    report(mp4)
    print(f"contact sheet: {sheet}")
    return 0


async def cmd_post(a) -> int:
    cfg = load_config()
    channel = CHANNEL_MAP[a.channel]
    dry = True if a.dry_run else False if a.live else cfg.dry_run
    src = Path(a.file)
    if not src.is_file():
        print("file not found")
        return 2
    report(src)
    try:
        if dry:
            name = src.name if publish.NAME_RE.match(src.name) else "dry-run.mp4"
            url = f"https://example.invalid/uploads/reels/{name}"
        else:
            uploads = Path(os.environ.get("UPLOAD_DIRECTORY") or "uploads")
            name = publish.stage(src, uploads)
            url = publish.public_url(cfg, name)
            print(f"staged {uploads / 'reels' / name}\n-> {url}")
        res = await publish.publish_reel(channel, url, a.caption, cfg=cfg, dry_run=dry,
                                         file_path=src if (a.upload_bytes and channel == "facebook_page") else None)
    except PublishError as e:
        print(f"FAILED: {e}")
        return 1
    print(f"{'DRY RUN' if dry else 'PUBLISHED'} {a.channel}: id={res.external_id} {res.permalink or ''}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    pv = sub.add_parser("preview")
    pv.add_argument("--template", choices=templates.TEMPLATES, default="tip")
    pv.add_argument("--out", default="reel-preview")
    pv.add_argument("--photos", nargs="*", default=[])
    pv.add_argument("--music", help="optional royalty-free audio file you have the rights to (nothing is bundled)")
    po = sub.add_parser("post")
    po.add_argument("--file", required=True)
    po.add_argument("--channel", choices=list(CHANNEL_MAP), required=True)
    po.add_argument("--caption", required=True)
    g = po.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--live", action="store_true")
    po.add_argument("--upload-bytes", action="store_true")
    a = ap.parse_args()
    return cmd_preview(a) if a.cmd == "preview" else asyncio.run(cmd_post(a))


if __name__ == "__main__":
    sys.exit(main())
