/** The old phone stylesheet must not pad Studio's own frame or its sheets: a 16 px border went round the whole app on phones. */
import fs from 'fs'
import path from 'path'

it('every .fixed.inset-0 rule in mobile.css leaves Studio (data-surface v2) alone', () => {
  const css = fs.readFileSync(path.join(__dirname, '../../styles/mobile.css'), 'utf8')
  const selectors = css.split('\n').filter((l) => l.includes('.fixed.inset-0') && l.includes('{'))
  expect(selectors.length).toBeGreaterThan(0)
  for (const s of selectors) expect(s).toContain(':not([data-surface="v2"]):not([data-surface="v2"] *)')
})
