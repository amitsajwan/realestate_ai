/*
 * Screenshots of the 'About the project and area' step and the public About section (390x844, system Chrome), fixtures mode.
 * Start: NEXT_PUBLIC_APP_FIXTURES=1 SITE_USE_FIXTURES=1 npx next dev -p 3107   then: APP_URL=http://localhost:3107 node e2e/about-step-shots.js
 */
const fs = require('fs')
const path = require('path')
const { chromium } = require('playwright-core')

const OUT = process.env.OUT || path.join(__dirname, '.out', 'about')
fs.mkdirSync(OUT, { recursive: true })
const APP = process.env.APP_URL || 'http://localhost:3107'

;(async () => {
  const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || 'chrome', headless: true })
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true })
  await ctx.addInitScript(() => {
    try { localStorage.setItem('app_token', 'fixture-token'); localStorage.setItem('app_fixtures', '1') } catch (e) {}
  })
  const page = await ctx.newPage()
  const shot = (n, full = false) => page.screenshot({ path: path.join(OUT, n + '.jpg'), type: 'jpeg', quality: 78, fullPage: full })
  await page.goto(APP + '/studio/listings/new', { waitUntil: 'domcontentloaded', timeout: 120000 })
  await page.locator('textarea').waitFor({ timeout: 120000 }); await page.locator('textarea').fill('2 BHK for sale in Kharadi Pune, 1100 sq ft carpet, 98 lakh, ready to move, east facing corner flat, 1 covered parking, lift, gym, 24x7 water, maintenance 3000 per month, school nearby')
  await page.getByRole('button', { name: 'Next', exact: true }).click()
  await page.getByTestId('about-step').waitFor({ timeout: 20000 })
  await shot('1-about-top')
  await page.getByRole('button', { name: /Suggest from my description/ }).click()
  await page.getByRole('list', { name: 'Suggestions' }).waitFor()
  await page.getByRole('button', { name: /Keep: East facing/ }).click()
  await page.getByRole('button', { name: /Keep: Lift/ }).click()
  await shot('2-about-suggestions')
  await page.getByRole('button', { name: /Keep all/ }).click()
  await page.getByLabel('Your answer 1').fill('Yes, one covered slot is included.')
  await shot('3-about-full', true)
  await page.getByRole('button', { name: /^Continue$/ }).click()
  await page.getByText('Check and confirm').waitFor()
  await page.getByRole('region', { name: 'About the project and area' }).scrollIntoViewIfNeeded()
  await shot('4-review-summary')
  await page.goto(APP + '/agent/priya-deshmukh-pune/listings/fx-kharadi-2bhk-uc', { waitUntil: 'domcontentloaded', timeout: 120000 })
  const sec = page.getByTestId('listing-about')
  await sec.waitFor({ timeout: 120000 }); await sec.scrollIntoViewIfNeeded(); await page.waitForTimeout(800)
  await shot('5-public-section')
  await page.evaluate(() => document.querySelectorAll('*').forEach((el) => { const s = getComputedStyle(el); if (s.position === 'fixed') el.style.display = 'none' }))
  await sec.screenshot({ path: path.join(OUT, '6-public-section-only.jpg'), type: 'jpeg', quality: 80 })
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)
  console.log('horizontal overflow on public page:', overflow)
  await browser.close()
})().catch((e) => { console.error(e); process.exit(1) })
