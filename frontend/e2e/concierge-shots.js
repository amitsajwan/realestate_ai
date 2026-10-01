/*
 * Screenshots of the Studio Agents screens (390x844, system Chrome) in fixtures mode.
 * Start:  NEXT_PUBLIC_APP_FIXTURES=1 SITE_USE_FIXTURES=1 npx next dev --webpack -p 3121
 * Run:    APP_URL=http://localhost:3121 OUT=<folder> node e2e/concierge-shots.js
 */
const fs = require('fs')
const path = require('path')
const { chromium } = require('playwright-core')

const OUT = process.env.OUT || path.join(__dirname, '.out', 'concierge')
const APP = process.env.APP_URL || 'http://localhost:3121'
fs.mkdirSync(OUT, { recursive: true })

;(async () => {
  const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || 'chrome', headless: true })
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true })
  await ctx.addInitScript(() => {
    try { localStorage.setItem('app_token', 'fixture-token'); localStorage.setItem('app_fixtures', '1') } catch (e) {}
  })
  const page = await ctx.newPage()
  const shot = (name, full = false) => page.screenshot({ path: path.join(OUT, name + '.jpg'), type: 'jpeg', quality: 70, fullPage: full })
  const settle = async () => { await page.waitForLoadState('networkidle').catch(() => {}); await page.waitForTimeout(600) }
  const overflow = async (label) => console.log(label, 'overflow:', await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth))
  await page.goto(APP + '/studio/agents', { waitUntil: 'domcontentloaded', timeout: 180000 })
  await page.getByTestId('agent-row').first().waitFor({ timeout: 180000 }); await settle()
  await shot('1-agents-list'); await overflow('list')

  await page.getByRole('button', { name: '+ Add agent' }).click(); await page.waitForTimeout(300)
  await page.getByLabel('His name').fill('Neha Joshi')
  await page.getByLabel('His mobile number').fill('98123 45678')
  await page.getByLabel(/Label for you/).fill('Neha, Kothrud')
  await shot('2-add-agent-sheet')
  await page.getByRole('button', { name: 'Create agent' }).click()
  await page.getByTestId('invite-code').waitFor(); await page.waitForTimeout(300)
  await shot('3-add-agent-code')
  await page.getByRole('button', { name: 'Done' }).click()

  await page.goto(APP + '/studio/agents/fx-a1', { waitUntil: 'domcontentloaded', timeout: 180000 })
  await page.getByTestId('check-logo').waitFor({ timeout: 180000 }); await settle()
  await shot('4-agent-detail-top'); await overflow('detail')
  await page.evaluate(() => document.querySelector('[data-surface=v2] main').scrollTo(0, 700)); await page.waitForTimeout(300)
  await shot('5-agent-detail-middle')
  await page.evaluate(() => document.querySelector('[data-surface=v2] main').scrollTo(0, 99999)); await page.waitForTimeout(300)
  await shot('5b-agent-detail-bottom')

  await page.getByRole('button', { name: 'Post to PUNE Property' }).first().scrollIntoViewIfNeeded()
  await page.getByRole('button', { name: 'Post to PUNE Property' }).first().click()
  await page.getByTestId('caption-facebook_page').waitFor(); await page.waitForTimeout(400)
  await shot('6-post-captions')
  await page.getByRole('button', { name: /Approve and post/ }).click(); await page.waitForTimeout(500)
  await shot('8-post-done')

  await page.goto(APP + '/studio/agents/fx-a1/listings/new', { waitUntil: 'domcontentloaded', timeout: 180000 })
  await page.getByText('Listing for Rahul').waitFor({ timeout: 180000 }); await settle()
  await shot('9-listing-for-agent'); await overflow('listing')
  await browser.close()
})().catch((e) => { console.error(e); process.exit(1) })
