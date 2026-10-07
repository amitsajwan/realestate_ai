import React from 'react'
import { render, screen } from '@testing-library/react'
import TrialPage from '@/app/trial/page'
import { claimHref } from '@/lib/marketing/trial'

describe('claim your free trial', () => {
  const saved = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER
  afterEach(() => { if (saved === undefined) delete process.env.NEXT_PUBLIC_WHATSAPP_NUMBER; else process.env.NEXT_PUBLIC_WHATSAPP_NUMBER = saved })

  it('opens WhatsApp with TRIAL typed in when the platform number is set, else the call-back form with the src tag', () => {
    expect(claimHref('reel_e1_fb', '98765 43210')).toBe('https://wa.me/919876543210?text=TRIAL')
    expect(claimHref('reel_e1_fb', undefined)).toBe('/request-invite?src=reel_e1_fb')
  })

  it('states the offer honestly and leads with the claim button', async () => {
    process.env.NEXT_PUBLIC_WHATSAPP_NUMBER = '9876543210'
    render(await TrialPage({ searchParams: Promise.resolve({ src: 'reel_e1_fb' }) }))
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/give us one property\. watch it go live\./i)
    expect(screen.getByTestId('trial-claim')).toHaveAttribute('href', 'https://wa.me/919876543210?text=TRIAL')
    expect(screen.getByText(/first 3 properties marketed free, no card/i)).toBeInTheDocument()
    expect(document.body.textContent).toMatch(/Avasetu.s Facebook and Instagram with your name/)   // never "on your own Page"
    expect(document.body.textContent).not.toMatch(/pilot|in seconds|instantly|guaranteed/i)
    expect(screen.getAllByRole('link', { name: /^sign in$/i }).map((a) => a.getAttribute('href'))).toContain('/join')
  })
})
