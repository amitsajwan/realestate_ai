/*
 * Sprint 6 browser check: public landing + legal pages + invite request form (with rate limit and honeypot),
 * the per-listing activity page, and the "still available?" freshness flow (hidden listings vanish from the public site).
 * Same prereqs as browser-journey.js (MongoDB, backend :8000 with JOIN_MODE=otp, `npx next dev -p 3000`) and DATABASE_NAME set
 * to the backend's database (used by backend/scripts/dev_set_freshness.py). Run: node e2e/pilot-pages.js
 */
const fs = require('fs')
const path = require('path')
const { execSync } = require('child_process')
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, '.out', 'shots')
fs.mkdirSync(OUT, { recursive: true })
const APP = process.env.APP_URL || 'http://localhost:3000'
const API = (process.env.API_URL || 'http://localhost:8000') + '/api/v1'
const BACKEND = path.join(__dirname, '..', '..', 'backend')
const PY = process.env.PYTHON || path.join(BACKEND, '.venv', 'Scripts', 'python.exe')
const UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
const rnd = (n) => Array.from({ length: n }, () => Math.floor(Math.random() * 10)).join('')
const results = []
const log = (ok, name, extra = '') => { results.push(ok); console.log((ok ? 'PASS ' : 'FAIL ') + name + (extra ? '  ' + extra : '')) }
const post = async (p, body, token, h = {}) => fetch(API + p, { method: 'POST', headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: 'Bearer ' + token } : {}), ...h }, body: JSON.stringify(body) })
const getj = async (p, token) => (await fetch(API + p, { headers: token ? { Authorization: 'Bearer ' + token } : {} })).json()
const setFresh = (id, days) => execSync(`"${PY}" scripts/dev_set_freshness.py ${id} ${days}`, { cwd: BACKEND, env: { ...process.env, PYTHONPATH: '.' } })

;(async () => {
  const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || 'chrome', headless: true })
  const errors = []
  const mobile = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true })
  const page = await mobile.newPage()
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message))
  page.on('response', (r) => { if (r.status() >= 500) errors.push(`HTTP ${r.status()} ${r.url()}`) })
  const shot = (name, full = false) => page.screenshot({ path: path.join(OUT, name + '.jpg'), type: 'jpeg', quality: 80, fullPage: full })

  // ---- public pages
  await page.goto(APP + '/', { waitUntil: 'networkidle' })
  const landing = await page.locator('body').innerText()
  log((await page.locator('a[href="/request-invite"]').count()) > 0, 'landing has a link to /request-invite')
  log(!/testimonial|rated|customers served/i.test(landing), 'landing has no fabricated proof (testimonials, ratings)')
  await shot('50-landing-top')
  await shot('51-landing-full', true)
  for (const [p, heading] of [['/privacy', /privacy/i], ['/terms', /terms/i], ['/data-deletion', /delet/i]]) {
    await page.goto(APP + p, { waitUntil: 'networkidle' })
    const t = await page.locator('body').innerText()
    const h1 = await page.locator('h1').first().innerText()
    log(heading.test(h1) && /last updated/i.test(t) && (await page.locator('a[href^="mailto:"]').count()) === 0, `${p} renders with a date and no invented email`)
  }
  await shot('52-privacy')

  // ---- invite request
  const phone = '9' + rnd(9)
  await page.goto(APP + '/request-invite', { waitUntil: 'networkidle' })
  await page.locator('input[name=name], #name').first().fill('Test Agent')
  await page.locator('input[type=tel], input[name=phone], #phone').first().fill(phone)
  await page.locator('input[type=checkbox]').first().check()
  await shot('53-request-invite-form')
  const hp0 = await page.locator('input[name=website]').first()
  const box = await hp0.boundingBox()
  const hidden = await hp0.evaluate((el) => !!el.closest('[aria-hidden="true"]') && el.tabIndex === -1)
  log(box !== null && box.x + box.width < 0 && hidden, 'honeypot is off-screen, aria-hidden and skipped by Tab (people never see or reach it)')
  await page.getByRole('button', { name: /request|send|submit/i }).last().click()
  await page.waitForTimeout(2500)
  const after = await page.locator('body').innerText()
  log(/thank|received|we will|we.ll/i.test(after), 'invite request shows a friendly confirmation')
  await shot('54-request-invite-sent')
  const body = { name: 'Test Agent', phone, city: 'Pune', consent: true }
  const r2 = await post('/join/request-invite', body)
  const r3 = await post('/join/request-invite', body)
  const r4 = await post('/join/request-invite', body)
  log(r2.status === 200 && r3.status === 200 && r4.status === 429, 'rate limit: 3 per hour per phone, then 429', [r2.status, r3.status, r4.status].join(','))
  const hp = await post('/join/request-invite', { ...body, phone: '9' + rnd(9), website: 'http://spam.example' })
  log(hp.status === 200 && (await hp.json()).received === true, 'honeypot hit gets the normal success response')
  const noConsent = await post('/join/request-invite', { ...body, phone: '9' + rnd(9), consent: false })
  log(noConsent.status === 422, 'consent is required (422)')

  // ---- agent, listing, buyers
  const aphone = '98' + rnd(8)
  const dev = await (await post('/join/otp/request', { phone: aphone })).json()
  const login = await (await post('/join/otp/verify', { phone: aphone, code: dev.dev_code })).json()
  const T = login.access_token
  const site = await (await post('/join/site', { name: 'Rahul Sharma', city: 'Pune' }, T)).json()
  const fd = new FormData()
  fd.append('text', '2 BHK for sale in Baner Pune, 1100 sq ft carpet, 85 lakh, ready possession, parking, lift, gym')
  const draft = (await (await fetch(API + '/listings/ai/draft', { method: 'POST', headers: { Authorization: 'Bearer ' + T }, body: fd })).json()).draft
  const listing = await (await post('/listings', Object.fromEntries(Object.entries(draft).filter(([, v]) => v != null)), T)).json()
  await post('/listings/' + listing.id + '/publish', {}, T)
  const H = { 'User-Agent': UA }
  for (const [anon, src, n] of [['anon-aaaa-0001', 'instagram', 2], ['anon-bbbb-0002', 'whatsapp', 1], ['anon-cccc-0003', 'facebook', 1]]) {
    for (let i = 0; i < n; i++) await post('/t/event', { agent_slug: site.slug, anon_id: anon, listing_id: listing.id, source: src, type: 'listing_view' }, null, H)
  }
  await post('/t/event', { agent_slug: site.slug, anon_id: 'anon-aaaa-0001', listing_id: listing.id, source: 'instagram', type: 'whatsapp_click' }, null, H)
  await post('/t/inquiry', { agent_slug: site.slug, anon_id: 'anon-aaaa-0001', listing_id: listing.id, source: 'instagram', name: 'Priya Sharma', phone: '9876500001', message: 'Is it available?', consent: true, bhk: 2, budget_min_inr: 8000000, budget_max_inr: 9000000 }, null, H)
  await page.evaluate((t) => localStorage.setItem('app_token', t), T)

  // ---- activity page
  await page.goto(`${APP}/studio/listings/${listing.id}/activity`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(1500)
  const act = await page.locator('body').innerText()
  log(/Views/.test(act) && /Enquiries/.test(act) && /people/i.test(act), 'activity page shows the totals and interested people')
  log(/Priya Sharma/.test(act) && /Visitor \d/.test(act), 'feed names the buyer and labels anonymous visitors (no ids)')
  log(!/anon-aaaa|anon-bbbb/.test(act), 'anonymous ids are never shown')
  log(/instagram/i.test(act), 'sources are listed')
  await shot('55-activity')

  // ---- freshness: fresh -> confirm -> hidden
  setFresh(listing.id, 30)
  await page.goto(APP + '/studio/listings', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1500)
  log(/Is this still available\?/.test(await page.locator('body').innerText()), 'a 30-day-old listing asks "Is this still available?"')
  await shot('56-freshness-confirm')
  await page.getByRole('button', { name: 'Yes, still available' }).first().click()
  await page.waitForTimeout(1500)
  const l = await getj('/listings/' + listing.id, T)
  log(l.freshness === 'fresh', 'tapping Yes makes it fresh again', l.freshness)
  setFresh(listing.id, 50)
  const hiddenApi = await getj(`/public/agents/${site.slug}/listings`)
  const hiddenPage = await fetch(`${APP}/agent/${site.slug}/listings/${listing.id}`)
  log(hiddenApi.total === 0, 'a 50-day-old listing is removed from the public API', 'total=' + hiddenApi.total)
  log(hiddenPage.status === 404, 'and its public page is 404', String(hiddenPage.status))
  await page.goto(APP + '/studio/listings', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1500)
  log(/Hidden from buyers until you confirm/.test(await page.locator('body').innerText()), 'the agent sees "Hidden from buyers until you confirm"')
  await shot('57-freshness-hidden')
  await page.getByRole('button', { name: 'Yes, still available' }).first().click()
  await page.waitForTimeout(1500)
  const back = await getj(`/public/agents/${site.slug}/listings`)
  log(back.total === 1, 'confirming brings it back to the public site', 'total=' + back.total)

  console.log('server errors seen:', errors.length ? [...new Set(errors)].slice(0, 6) : 'none')
  await browser.close()
  console.log(results.every(Boolean) ? '\nALL PASSED' : '\nSOME FAILED')
  process.exit(results.every(Boolean) ? 0 : 1)
})().catch((e) => { console.error('FAILED', e.message.split('\n').slice(0, 3).join(' | ')); process.exit(1) })
