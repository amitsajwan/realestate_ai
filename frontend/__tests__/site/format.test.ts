import { bhkLabel, floorLabel, formatArea, formatInr, formatPrice, groupIndian } from '@/lib/site/format'
import { themeVars } from '@/lib/site/theme'
import { withParam, whatsappLink, telLink } from '@/lib/site/links'

describe('formatInr', () => {
  it('formats lakh and crore', () => {
    expect(formatInr(8500000)).toBe('85 L')
    expect(formatInr(12500000)).toBe('1.25 Cr')
    expect(formatInr(10000000)).toBe('1 Cr')
    expect(formatInr(9800000)).toBe('98 L')
    expect(formatInr(950000)).toBe('9.5 L')
  })
  it('formats rent per month with Indian grouping', () => {
    expect(formatInr(45000, 'rent')).toBe('₹45,000/mo')
    expect(formatInr(125000, 'rent')).toBe('₹1,25,000/mo')
  })
  it('small sale amounts and bad input', () => {
    expect(formatInr(50000)).toBe('₹50,000')
    expect(formatInr(-1)).toBe('')
    expect(formatInr(NaN)).toBe('')
  })
  it('formatPrice adds the rupee sign', () => {
    expect(formatPrice(8500000)).toBe('₹85 L')
    expect(formatPrice(22000, 'rent')).toBe('₹22,000/mo')
  })
})

describe('labels', () => {
  it('groupIndian', () => expect(groupIndian(4500000)).toBe('45,00,000'))
  it('formatArea', () => {
    expect(formatArea(1150)).toBe('1,150 sq.ft')
    expect(formatArea(null)).toBe('')
  })
  it('bhkLabel', () => {
    expect(bhkLabel(2)).toBe('2 BHK')
    expect(bhkLabel(2.5)).toBe('2.5 BHK')
    expect(bhkLabel(null, 'plot')).toBe('Plot')
  })
  it('floorLabel', () => {
    expect(floorLabel(7, 14)).toBe('7 of 14')
    expect(floorLabel(0, 3)).toBe('Ground of 3')
    expect(floorLabel(null)).toBe('')
  })
})

describe('links and theme', () => {
  it('builds wa.me and tel links only for valid Indian mobiles', () => {
    expect(whatsappLink('+91 98765 43210', 'Hi there')).toBe('https://wa.me/919876543210?text=Hi%20there')
    expect(telLink('9876543210')).toBe('tel:+919876543210')
    expect(whatsappLink('12345', 'x')).toBeNull()
  })
  it('withParam appends and keeps hash', () => {
    expect(withParam('https://a.in/x', 'src', 'share')).toBe('https://a.in/x?src=share')
    expect(withParam('https://a.in/x?a=1#h', 'src', 'share')).toBe('https://a.in/x?a=1&src=share#h')
  })
  it('themeVars always uses the Avasetu brand (stored agent colours, even hostile ones, are ignored)', () => {
    const v = themeVars({ colors: { primary: '#0f766e', secondary: 'red;}', accent: '#fff' } })
    expect(v['--site-primary']).toBe('#102340')
    expect(v['--site-secondary']).toBe('#0b1a33')
    expect(v['--site-accent']).toBe('#f0b440')
    expect(v['--site-on-primary']).toBe('#ffffff')
    expect(themeVars(null)['--site-primary']).toBe('#102340')
  })
})
