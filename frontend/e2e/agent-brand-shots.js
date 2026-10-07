/*
 * Screenshots of the branded public agent pages (fictional agents, fixtures mode) and of the Studio BrandEditor.
 * Start:  NEXT_PUBLIC_APP_FIXTURES=1 SITE_USE_FIXTURES=1 npx next dev --webpack -p 3141
 * Run:    APP_URL=http://localhost:3141 OUT=<folder> node e2e/agent-brand-shots.js
 * Stock photos come from backend/app/modules/showcase/assets/photos (Unsplash, see docs/brand/photo-credits.md); fixtures point at
 * /uploads/images/fx-*.jpg and picsum.photos, which are answered locally, so no network is needed.
 */
const fs = require('fs')
const path = require('path')
const { chromium } = require('playwright-core')

const APP = process.env.APP_URL || 'http://localhost:3141'
const OUT = process.env.OUT || path.join(__dirname, '.out', 'brand')
const PHOTOS = path.join(__dirname, '..', '..', 'backend', 'app', 'modules', 'showcase', 'assets', 'photos')
fs.mkdirSync(OUT, { recursive: true })

const BANNERS = { 'fx-banner-aundh': 'u4453DIQWtsQ', 'fx-banner-hinjewadi': 'uNEgt3edkuR4', 'fx-banner-kharadi': 'u2EmCXrpIKA0' }
const LISTING = ['uRUOLhYJF75w', 'uAB_q9lwCVv8', 'u7Cwct_F0Gbs', 'uOhezdWyzXTI', 'uIjccw_xakzY', 'u0tVimluL_ls']
const AGENTS = [
  ['rohan-kulkarni-aundh', 'emerald-banner'],
  ['meera-joshi-kothrud', 'terracotta'],
  ['sanjay-patil-hinjewadi', 'purple-banner'],
  ['aditi-rao-koregaon', 'cream-ink'],
  ['neha-kapoor-kharadi', 'slate-banner'],
  ['priya-deshmukh-pune', 'navy-default'],
]
const avatar = (c) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="${c}"/><circle cx="50" cy="38" r="18" fill="#f1f5f9"/><path d="M14 100c2-26 18-38 36-38s34 12 36 38z" fill="#f1f5f9"/></svg>`

async function routes(ctx) {
  await ctx.route('**/uploads/images/**', (route) => {
    const name = path.basename(new URL(route.request().url()).pathname, '.jpg')
    if (BANNERS[name]) return route.fulfill({ path: path.join(PHOTOS, BANNERS[name] + '.jpg'), contentType: 'image/jpeg' })
    return route.fulfill({ body: avatar(name.endsWith('m') ? '#64748b' : '#94a3b8'), contentType: 'image/svg+xml' })
  })
  await ctx.route('https://picsum.photos/**', (route) => {
    const n = [...route.request().url()].reduce((a, c) => a + c.charCodeAt(0), 0) % LISTING.length
    return route.fulfill({ path: path.join(PHOTOS, LISTING[n] + '.jpg'), contentType: 'image/jpeg' })
  })
}

;(async () => {
  const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || 'chrome', headless: true })
  for (const [label, vp, mobile] of [['m', { width: 390, height: 844 }, true], ['d', { width: 1280, height: 800 }, false]]) {
    const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: mobile ? 2 : 1, isMobile: mobile, hasTouch: mobile })
    await routes(ctx)
    const page = await ctx.newPage()
    for (const [slug, name] of AGENTS) {
      await page.goto(`${APP}/agent/${slug}`, { waitUntil: 'domcontentloaded', timeout: 180000 })
      await page.getByRole('heading', { level: 1 }).waitFor({ timeout: 180000 })
      await page.waitForLoadState('networkidle').catch(() => {})
      await page.waitForTimeout(500)
      await page.screenshot({ path: path.join(OUT, `${name}-${label}-top.jpg`), type: 'jpeg', quality: 78 })
      await page.locator('#about').scrollIntoViewIfNeeded()
      await page.evaluate(() => document.querySelector('#about').scrollIntoView())
      await page.waitForTimeout(300)
      await page.screenshot({ path: path.join(OUT, `${name}-${label}-about.jpg`), type: 'jpeg', quality: 78 })
      console.log(name, label, 'overflow:', await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth))
    }
    await ctx.close()
  }
  // Studio brand editor (390 wide), fixtures session
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true })
  await routes(ctx)
  await ctx.addInitScript(() => { try { localStorage.setItem('app_token', 'fixture-token'); localStorage.setItem('app_fixtures', '1') } catch (e) {} })
  const page = await ctx.newPage()
  await page.goto(APP + '/studio/profile', { waitUntil: 'domcontentloaded', timeout: 180000 })
  await page.getByTestId('brand-editor').waitFor({ timeout: 180000 })
  await page.waitForLoadState('networkidle').catch(() => {})
  await page.waitForTimeout(600)
  await page.screenshot({ path: path.join(OUT, 'editor-m-top.jpg'), type: 'jpeg', quality: 78 })
  await page.evaluate(() => { const m = document.querySelector('[data-surface="v2"] main'); m.scrollTop = 1500 })
  await page.waitForTimeout(300)
  await page.screenshot({ path: path.join(OUT, 'editor-m-mid.jpg'), type: 'jpeg', quality: 78 })
  await page.evaluate(() => { const m = document.querySelector('[data-surface="v2"] main'); m.scrollTop = 99999 })
  await page.waitForTimeout(300)
  await page.screenshot({ path: path.join(OUT, 'editor-m-bottom.jpg'), type: 'jpeg', quality: 78 })
  console.log('editor overflow:', await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth))
  await browser.close()
})().catch((e) => { console.error(e); process.exit(1) })
