/*
 * Real-browser journey (phone viewport, system Chrome):
 *   join -> site -> add listing (typed + photo) -> AI review -> publish -> public site + listing page
 *   -> buyer enquiry (Instagram source) -> lead inbox + timeline.
 *
 * Prereqs: MongoDB      docker run -d --name pai-mongo -p 27017:27017 mongo:7
 *          backend      cd backend && DATABASE_NAME=propertyai_browser PYTHONPATH=. .venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
 *                       (JOIN_MODE=otp, the default, so the OTP is returned as dev_code)
 *          frontend     cd frontend && npx next dev -p 3000
 * Run:     node e2e/browser-journey.js      (screenshots land in e2e/.out/shots; set PW_CHANNEL=msedge to use Edge)
 */
const path = require('path')
const fs = require('fs')
const zlib = require('zlib')
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, '.out')
fs.mkdirSync(path.join(OUT, 'shots'), { recursive: true })
const APP = process.env.APP_URL || 'http://localhost:3000'

function writePng(file) {
  const t = []
  for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0 }
  const crc = (b) => { let r = 0xffffffff; for (const x of b) r = t[(r ^ x) & 255] ^ (r >>> 8); return (r ^ 0xffffffff) >>> 0 }
  const chunk = (type, data) => {
    const l = Buffer.alloc(4); l.writeUInt32BE(data.length)
    const td = Buffer.concat([Buffer.from(type), data]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td))
    return Buffer.concat([l, td, c])
  }
  const w = 64, h = 64, raw = Buffer.alloc((w * 3 + 1) * h)
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const o = y * (w * 3 + 1) + 1 + x * 3; raw[o] = 200; raw[o + 1] = 60; raw[o + 2] = 60 }
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 2
  fs.writeFileSync(file, Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]))
}
const PHOTO = path.join(OUT, 'flat.png')
writePng(PHOTO)

const phone = '9' + Array.from({ length: 9 }, () => Math.floor(Math.random() * 10)).join('')
const results = []
let n = 0
const log = (ok, name, extra = '') => { results.push(ok); console.log((ok ? 'PASS ' : 'FAIL ') + name + (extra ? '  ' + extra : '')) }

;(async () => {
  const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || 'chrome', headless: true })
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true })
  const page = await ctx.newPage()
  const errors = []
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message))
  page.on('response', (r) => { if (r.status() >= 400 && r.url().includes('/api/')) errors.push(`HTTP ${r.status()} ${r.request().method()} ${r.url().replace(/^.*\/api\/v1/, '')}`) })
  const shot = (name, p = page) => p.screenshot({ path: path.join(OUT, 'shots', `${String(++n).padStart(2, '0')}-${name}.png`) })

  try {
    // 1. join: phone -> OTP (dev code) -> profile -> live site
    await page.goto(APP + '/join', { waitUntil: 'networkidle' })
    await shot('join-phone')
    await page.locator('#phone').fill(phone)
    await page.getByRole('button', { name: 'Send OTP' }).click()
    await page.getByText('Dev only: OTP is').waitFor({ timeout: 15000 })
    await page.getByRole('button', { name: 'Fill it' }).click()
    await page.locator('#name').waitFor({ timeout: 15000 })
    log(true, 'OTP login reaches profile step')
    await page.locator('#name').fill('Rahul Sharma')
    await page.locator('#city').fill('Pune')
    await shot('join-profile')
    await page.getByRole('button', { name: 'Create my website' }).click()
    await page.getByText('Your website is live').waitFor({ timeout: 20000 })
    await shot('join-done')
    const m = (await page.locator('body').innerText()).match(/http:\/\/localhost:3000\/agent\/[a-z0-9-]+/)
    log(!!m, 'site created and link shown', m && m[0])
    const siteUrl = m[0]

    // 2. add listing: typed description + photo -> AI draft -> review -> confirm
    await page.goto(APP + '/studio/listings/new', { waitUntil: 'networkidle' })
    await page.locator('textarea').fill('2 BHK for sale in Baner Pune, 1100 sq ft carpet, 85 lakh, ready possession, 3rd floor of 12, semi furnished, parking, lift, gym')
    await page.locator('input[type=file]').first().setInputFiles(PHOTO)
    await page.waitForTimeout(1500)
    await shot('new-listing-capture')
    await page.getByRole('button', { name: 'Next', exact: true }).click()
    await page.getByText('Check and confirm').waitFor({ timeout: 30000 })
    await shot('review')
    const review = await page.locator('input,textarea').evaluateAll((els) => els.map((e) => e.value).join(' | '))
    log(/Baner/i.test(review) && /85/.test(review), 'AI draft fills Baner + price in review')
    await page.getByRole('button', { name: /Confirm & post/ }).click()
    await page.getByText('Your property is ready').waitFor({ timeout: 30000 })
    await shot('posted')
    log(true, 'listing published from the app')

    // 3. public site + listing page
    await page.goto(siteUrl, { waitUntil: 'networkidle' })
    await shot('public-site')
    log(/Baner/i.test(await page.locator('body').innerText()), 'public site shows the listing')
    const href = await page.locator('a[href*="/listings/"]').first().getAttribute('href')
    await page.goto(new URL(href, APP).toString(), { waitUntil: 'networkidle' })
    await shot('public-listing')
    log(/1100|1,100|85 L/i.test(await page.locator('body').innerText()), 'listing page shows facts')

    // 4. buyer (separate browser context = separate anonymous visitor) arrives from Instagram and enquires
    const buyer = await browser.newContext({ viewport: { width: 390, height: 844 }, userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' })
    const bp = await buyer.newPage()
    bp.on('response', (r) => { if (r.status() >= 400 && r.url().includes('/api/')) errors.push(`buyer HTTP ${r.status()} ${r.request().method()} ${r.url().replace(/^.*\/api\/v1/, '')}`) })
    await bp.goto(page.url() + '?src=instagram', { waitUntil: 'networkidle' })
    await bp.waitForTimeout(1500)
    await bp.locator('input[type=tel], input[name=phone]').first().fill('98765 43210')
    await bp.getByLabel(/name/i).first().fill('Amit Buyer')
    await bp.getByLabel(/message/i).first().fill('Is this still available?')
    await bp.locator('input[type=checkbox]').first().check()
    await shot('buyer-form', bp)
    await bp.getByRole('button', { name: /send|enquire|submit|contact/i }).last().click()
    await bp.waitForTimeout(2500)
    await shot('buyer-sent', bp)
    log(/thank|received|sent|will contact|success/i.test(await bp.locator('body').innerText()), 'buyer enquiry submitted')

    // 5. agent lead inbox + timeline
    await page.goto(APP + '/studio/leads', { waitUntil: 'networkidle' })
    await page.waitForTimeout(1500)
    await shot('leads')
    log(/Amit Buyer/.test(await page.locator('body').innerText()), 'lead appears in the agent inbox')
    await page.getByText('Amit Buyer').first().click()
    await page.waitForURL(/studio\/leads\/[a-f0-9]+/, { timeout: 15000 })
    await page.waitForTimeout(1500)
    await shot('lead-detail')
    log(/instagram/i.test(await page.locator('body').innerText()), 'lead timeline shows Instagram source')
  } catch (e) {
    log(false, 'journey aborted', e.message.split('\n')[0])
    await page.screenshot({ path: path.join(OUT, 'shots', 'ZZ-failure.png') }).catch(() => {})
    console.log('URL at failure:', page.url())
  }
  console.log('\nAPI errors seen:', errors.length ? '' : 'none')
  ;[...new Set(errors)].slice(0, 20).forEach((e) => console.log('  ', e))
  await browser.close()
  console.log(results.every(Boolean) ? '\nALL PASSED' : '\nSOME FAILED')
  process.exit(results.every(Boolean) ? 0 : 1)
})()
