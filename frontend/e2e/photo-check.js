// Photos are optional and compressed in the browser: publishes with NO photo, then uploads a ~12 MB image and
// checks the stored file is a small fraction of it. Same prereqs as browser-journey.js. Run: node e2e/photo-check.js
const fs = require('fs'), path = require('path')
const { chromium } = require('playwright-core')
const APP = 'http://localhost:3000'
;(async () => {
  const b = await chromium.launch({ channel: 'chrome', headless: true })
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true })
  const p = await ctx.newPage()
  const phone = '9' + Array.from({ length: 9 }, () => Math.floor(Math.random() * 10)).join('')
  await p.goto(APP + '/join', { waitUntil: 'networkidle' })
  await p.locator('#phone').fill(phone); await p.getByRole('button', { name: 'Send OTP' }).click()
  await p.getByRole('button', { name: 'Fill it' }).click(); await p.locator('#name').waitFor()
  await p.locator('#name').fill('Photo Tester'); await p.locator('#city').fill('Pune')
  await p.getByRole('button', { name: 'Create my website' }).click(); await p.getByText('Your website is live').waitFor()

  const text = '3 BHK for sale in Wakad Pune, 1400 sq ft carpet, 1.2 crore, ready possession'
  // A) no photo at all
  await p.goto(APP + '/studio/listings/new', { waitUntil: 'networkidle' })
  await p.locator('textarea').fill(text)
  await p.getByRole('button', { name: 'Next', exact: true }).click()
  await p.getByText('Check and confirm').waitFor({ timeout: 30000 })
  await p.getByRole('button', { name: /Confirm & post/ }).click()
  await p.getByText('Your property is ready').waitFor({ timeout: 30000 })
  console.log('PASS listing with NO photo published')

  // B) large noisy photo -> measure what is actually uploaded
  const dir = require('path').join(__dirname, '..', '..', 'backend', 'uploads', 'images')
  const before = new Set(fs.readdirSync(dir))
  await p.goto(APP + '/studio/listings/new', { waitUntil: 'networkidle' })
  await p.locator('textarea').fill(text)
  const originalSize = await p.evaluate(async () => {
    const c = document.createElement('canvas'); c.width = 4000; c.height = 3000
    const x = c.getContext('2d'); const img = x.createImageData(4000, 3000)
    for (let i = 0; i < img.data.length; i += 4) { img.data[i] = Math.random() * 256; img.data[i + 1] = Math.random() * 256; img.data[i + 2] = Math.random() * 256; img.data[i + 3] = 255 }
    x.putImageData(img, 0, 0)
    const blob = await new Promise((r) => c.toBlob(r, 'image/jpeg', 0.95))
    const dt = new DataTransfer(); dt.items.add(new File([blob], 'big.jpg', { type: 'image/jpeg' }))
    const input = document.querySelector('input[type=file]'); input.files = dt.files
    input.dispatchEvent(new Event('change', { bubbles: true }))
    return blob.size
  })
  await p.getByRole('button', { name: 'Next', exact: true }).click()
  await p.getByText('Check and confirm').waitFor({ timeout: 60000 })
  await p.getByRole('button', { name: /Confirm & post/ }).click()
  await p.getByText('Your property is ready').waitFor({ timeout: 60000 })
  const fresh = fs.readdirSync(dir).filter((f) => !before.has(f))
  const uploaded = fresh.length ? fs.statSync(path.join(dir, fresh[0])).size : 0
  const kb = (n) => Math.round(n / 1024) + ' KB'
  console.log(`original ${kb(originalSize)} JPEG -> stored on server ${kb(uploaded)} ${fresh[0] || '(nothing stored)'}  (${(100 - (uploaded / originalSize) * 100).toFixed(0)}% smaller)`)
  console.log(uploaded > 0 && uploaded < originalSize / 3 ? 'PASS compression works in the browser' : 'FAIL compression did not shrink the upload')
  await b.close()
})()
