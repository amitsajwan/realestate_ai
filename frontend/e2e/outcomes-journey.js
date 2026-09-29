/*
 * Deal outcomes in a real browser: win a deal (Won sheet, mark-sold prompt), lose another (reason), see "This month" on home,
 * reopen. Same prereqs as browser-journey.js (MongoDB, backend :8000 with JOIN_MODE=otp, `npx next dev -p 3000`).
 * Run: node e2e/outcomes-journey.js
 */
const fs = require('fs')
const path = require('path')
const { chromium } = require('playwright-core')
const OUT = path.join(__dirname, '.out', 'shots')
fs.mkdirSync(OUT, { recursive: true })
const APP = 'http://localhost:3000'
const API = 'http://localhost:8000/api/v1'
const UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
const phone = '98' + Array.from({ length: 8 }, () => Math.floor(Math.random() * 10)).join('')
const results = []
const log = (ok, name, extra = '') => { results.push(ok); console.log((ok ? 'PASS ' : 'FAIL ') + name + (extra ? '  ' + extra : '')) }
const post = async (p, body, token, h = {}) => (await fetch(API + p, { method: 'POST', headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: 'Bearer ' + token } : {}), ...h }, body: JSON.stringify(body) })).json()
const get = async (p, token) => (await fetch(API + p, { headers: { Authorization: 'Bearer ' + token } })).json()

;(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true })
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true })
  const page = await ctx.newPage()
  const errors = []
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message))
  page.on('response', (r) => { if (r.status() >= 400 && r.url().includes(':8000')) errors.push(`HTTP ${r.status()} ${r.request().method()} ${r.url().replace(/^.*\/api\/v1/, '')}`) })
  const shot = async (name) => { await page.evaluate(() => document.fonts.ready); await page.waitForTimeout(700); await page.screenshot({ path: path.join(OUT, name + '.jpg'), type: 'jpeg', quality: 82 }); console.log('shot', name) }

  // seed: agent, a Baner listing, two buyers from different channels
  const dev = await post('/join/otp/request', { phone })
  const login = await post('/join/otp/verify', { phone, code: dev.dev_code })
  const T = login.access_token
  const site = await post('/join/site', { name: 'Rahul Sharma', city: 'Pune' }, T)
  const fd = new FormData(); fd.append('text', '2 BHK for sale in Baner Pune, 1100 sq ft carpet, 85 lakh, ready possession, parking, lift, gym')
  const draft = (await (await fetch(API + '/listings/ai/draft', { method: 'POST', headers: { Authorization: 'Bearer ' + T }, body: fd })).json()).draft
  const lst = await post('/listings', Object.fromEntries(Object.entries(draft).filter(([, v]) => v != null)), T)
  await fetch(API + '/listings/' + lst.id + '/publish', { method: 'POST', headers: { Authorization: 'Bearer ' + T } })
  const H = { 'User-Agent': UA }
  const buyer = (anon, name, ph, msg, src, events) => (async () => {
    for (const t of events) await post('/t/event', { agent_slug: site.slug, anon_id: anon, listing_id: lst.id, source: src, type: t }, null, H)
    return post('/t/inquiry', { agent_slug: site.slug, anon_id: anon, listing_id: lst.id, source: src, name, phone: ph, message: msg, consent: true, bhk: 2, budget_min_inr: 8000000, budget_max_inr: 9000000 }, null, H)
  })()
  await buyer('anon-priya-0001', 'Priya Sharma', '9876500001', 'Is this still available?', 'instagram', ['listing_view', 'listing_view', 'whatsapp_click'])
  await buyer('anon-vikram-0005', 'Vikram Patil', '9876500005', 'Any discount on the price?', 'facebook', ['listing_view'])
  log(true, 'seeded agent, listing, two buyers (Instagram, Facebook)')

  await page.waitForTimeout(32000) // OTP resend cooldown
  await page.goto(APP + '/join', { waitUntil: 'networkidle' })
  await page.locator('#phone').fill(phone); await page.getByRole('button', { name: 'Send OTP' }).click()
  await page.getByRole('button', { name: 'Fill it' }).click()
  await page.waitForURL(/studio/, { timeout: 20000 }); await page.waitForTimeout(1200)
  let home = await page.locator('body').innerText()
  log(!/This month/.test(home), 'no "This month" card before any deal (new agent)')

  // ---- win Priya's deal
  await page.goto(APP + '/studio/leads', { waitUntil: 'networkidle' }); await page.waitForTimeout(1000)
  await page.getByText('Priya Sharma').first().click()
  await page.waitForURL(/studio\/leads\/[a-f0-9]+/); await page.waitForTimeout(1200)
  await page.getByRole('button', { name: 'Won', exact: true }).click()
  await page.getByText('Deal closed').waitFor({ timeout: 8000 })
  const prefilled = await page.locator('#deal-price').inputValue()
  log(/85/.test(prefilled), 'Won sheet pre-fills the listing price', prefilled)
  await shot('31-deal-closed-sheet')
  await page.locator('#deal-price').fill('82 lakh')
  await page.getByRole('dialog').getByRole('button', { name: 'Save' }).click()
  await page.getByText(/as sold\?/).waitFor({ timeout: 10000 })
  await shot('32-mark-sold-prompt')
  log(true, 'mark-as-sold prompt appears after a won deal')
  await page.getByRole('dialog').getByRole('button', { name: 'Yes' }).click()
  await page.waitForTimeout(1500)
  let detail = await page.locator('body').innerText()
  log(/Won/.test(detail) && /82/.test(detail), 'lead shows the Won summary with the price', (detail.match(/Won:[^\n]*/) || [''])[0])
  await shot('33-lead-won-summary')
  const priya = (await get('/inbox/leads', T)).leads.find((l) => l.name === 'Priya Sharma')
  log(priya.stage === 'won' && priya.outcome && priya.outcome.deal_price_inr === 8200000 && priya.outcome.listing_id === lst.id, 'API: outcome stored (Rs 82 L on the Baner listing)', JSON.stringify(priya.outcome))
  const listing = await get('/listings/' + lst.id, T)
  log(listing.status === 'sold', 'API: the listing was marked sold after "Yes"', listing.status)

  // ---- lose Vikram's deal
  await page.goto(APP + '/studio/leads', { waitUntil: 'networkidle' }); await page.waitForTimeout(1000)
  await page.getByText('Vikram Patil').first().click()
  await page.waitForURL(/studio\/leads\/[a-f0-9]+/); await page.waitForTimeout(1200)
  await page.getByRole('button', { name: 'Lost', exact: true }).click()
  await page.getByText('Why was it lost?').waitFor({ timeout: 8000 })
  await shot('34-lost-reason-sheet')
  await page.getByRole('dialog').getByRole('button', { name: 'Price', exact: true }).click()
  await page.waitForTimeout(1500)
  const vik = (await get('/inbox/leads', T)).leads.find((l) => l.name === 'Vikram Patil')
  log(vik.stage === 'lost' && vik.outcome.lost_reason === 'price', 'API: lost with reason "price"', JSON.stringify(vik.outcome))

  // ---- home: This month
  await page.goto(APP + '/studio', { waitUntil: 'networkidle' }); await page.waitForTimeout(1500)
  home = await page.locator('body').innerText()
  log(/This month/.test(home) && /Best channel/i.test(home) && /Instagram/.test(home), 'home shows "This month" with Instagram as the best channel', (home.match(/This month[\s\S]{0,160}/) || [''])[0].replace(/\s+/g, ' '))
  log(/price/i.test(home), 'home hints that deals were lost on price')
  await shot('35-home-this-month')
  await page.goto(APP + '/studio/listings', { waitUntil: 'networkidle' }); await page.waitForTimeout(1500)
  const lstText = await page.locator('body').innerText()
  log(/1 deal/.test(lstText), 'listing card shows the deal', (lstText.match(/1 deal[^\n]*/) || [''])[0])
  await shot('36-listing-deal')

  // ---- reopen
  await page.goto(APP + '/studio/leads', { waitUntil: 'networkidle' }); await page.waitForTimeout(1000)
  await page.getByText('Vikram Patil').first().click()
  await page.waitForURL(/studio\/leads\/[a-f0-9]+/); await page.waitForTimeout(1200)
  await page.getByRole('button', { name: 'Reopen' }).click(); await page.waitForTimeout(1500)
  const vik2 = (await get('/inbox/leads', T)).leads.find((l) => l.name === 'Vikram Patil')
  log(vik2.stage === 'contacted' && !vik2.outcome, 'reopen moves the lead to Contacted and clears the outcome', vik2.stage)

  const today = await get('/inbox/today', T)
  log(today.results.deals_won === 1 && today.results.deal_value_inr === 8200000 && today.results.top_source === 'instagram' && today.results.deals_lost === 0, 'API: results reflect the reopened lead', JSON.stringify(today.results))
  console.log('errors:', [...new Set(errors)].slice(0, 8))
  await browser.close()
  console.log(results.every(Boolean) ? '\nALL PASSED' : '\nSOME FAILED')
  process.exit(results.every(Boolean) ? 0 : 1)
})().catch((e) => { console.error('FAILED', e.message.split('\n').slice(0, 3).join(' | ')); process.exit(1) })
