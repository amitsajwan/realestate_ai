"""Listing showcase admin (labelled SAMPLE homes for the Page and Instagram).

  python scripts/showcase_admin.py preview --out DIR [--slug SLUG]        render everything + contact sheets (no network, no database)
  python scripts/showcase_admin.py post --slug SLUG --channel instagram|facebook|both [--polish]
        dry run by default (SOCIAL_DRY_RUN is on unless set to false); a real post needs META_* tokens and PUBLIC_MEDIA_BASE_URL (https)
  python scripts/showcase_admin.py schedule-plan [--start 2026-10-06] [--days 14]   print a proposed posting plan (posts nothing)
  python scripts/showcase_admin.py list
Run on the server:  docker compose exec -T -e PYTHONPATH=. backend python scripts/showcase_admin.py post --slug kharadi-2bhk-ready --channel instagram
"""
import argparse
import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.modules.showcase import captions, plan, publish, render, samples  # noqa: E402


def cmd_list(_a) -> int:
    for h in samples.HOMES:
        print(f"{h.slug:42} {h.title:24} {h.carpet_text:10} {h.price_text:10} {h.possession}")
    return 0


def cmd_preview(a) -> int:
    out = Path(a.out)
    homes = [samples.get(a.slug)] if a.slug else samples.HOMES
    covers, fbs, stories = [], [], []
    for h in homes:
        files = render.write_home(h, out)
        cars = [render.Image.open(p).convert("RGB") for p in files["carousel"]]
        render.contact_sheet(cars, 5, 340).save(out / f"sheet-{h.slug}.jpg", quality=86)
        covers.append(cars[0])
        fbs.append(render.Image.open(files["facebook"][0]).convert("RGB"))
        stories.append(render.Image.open(files["scenes"][0]).convert("RGB"))
        (out / h.slug / "caption-instagram.txt").write_text(captions.instagram_caption(h), encoding="utf-8")
        (out / h.slug / "caption-facebook.txt").write_text(captions.facebook_caption(h), encoding="utf-8")
        print(f"rendered {h.slug}")
    if len(homes) > 1:
        render.contact_sheet(covers, 5, 360).save(out / "sheet-covers.jpg", quality=86)
        render.contact_sheet(fbs, 3, 560).save(out / "sheet-facebook.jpg", quality=86)
        render.contact_sheet(stories, 9, 220).save(out / "sheet-story-covers.jpg", quality=86)
    print(f"wrote {out}")
    return 0


def cmd_post(a) -> int:
    llm = None
    if a.polish:
        from app.platform.llm import default_llm
        llm = default_llm()
    try:
        results = asyncio.run(publish.publish_showcase(a.slug, a.channel, llm=llm))
    except (publish.ShowcaseError, KeyError) as e:
        print(f"refused: {e}")
        return 1
    for r in results:
        print(f"[{r.channel}] {'DRY RUN' if r.dry_run else 'POSTED'} id={r.external_id} permalink={r.permalink or '-'}")
        print("  images:", *r.image_urls, sep="\n    ")
        print("  caption:\n" + "\n".join("    " + ln for ln in r.caption.splitlines()))
    return 0


def cmd_plan(a) -> int:
    start = date.fromisoformat(a.start) if a.start else date.today() + timedelta(days=1)
    for s in plan.schedule_plan(start, a.days):
        h = samples.get(s.slug)
        print(f"{s.day:%a %d %b}  {s.channel:9} {s.locality:14} {h.title:20} {h.possession.split(',')[0]:16} {s.slug}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    p = sub.add_parser("preview")
    p.add_argument("--out", required=True)
    p.add_argument("--slug")
    p.set_defaults(fn=cmd_preview)
    p = sub.add_parser("post")
    p.add_argument("--slug", required=True)
    p.add_argument("--channel", choices=["instagram", "facebook", "both"], required=True)
    p.add_argument("--polish", action="store_true", help="optional LLM re-wording (guarded)")
    p.set_defaults(fn=cmd_post)
    p = sub.add_parser("schedule-plan")
    p.add_argument("--start")
    p.add_argument("--days", type=int, default=14)
    p.set_defaults(fn=cmd_plan)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
