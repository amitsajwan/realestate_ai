"""Weekly check of the live site the way a search engine reads it (.github/workflows/seo-audit.yml).

    python -m app.modules.seo.audit https://avasetu.in [--max-pages 300]

Reads robots.txt and the sitemap, then up to --max-pages pages from the sitemap (all of them when there are fewer, else an even
spread), and reports:
  errors   (exit 1): a sitemap page that is not a plain 200 (a 5xx or unreadable page is read once more after RETRY_S, so a
           restart during the run is a warning, not a failure), is blocked by robots.txt, says noindex, names another page as
           canonical, has no <title>, or has structured data (JSON-LD) that does not parse; robots.txt without the sitemap
  warnings (exit 0): a long or duplicate title, a missing or odd-length description, not exactly one <h1>, images without alt
The report is printed as Markdown and, on GitHub, added to the job summary. Reads only; standard library and httpx only.
"""
import argparse
import asyncio
import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

import httpx

AGENT = "AvasetuSeoAudit/1.0 (+https://github.com/amitsajwan/realestate_ai)"
TITLE_MAX = 70
DESC_MIN, DESC_MAX = 50, 170
CONCURRENCY = 4
RETRY_S = 30.0       # a page that answered 5xx (or nothing) is read again after this
_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


class _Page(HTMLParser):
    """The parts of a page search engines read first."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.titles: List[str] = []
        self.description: Optional[str] = None
        self.robots = ""
        self.canonical: Optional[str] = None
        self.h1 = 0
        self.img_no_alt = 0
        self.ld: List[str] = []
        self._in: Optional[str] = None
        self._buf: List[str] = []
        self._head = True

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "title" and self._head:
            self._in, self._buf = "title", []
        elif tag == "script" and a.get("type", "").lower() == "application/ld+json":
            self._in, self._buf = "ld", []
        elif tag == "meta":
            name = a.get("name", "").lower()
            if name == "description":
                self.description = a.get("content", "")
            elif name in ("robots", "googlebot"):
                self.robots += " " + a.get("content", "").lower()
        elif tag == "link" and "canonical" in a.get("rel", "").lower().split():
            self.canonical = a.get("href") or None
        elif tag == "h1":
            self.h1 += 1
        elif tag == "img" and "alt" not in a:
            self.img_no_alt += 1
        elif tag == "body":
            self._head = False   # an <svg><title> in the body is not the page title

    def handle_endtag(self, tag):
        if self._in == "title" and tag == "title":
            self.titles.append("".join(self._buf).strip())
            self._in = None
        elif self._in == "ld" and tag == "script":
            self.ld.append("".join(self._buf))
            self._in = None

    def handle_data(self, data):
        if self._in:
            self._buf.append(data)


@dataclass
class Report:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checked: int = 0
    listed: int = 0


def _same(a: str, b: str) -> bool:
    pa, pb = urlparse(a), urlparse(b)
    return (pa.scheme, pa.netloc.lower(), pa.path.rstrip("/") or "/", pa.query) == (pb.scheme, pb.netloc.lower(), pb.path.rstrip("/") or "/", pb.query)


class Robots:
    """robots.txt read the way Googlebot reads it: the `Googlebot` group, else `*`; the longest matching rule wins and Allow
    wins a tie (Python's RobotFileParser takes the first match instead, so `Allow: /` before `Disallow: /studio` hid the block)."""

    def __init__(self, text: str):
        groups: Dict[str, List[Tuple[bool, str]]] = {}
        agents: List[str] = []
        in_rules = False
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            key, val = (x.strip() for x in line.split(":", 1))
            key = key.lower()
            if key == "user-agent":
                if in_rules:
                    agents, in_rules = [], False
                agents.append(val.lower())
                for a in agents:
                    groups.setdefault(a, [])
            elif key in ("allow", "disallow"):
                in_rules = True
                if val:
                    for a in agents:
                        groups[a].append((key == "allow", val))
        self.rules = groups.get("googlebot", groups.get("*", []))

    def can_fetch(self, agent: str, url: str) -> bool:
        path = urlparse(url).path or "/"
        best: Optional[Tuple[int, bool]] = None
        for allow, prefix in self.rules:
            pat = re.escape(prefix.rstrip("$")).replace(r"\*", ".*") + ("$" if prefix.endswith("$") else "")
            if re.match(pat, path):
                cand = (len(prefix), allow)
                if best is None or cand > best:   # longer wins; same length: allow (True) wins
                    best = cand
        return True if best is None else best[1]


def check_page(url: str, status: int, headers: Dict[str, str], html: str, robots: Optional[Robots]) -> Tuple[List[str], List[str], Optional[str]]:
    """(errors, warnings, title) for one sitemap page."""
    errs: List[str] = []
    warns: List[str] = []
    path = urlparse(url).path or "/"
    if robots is not None and not robots.can_fetch("Googlebot", url):
        errs.append(f"`{path}` is in the sitemap but robots.txt blocks it")
    if status != 200:
        errs.append(f"`{path}` answers {status} (sitemap pages must answer 200 without a redirect)")
        return errs, warns, None
    p = _Page()
    p.feed(html)
    if "noindex" in p.robots or "noindex" in (headers.get("x-robots-tag") or "").lower():
        errs.append(f"`{path}` is in the sitemap but says noindex")
    if p.canonical and not _same(p.canonical, url):
        errs.append(f"`{path}` is in the sitemap but names `{p.canonical}` as canonical")
    elif not p.canonical:
        warns.append(f"`{path}` has no canonical link")
    title = p.titles[0] if p.titles else ""
    if not title:
        errs.append(f"`{path}` has no <title>")
    elif len(title) > TITLE_MAX:
        warns.append(f"`{path}` title is {len(title)} characters (Google shows about {TITLE_MAX})")
    for i, block in enumerate(p.ld):
        try:
            json.loads(block)
        except ValueError:
            errs.append(f"`{path}` structured data block {i + 1} is not valid JSON")
    d = (p.description or "").strip()
    if not d:
        warns.append(f"`{path}` has no meta description")
    elif not DESC_MIN <= len(d) <= DESC_MAX:
        warns.append(f"`{path}` description is {len(d)} characters (aim for {DESC_MIN} to {DESC_MAX})")
    if p.h1 != 1:
        warns.append(f"`{path}` has {p.h1} <h1> headings (one is clearest)")
    if p.img_no_alt:
        warns.append(f"`{path}` has {p.img_no_alt} image(s) without alt text")
    return errs, warns, title or None


def parse_sitemap(xml: str) -> List[str]:
    return [(u.findtext(f"{_NS}loc") or "").strip() for u in ET.fromstring(xml).iter(f"{_NS}url") if (u.findtext(f"{_NS}loc") or "").strip()]


def spread(urls: List[str], most: int) -> List[str]:
    """All of them, or `most` evenly spaced so every kind of page in the sitemap is sampled."""
    if len(urls) <= most:
        return urls
    step = len(urls) / most
    return [urls[int(i * step)] for i in range(most)]


async def audit(site: str, max_pages: int = 300, transport: Optional[httpx.AsyncBaseTransport] = None) -> Report:
    site = site.rstrip("/")
    rep = Report()
    async with httpx.AsyncClient(timeout=30, transport=transport, headers={"User-Agent": AGENT}) as c:
        robots: Optional[Robots] = None
        r = await c.get(site + "/robots.txt")
        if r.status_code == 200:
            robots = Robots(r.text)
            if "sitemap:" not in r.text.lower():
                rep.errors.append("robots.txt does not name the sitemap")
        else:
            rep.errors.append(f"robots.txt answers {r.status_code}")
        sm = await c.get(site + "/sitemap.xml")
        if sm.status_code != 200:
            rep.errors.append(f"sitemap.xml answers {sm.status_code}")
            return rep
        urls = parse_sitemap(sm.text)
        root = ET.fromstring(sm.text)
        if root.tag == f"{_NS}sitemapindex":   # one sitemap per Pune place (frontend/app/sitemap.xml): read each of them
            urls = []
            for loc in [(s.findtext(f"{_NS}loc") or "").strip() for s in root.iter(f"{_NS}sitemap")]:
                child = await c.get(loc) if loc else None
                if child is None or child.status_code != 200:
                    rep.errors.append(f"`{loc}` (in sitemap.xml) answers {child.status_code if child is not None else 'nothing'}")
                    continue
                urls.extend(parse_sitemap(child.text))
        rep.listed = len(urls)
        if not urls:
            rep.errors.append("sitemap.xml lists no pages")
            return rep
        gate = asyncio.Semaphore(CONCURRENCY)
        titles: Counter = Counter()

        async def read(u: str):
            async with gate:
                try:
                    res = await c.get(u)
                    return res, None
                except httpx.HTTPError as e:
                    return None, type(e).__name__

        async def one(u: str):
            res, err = await read(u)
            first = None
            if res is None or res.status_code >= 500:   # a restart or a slow backend: Google retries too, so read once more
                first = err or str(res.status_code)
                await asyncio.sleep(RETRY_S)
                res, err = await read(u)
            if res is None:
                return [f"`{urlparse(u).path or '/'}` could not be read ({err}, twice)"], [], None
            errs, warns, title = check_page(u, res.status_code, dict(res.headers), res.text, robots)
            if first is not None and res.status_code < 500:
                warns.append(f"`{urlparse(u).path or '/'}` answered {first}, then {res.status_code} {RETRY_S:.0f} s later")
            return errs, warns, title

        for errs, warns, title in await asyncio.gather(*(one(u) for u in spread(urls, max_pages))):
            rep.errors += errs
            rep.warnings += warns
            rep.checked += 1
            if title:
                titles[title] += 1
        rep.warnings += [f'{n} pages share the title "{t}"' for t, n in titles.items() if n > 1]
    return rep


def markdown(site: str, rep: Report) -> str:
    lines = [f"## SEO audit of {site}", "", f"Checked {rep.checked} of {rep.listed} sitemap pages: "
             f"**{len(rep.errors)} errors**, {len(rep.warnings)} warnings.", ""]
    for head, items in (("Errors", rep.errors), ("Warnings", rep.warnings)):
        if items:
            lines += [f"### {head}", ""] + [f"- {x}" for x in items[:200]]
            if len(items) > 200:
                lines.append(f"- … and {len(items) - 200} more")
            lines.append("")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("site")
    ap.add_argument("--max-pages", type=int, default=300)
    args = ap.parse_args(argv)
    rep = asyncio.run(audit(args.site, args.max_pages))
    text = markdown(args.site.rstrip("/"), rep)
    print(text)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
