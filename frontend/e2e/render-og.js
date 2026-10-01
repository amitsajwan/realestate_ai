/* Renders the agent-pilot share card (1200x630) from inline HTML in the brand look. Run: node e2e/render-og.js
   Note: public/brand/og-landing.jpg is now the Avasetu share image (docs/brand/avasetu/og.png); running this replaces it. */
const path = require('path')
const { chromium } = require('playwright-core')
const OUT = path.join(__dirname, '..', 'public', 'brand', 'og-landing.jpg')
const LOGO = 'data:image/png;base64,' + require('fs').readFileSync(path.join(__dirname, '..', 'public', 'brand', 'mark.png')).toString('base64')
const html = `<!doctype html><meta charset="utf-8"><style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;700;800&display=swap');
*{box-sizing:border-box;margin:0}
body{width:1200px;height:630px;font-family:Poppins,Arial,sans-serif;background:linear-gradient(160deg,#0f2340,#183a5d);color:#fff;display:flex;align-items:center;padding:0 70px;gap:50px;overflow:hidden}
.l{flex:1}.brand{display:flex;align-items:center;gap:14px;font-weight:700;font-size:28px;color:#f0b440}
.brand img{width:52px;height:52px;border-radius:50%}
h1{font-size:58px;line-height:1.1;font-weight:800;margin-top:26px}
h1 b{background:#f0b440;color:#0f2340;padding:0 14px;border-radius:12px}
p{font-size:28px;margin-top:26px;color:#e8eef6;font-weight:500}
.pill{display:inline-block;margin-top:30px;background:#f0b440;color:#0f2340;font-weight:800;font-size:26px;padding:14px 30px;border-radius:14px}
.ph{width:340px;background:#050d1a;border-radius:44px;padding:12px;box-shadow:0 30px 60px rgba(0,0,0,.5)}
.s{background:#fbf6ea;border-radius:34px;padding:16px;color:#0f2340}
.c{background:#fff;border-radius:16px;padding:12px;font-size:17px;color:#334}
.c b.i{background:#f0b440;padding:2px 8px;border-radius:6px;font-weight:800}
.card{margin-top:14px;background:#fff;border:1px solid #ead9ae;border-radius:18px;padding:16px}
.hot{float:right;background:#c2410c;color:#fff;border-radius:99px;padding:3px 12px;font-weight:800;font-size:15px}
.card h3{font-size:22px}.card small{display:block;margin-top:6px;font-size:15px;color:#445;line-height:1.35}
.ch{margin-top:10px;display:flex;gap:6px;flex-wrap:wrap}.ch span{background:#e6f4f1;color:#0b5f56;border-radius:99px;padding:3px 10px;font-size:14px;font-weight:700}
.btns{display:flex;gap:8px;margin-top:12px}.btns span{flex:1;text-align:center;border-radius:10px;padding:9px;color:#fff;font-weight:700;font-size:16px}
</style>
<div class="l"><div class="brand"><img src="${LOGO}">Avasetu</div>
<h1>A buyer comments <b>INTERESTED</b>.<br>Who are they?</h1>
<p>Every enquiry becomes a lead card. Free invite-only pilot for Pune agents.</p>
<span class="pill">Request an invite</span></div>
<div class="ph"><div class="s"><div class="c"><b>Sample buyer</b> <b class="i">INTERESTED</b></div>
<div class="card"><span class="hot">HOT</span><h3>Sample buyer</h3><small>Wants a 2 BHK in Baner, 80 L to 1.2 Cr, ready in 1-3 months.</small>
<div class="ch"><span>2 BHK</span><span>Baner</span><span>Home loan</span></div>
<div class="btns"><span style="background:#0f2340">Call</span><span style="background:#14877b">WhatsApp</span></div></div></div></div>`
;(async () => {
  const b = await chromium.launch({ channel: 'chrome', headless: true })
  const pg = await b.newPage({ viewport: { width: 1200, height: 630 } })
  await pg.setContent(html, { waitUntil: 'networkidle' })
  await pg.screenshot({ path: OUT, type: 'jpeg', quality: 85 })
  await b.close()
  console.log('wrote', OUT)
})()
