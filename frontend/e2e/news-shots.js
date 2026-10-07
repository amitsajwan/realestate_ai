/*
 * Screenshots of the public news pages (390x844, system Chrome) and the Studio Newsroom preview, in fixtures mode.
 * Start:  NEXT_PUBLIC_APP_FIXTURES=1 SITE_USE_FIXTURES=1 npx next dev -p 3109
 * Run:    APP_URL=http://localhost:3109 CARDS=<folder holding news/<id>-fb.jpg and -ig.jpg> OUT=<folder> node e2e/news-shots.js
 * The fixture items point at https://media.example.com/uploads/news/...; those requests are answered from CARDS, so no network is needed.
 */
const fs = require('fs')
const path = require('path')
const { chromium } = require('playwright-core')

const OUT = process.env.OUT || path.join(__dirname, '.out', 'news')
const CARDS = process.env.CARDS || path.join(__dirname, '.out', 'cards')
const APP = process.env.APP_URL || 'http://localhost:3109'
fs.mkdirSync(OUT, { recursive: true })

;(async () => {
  const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || 'chrome', headless: true })
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true })
  await ctx.addInitScript(() => {
    try { localStorage.setItem('app_token', 'fixture-token'); localStorage.setItem('app_fixtures', '1') } catch (e) {}
  })
  await ctx.route('https://media.example.com/**', (route) => {
    const file = path.join(CARDS, new URL(route.request().url()).pathname.replace('/uploads/', ''))
    return fs.existsSync(file) ? route.fulfill({ path: file, contentType: 'image/jpeg' }) : route.abort()
  })
  const page = await ctx.newPage()
  const shot = (name, full = true) => page.screenshot({ path: path.join(OUT, name + '.jpg'), type: 'jpeg', quality: 72, fullPage: full })
  const settle = async () => { await page.waitForLoadState('networkidle').catch(() => {}); await page.waitForTimeout(700) }

  await page.goto(APP + '/news', { waitUntil: 'domcontentloaded', timeout: 180000 })
  await page.getByTestId('news-card').first().waitFor({ timeout: 180000 }); await settle()
  await shot('news-list-top', false)
  await shot('news-list')
  console.log('list overflow:', await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth))

  await page.goto(APP + '/news/a1b2c3d4e5', { waitUntil: 'domcontentloaded', timeout: 180000 })
  await page.getByTestId('news-article').waitFor({ timeout: 180000 }); await settle()
  await shot('news-item-top', false)
  await shot('news-item')
  console.log('item overflow:', await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth))
  console.log('google link visible:', await page.evaluate(() => /news\.google\.com/.test(document.body.innerText)))

  await page.goto(APP + '/news/digest-2026-w40', { waitUntil: 'domcontentloaded', timeout: 180000 })
  await page.getByTestId('news-article').waitFor({ timeout: 180000 }); await settle()
  await shot('news-digest')

  await page.goto(APP + '/studio/newsroom', { waitUntil: 'domcontentloaded', timeout: 180000 })
  await page.getByTestId('queue-card').first().waitFor({ timeout: 180000 }); await settle()
  await shot('studio-newsroom-top', false)
  await page.getByTestId('post-preview').first().scrollIntoViewIfNeeded(); await page.waitForTimeout(400)
  await shot('studio-newsroom')
  await browser.close()
})().catch((e) => { console.error(e); process.exit(1) })
