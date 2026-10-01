/*
 * Visual + behaviour check of the branded agent site (phone viewport, system Chrome). Prereqs as browser-journey.js; the agent must
 * already have sample listings (backend/scripts/seed_samples.py). Usage: node e2e/site-brand-check.js <agent-slug>
 */
const fs = require('fs')
const path = require('path')
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, '.out', 'shots')
fs.mkdirSync(OUT, { recursive: true })
const APP = process.env.APP_URL || 'http://localhost:3000'
const slug = process.argv[2]
const results = []
const log = (ok, name, extra = '') => { results.push(ok); console.log((ok ? 'PASS ' : 'FAIL ') + name + (extra ? '  ' + extra : '')) }

;(async () => {
  const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || 'chrome', headless: true })
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true })
  const page = await ctx.newPage()
  try {
    await page.goto(`${APP}/agent/${slug}`, { waitUntil: 'networkidle' })
    await page.screenshot({ path: path.join(OUT, 'site-1-top.png') })
    await page.screenshot({ path: path.join(OUT, 'site-2-full.png'), fullPage: true })
    const body = await page.locator('body').innerText()
    // Agent pages carry the AGENT's own brand (name, colours, optional logo and banner); only the footer credits the platform.
    const head = await page.evaluate(() => {
      const h = document.querySelector('header')
      return { bg: getComputedStyle(h).backgroundColor, text: h.innerText.trim() }
    })
    log(head.text.length > 0 && head.bg !== 'rgba(0, 0, 0, 0)', "the header shows the agent's own name on a branded background", `${head.bg} | ${head.text.split('\n')[0]}`)
    log(/I'm interested/.test(body), "the hero carries the I'm interested action")
    log(/Powered by PUNE Property/.test(body), 'the footer credits the platform ("Powered by PUNE Property")')
    log(!/Verified by PUNE Property/i.test(body), 'we never claim the agent is verified')
    log((await page.locator('a[href^="tel:"]').count()) === 0 && (await page.locator('a[href*="wa.me"]').count()) === 0, 'no call/WhatsApp links (no phone number exposed)')
    log(!/\b[6-9]\d{9}\b/.test(body), 'no phone number in the page text')
    log(/Guides for Pune home buyers/.test(body) && (await page.locator('a[href^="/insights/"]').count()) >= 3, 'the guides are on the home page and link to /insights')
    log((await page.getByText('Sample listing').count()) >= 6, 'sample listings are labelled on their cards', String(await page.getByText('Sample listing').count()))
    const href = await page.locator('a[href*="/listings/"]').first().getAttribute('href')
    await page.goto(new URL(href, APP).toString(), { waitUntil: 'networkidle' })
    await page.screenshot({ path: path.join(OUT, 'site-3-listing.png') })
    const lb = await page.locator('body').innerText()
    log(/This home is not available/.test(lb), 'the listing page says the sample is not available')
    log((await page.locator('a[href^="tel:"]').count()) === 0, 'no call link on the listing page either')
  } catch (e) {
    log(false, 'aborted', e.message.split('\n')[0])
    await page.screenshot({ path: path.join(OUT, 'site-ZZ-failure.png') }).catch(() => {})
  }
  await browser.close()
  console.log(results.every(Boolean) ? '\nALL PASSED' : '\nSOME FAILED')
  process.exit(results.every(Boolean) ? 0 : 1)
})()
