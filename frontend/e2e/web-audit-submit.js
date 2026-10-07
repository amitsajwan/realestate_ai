/* Checks the landing-page invite form submit path with the API MOCKED (nothing is sent anywhere). Usage: node e2e/web-audit-submit.js <outdir> <baseUrl> */
const path = require('path')
const { chromium } = require('playwright-core')
;(async () => {
  const b = await chromium.launch({ channel: 'chrome', headless: true })
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true })
  let body = null
  await ctx.route('**/request-invite', (r) => {
    if (r.request().method() === 'POST') { body = r.request().postData(); return r.fulfill({ status: 200, contentType: 'application/json', body: '{}' }) }
    return r.continue()
  })
  await ctx.route('**/api/**', (r) => (r.request().method() === 'GET' || /request-invite/.test(r.request().url()) ? r.fallback() : r.abort()))
  const p = await ctx.newPage()
  await p.goto(process.argv[3] + '/#invite', { waitUntil: 'networkidle' })
  await p.getByLabel('Your name').fill('Test Agent')
  await p.getByLabel('Mobile number').fill('98765 43210')
  await p.getByLabel(/OK to contact/).check()
  await p.getByRole('button', { name: /send request/i }).click()
  await p.getByText(/thank you/i).first().waitFor()
  await p.screenshot({ path: path.join(process.argv[2], 'landing-submit-ok-m.jpg'), type: 'jpeg', quality: 70 })
  console.log('mocked POST body:', body)
  await b.close()
})()
