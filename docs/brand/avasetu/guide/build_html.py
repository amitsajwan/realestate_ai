"""Build AGENT_GUIDE.html (self-contained, phone-first, Avasetu look) from docs/AGENT_GUIDE.md.

    backend/.venv/Scripts/python.exe docs/brand/avasetu/guide/build_html.py

Handles only the Markdown the guide uses: headings, paragraphs, lists, task lists, tables, quotes, code blocks, <img> tags,
**bold**, *italic*, `code`. Screenshots are shrunk to 520 px wide and embedded as data URIs (the page stays under 4 MB).
"""
import base64
import html
import io
import re
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
DOCS = HERE.parents[2]
MD = DOCS / "AGENT_GUIDE.md"
OUT = HERE / "AGENT_GUIDE.html"
_cache: dict = {}


def data_uri(src: str) -> str:
    if src not in _cache:
        im = Image.open(DOCS / src).convert("RGB")
        w = 520
        if im.width > w:
            im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=68, optimize=True, progressive=True)
        _cache[src] = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    return _cache[src]


def inline(text: str) -> str:
    imgs = []

    def keep_img(m):
        alt = re.search(r'alt="([^"]*)"', m.group(0))
        src = re.search(r'src="([^"]*)"', m.group(0)).group(1)
        a = html.escape(alt.group(1) if alt else "")
        imgs.append(f'<figure class="shot"><img src="{data_uri(src)}" alt="{a}" loading="lazy"><figcaption>{a}</figcaption></figure>')
        return f"\x00{len(imgs) - 1}\x00"

    text = re.sub(r"<img [^>]*>", keep_img, text)
    text = text.replace("<br>", "\x01")
    t = html.escape(text, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"(https://[A-Za-z0-9./_?=&%-]+[A-Za-z0-9/])", r'<a href="\1">\1</a>', t)
    t = t.replace("\x01", "")
    for i, tag in enumerate(imgs):
        t = t.replace(f"\x00{i}\x00", tag)
    # consecutive figures become one swipeable strip
    t = re.sub(r"((?:<figure class=\"shot\">.*?</figure>\s*){1,})", lambda m: f'<div class="strip">{m.group(1)}</div>', t)
    return t


def convert(md: str) -> str:
    out, lines, i = [], md.splitlines(), 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        if ln.startswith("```"):
            j = i + 1
            while not lines[j].startswith("```"):
                j += 1
            out.append("<pre><code>" + html.escape("\n".join(lines[i + 1:j])) + "</code></pre>")
            i = j + 1
            continue
        m = re.match(r"(#{1,4}) (.*)", ln)
        if m:
            lvl, txt = len(m.group(1)), m.group(2)
            slug = re.sub(r"[^a-z0-9]+", "-", txt.lower()).strip("-")[:40]
            out.append(f'<h{lvl} id="{slug}">{inline(txt)}</h{lvl}>')
            i += 1
            continue
        if ln.strip() == "---":
            out.append("<hr>")
            i += 1
            continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head, body = rows[0], [r for r in rows[1:] if not re.match(r"^:?-+:?$", r[0])]
            th = "".join(f"<th>{inline(c)}</th>" for c in head)
            trs = "".join("<tr>" + "".join(f'<td data-h="{html.escape(head[k] if k < len(head) else "")}">{inline(c)}</td>'
                                            for k, c in enumerate(r)) + "</tr>" for r in body)
            out.append(f'<div class="table"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>')
            continue
        if ln.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i][1:].strip())
                i += 1
            items, para = [], []
            for b in buf:
                mm = re.match(r"\d+\. (.*)", b)
                if mm:
                    items.append(mm.group(1))
                elif items and b and not re.match(r"\d+\.", b):
                    items[-1] += " " + b
                else:
                    para.append(b)
            inner = "".join(f"<p>{inline(p)}</p>" for p in para if p)
            if items:
                inner += "<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>"
            out.append(f"<blockquote>{inner}</blockquote>")
            continue
        if re.match(r"(\d+\.|-) ", ln):
            ordered = bool(re.match(r"\d+\.", ln))
            items = []
            while i < len(lines) and (re.match(r"(\d+\.|-) ", lines[i]) or (lines[i].startswith("   ") and items)):
                cur = lines[i]
                if re.match(r"(\d+\.|-) ", cur):
                    items.append(re.sub(r"^(\d+\.|-) ", "", cur))
                elif cur.strip().startswith("```"):
                    j = i + 1
                    while not lines[j].strip().startswith("```"):
                        j += 1
                    items[-1] += "\x02" + html.escape("\n".join(x.strip() for x in lines[i + 1:j])) + "\x03"
                    i = j
                elif cur.strip().startswith("- "):
                    items[-1] += "\x04" + cur.strip()[2:]
                else:
                    items[-1] += " " + cur.strip()
                i += 1
            lis = []
            for it in items:
                task = re.match(r"\[ \] (.*)", it)
                body = task.group(1) if task else it
                parts = re.split(r"(\x02.*?\x03)", body, flags=re.S)
                rendered = ""
                for p in parts:
                    if p.startswith("\x02"):
                        rendered += "<pre><code>" + p[1:-1] + "</code></pre>"
                    else:
                        segs = p.split("\x04")
                        rendered += inline(segs[0])
                        if len(segs) > 1:
                            rendered += "<ul>" + "".join(f"<li>{inline(s)}</li>" for s in segs[1:]) + "</ul>"
                if task:
                    lis.append(f'<li class="task"><label><input type="checkbox"> <span>{rendered}</span></label></li>')
                else:
                    lis.append(f"<li>{rendered}</li>")
            tag = "ol" if ordered else "ul"
            cls = ' class="checklist"' if any("task" in x for x in lis) else ""
            out.append(f"<{tag}{cls}>{''.join(lis)}</{tag}>")
            continue
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(r"(#{1,4} |\||>|```|(\d+\.|-) |---$)", lines[i]):
            buf.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(buf))}</p>")
    return "\n".join(out)


CSS = """
:root{--navy:#102340;--gold:#F0B13B;--cream:#FBF6EA;--ink:#14213a;--muted:#5b6475;--line:#e6dfcd;--card:#fff;--ok:#1b7f4b;--warn:#a05a00;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--cream:#0d1628;--ink:#eef1f6;--muted:#a9b2c3;--line:#26324a;--card:#15213a;--ok:#52c58a;--warn:#f0b13b;color-scheme:dark}}
:root[data-theme=dark]{--cream:#0d1628;--ink:#eef1f6;--muted:#a9b2c3;--line:#26324a;--card:#15213a;--ok:#52c58a;--warn:#f0b13b;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--cream);color:var(--ink);font:16px/1.6 Hind,"Noto Sans","Segoe UI",system-ui,sans-serif}
header.top{background:var(--navy);color:#fff;padding:calc(18px + env(safe-area-inset-top,0px)) 16px 22px}
.brand{display:flex;align-items:center;gap:10px;font:800 26px/1 "Baloo 2",Hind,system-ui,sans-serif}
.brand svg{width:38px;height:38px}
.tag{color:var(--gold);font-weight:600;margin:6px 0 0}
main{max-width:760px;margin:0 auto;padding:8px 16px 48px}
h1{font:800 30px/1.15 "Baloo 2",Hind,system-ui,sans-serif;margin:18px 0 6px}
h2{font:800 23px/1.2 "Baloo 2",Hind,system-ui,sans-serif;margin:34px 0 8px;padding-top:6px;border-top:4px solid var(--gold);display:inline-block}
h3{font-size:18px;margin:24px 0 6px}
p,li{overflow-wrap:anywhere}
a{color:inherit;text-decoration-color:var(--gold);text-decoration-thickness:2px}
code{background:rgba(16,35,64,.08);padding:1px 5px;border-radius:5px;font-size:.9em}
pre{background:var(--navy);color:#f6f1e3;padding:12px;border-radius:10px;overflow-x:auto}
pre code{background:none;color:inherit;padding:0}
blockquote{margin:12px 0;padding:12px 14px;background:var(--card);border-left:5px solid var(--gold);border-radius:10px}
blockquote ol{padding-left:20px}
hr{border:0;margin:20px 0}
ul.checklist{list-style:none;padding:0}
ul.checklist li{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:6px 0;padding:8px 10px}
ul.checklist label{display:flex;gap:10px;align-items:flex-start;cursor:pointer}
ul.checklist input{width:22px;height:22px;margin-top:2px;accent-color:var(--navy);flex:none}
ul.checklist input:checked+span{text-decoration:line-through;color:var(--muted)}
.table{overflow-x:auto;margin:10px 0}
table{border-collapse:collapse;width:100%;background:var(--card);border-radius:10px;overflow:hidden}
th{background:var(--navy);color:#fff;text-align:left}
th,td{padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}
@media (max-width:600px){table,thead,tbody,tr,td{display:block;width:100%}thead{display:none}
 tr{border:1px solid var(--line);border-radius:12px;margin:10px 0;background:var(--card)}td{border:0;padding:6px 12px}
 td::before{content:attr(data-h);display:block;font-size:12px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}}
.strip{display:flex;gap:10px;overflow-x:auto;padding:8px 2px 12px;scroll-snap-type:x mandatory}
figure.shot{margin:0;flex:0 0 auto;width:min(56vw,230px);scroll-snap-align:start}
figure.shot img{width:100%;height:auto;border-radius:16px;border:3px solid var(--navy);display:block;background:#fff}
figcaption{font-size:13px;color:var(--muted);text-align:center;margin-top:4px}
.legend{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}.legend span{background:var(--card);border:1px solid var(--line);border-radius:999px;padding:3px 10px;font-size:14px}
footer{text-align:center;color:var(--muted);font-size:14px;padding:24px 16px calc(24px + env(safe-area-inset-bottom,0px))}
"""
MARK = ('<svg viewBox="0 0 512 512" aria-hidden="true"><rect width="512" height="512" rx="256" fill="#F0B13B"/>'
        '<path d="M96 222 L256 98 L416 222" fill="none" stroke="#102340" stroke-width="36" stroke-linecap="round" stroke-linejoin="round"/>'
        '<path d="M120 396 L120 290 Q256 150 392 290 L392 396" fill="none" stroke="#102340" stroke-width="40" stroke-linecap="round"/>'
        '<path d="M120 330 L392 330" stroke="#102340" stroke-width="24" stroke-linecap="round"/>'
        '<path d="M188 330 L188 396 M256 330 L256 396 M324 330 L324 396" stroke="#102340" stroke-width="18" stroke-linecap="round"/></svg>')


def main() -> None:
    md = MD.read_text(encoding="utf8")
    md = re.sub(r"^# .*\n", "", md, count=1)  # the title goes in the header
    body = convert(md)
    page = f"""<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Avasetu Agent Guide</title>
<meta name="description" content="Show Avasetu to a Pune agent, onboard him, his first listing and leads, the day-7 check-in and troubleshooting.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@800&family=Hind:wght@400;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
<header class="top"><div class="brand">{MARK}<span>Avasetu</span></div><p class="tag">Agent guide: showcase, onboard, first leads</p></header>
<main>
<div class="legend"><span>✅ run on the live site</span><span>⚠️ not run, instructions only</span></div>
{body}
</main>
<footer>Avasetu · Your bridge to the right home · आवासेतु</footer>
"""
    OUT.write_text(page, encoding="utf8")
    print(f"{OUT.name}: {OUT.stat().st_size / 1e6:.2f} MB, {len(_cache)} images")


if __name__ == "__main__":
    main()
