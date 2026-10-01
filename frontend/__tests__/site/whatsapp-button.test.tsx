import React from 'react'
import { render, screen } from '@testing-library/react'
import WhatsAppButton, { waLink, waNumber, waText } from '@/components/site/WhatsAppButton'

describe('WhatsAppButton', () => {
  const saved = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER
  afterEach(() => {
    if (saved === undefined) delete process.env.NEXT_PUBLIC_WHATSAPP_NUMBER
    else process.env.NEXT_PUBLIC_WHATSAPP_NUMBER = saved
  })

  it('renders nothing when no platform number is configured', () => {
    delete process.env.NEXT_PUBLIC_WHATSAPP_NUMBER
    const { container } = render(<WhatsAppButton title="2 BHK in Kharadi" code="abcd234" />)
    expect(container).toBeEmptyDOMElement()
  })

  it('opens wa.me with the prefilled interest message and the ref code', () => {
    process.env.NEXT_PUBLIC_WHATSAPP_NUMBER = '+1 555 078 3881'
    render(<WhatsAppButton title="2 BHK in Kharadi" code="abcd234" />)
    const a = screen.getByRole('link', { name: /chat on whatsapp/i })
    const url = new URL(a.getAttribute('href') as string)
    expect(url.origin + url.pathname).toBe('https://wa.me/15550783881')
    expect(url.searchParams.get('text')).toBe('Hi, I am interested in 2 BHK in Kharadi (ref abcd234)')
    expect(a).toHaveAttribute('target', '_blank')
    expect(a.getAttribute('rel')).toContain('noopener')
  })

  it("never shows the agent's own number unless his branding opts in", () => {
    process.env.NEXT_PUBLIC_WHATSAPP_NUMBER = '15550783881'
    const { rerender } = render(<WhatsAppButton title="Home" code="abcd234" agentNumber="98765 43210" />)
    expect(screen.getByRole('link').getAttribute('href')).toContain('wa.me/15550783881')
    rerender(<WhatsAppButton title="Home" code="abcd234" agentNumber="98765 43210" showAgentNumber />)
    expect(screen.getByRole('link').getAttribute('href')).toContain('wa.me/919876543210')
  })

  it('an opted-in agent number works even without a platform number', () => {
    delete process.env.NEXT_PUBLIC_WHATSAPP_NUMBER
    render(<WhatsAppButton title="Home" agentNumber="9876543210" showAgentNumber />)
    expect(screen.getByRole('link').getAttribute('href')).toContain('wa.me/919876543210')
  })

  it('helpers', () => {
    expect(waNumber('98765 43210')).toBe('919876543210')
    expect(waNumber('12345')).toBe('')
    expect(waNumber(undefined)).toBe('')
    expect(waText('', null)).toBe('Hi, I am interested in a home on PUNE Property')
    expect(waLink('919876543210', 'A & B', 'x')).toBe('https://wa.me/919876543210?text=' + encodeURIComponent('Hi, I am interested in A & B (ref x)'))
  })
})
