/* Screenshots key public pages at mobile + desktop. Usage: node e2e/web-audit-shots.js <outdir> [baseUrl] */
const path = require('path')
const fs = require('fs')
const { chromium } = require('playwright-core')
const OUT = process.argv[2]
const APP = process.argv[3] || 'https://34-180-39-243.sslip.io'
fs.mkdirSync(OUT, { recursive: true })
const PAGES = { landing: '/', invite: '/request-invite', localities: '/localities', locality: '/localities/kharadi', insights: '/insights', agent: '/agent/avasetu', join: '/join', studio: '/studio' }
;(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true })
  for (const [vp, w, h, mobile] of [['m', 390, 844, true], ['d', 1280, 800, false]]) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 1, isMobile: mobile, hasTouch: mobile })
    // read-only: never let a screenshot run write to the live API (tracking beacons, chat, forms)
    await ctx.route('**/api/**', (route) => (route.request().method() === 'GET' ? route.continue() : route.abort()))
    const page = await ctx.newPage()
    for (const [name, p] of Object.entries(PAGES)) {
      try {
        await page.goto(APP + p, { waitUntil: 'networkidle', timeout: 45000 })
        await page.waitForTimeout(600)
        await page.screenshot({ path: path.join(OUT, `${name}-${vp}.jpg`), type: 'jpeg', quality: 55, fullPage: true })
        console.log('ok', name, vp)
      } catch (e) { console.log('FAIL', name, vp, e.message.slice(0, 80)) }
    }
    await ctx.close()
  }
  await browser.close()
})()
