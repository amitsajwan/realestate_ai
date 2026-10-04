/**
 * Landing page check (phone + desktop): full-page screenshots, no horizontal scroll, the sticky join bar appears after the hero
 * and hides at the form. Usage: node e2e/landing-shots.js [baseUrl] [outDir]
 */
const path = require('path')
const { chromium } = require('playwright-core')

const BASE = process.argv[2] || 'http://localhost:3100'
const OUT = process.argv[3] || path.join(__dirname, 'shots')

;(async () => {
  const b = await chromium.launch({ channel: 'chrome', headless: true })
  const problems = []
  for (const [name, vp] of [['phone', { width: 375, height: 800 }], ['desktop', { width: 1366, height: 900 }]]) {
    const p = await b.newPage({ viewport: vp, deviceScaleFactor: 1 })
    await p.goto(BASE + '/', { waitUntil: 'networkidle' })
    const overflow = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
    if (overflow > 0) problems.push(`${name}: page scrolls sideways by ${overflow}px`)
    await p.screenshot({ path: path.join(OUT, `landing-${name}-top.png`) })
    await p.screenshot({ path: path.join(OUT, `landing-${name}-full.png`), fullPage: true })
    if (name === 'phone') {
      const bar = p.getByTestId('sticky-join')
      const shown = async () => (await bar.getAttribute('aria-hidden')) === 'false'
      if (await shown()) problems.push('phone: sticky bar visible over the hero')
      await p.evaluate(() => window.scrollTo(0, 1400)); await p.waitForTimeout(400)
      if (!(await shown())) problems.push('phone: sticky bar missing after the hero')
      await p.screenshot({ path: path.join(OUT, 'landing-phone-sticky.png') })
      await p.evaluate(() => document.getElementById('invite').scrollIntoView()); await p.waitForTimeout(400)
      if (await shown()) problems.push('phone: sticky bar covers the form')
    }
    await p.close()
  }
  await b.close()
  console.log(problems.length ? 'PROBLEMS:\n' + problems.join('\n') : 'ALL OK')
})()
