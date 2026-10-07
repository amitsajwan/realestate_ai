/* Above-the-fold + form-error screenshots. Usage: node e2e/web-audit-fold.js <outdir> <baseUrl> */
const path = require('path')
const fs = require('fs')
const { chromium } = require('playwright-core')
const OUT = process.argv[2]
const APP = process.argv[3]
fs.mkdirSync(OUT, { recursive: true })
;(async () => {
  const b = await chromium.launch({ channel: 'chrome', headless: true })
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true })
  await ctx.route('**/api/**', (r) => (r.request().method() === 'GET' ? r.continue() : r.abort()))
  const p = await ctx.newPage()
  await p.goto(APP + '/', { waitUntil: 'networkidle' })
  await p.screenshot({ path: path.join(OUT, 'landing-fold-m.jpg'), type: 'jpeg', quality: 70 })
  await p.goto(APP + '/request-invite', { waitUntil: 'networkidle' })
  await p.getByRole('button', { name: /send request/i }).click()
  await p.screenshot({ path: path.join(OUT, 'invite-errors-m.jpg'), type: 'jpeg', quality: 70 })
  await b.close()
})()
