/*
 * Browser check of the weekly summary card on the agent's home screen: real views/enquiry data in, correct numbers, concrete tips, and a WhatsApp
 * share link that carries no phone number. Same prereqs as browser-journey.js. Run: node e2e/weekly-check.js
 */
const fs = require('fs')
const path = require('path')
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, '.out', 'shots')
fs.mkdirSync(OUT, { recursive: true })
const APP = process.env.APP_URL || 'http://localhost:3000'
const API = (process.env.API_URL || 'http://localhost:8000') + '/api/v1'
const rnd = (n) => Array.from({ length: n }, () => Math.floor(Math.random() * 10)).join('')
const results = []
const log = (ok, name, extra = '') => { results.push(ok); console.log((ok ? 'PASS ' : 'FAIL ') + name + (extra ? '  ' + extra : '')) }
const post = (p, body, token, h = {}) => fetch(API + p, { method: 'POST', headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: 'Bearer ' + token } : {}), ...h }, body: JSON.stringify(body) })
const UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'

;(async () => {
  const phone = '98' + rnd(8)
  const dev = await (await post('/join/otp/request', { phone })).json()
  const login = await (await post('/join/otp/verify', { phone, code: dev.dev_code })).json()
  const T = login.access_token
  const site = await (await post('/join/site', { name: 'Weekly Tester', city: 'Pune' }, T)).json()
  const fd = new FormData(); fd.append('text', '2 BHK for sale in Wagholi Pune, 850 sq ft carpet, 58 lakh, ready possession, parking, lift')
  const draft = (await (await fetch(API + '/listings/ai/draft', { method: 'POST', headers: { Authorization: 'Bearer ' + T }, body: fd })).json()).draft
  const listing = await (await post('/listings', Object.fromEntries(Object.entries(draft).filter(([, v]) => v != null)), T)).json()
  await post(`/listings/${listing.id}/publish`, {}, T)
  for (const anon of ['anon-aaaa-0001', 'anon-bbbb-0002', 'anon-cccc-0003'])
    await post('/t/event', { agent_slug: site.slug, anon_id: anon, listing_id: listing.id, source: 'facebook', type: 'listing_view' }, null, { 'User-Agent': UA })
  await post('/t/inquiry', { agent_slug: site.slug, anon_id: 'anon-aaaa-0001', listing_id: listing.id, source: 'facebook', name: 'Neha Rao', phone: '9876500123', message: 'Is it available?', consent: true, bhk: 2, budget_max_inr: 6000000 }, null, { 'User-Agent': UA })

  const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || 'chrome', headless: true })
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true })
  const page = await ctx.newPage()
  try {
    await page.goto(APP + '/join', { waitUntil: 'networkidle' })
    await page.evaluate((t) => localStorage.setItem('app_token', t), T)
    await page.goto(APP + '/studio', { waitUntil: 'networkidle' })
    const card = page.locator('section[aria-label="This week"]')
    await card.waitFor({ timeout: 20000 })
    const text = await card.innerText()
    log(/3\s*Views/.test(text.replace(/\n/g, ' ')) && /1\s*Enquiries/.test(text.replace(/\n/g, ' ')), 'the card shows 3 views and 1 enquiry', text.replace(/\n/g, ' ').slice(0, 90))
    log(/Most viewed/.test(text), 'it names the most viewed listing')
    log(/Add photos to 1 live listing/.test(text), 'it tells the agent, concretely, to add photos to the listing that has none')
    log(/not been contacted for over a day/.test(text) === false, 'it does not nag about a fresh enquiry')
    const href = await card.getByRole('link', { name: /Share my week on WhatsApp/ }).getAttribute('href')
    const shared = decodeURIComponent(href.split('text=')[1])
    console.log("SHARED>>", JSON.stringify(shared)); log(/3 listing views from 3 visitors/.test(shared) && /1 new enquiry/.test(shared) && /http/.test(shared), 'the WhatsApp message has the real numbers and a link to the site', shared.split('\n').length + ' lines')
    log(!/\d{10}/.test(shared) && !/Neha|9876500123/.test(shared), 'and contains no phone number or buyer name')
    await page.screenshot({ path: path.join(OUT, 'weekly-1.png'), fullPage: false })
  } catch (e) {
    log(false, 'journey aborted', e.message.split('\n')[0])
    await page.screenshot({ path: path.join(OUT, 'weekly-ZZ-failure.png') }).catch(() => {})
  }
  await browser.close()
  console.log(results.every(Boolean) ? '\nALL PASSED' : '\nSOME FAILED')
  process.exit(results.every(Boolean) ? 0 : 1)
})()
