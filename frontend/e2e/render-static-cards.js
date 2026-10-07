/*
 * Renders the Avasetu brand cards whose text needs proper Devanagari shaping (Hindi / Marathi) with Chrome, which shapes conjuncts
 * correctly (the Pillow renderer on the server does not). Output: backend/app/modules/marketing/static_cards/<slug>.jpg, which brand_posts.py uses
 * in preference to its own renderer.
 * Usage: node e2e/render-static-cards.js <cards.json>     (cards.json: [{slug,kicker,title,points[]}])
 */
const fs = require('fs')
const path = require('path')
const { chromium } = require('playwright-core')

const ROOT = path.join(__dirname, '..', '..')
const FONT_DIR = path.join(ROOT, 'backend', 'app', 'modules', 'marketing', 'fonts')
const LOGO = path.join(ROOT, 'backend', 'app', 'modules', 'marketing', 'assets', 'avasetu-mark.png')
const OUT = path.join(ROOT, 'backend', 'app', 'modules', 'marketing', 'static_cards')
const LOGO_URI = 'data:image/png;base64,' + fs.readFileSync(LOGO).toString('base64')
const url = (p) => 'file:///' + p.replace(/\\/g, '/')
const esc = (s) => s.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]))

const skyline = () => {
  const towers = [[0, 46, 70], [78, 74, 60], [146, 58, 80], [234, 92, 64], [306, 64, 72], [386, 84, 60], [454, 52, 84], [546, 78, 66], [620, 96, 62], [690, 60, 76], [774, 80, 64], [846, 66, 70]]
  const g = towers.map(([x, h, w], i) => {
    const win = [0, 1, 2].flatMap((r) => [0, 1].map((c) => ((i + r * 2 + c) % 3 !== 0 ? `<rect x="${x + 10 + c * 24}" y="${100 - h + 10 + r * 18}" width="8" height="10" fill="#f0b440" opacity="0.7"/>` : ''))).join('')
    return `<rect x="${x}" y="${100 - h}" width="${w}" height="${h}" fill="#09152c"/>${win}`
  }).join('')
  return `<svg viewBox="0 0 920 100" preserveAspectRatio="none" style="position:absolute;left:0;right:0;bottom:0;width:100%;height:170px">${g}</svg>`
}

const html = (c) => `<!doctype html><meta charset="utf-8"><style>
@font-face{font-family:P;font-weight:400;src:url("${url(path.join(FONT_DIR, 'Poppins-Regular.ttf'))}")}
@font-face{font-family:P;font-weight:500;src:url("${url(path.join(FONT_DIR, 'Poppins-Medium.ttf'))}")}
@font-face{font-family:P;font-weight:600;src:url("${url(path.join(FONT_DIR, 'Poppins-SemiBold.ttf'))}")}
@font-face{font-family:P;font-weight:700;src:url("${url(path.join(FONT_DIR, 'Poppins-Bold.ttf'))}")}
*{box-sizing:border-box;margin:0}
body{width:1080px;height:1080px;position:relative;overflow:hidden;font-family:P,'Nirmala UI','Noto Sans Devanagari',sans-serif;color:#fff;background:linear-gradient(#102340,#183a5d)}
.wrap{position:absolute;left:84px;right:84px;top:84px}
.chip{display:inline-block;background:#f0b440;color:#18202c;font-weight:600;font-size:28px;padding:14px 26px;border-radius:99px}
h1{font-size:66px;line-height:1.28;font-weight:700;margin:34px 0 24px}
ol{list-style:none;padding:0}
li{display:flex;gap:22px;align-items:flex-start;font-size:37px;line-height:1.42;font-weight:500;margin-bottom:14px}
.n{flex:none;width:42px;height:42px;border-radius:50%;background:#f0b440;color:#18202c;font-weight:700;font-size:26px;display:flex;align-items:center;justify-content:center;margin-top:9px}
.foot{position:absolute;left:84px;bottom:84px;display:flex;align-items:center;gap:20px}
.foot img{width:88px;height:88px;border-radius:50%}
.b{color:#f0b440;font-weight:600;font-size:34px;line-height:1.2}.t{color:#d6dae4;font-weight:500;font-size:26px}
</style><body>${skyline()}
<div class="wrap"><span class="chip">${esc(c.kicker)}</span><h1>${esc(c.title)}</h1>
<ol>${c.points.map((p, i) => `<li><span class="n">${i + 1}</span><span>${esc(p)}</span></li>`).join('')}</ol></div>
<div class="foot"><img src="${LOGO_URI}"><div><div class="b">Avasetu</div><div class="t">Your bridge to the right home</div></div></div></body>`

;(async () => {
  const cards = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'))
  fs.mkdirSync(OUT, { recursive: true })
  const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || 'chrome', headless: true })
  const page = await browser.newPage({ viewport: { width: 1080, height: 1080 } })
  for (const c of cards) {
    await page.setContent(html(c), { waitUntil: 'load' })
    await page.evaluate(() => document.fonts.ready)
    await page.waitForTimeout(300)
    const file = path.join(OUT, c.slug + '.jpg')
    await page.screenshot({ path: file, type: 'jpeg', quality: 88 })
    console.log('rendered', c.slug, fs.statSync(file).size, 'bytes')
  }
  await browser.close()
})().catch((e) => { console.error('FAILED', e.message); process.exit(1) })
