/*
 * Admin run (stream AD1): the owner's Admin home, step by step on the LIVE site with test data, phone viewport, system Chrome.
 *
 *   PHASE=signup CODE=<invite code for the temp owner 9000000015> node e2e/admin-run.js   # sign in, create his site, keep the session
 *   (then on the server: python scripts/g1_testdata.py promote 9000000015)
 *   PHASE=admin node e2e/admin-run.js       # every Admin section; pauses after "Pause posting" until OUT/resume.flag exists
 *
 * Env: APP_URL (default the live site), OUT (screenshots + log, default e2e/.out/admin), SHOTS (copy of the guide screenshots,
 * default docs/brand/avasetu/guide). Test data only: temp owner 9000000015, agent 9000000016 'Admin Test Agent', website request
 * 9000000017 'Admin Web Person'. Nothing is posted to Facebook or Instagram. Clean up with backend/scripts/g1_testdata.py.
 */
const fs = require('fs')
const path = require('path')
const { chromium } = require('playwright-core')

const APP = process.env.APP_URL || 'https://34-180-39-243.sslip.io'
const OUT = process.env.OUT || path.join(__dirname, '.out', 'admin')
const SHOTS = process.env.SHOTS || path.join(__dirname, '..', '..', 'docs', 'brand', 'avasetu', 'guide')
const PHASE = process.env.PHASE || 'admin'
const CODE = process.env.CODE || ''
const STATE = path.join(OUT, 'state.json')
const SESSION = path.join(OUT, 'owner-session.json')
const RESUME = path.join(OUT, 'resume.flag')
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

async function newPhone(browser, storageState) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: 'en-IN', storageState })
  await ctx.grantPermissions(['clipboard-read', 'clipboard-write'], { origin: APP }).catch(() => {})
  const page = await ctx.newPage()
  page.setDefaultTimeout(45000)
  curPage = page
  const errors = []
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message.slice(0, 160)))
  page.on('response', (r) => { if (r.status() >= 400 && r.url().includes('/api/')) errors.push(`HTTP ${r.status()} ${r.request().method()} ${r.url().replace(/^.*\/api\/v1/, '').slice(0, 90)}`) })
  return { ctx, page, errors }
}
/** Guide screenshots: jpg under 130 KB (quality steps down until it fits). */
async function shot(page, name) {
  for (const q of [62, 52, 42, 34]) {
    const buf = await page.screenshot({ type: 'jpeg', quality: q })
    if (buf.length < 130 * 1024 || q === 34) {
      fs.writeFileSync(path.join(OUT, name + '.jpg'), buf)
      if (name.startsWith('admin-')) fs.writeFileSync(path.join(SHOTS, name + '.jpg'), buf)
      return
    }
  }
}
const settle = async (page, ms = 800) => { await page.waitForLoadState('networkidle', { timeout: 20000 }).catch(() => {}); await page.waitForTimeout(ms) }
const text = (page) => page.locator('body').innerText()
const top = (page, sel) => page.locator(sel).first().evaluate((el) => el.scrollIntoView({ block: 'start' }))

async function makeLogo(browser, file) {
  const p = await browser.newPage({ viewport: { width: 400, height: 400 } })
  await p.setContent(`<div id=l style="width:400px;height:400px;display:flex;align-items:center;justify-content:center;background:#102340;
    font:800 140px/1 Arial,sans-serif;color:#F0B13B;letter-spacing:-6px">AD1</div>`)
  await p.locator('#l').screenshot({ path: file, type: 'png' })
  await p.close()
}

async function signup(browser) {
  if (!CODE) throw new Error('CODE is required')
  const { ctx, page, errors } = await newPhone(browser)
  try {
    await step('S1 temp owner 9000000015 signs in with his invite code', async () => {
      await page.goto(APP + '/join', { waitUntil: 'domcontentloaded' })
      await page.locator('#phone').waitFor()
      await settle(page, 1500)
      await page.locator('#phone').fill('9000000015')
      await page.getByRole('button', { name: /Send OTP|Continue|Next/ }).click()
      await page.getByText('Enter your 6-digit invite code').waitFor()
      await page.getByLabel(/code|OTP/i).first().fill(CODE)
      await Promise.race([page.locator('#name').waitFor({ timeout: 30000 }), page.waitForURL(/\/studio/, { timeout: 30000 })])
    })
    if (await page.locator('#name').count()) await step('S2 create his site', async () => {
      await page.locator('#name').fill('Admin Temp Owner')
      await page.locator('#city').fill('Pune')
      await page.locator('#biz').fill('Admin Temp Owner')
      await page.getByTestId('join-preset-navy-gold').click()
      await page.getByRole('button', { name: 'Create my website' }).click()
      await page.getByText('Your website is live').waitFor({ timeout: 60000 })
    })
    await ctx.storageState({ path: SESSION })
  } finally {
    console.log('API errors:', [...new Set(errors)].join('\n  ') || 'none')
  }
}

async function admin(browser) {
  const { page, errors } = await newPhone(browser, SESSION)
  const adminSection = (id) => page.getByTestId('admin-' + id)
  try {
    await step('D1 open Admin (first owner tab)', async () => {
      await page.goto(APP + '/studio', { waitUntil: 'domcontentloaded' })
      await settle(page, 2000)
      const tab = page.locator('nav[aria-label=Main] a[href="/studio/admin"]')
      await tab.waitFor({ timeout: 20000 })
      const labels = await page.locator('nav[aria-label=Main] a').allInnerTexts()
      await tab.click()
      await page.getByTestId('admin-screen').waitFor({ timeout: 30000 })
      await settle(page, 1500)
      await shot(page, 'admin-01-top')
      return 'tabs: ' + labels.map((l) => l.trim()).join(' | ')
    })
    await step('D2 Today tiles; the Leads tile opens Leads', async () => {
      await top(page, '[data-testid=admin-today]')
      await page.waitForTimeout(400)
      await shot(page, 'admin-02-today')
      const tiles = await adminSection('today').locator('a').allInnerTexts()
      await page.getByTestId('tile-leads').click()
      await page.waitForURL(/\/studio\/leads/)
      await page.goBack()
      await page.getByTestId('admin-screen').waitFor()
      return tiles.map((t) => t.replace(/\s+/g, ' ').trim()).join(' / ')
    })
    await step('D3 Add agent: Admin Test Agent 9000000016, code and WhatsApp message, copy', async () => {
      await page.getByTestId('admin-add-agent').click()
      await page.getByLabel('His name').fill('Admin Test Agent')
      await page.getByLabel('His mobile number').fill('9000000016')
      await page.getByLabel(/Label for you/).fill('AD1 admin guide test')
      await shot(page, 'admin-03-add-agent')
      await page.getByRole('button', { name: 'Create agent' }).click()
      await page.getByTestId('invite-code').waitFor({ timeout: 30000 })
      const msg = await page.locator('#ag-msg').inputValue()
      await page.getByRole('button', { name: 'Copy message' }).click()
      await page.getByRole('button', { name: 'Copied!' }).waitFor({ timeout: 5000 })
      const clip = await page.evaluate(() => navigator.clipboard.readText()).catch(() => '')
      await page.getByTestId('invite-code').evaluate((el) => { el.textContent = '••••••' })
      await page.locator('#ag-msg').evaluate((el) => { el.value = el.value.replace(/\b\d{6}\b/g, '••••••').replace(/\b(\d{2})\d{6}(\d{2})\b/g, '$1******$2') })
      await shot(page, 'admin-03-agent-code')
      await page.getByRole('button', { name: 'Done' }).click()
      state.addMsg = msg.replace(/\b\d{6}\b/g, '<code>')
      save()
      if (clip && clip !== msg) throw new Error('clipboard does not hold the message')
      return (clip ? 'copied; ' : 'copy button confirmed; ') + state.addMsg.slice(0, 120)
    })
    await step('D4 Agents section shows him with a ring and hints; tap opens his detail', async () => {
      await settle(page, 1500)
      const row = page.getByTestId('admin-agent-row').filter({ hasText: 'Admin Test Agent' }).first()
      await row.waitFor({ timeout: 30000 })
      await top(page, '[data-testid=admin-agents]')
      await page.waitForTimeout(400)
      await shot(page, 'admin-04-agents')
      const hint = (await row.innerText()).replace(/\s+/g, ' ')
      await row.click()
      await page.waitForURL(/\/studio\/agents\/[^/]+$/)
      state.agentId = page.url().split('/').pop()
      save()
      await settle(page, 1500)
      await shot(page, 'admin-04-agent-detail')
      if (/9000000016/.test(await text(page))) throw new Error('unmasked number on the detail screen')
      return hint
    })
    await step('D5 his brand: business name, tagline, area, logo, RERA, save', async () => {
      const ed = page.getByTestId('brand-editor')
      await ed.waitFor()
      await page.locator('#brand-name').fill('AD1 Test Homes')
      await page.locator('#brand-tagline').fill('Resale flats in Kharadi')
      const b = ed.getByRole('button', { name: 'Kharadi', exact: true })
      if ((await b.getAttribute('aria-pressed')) !== 'true') await b.click()
      const logo = path.join(OUT, 'ad1-logo.png')
      await makeLogo(browser, logo)
      await page.locator('#brand-logo').setInputFiles(logo)
      await page.waitForFunction(() => !!document.querySelector('[data-testid=brand-editor] img'), null, { timeout: 30000 })
      await page.locator('#brand-rera').fill('A51800077777').catch(() => {})
      await ed.scrollIntoViewIfNeeded()
      await shot(page, 'admin-05-brand')
      await page.getByRole('button', { name: /Save/ }).first().click()
      await page.getByText(/Saved/).first().waitFor({ timeout: 30000 })
    })
    await step('D6 record his consent', async () => {
      await page.getByTestId('consent-text').waitFor()
      const sw = page.getByRole('switch')
      if ((await sw.getAttribute('aria-checked')) !== 'true') await sw.click()
      await page.waitForFunction(() => document.querySelector('[role=switch]')?.getAttribute('aria-checked') === 'true', null, { timeout: 30000 })
      await page.getByTestId('consent-text').scrollIntoViewIfNeeded()
      await page.waitForTimeout(500)
      await shot(page, 'admin-06-consent')
    })
    await step('D7 back in Admin: his ring moved and the hints changed', async () => {
      await page.goto(APP + '/studio/admin', { waitUntil: 'domcontentloaded' })
      await page.getByTestId('admin-screen').waitFor()
      const row = page.getByTestId('admin-agent-row').filter({ hasText: 'Admin Test Agent' }).first()
      await row.waitFor()
      const ring = await row.getByTestId('progress-ring').getAttribute('aria-label')
      const t = (await row.innerText()).replace(/\s+/g, ' ')
      if (/record consent|add logo/.test(t)) throw new Error('hints still ask for logo or consent: ' + t)
      return `${ring}; ${t}`
    })
    await step('D8 a person asks to join on /request-invite (9000000017)', async () => {
      const p = await newPhone(browser)
      const pg = p.page
      await pg.goto(APP + '/request-invite', { waitUntil: 'domcontentloaded' })
      await settle(pg, 1500)
      await pg.getByLabel('Your name').fill('Admin Web Person')
      await pg.getByLabel('Mobile number').fill('9000000017')
      const more = pg.locator('details summary').first()
      if (await more.count()) await more.click()
      await pg.getByLabel(/Anything you would like us to know/).fill('Test request from the admin guide run, Kharadi resale').catch(() => {})
      await pg.getByLabel('OK to contact me about the pilot').check()
      await pg.getByRole('button', { name: 'Send request' }).click()
      await pg.getByText(/Thank you/).first().waitFor({ timeout: 30000 })
      await shot(pg, 'admin-07-request-sent')
      await p.ctx.close()
      curPage = page
    })
    await step('D9 Needs you shows the request; Invite gives his code and message', async () => {
      await page.goto(APP + '/studio/admin', { waitUntil: 'domcontentloaded' })
      await page.getByTestId('admin-screen').waitFor()
      await settle(page, 1000)
      const row = page.getByTestId('invite-row').filter({ hasText: 'Admin Web Person' }).first()
      await row.waitFor({ timeout: 30000 })
      await top(page, '[data-testid=admin-needs]')
      await page.waitForTimeout(400)
      await shot(page, 'admin-08-needs-you')
      const shown = (await row.innerText()).replace(/\s+/g, ' ')
      if (/9000000017/.test(shown)) throw new Error('unmasked number in Needs you')
      await row.getByRole('button', { name: 'Invite' }).click()
      await page.getByTestId('invite-code').waitFor({ timeout: 30000 })
      const msg = await page.locator('#adm-msg').inputValue()
      await page.getByTestId('invite-code').evaluate((el) => { el.textContent = '••••••' })
      await page.locator('#adm-msg').evaluate((el) => { el.value = el.value.replace(/\b\d{6}\b/g, '••••••').replace(/\b(\d{2})\d{6}(\d{2})\b/g, '$1******$2') })
      await shot(page, 'admin-08-invited')
      await page.getByRole('button', { name: 'Done' }).click()
      return shown + ' -> ' + msg.replace(/\b\d{6}\b/g, '<code>').slice(0, 110)
    })
    await step('D10 the invited person is now in Agents and the request is gone', async () => {
      await settle(page, 1500)
      await page.getByTestId('admin-agent-row').filter({ hasText: 'Admin Web Person' }).first().waitFor({ timeout: 30000 })
      if (await page.getByTestId('invite-row').filter({ hasText: 'Admin Web Person' }).count()) throw new Error('request still listed')
      await top(page, '[data-testid=admin-agents]')
      await page.waitForTimeout(400)
      await shot(page, 'admin-09-agents-after')
    })
    await step('D11 Pause posting (with confirmation)', async () => {
      await top(page, '[data-testid=admin-controls]')
      const sw = page.getByRole('switch', { name: 'Pause posting' })
      await sw.click()
      await page.getByTestId('control-confirm').waitFor()
      await shot(page, 'admin-10-pause-confirm')
      await page.getByRole('button', { name: 'Yes, pause posting' }).click()
      await page.waitForFunction(() => document.querySelector('[aria-label="Pause posting"]')?.getAttribute('aria-checked') === 'true', null, { timeout: 30000 })
      await settle(page, 1500)
      await top(page, '[data-testid=admin-controls]')
      await page.waitForTimeout(400)
      await shot(page, 'admin-10-paused')
      const posting = await page.getByTestId('health-row').filter({ hasText: 'Posting' }).innerText()
      if (!/Paused by you/.test(posting)) throw new Error('Health does not say Paused by you: ' + posting)
      state.pausedAt = new Date().toISOString()
      save()
      return 'Health: ' + posting.replace(/\s+/g, ' ')
    })
    await step('D12 (outside) flag stored and the calendar runner logs "paused by owner"; waiting for resume.flag', async () => {
      if (fs.existsSync(RESUME)) fs.unlinkSync(RESUME)
      const t0 = Date.now()
      while (!fs.existsSync(RESUME)) {
        if (Date.now() - t0 > 20 * 60 * 1000) throw new Error('no resume.flag after 20 minutes')
        await page.waitForTimeout(3000)
      }
      return fs.readFileSync(RESUME, 'utf8').trim().slice(0, 200)
    })
    await step('D13 Resume posting', async () => {
      await page.reload({ waitUntil: 'domcontentloaded' })
      await page.getByTestId('admin-screen').waitFor()
      await top(page, '[data-testid=admin-controls]')
      await page.getByRole('switch', { name: 'Pause posting' }).click()
      await page.getByRole('button', { name: 'Yes, resume posting' }).click()
      await page.waitForFunction(() => document.querySelector('[aria-label="Pause posting"]')?.getAttribute('aria-checked') === 'false', null, { timeout: 30000 })
      await settle(page, 1000)
      const posting = await page.getByTestId('health-row').filter({ hasText: 'Posting' }).innerText()
      if (/Paused by you/.test(posting)) throw new Error('still paused in Health')
      return 'Health: ' + posting.replace(/\s+/g, ' ')
    })
    await step('D14 Health section', async () => {
      await top(page, '[data-testid=admin-health]')
      await page.waitForTimeout(400)
      await shot(page, 'admin-11-health')
      const rowsTxt = await page.getByTestId('health-row').evaluateAll((els) => els.map((e) => `${e.getAttribute('data-status')}: ${e.innerText.replace(/\s+/g, ' ')}`))
      state.health = rowsTxt
      save()
      return '\n    ' + rowsTxt.join('\n    ')
    })
  } finally {
    console.log('API errors:', [...new Set(errors)].join('\n  ') || 'none')
  }
}

;(async () => {
  const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || 'chrome', headless: true })
  let failed = false
  try {
    await ({ signup, admin }[PHASE])(browser)
  } catch (e) {
    failed = true
  }
  await browser.close()
  fs.writeFileSync(path.join(OUT, `log-${PHASE}.json`), JSON.stringify(rows, null, 2))
  console.log(failed ? '\nSTOPPED ON A FAILURE' : '\nALL STEPS PASSED')
  process.exit(failed ? 1 : 0)
})()
