/*
 * Browser check of the buyer chat (phone viewport, system Chrome): a visitor chats on an agent's site, asks a question mid-way, gives a requirement
 * with the quick-reply chips, is asked for consent before the phone number, and the agent then finds the lead (with the summary) in the inbox.
 * Same prereqs as browser-journey.js. Run: node e2e/chat-journey.js
 */
const fs = require('fs')
const path = require('path')
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, '.out', 'shots')
fs.mkdirSync(OUT, { recursive: true })
const APP = process.env.APP_URL || 'http://localhost:3000'
const API = (process.env.API_URL || 'http://localhost:8000') + '/api/v1'
const rnd = (n) => Array.from({ length: n }, () => Math.floor(Math.random() * 10)).join('')
const agentPhone = '98' + rnd(8)
const buyerPhone = '9' + '8' + rnd(8)
const results = []
const log = (ok, name, extra = '') => { results.push(ok); console.log((ok ? 'PASS ' : 'FAIL ') + name + (extra ? '  ' + extra : '')) }
const post = (p, body, token) => fetch(API + p, { method: 'POST', headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: 'Bearer ' + token } : {}) }, body: JSON.stringify(body) })

;(async () => {
  const dev = await (await post('/join/otp/request', { phone: agentPhone })).json()
  const login = await (await post('/join/otp/verify', { phone: agentPhone, code: dev.dev_code })).json()
  const site = await (await post('/join/site', { name: 'Chat Tester', city: 'Pune' }, login.access_token)).json()
  const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || 'chrome', headless: true })
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true })
  const page = await ctx.newPage()
  const widget = page.getByTestId('chat-widget')
  const lastBot = async () => (await widget.locator('[role=log] p').allInnerTexts()).pop() || ''
  const waitFor = async (re, ms = 20000) => { const t = Date.now(); while (Date.now() - t < ms) { if (re.test(await lastBot())) return true; await page.waitForTimeout(300) } return false }
  try {
    await page.goto(`${APP}/agent/${site.slug}`, { waitUntil: 'networkidle' })
    await widget.getByRole('button', { name: /Chat with us/ }).click()
    log(await waitFor(/buy or to rent/), 'the chat opens with a greeting and asks buy or rent')
    await page.screenshot({ path: path.join(OUT, 'chat-1-open.png') })
    await widget.getByRole('button', { name: 'Buy' }).click()
    log(await waitFor(/Which area/), 'a quick-reply chip answers and the next question follows')
    // a question in the middle
    await widget.getByLabel('Your message').fill('How do I check RERA?')
    await widget.getByRole('button', { name: 'Send' }).click()
    log(await waitFor(/MahaRERA[\s\S]*Which area/), 'a basic question is answered from the knowledge base, then the same question is asked again')
    await widget.getByRole('button', { name: 'Kharadi', exact: true }).click()
    await waitFor(/bedrooms/)
    await widget.getByRole('button', { name: '2 BHK' }).click()
    await waitFor(/budget/)
    await widget.getByRole('button', { name: '80 lakh to 1.2 crore' }).click()
    // a new agent has no listings yet: the chat says so honestly and offers the agent's help, with consent next to the ask
    log(await waitFor(/could not find a listed home[\s\S]*mobile number[\s\S]*agree that Avasetu may contact you/),
      'no matching home is said plainly; consent is shown together with the request for the phone number')
    await page.screenshot({ path: path.join(OUT, 'chat-2-consent.png') })
    await widget.getByLabel('Your message').fill('I am Priya Sharma')
    await widget.getByRole('button', { name: 'Send' }).click()
    log(await waitFor(/Thanks, Priya[\s\S]*planning to move/), 'the name is taken and the next question follows, without asking for the number again')
    let leads = await (await fetch(API + '/inbox/leads', { headers: { Authorization: 'Bearer ' + login.access_token } })).json()
    log(leads.leads.length === 0, 'no lead exists before the visitor shares a number')
    await widget.getByLabel('Your message').fill(buyerPhone)
    await widget.getByRole('button', { name: 'Send' }).click()
    log(await waitFor(/Thank you, Priya/), 'after the number, the assistant thanks the visitor by name')
    await page.screenshot({ path: path.join(OUT, 'chat-3-done.png') })

    leads = await (await fetch(API + '/inbox/leads', { headers: { Authorization: 'Bearer ' + login.access_token } })).json()
    const lead = leads.leads[0]
    log(leads.leads.length === 1 && lead.name === 'Priya Sharma', 'the agent sees exactly one new lead with the visitor\'s name', lead && lead.name)
    const detail = await (await fetch(API + `/inbox/leads/${lead.id}`, { headers: { Authorization: 'Bearer ' + login.access_token } })).json()
    const blob = JSON.stringify(detail)
    log(/Kharadi/.test(blob) && /chat/i.test(blob) && /RERA/.test(blob), 'the lead carries the chat summary (area, source, the question asked)')

    // it persists across a reload
    await page.reload({ waitUntil: 'networkidle' })
    await widget.getByRole('button', { name: /Chat with us/ }).click()
    log((await widget.locator('[role=log] p').count()) >= 6, 'the conversation is still there after a reload')
  } catch (e) {
    log(false, 'journey aborted', e.message.split('\n')[0])
    await page.screenshot({ path: path.join(OUT, 'chat-ZZ-failure.png') }).catch(() => {})
  }
  await browser.close()
  console.log(results.every(Boolean) ? '\nALL PASSED' : '\nSOME FAILED')
  process.exit(results.every(Boolean) ? 0 : 1)
})()
