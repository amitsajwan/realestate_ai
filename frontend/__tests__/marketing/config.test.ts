import { buildMarketingConfig, hasContact } from '@/lib/marketing/config'
import { organizationJsonLd } from '@/lib/marketing/seo'

describe('marketing config', () => {
  it('defaults the business name and shows no contact when nothing is set', () => {
    const c = buildMarketingConfig({})
    expect(c.businessName).toBe('PUNE Property')
    expect(c.email).toBeNull()
    expect(c.whatsappUrl).toBeNull()
    expect(c.whatsappDisplay).toBeNull()
    expect(hasContact(c)).toBe(false)
  })

  it('treats blank or malformed values as unset', () => {
    const c = buildMarketingConfig({ NEXT_PUBLIC_CONTACT_EMAIL: '  ', NEXT_PUBLIC_CONTACT_WHATSAPP: 'abc', NEXT_PUBLIC_BUSINESS_NAME: ' ' })
    expect(c.email).toBeNull()
    expect(c.whatsappUrl).toBeNull()
    expect(c.businessName).toBe('PUNE Property')
    expect(buildMarketingConfig({ NEXT_PUBLIC_CONTACT_EMAIL: 'not an email' }).email).toBeNull()
  })

  it('uses configured values', () => {
    const c = buildMarketingConfig({
      NEXT_PUBLIC_BUSINESS_NAME: 'Acme Homes', NEXT_PUBLIC_CONTACT_EMAIL: 'hello@example.com',
      NEXT_PUBLIC_CONTACT_WHATSAPP: '919876543210', NEXT_PUBLIC_SITE_URL: 'https://example.in/',
    })
    expect(c).toMatchObject({
      businessName: 'Acme Homes', email: 'hello@example.com', whatsappUrl: 'https://wa.me/919876543210',
      whatsappDisplay: '+91 98765 43210', siteUrl: 'https://example.in',
    })
    expect(hasContact(c)).toBe(true)
  })

  it('adds the country code to a bare 10-digit WhatsApp number', () => {
    expect(buildMarketingConfig({ NEXT_PUBLIC_CONTACT_WHATSAPP: '98765 43210' }).whatsappDigits).toBe('919876543210')
  })

  it('org JSON-LD carries only known facts', () => {
    const bare = organizationJsonLd(buildMarketingConfig({}), 'desc')
    expect(bare).toMatchObject({ '@type': 'Organization', name: 'PUNE Property' })
    expect(bare.contactPoint).toBeUndefined()
    expect(JSON.stringify(bare)).not.toMatch(/mailto|"email"|telephone/)
    const withEmail = organizationJsonLd(buildMarketingConfig({ NEXT_PUBLIC_CONTACT_EMAIL: 'a@b.in' }), 'desc')
    expect(JSON.stringify(withEmail.contactPoint)).toContain('a@b.in')
  })
})
