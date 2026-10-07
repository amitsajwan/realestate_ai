/*
 * Browser check: optional onboarding extras (photo, logo, Instagram, Facebook) show on the public site as links/images, hostile values are
 * refused, a first listing without photos gets the "Add 3 photos" prompt, and the editor can add photos. Same prereqs as browser-journey.js.
 * Run: node e2e/onboarding-extras.js
 */
const fs = require('fs')
const path = require('path')
const zlib = require('zlib')
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, '.out')
fs.mkdirSync(path.join(OUT, 'shots'), { recursive: true })
const APP = process.env.APP_URL || 'http://localhost:3000'
const API = (process.env.API_URL || 'http://localhost:8000') + '/api/v1'

function writePng(file, rgb) {
  const t = []
  for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0 }
  const crc = (b) => { let r = 0xffffffff; for (const x of b) r = t[(r ^ x) & 255] ^ (r >>> 8); return (r ^ 0xffffffff) >>> 0 }
  const chunk = (type, data) => { const l = Buffer.alloc(4); l.writeUInt32BE(data.length); const td = Buffer.concat([Buffer.from(type), data]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td)); return Buffer.concat([l, td, c]) }
  const w = 96, h = 96, raw = Buffer.alloc((w * 3 + 1) * h)
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const o = y * (w * 3 + 1) + 1 + x * 3; raw[o] = rgb[0]; raw[o + 1] = rgb[1]; raw[o + 2] = rgb[2] }
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 2
  fs.writeFileSync(file, Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]))
}
const PHOTO = path.join(OUT, 'me.png'); writePng(PHOTO, [200, 120, 60])
const LOGO = path.join(OUT, 'logo.png'); writePng(LOGO, [30, 60, 120])
const PHOTO2 = path.join(OUT, 'flat.png'); writePng(PHOTO2, [90, 150, 200])

const phone = '9' + Array.from({ length: 9 }, () => Math.floor(Math.random() * 10)).join('')
const results = []
const log = (ok, name, extra = '') => { results.push(ok); console.log((ok ? 'PASS ' : 'FAIL ') + name + (extra ? '  ' + extra : '')) }

;(async () => {
  const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || 'chrome', headless: true })
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true })
  const page = await ctx.newPage()
  try {
    await page.goto(APP + '/join', { waitUntil: 'networkidle' })
    await page.locator('#phone').fill(phone)
    await page.getByRole('button', { name: 'Send OTP' }).click()
    await page.getByText('Dev only: OTP is').waitFor({ timeout: 15000 })
    await page.getByRole('button', { name: 'Fill it' }).click()
    await page.locator('#name').waitFor({ timeout: 15000 })
    await page.locator('#name').fill('Meera Joshi')
    await page.locator('#city').fill('Pune')
    log(await page.getByText('Optional: make it yours').isVisible(), 'the profile step offers optional photo, logo, Instagram and Facebook')
    await page.getByTestId('extras-your-photo').setInputFiles(PHOTO)
    await page.getByTestId('extras-your-logo').setInputFiles(LOGO)
    await page.locator('#ig').fill('@meera.homes')
    await page.locator('#fb').fill('facebook.com/meerahomes')
    await page.screenshot({ path: path.join(OUT, 'shots', 'extras-1-form.png'), fullPage: true })
    await page.getByRole('button', { name: 'Create my website' }).click()
    await page.getByText('Your website is live').waitFor({ timeout: 30000 })
    const siteUrl = (await page.locator('body').innerText()).match(/http:\/\/localhost:3000\/agent\/[a-z0-9-]+/)[0]
    log(true, 'site created with the extras', siteUrl)

    await page.waitForTimeout(31000) // the public site caches data for 30 s
    await page.goto(siteUrl, { waitUntil: 'networkidle' })
    const html = await page.content()
    log(/href="https:\/\/www\.instagram\.com\/meera\.homes"/.test(html), 'Instagram link is on the public site')
    log(/href="https:\/\/www\.facebook\.com\/meerahomes"/.test(html), 'Facebook link is on the public site')
    log((await page.locator('img[alt="Meera Joshi logo"]').count()) === 1 && (await page.locator('img[alt="Photo of Meera Joshi"]').count()) >= 1, 'photo and logo are shown in the About section')
    await page.screenshot({ path: path.join(OUT, 'shots', 'extras-2-site.png'), fullPage: true })

    // hostile values are refused by the API
    const token = await page.evaluate(() => localStorage.getItem('app_token'))
    const bad = await fetch(API + '/join/site', { method: 'PATCH', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token }, body: JSON.stringify({ facebook_url: 'https://evil.example/x' }) })
    log(bad.status === 422, 'a non-Facebook link is refused (422)', String(bad.status))

    // first listing without photos -> prompt -> editor adds photos
    await page.goto(APP + '/studio/listings/new', { waitUntil: 'networkidle' })
    await page.locator('textarea').fill('2 BHK for sale in Wagholi Pune, 850 sq ft carpet, 58 lakh, ready possession, parking, lift')
    await page.getByRole('button', { name: 'Next', exact: true }).click()
    await page.getByText('Check and confirm').waitFor({ timeout: 30000 })
    await page.getByRole('button', { name: /Confirm & post/ }).click()
    await page.getByText('Your property is ready').waitFor({ timeout: 30000 })
    log(await page.getByText('Add 3 photos to make this post much better').isVisible(), 'a listing posted without photos shows the "Add 3 photos" prompt')
    await page.getByRole('link', { name: 'Add photos' }).first().click()
    await page.waitForURL(/studio\/listings\/[a-f0-9]+$/, { timeout: 15000 })
    await page.getByText('None yet').waitFor({ timeout: 15000 })
    await page.getByTestId('gallery-input').setInputFiles([PHOTO2])
    await page.getByRole('button', { name: /Add 1 photo/ }).click()
    await page.getByText(/Photos added/).waitFor({ timeout: 30000 })
    log((await page.locator('section[aria-label="Photos"]').count()) === 1 && (await page.locator('img[src*="/uploads/images/"]').count()) >= 1, 'the editor uploaded the photo and shows it')
    await page.screenshot({ path: path.join(OUT, 'shots', 'extras-3-editor.png') })
  } catch (e) {
    log(false, 'journey aborted', e.message.split('\n')[0])
    await page.screenshot({ path: path.join(OUT, 'shots', 'extras-ZZ-failure.png') }).catch(() => {})
  }
  await browser.close()
  console.log(results.every(Boolean) ? '\nALL PASSED' : '\nSOME FAILED')
  process.exit(results.every(Boolean) ? 0 : 1)
})()
