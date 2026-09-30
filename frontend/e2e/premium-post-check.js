/*
 * Browser check (phone viewport, system Chrome): voice shows as a disabled Premium feature; the posted listing's marketing pack and
 * the "Post to PUNE Property" panel carry no phone number or personal name, and a spoken/recorded upload is refused by the server.
 * Same prereqs as browser-journey.js. Run: node e2e/premium-post-check.js
 */
const fs = require('fs')
const path = require('path')
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, '.out', 'shots')
fs.mkdirSync(OUT, { recursive: true })
const APP = process.env.APP_URL || 'http://localhost:3000'
const API = (process.env.API_URL || 'http://localhost:8000') + '/api/v1'
const phone = '9' + Array.from({ length: 9 }, () => Math.floor(Math.random() * 10)).join('')
const results = []
const log = (ok, name, extra = '') => { results.push(ok); console.log((ok ? 'PASS ' : 'FAIL ') + name + (extra ? '  ' + extra : '')) }

;(async () => {
  const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || 'chrome', headless: true })
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true })
  const page = await ctx.newPage()
  const shot = (n, full = false) => page.screenshot({ path: path.join(OUT, `pp-${n}.png`), fullPage: full })
  try {
    await page.goto(APP + '/join', { waitUntil: 'networkidle' })
    await page.locator('#phone').fill(phone)
    await page.getByRole('button', { name: 'Send OTP' }).click()
    await page.getByText('Dev only: OTP is').waitFor({ timeout: 15000 })
    await page.getByRole('button', { name: 'Fill it' }).click()
    await page.locator('#name').waitFor({ timeout: 15000 })
    await page.locator('#name').fill('Amit Sajwan')
    await page.locator('#city').fill('Pune')
    await page.getByRole('button', { name: 'Create my website' }).click()
    await page.getByText('Your website is live').waitFor({ timeout: 20000 })
    const token = await page.evaluate(() => localStorage.getItem('app_token'))

    await page.goto(APP + '/studio/listings/new', { waitUntil: 'networkidle' })
    const mic = page.getByRole('button', { name: /Voice listing \(Premium\)/ })
    log((await mic.count()) === 1 && await mic.isDisabled(), 'voice is shown as a disabled mic labelled Premium')
    log(await page.getByText('Premium', { exact: true }).isVisible() && (await page.getByText('Tap to speak').count()) === 0, 'with a Premium badge and no "Tap to speak"')
    await shot('1-capture')

    const fd = new FormData()
    fd.append('audio', new Blob([Buffer.from('1234')], { type: 'audio/webm' }), 'n.webm')
    const r = await fetch(API + '/listings/ai/draft', { method: 'POST', headers: { Authorization: 'Bearer ' + token }, body: fd })
    log(r.status === 403 && /Premium/.test(JSON.stringify(await r.json())), 'the server refuses a voice upload (403, Premium) so nothing can be spent on it', String(r.status))

    await page.locator('textarea').fill('2 BHK for sale in Kharadi Pune, 1100 sq ft carpet, 85 lakh, ready possession, parking, lift, gym')
    await page.getByRole('button', { name: 'Next', exact: true }).click()
    await page.getByText('Check and confirm').waitFor({ timeout: 30000 })
    await page.getByRole('button', { name: /Confirm & post/ }).click()
    await page.getByText('Your property is ready').waitFor({ timeout: 30000 })
    await page.waitForTimeout(6000)
    await shot('2-posted', true)

    const body = await page.locator('body').innerText()
    log(!/\+?91\d{10}|\b[6-9]\d{9}\b/.test(body.replace(/\d{6,}[a-f0-9]{20,}/g, '')), 'the posted screen shows no phone number', '')
    log(!/Amit Sajwan/.test(body.split('Your property is ready')[1] || ''), 'and no personal agent name in the post pack area')
    log(/PUNE Property team/.test(body), 'the pack is signed by the PUNE Property team')

    const listings = await (await fetch(API + '/listings', { headers: { Authorization: 'Bearer ' + token } })).json()
    const id = (listings.items || listings)[0].id
    const pack = await (await fetch(`${API}/listings/${id}/marketing`, { headers: { Authorization: 'Bearer ' + token } })).json()
    const text = JSON.stringify(pack)
    log(!/\b[6-9]\d{9}\b/.test(text.replace(/[a-f0-9]{24,}/g, '')) && !/Amit Sajwan/.test(text), 'the marketing pack API has no phone number or personal name')
    log(/Comment INTERESTED/.test(pack.instagram.caption) && /Comment INTERESTED/.test(pack.facebook.post), 'captions ask buyers to Comment INTERESTED')
    fs.writeFileSync(path.join(OUT, 'pp-pack.json'), JSON.stringify(pack, null, 2))
    for (const im of pack.instagram.images.slice(0, 1)) log(!!im.url, 'cover card url present', im.url)
    fs.writeFileSync(path.join(OUT, 'pp-cover-url.txt'), pack.instagram.images[0].url)
  } catch (e) {
    log(false, 'journey aborted', e.message.split('\n')[0])
    await page.screenshot({ path: path.join(OUT, 'pp-ZZ-failure.png') }).catch(() => {})
  }
  await browser.close()
  console.log(results.every(Boolean) ? '\nALL PASSED' : '\nSOME FAILED')
  process.exit(results.every(Boolean) ? 0 : 1)
})()
