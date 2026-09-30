/*
 * Real-browser check for the price sanity guard in the new-listing review step (phone viewport, system Chrome):
 *   "85 cr" for a 2 BHK -> amber warning + post button disabled -> tick "Yes, this price is correct" -> enabled
 *   -> fixing the price to "85 lakh" clears the warning and the tick is no longer needed -> post works.
 * Same prereqs as browser-journey.js (MongoDB, backend :8000 with JOIN_MODE=otp, `npx next dev -p 3000`). Run: node e2e/price-check.js
 */
const fs = require('fs')
const path = require('path')
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, '.out', 'shots')
fs.mkdirSync(OUT, { recursive: true })
const APP = process.env.APP_URL || 'http://localhost:3000'
const phone = '9' + Array.from({ length: 9 }, () => Math.floor(Math.random() * 10)).join('')
const results = []
const log = (ok, name, extra = '') => { results.push(ok); console.log((ok ? 'PASS ' : 'FAIL ') + name + (extra ? '  ' + extra : '')) }

;(async () => {
  const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || 'chrome', headless: true })
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true })
  const page = await ctx.newPage()
  const shot = (n) => page.screenshot({ path: path.join(OUT, `price-${n}.png`) })
  try {
    await page.goto(APP + '/join', { waitUntil: 'networkidle' })
    await page.locator('#phone').fill(phone)
    await page.getByRole('button', { name: 'Send OTP' }).click()
    await page.getByText('Dev only: OTP is').waitFor({ timeout: 15000 })
    await page.getByRole('button', { name: 'Fill it' }).click()
    await page.locator('#name').waitFor({ timeout: 15000 })
    await page.locator('#name').fill('Price Tester')
    await page.locator('#city').fill('Pune')
    await page.getByRole('button', { name: 'Create my website' }).click()
    await page.getByText('Your website is live').waitFor({ timeout: 20000 })

    await page.goto(APP + '/studio/listings/new', { waitUntil: 'networkidle' })
    await page.locator('textarea').fill('2 BHK for sale in Baner Pune, 1100 sq ft carpet, 85 lakh, ready possession, parking, lift')
    await page.getByRole('button', { name: 'Next', exact: true }).click()
    await page.getByText('Check and confirm').waitFor({ timeout: 30000 })
    const post = page.getByRole('button', { name: /Confirm & post/ })
    const price = page.locator('#price')

    log(/85 lakh|85/.test(await price.inputValue()) && (await page.getByText(/Yes, this price is correct/).count()) === 0 && await post.isEnabled(),
      'a normal price (85 lakh) shows no warning and posting is enabled')

    await price.fill('85 cr')
    await page.waitForTimeout(300)
    const body = await page.locator('body').innerText()
    log(/very high for a 2 BHK apartment/.test(body) && /Did you mean ₹85 L\?/.test(body), '"85 cr" for a 2 BHK shows the warning with the 85 lakh suggestion')
    log(await post.isDisabled(), 'and the post button is disabled until the agent confirms')
    await shot('1-warning')

    await page.getByLabel(/Yes, this price is correct/).check()
    log(await post.isEnabled(), 'ticking "Yes, this price is correct" enables posting')
    await price.fill('86 cr')
    await page.waitForTimeout(300)
    log(await post.isDisabled(), 'changing the price clears the tick (a new price must be confirmed again)')

    await price.fill('85 lakh')
    await page.waitForTimeout(300)
    log((await page.getByText(/Yes, this price is correct/).count()) === 0 && await post.isEnabled(), 'fixing the price to 85 lakh removes the warning and enables posting')
    await shot('2-fixed')
    await post.click()
    await page.getByText('Your property is ready').waitFor({ timeout: 30000 })
    log(/85 L/.test(await page.locator('body').innerText()), 'the listing posts with ₹85 L')
  } catch (e) {
    log(false, 'journey aborted', e.message.split('\n')[0])
    await page.screenshot({ path: path.join(OUT, 'price-ZZ-failure.png') }).catch(() => {})
  }
  await browser.close()
  console.log(results.every(Boolean) ? '\nALL PASSED' : '\nSOME FAILED')
  process.exit(results.every(Boolean) ? 0 : 1)
})()
