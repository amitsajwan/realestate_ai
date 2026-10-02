/*
 * Guide run (stream G1): every step of docs/AGENT_GUIDE.md, run on the LIVE site with test data, phone viewport, system Chrome.
 *
 *   PHASE=self  CODE=<invite code for 9000000011> node e2e/guide-run.js     # A: agent signs up himself, brand, listing, pack, chat lead
 *   PHASE=owner CODE=<invite code for the temp owner 9000000014> node e2e/guide-run.js   # B: owner concierge (stops at the caption preview)
 *   PHASE=show  node e2e/guide-run.js                                        # C: showcase links
 *
 * Env: APP_URL (default the live site), OUT (screenshots, default e2e/.out/guide). Nothing is posted to Facebook or Instagram.
 * Test data only: agent 9000000011 'Test Agent G1', buyer 9000000012, concierge agent 9000000013. Clean up with
 * backend/scripts/g1_testdata.py afterwards.
 */
const fs = require('fs')
const path = require('path')
const { chromium } = require('playwright-core')

const APP = process.env.APP_URL || 'https://34-180-39-243.sslip.io'
const OUT = process.env.OUT || path.join(__dirname, '.out', 'guide')
const PHASE = process.env.PHASE || 'self'
const CODE = process.env.CODE || ''
const ROOT = path.join(__dirname, '..', '..')
const PHOTOS = ['living-room.jpg', 'living-sofa.jpg'].map((f) => path.join(ROOT, 'backend', 'app', 'modules', 'creative', 'assets', 'photos', f))
const STATE = path.join(OUT, 'state.json')
fs.mkdirSync(OUT, { recursive: true })
const state = fs.existsSync(STATE) ? JSON.parse(fs.readFileSync(STATE, 'utf8')) : {}
const save = () => fs.writeFileSync(STATE, JSON.stringify(state, null, 2))

const rows = []
let curPage = null
async function step(name, fn) {
  const t0 = Date.now()
  try {
    const note = await fn()
    const s = ((Date.now() - t0) / 1000).toFixed(1)
    rows.push({ name, ok: true, s, note: note || '' })
    console.log(`PASS ${s.padStart(6)}s  ${name}${note ? '  -- ' + note : ''}`)
  } catch (e) {
    const s = ((Date.now() - t0) / 1000).toFixed(1)
    rows.push({ name, ok: false, s, note: e.message.split('\n')[0] })
    console.log(`FAIL ${s.padStart(6)}s  ${name}  -- ${e.message.split('\n')[0]}`)
    if (curPage) await curPage.screenshot({ path: path.join(OUT, 'ZZ-fail.jpg'), type: 'jpeg', quality: 60 }).catch(() => {})
    throw e
  }
}

async function newPhone(browser) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: 'en-IN' })
  const page = await ctx.newPage()
  page.setDefaultTimeout(45000)
  curPage = page
  const errors = []
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message.slice(0, 160)))
  page.on('response', (r) => { if (r.status() >= 400 && r.url().includes('/api/')) errors.push(`HTTP ${r.status()} ${r.request().method()} ${r.url().replace(/^.*\/api\/v1/, '').slice(0, 90)}`) })
  return { ctx, page, errors }
}
const shot = (page, name, full = false) => page.screenshot({ path: path.join(OUT, name + '.jpg'), type: 'jpeg', quality: 60, fullPage: full })
const settle = async (page, ms = 800) => { await page.waitForLoadState('networkidle', { timeout: 20000 }).catch(() => {}); await page.waitForTimeout(ms) }
const text = (page) => page.locator('body').innerText()

async function makeLogo(browser, file) {
  const p = await browser.newPage({ viewport: { width: 400, height: 400 } })
  await p.setContent(`<div id=l style="width:400px;height:400px;display:flex;align-items:center;justify-content:center;background:#0b3d5c;
    font:800 150px/1 Arial,sans-serif;color:#f4c95d;letter-spacing:-6px">G1</div>`)
  await p.locator('#l').screenshot({ path: file, type: 'png' })
  await p.close()
}

async function signIn(page, phone, code, shotPrefix) {
  await page.goto(APP + '/join', { waitUntil: 'domcontentloaded' })
  await page.locator('#phone').waitFor()
  await settle(page, 1500) // let the page finish loading before typing (a too-early tap reloads the form)
  if (shotPrefix) await shot(page, shotPrefix + '-join-phone')
  await page.locator('#phone').fill(phone)
  await page.getByRole('button', { name: /Send OTP|Continue|Next/ }).click()
  await page.getByText('Enter your 6-digit invite code').waitFor()
  if (shotPrefix) await shot(page, shotPrefix + '-join-code')
  await page.getByLabel(/code|OTP/i).first().fill(code) // 6 digits submit on their own
  await Promise.race([page.locator('#name').waitFor({ timeout: 30000 }), page.waitForURL(/\/studio/, { timeout: 30000 })])
}

async function createSite(page, { name, business, preset }, shotPrefix) {
  await page.locator('#name').fill(name)
  await page.locator('#city').fill('Pune')
  await page.locator('#biz').fill(business)
  await page.getByTestId('join-preset-' + preset).click()
  await shot(page, shotPrefix + '-join-profile')
  await page.getByRole('button', { name: 'Create my website' }).click()
  await page.getByText('Your website is live').waitFor({ timeout: 60000 })
  await settle(page)
  await shot(page, shotPrefix + '-join-done')
  const m = (await text(page)).match(/https?:\/\/\S+\/agent\/[a-z0-9-]+/)
  return m && m[0]
}

// ---------------- Part A: the agent signs up and works himself ----------------
async function self(browser) {
  if (!CODE) throw new Error('CODE is required')
  const { page, errors } = await newPhone(browser)
  try {
    await step('A1 open /join, enter mobile and invite code', async () => { await signIn(page, '9000000011', CODE, 'a01') })
    if (await page.locator('#name').count()) await step('A2 create the website (name, Pune, business name, colour theme)', async () => {
      state.siteUrl = await createSite(page, { name: 'Test Agent G1', business: 'G1 Test Realty', preset: 'emerald' }, 'a02')
      state.slug = state.siteUrl && state.siteUrl.split('/agent/')[1]
      save()
      return state.siteUrl
    })
    await step('A3 land in Studio', async () => {
      const go = page.getByRole('link', { name: 'Go to my app' })
      if (await go.count()) await go.click()
      await page.waitForURL(/\/studio$/)
      await settle(page, 1500)
      await shot(page, 'a03-studio-home')
    })
    await step('A4 My brand: tagline, areas, logo upload, save', async () => {
      await page.getByRole('link', { name: /My brand/ }).first().click()
      await page.getByTestId('brand-editor').waitFor()
      await settle(page)
      await shot(page, 'a04-brand-top')
      await page.locator('#brand-tagline').fill('Kharadi and Wagholi homes, explained properly')
      for (const a of ['Kharadi', 'Wagholi']) {
        const b = page.getByTestId('brand-editor').getByRole('button', { name: a, exact: true })
        if ((await b.getAttribute('aria-pressed')) !== 'true') await b.click()
      }
      const logo = path.join(OUT, 'g1-logo.png')
      await makeLogo(browser, logo)
      await page.locator('#brand-logo').setInputFiles(logo)
      await page.waitForFunction(() => !!document.querySelector('[data-testid=brand-editor] img'), null, { timeout: 30000 })
      await page.locator('#brand-rera').fill('A51800099999').catch(() => {})
      await shot(page, 'a04-brand-filled')
      await page.getByRole('button', { name: 'Save my brand' }).click()
      await page.getByText('Saved. Your site now shows this look.').waitFor({ timeout: 30000 })
      await page.getByText('Saved. Your site now shows this look.').scrollIntoViewIfNeeded()
      await shot(page, 'a04-brand-saved')
    })
    await step('A5 add listing: type the description, add 2 photos, AI draft', async () => {
      await page.goto(APP + '/studio/listings/new', { waitUntil: 'domcontentloaded' })
      await page.getByRole('textbox').first().waitFor()
      await page.getByRole('textbox').first().fill('2 BHK Kharadi 85 lakh ready to move, 950 sq ft carpet, 7th floor, parking, gym')
      await page.locator('input[type=file]').first().setInputFiles(PHOTOS)
      await page.waitForTimeout(1500)
      await shot(page, 'a05-listing-typed')
      await page.getByRole('button', { name: 'Next', exact: true }).click()
      await page.getByText(/About the project|project and area/i).first().waitFor({ timeout: 90000 })
      await settle(page)
      await shot(page, 'a05-about-step')
    })
    await step('A6 About the project: Suggest from my description, keep all, continue', async () => {
      await page.getByRole('button', { name: /Suggest from my description/ }).click()
      await page.getByRole('button', { name: 'Keep all' }).waitFor({ timeout: 60000 })
      await page.getByRole('button', { name: 'Keep all' }).click()
      await page.waitForTimeout(500)
      await shot(page, 'a06-about-suggested')
      const kept = await page.getByRole('button', { name: /^Remove:/ }).count()
      await page.getByRole('button', { name: 'Continue', exact: true }).click()
      return `${kept} suggestions kept`
    })
    await step('A7 review the AI draft and publish', async () => {
      await page.getByRole('button', { name: /Confirm & post/ }).waitFor()
      await settle(page)
      await shot(page, 'a07-review-top')
      const vals = await page.locator('input,textarea,select').evaluateAll((els) => els.map((e) => e.value).join(' | '))
      const ok = /Kharadi/i.test(vals) && /950/.test(vals) && /(8500000|85)/.test(vals)
      if (!ok) throw new Error('AI draft did not fill Kharadi / 950 / 85 lakh: ' + vals.slice(0, 200))
      const tick = page.getByText('Yes, this price is correct')
      if (await tick.count()) await tick.click()
      await page.getByRole('button', { name: /Confirm & post/ }).scrollIntoViewIfNeeded()
      await shot(page, 'a07-review-bottom')
      await page.getByRole('button', { name: /Confirm & post/ }).click()
      await page.getByText('Your property is ready').waitFor({ timeout: 90000 })
      await settle(page, 2000)
      await shot(page, 'a07-published')
      return 'draft had Kharadi, 950 sq ft and 85 lakh'
    })
    await step('A8 open the listing marketing pack', async () => {
      await page.goto(APP + '/studio/listings', { waitUntil: 'domcontentloaded' })
      await page.locator('a[href^="/studio/listings/"]').first().waitFor()
      const href = await page.locator('a[href^="/studio/listings/"]:not([href$="/new"])').first().getAttribute('href')
      state.listingId = href.split('/')[3]
      save()
      await settle(page)
      await shot(page, 'a08-listings')
      await page.goto(APP + `/studio/listings/${state.listingId}/marketing`, { waitUntil: 'domcontentloaded' })
      await settle(page, 4000)
      await page.locator('img').first().waitFor({ timeout: 90000 })
      await page.waitForTimeout(3000)
      await shot(page, 'a08-marketing-pack')
      return `listing ${state.listingId}`
    })
    await step('A9 the agent\'s public page and the listing page', async () => {
      await page.goto(`${APP}/agent/${state.slug}`, { waitUntil: 'domcontentloaded' })
      await settle(page, 1500)
      await shot(page, 'a09-public-page')
      const body = await text(page)
      if (!/G1 Test Realty/.test(body)) throw new Error('business name not on the public page')
      await page.goto(`${APP}/agent/${state.slug}/listings/${state.listingId}`, { waitUntil: 'domcontentloaded' })
      await settle(page, 1500)
      await shot(page, 'a09-listing-page')
      if (!/Kharadi/.test(await text(page))) throw new Error('listing page does not show Kharadi')
    })
    await step('A10 a buyer chats on the listing page and leaves 9000000012 with consent', async () => {
      const buyer = await newPhone(browser)
      const bp = buyer.page
      await bp.goto(`${APP}/agent/${state.slug}/listings/${state.listingId}`, { waitUntil: 'domcontentloaded' })
      await settle(bp, 1500)
      const widget = bp.getByTestId('chat-widget')
      await widget.getByRole('button', { name: /Chat with us/ }).click()
      const lastBot = async () => (await widget.locator('[role=log] p').allInnerTexts()).join('\n')
      const waitNew = async (prev, ms = 40000) => { const t = Date.now(); while (Date.now() - t < ms) { const s = await lastBot(); if (s.length > prev.length) { await bp.waitForTimeout(1500); return lastBot() } await bp.waitForTimeout(400) } return lastBot() }
      let log = await waitNew('')
      await shot(bp, 'a10-chat-open')
      const say = async (m) => { const prev = await lastBot(); await widget.getByLabel('Your message').fill(m); await widget.getByRole('button', { name: 'Send' }).click(); log = await waitNew(prev); return log }
      await say('Is parking included? My budget is 90 lakh, want to buy')
      await shot(bp, 'a10-chat-answer')
      const transcript = []
      for (let i = 0; i < 6 && !/Thank you|thanks for sharing|will (call|contact)|share your number with/i.test(log.split('\n').slice(-2).join(' ')); i++) {
        const tail = log.split('\n').slice(-3).join(' ')
        let reply = 'I am G1 Buyer'
        if (/mobile number|phone number|your number/i.test(tail)) reply = '9000000012'
        else if (/YES/.test(tail)) reply = 'YES'
        else if (/name/i.test(tail)) reply = 'I am G1 Buyer'
        else if (/when|move|planning/i.test(tail)) reply = 'within 3 months'
        else if (/anything else/i.test(tail)) reply = 'Please call me, my number is 9000000012'
        else reply = 'Please ask the agent to call me'
        transcript.push(reply)
        await say(reply)
        if (reply === '9000000012' || /9000000012/.test(reply)) { if (/YES/.test(log.split('\n').slice(-2).join(' '))) { transcript.push('YES'); await say('YES') } break }
      }
      await shot(bp, 'a10-chat-lead')
      await buyer.ctx.close()
      state.chatSaid = transcript
      save()
      return 'buyer replies: ' + transcript.join(' / ')
    })
    await step('A11 the lead shows in Studio (badge + Leads)', async () => {
      await page.goto(APP + '/studio', { waitUntil: 'domcontentloaded' })
      await settle(page, 2500)
      const badge = page.getByTestId('lead-alerts-badge')
      const hasBadge = await badge.count()
      await shot(page, 'a11-studio-badge')
      await page.goto(APP + '/studio/leads', { waitUntil: 'domcontentloaded' })
      await settle(page, 2500)
      await shot(page, 'a11-leads')
      const body = await text(page)
      if (!/G1 Buyer|Website visitor|0012/.test(body)) throw new Error('lead not in Leads')
      const lead = page.locator('a[href^="/studio/leads/"]').first()
      if (await lead.count()) { await lead.click(); await settle(page, 2000); await shot(page, 'a11-lead-detail') }
      await page.goto(APP + '/studio/interest', { waitUntil: 'domcontentloaded' })
      await settle(page, 2000)
      await shot(page, 'a11-interest')
      return hasBadge ? 'badge: ' + (await page.title()) : 'NO BADGE'
    })
  } finally {
    console.log('API errors:', [...new Set(errors)].join('\n  ') || 'none')
  }
}

// ---------------- Part B: owner concierge ----------------
async function owner(browser) {
  if (!CODE) throw new Error('CODE is required')
  const { page, errors } = await newPhone(browser)
  try {
    await step('B0 temp owner signs in', async () => {
      await signIn(page, '9000000014', CODE)
      if (await page.locator('#name').count()) await createSite(page, { name: 'G1 Temp Owner', business: 'G1 Temp Owner', preset: 'navy-gold' }, 'b00')
    })
    await step('B1 Studio > Agents', async () => {
      await page.goto(APP + '/studio', { waitUntil: 'domcontentloaded' })
      await settle(page, 2000)
      await page.locator('a[href="/studio/agents"]').first().click()
      await page.waitForURL(/\/studio\/agents/)
      await settle(page, 1500)
      await shot(page, 'b01-agents')
    })
    await step('B2 Add agent: name, mobile, label; code and WhatsApp message shown', async () => {
      await page.getByRole('button', { name: '+ Add agent' }).click()
      await page.getByLabel('His name').fill('G1 Concierge Agent')
      await page.getByLabel('His mobile number').fill('9000000013')
      await page.getByLabel(/Label for you/).fill('G1 guide test, Kharadi')
      await shot(page, 'b02-add-agent')
      await page.getByRole('button', { name: 'Create agent' }).click()
      await page.getByTestId('invite-code').waitFor({ timeout: 30000 })
      const msg = await page.locator('#ag-msg').inputValue()
      await page.getByRole('button', { name: 'Copy message' }).click().catch(() => {})
      // the code is a test code, but blur it in the screenshot anyway
      await page.getByTestId('invite-code').evaluate((el) => { el.style.filter = 'blur(8px)' })
      await page.locator('#ag-msg').evaluate((el) => { el.value = el.value.replace(/\b\d{6}\b/g, '••••••') })
      await shot(page, 'b02-agent-code')
      state.conciergeMsg = msg.replace(/\b\d{6}\b/g, '<code>')
      save()
      await page.getByRole('button', { name: 'Done' }).click()
      await settle(page, 1500)
      await page.getByTestId('agent-row').filter({ hasText: 'G1 Concierge Agent' }).first().click()
      await page.waitForURL(/\/studio\/agents\/[^/]+$/)
      state.conciergeId = page.url().split('/').pop()
      save()
      await settle(page, 1500)
      await shot(page, 'b03-agent-detail')
      return state.conciergeMsg.slice(0, 160)
    })
    await step('B3 fill his Brand', async () => {
      const ed = page.getByTestId('brand-editor')
      await ed.waitFor()
      await page.locator('#brand-name').fill('G1 Concierge Homes')
      await page.locator('#brand-tagline').fill('Resale flats in Kharadi')
      const b = ed.getByRole('button', { name: 'Kharadi', exact: true })
      if ((await b.getAttribute('aria-pressed')) !== 'true') await b.click()
      const logo = path.join(OUT, 'g1-logo.png')
      if (!fs.existsSync(logo)) await makeLogo(browser, logo)
      await page.locator('#brand-logo').setInputFiles(logo)
      await page.waitForFunction(() => !!document.querySelector('[data-testid=brand-editor] img'), null, { timeout: 30000 })
      await page.locator('#brand-rera').fill('A51800088888').catch(() => {})
      await ed.scrollIntoViewIfNeeded()
      await shot(page, 'b04-brand')
      await page.getByRole('button', { name: /Save/ }).first().click()
      await page.getByText(/Saved/).first().waitFor({ timeout: 30000 })
    })
    await step('B4 add a listing on his behalf (same flow), publish', async () => {
      await page.goto(`${APP}/studio/agents/${state.conciergeId}/listings/new`, { waitUntil: 'domcontentloaded' })
      await page.getByText(/Listing for G1/).waitFor()
      await page.getByRole('textbox').first().fill('2 BHK Kharadi 85 lakh ready to move, 950 sq ft carpet, 7th floor, parking, gym')
      await page.locator('input[type=file]').first().setInputFiles(PHOTOS)
      await page.waitForTimeout(1000)
      await shot(page, 'b05-behalf-typed')
      await page.getByRole('button', { name: 'Next', exact: true }).click()
      await page.getByRole('button', { name: /Skip for now/ }).waitFor({ timeout: 90000 })
      await page.getByRole('button', { name: /Suggest from my description/ }).click()
      await page.getByRole('button', { name: 'Keep all' }).waitFor({ timeout: 60000 })
      await page.getByRole('button', { name: 'Keep all' }).click()
      await page.getByRole('button', { name: 'Continue', exact: true }).click()
      const tick = page.getByText('Yes, this price is correct')
      await page.getByRole('button', { name: /Confirm & post/ }).waitFor()
      if (await tick.count()) await tick.click()
      await page.getByRole('button', { name: /Confirm & post/ }).click()
      await page.getByTestId('behalf-done').waitFor({ timeout: 90000 })
      await shot(page, 'b05-behalf-done')
    })
    await step('B5 record consent', async () => {
      await page.goto(`${APP}/studio/agents/${state.conciergeId}`, { waitUntil: 'domcontentloaded' })
      await page.getByTestId('consent-text').waitFor()
      const sw = page.getByRole('switch')
      if ((await sw.getAttribute('aria-checked')) !== 'true') await sw.click()
      await page.waitForFunction(() => document.querySelector('[role=switch]')?.getAttribute('aria-checked') === 'true', null, { timeout: 30000 })
      await page.getByTestId('consent-text').scrollIntoViewIfNeeded()
      await page.waitForTimeout(500)
      await shot(page, 'b06-consent')
    })
    await step('B6 preview his page', async () => {
      const href = await page.getByRole('link', { name: /Preview .*page/ }).getAttribute('href')
      state.conciergeSlug = href.split('/').pop()
      save()
      const p2 = await page.context().newPage()
      await p2.goto(APP + href, { waitUntil: 'domcontentloaded' })
      await settle(p2, 2000)
      await shot(p2, 'b07-his-page')
      const ok = /G1 Concierge Homes/.test(await text(p2))
      await p2.close()
      if (!ok) throw new Error('brand name not on his page')
      return href
    })
    await step('B7 Post to Avasetu: caption preview (stopped before approving)', async () => {
      await page.getByTestId('check-logo').scrollIntoViewIfNeeded()
      await page.getByRole('button', { name: /Post to Avasetu/ }).first().scrollIntoViewIfNeeded()
      await shot(page, 'b08-listings-section')
      await page.getByRole('button', { name: /Post to Avasetu/ }).first().click()
      await page.locator('[data-testid^=caption-]').first().waitFor({ timeout: 90000 })
      await page.waitForTimeout(800)
      await shot(page, 'b08-captions')
      const caps = await page.locator('[data-testid^=caption-]').allInnerTexts()
      state.captions = caps
      save()
      if (caps.some((c) => /\b9000000013\b/.test(c))) throw new Error('caption carries the phone number')
      await page.getByRole('button', { name: 'Cancel' }).click()
      return caps.map((c) => c.split('\n').find((l) => /Listed by/.test(l)) || '').join(' | ')
    })
  } finally {
    console.log('API errors:', [...new Set(errors)].join('\n  ') || 'none')
  }
}

// ---------------- Part C: showcase ----------------
async function show(browser) {
  const { page, errors } = await newPhone(browser)
  const pages = [['c01-for-agents', '/for-agents'], ['c02-demo', '/agent/demo'], ['c03-avasetu', '/agent/avasetu'], ['c04-go', '/go'], ['c05-news', '/news'], ['c06-request-invite', '/request-invite']]
  for (const [name, url] of pages) {
    await step(`C open ${url}`, async () => {
      const r = await page.goto(APP + url, { waitUntil: 'domcontentloaded' })
      await settle(page, 1500)
      await shot(page, name)
      if (!r || r.status() >= 400) throw new Error('status ' + (r && r.status()))
      return `${r.status()} ${page.url().replace(APP, '')} "${(await page.title()).slice(0, 60)}"`
    })
  }
  await step('C Instagram link on /for-agents resolves', async () => {
    await page.goto(APP + '/for-agents', { waitUntil: 'domcontentloaded' })
    const ig = await page.locator('a[href*="instagram.com"]').first().getAttribute('href')
    const r = await fetch(ig, { redirect: 'follow', headers: { 'User-Agent': 'Mozilla/5.0' } })
    if (r.status >= 400) throw new Error(`${ig} -> ${r.status}`)
    return `${ig} -> ${r.status}`
  })
  console.log('API errors:', [...new Set(errors)].join('\n  ') || 'none')
}

;(async () => {
  const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || 'chrome', headless: true })
  let failed = false
  try {
    await ({ self, owner, show }[PHASE])(browser)
  } catch (e) {
    failed = true
  }
  await browser.close()
  fs.writeFileSync(path.join(OUT, `log-${PHASE}.json`), JSON.stringify(rows, null, 2))
  console.log(failed ? '\nSTOPPED ON A FAILURE' : '\nALL STEPS PASSED')
  process.exit(failed ? 1 : 0)
})()
