import React from 'react'
import { render, screen, within } from '@testing-library/react'
import PrivacyPage from '@/app/privacy/page'
import TermsPage from '@/app/terms/page'
import DataDeletionPage from '@/app/data-deletion/page'
import { LEGAL_LAST_UPDATED } from '@/lib/marketing/strings'

const ENV = ['NEXT_PUBLIC_BUSINESS_NAME', 'NEXT_PUBLIC_CONTACT_EMAIL', 'NEXT_PUBLIC_CONTACT_WHATSAPP'] as const
const saved: Record<string, string | undefined> = {}
beforeEach(() => ENV.forEach((k) => { saved[k] = process.env[k]; delete process.env[k] }))
afterEach(() => ENV.forEach((k) => { if (saved[k] === undefined) delete process.env[k]; else process.env[k] = saved[k] }))

const headings = (names: RegExp[]) =>
  names.forEach((n) => expect(screen.getByRole('heading', { level: 2, name: n })).toBeInTheDocument())

const sharedChecks = (title: RegExp) => {
  expect(screen.getByRole('heading', { level: 1, name: title })).toBeInTheDocument()
  expect(screen.getByText(LEGAL_LAST_UPDATED)).toBeInTheDocument()
  const footer = screen.getByRole('contentinfo')
  for (const [name, href] of [['Privacy', '/privacy'], ['Terms', '/terms'], ['Data deletion', '/data-deletion'], ['Join free', '/trial'], ['Sign in', '/studio']]) {
    expect(within(footer).getByRole('link', { name })).toHaveAttribute('href', href)
  }
  expect(screen.getByText(/not legal advice/i)).toBeInTheDocument()
}

describe('privacy page', () => {
  it('renders its key headings, date and cross links', () => {
    render(<PrivacyPage />)
    sharedChecks(/privacy policy/i)
    headings([/who we are/i, /what we collect/i, /why we use it/i, /who sees your data/i, /how long we keep/i, /your rights/i, /children/i, /security/i, /contact and grievances/i])
    expect(screen.getByText(/Digital Personal Data Protection Act, 2023/)).toBeInTheDocument()
  })

  it('shows no email and says details are shared with an invite when none is configured', () => {
    const { container } = render(<PrivacyPage />)
    // the site footer names the team behind the site with its email (site-nav.test pins it); the policy itself names none
    container.querySelector('footer')?.remove()
    expect(container.querySelector('a[href^="mailto:"]')).toBeNull()
    expect(container.textContent).not.toMatch(/[\w.+-]+@[\w-]+\.[\w.]+/)
    expect(screen.getAllByText(/contact details are shared when you request an invite/i).length).toBeGreaterThan(0)
  })

  it('shows the configured email and WhatsApp', () => {
    process.env.NEXT_PUBLIC_BUSINESS_NAME = 'Acme Homes'
    process.env.NEXT_PUBLIC_CONTACT_EMAIL = 'privacy@acme.example'
    process.env.NEXT_PUBLIC_CONTACT_WHATSAPP = '919876543210'
    render(<PrivacyPage />)
    expect(screen.getAllByRole('link', { name: 'privacy@acme.example' })[0]).toHaveAttribute('href', 'mailto:privacy@acme.example')
    expect(screen.getAllByRole('link', { name: '+91 98765 43210' })[0]).toHaveAttribute('href', 'https://wa.me/919876543210')
    expect(screen.getAllByText(/Acme Homes/).length).toBeGreaterThan(0)
  })
})

describe('terms page', () => {
  it('renders its key headings, date and cross links', () => {
    render(<TermsPage />)
    sharedChecks(/terms of service/i)
    headings([/who may use it/i, /what agents are responsible for/i, /how agents may use buyer data/i, /service provided as is/i, /liability/i, /governing law/i])
    expect(screen.getByText(/Courts in Pune/)).toBeInTheDocument()
    expect(screen.getByText(/including RERA registration/)).toBeInTheDocument()
  })
})

describe('data deletion page', () => {
  it('renders the instructions, 30-day timeline and cross links', () => {
    render(<DataDeletionPage />)
    sharedChecks(/data deletion/i)
    headings([/data deletion instructions/i, /what we need from you/i, /what we delete/i, /how long it takes/i, /what we may keep/i])
    expect(screen.getAllByText(/within 30 days/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/Delete my data/, { selector: 'li' })).toBeInTheDocument()
  })

  it('points to the configured channels when set', () => {
    process.env.NEXT_PUBLIC_CONTACT_EMAIL = 'delete@acme.example'
    render(<DataDeletionPage />)
    expect(screen.getByText(/email delete@acme.example/i)).toBeInTheDocument()
  })
})

describe('YouTube API disclosures (YouTube API Services Terms, needed for the upload audit)', () => {
  it('the privacy policy says how we use YouTube and links Google\'s Privacy Policy, YouTube\'s Terms and the revoke page', () => {
    render(<PrivacyPage />)
    headings([/our youtube channel and the youtube api/i])
    expect(screen.getByRole('link', { name: 'Google Privacy Policy' })).toHaveAttribute('href', 'https://policies.google.com/privacy')
    expect(screen.getByRole('link', { name: 'YouTube Terms of Service' })).toHaveAttribute('href', 'https://www.youtube.com/t/terms')
    expect(screen.getByRole('link', { name: /google security settings/i })).toHaveAttribute('href', 'https://security.google.com/settings/security/permissions')
    expect(screen.getByText(/do not collect, store or share any YouTube or Google data about you/)).toBeInTheDocument()
  })

  it('the terms bind users of our YouTube content to YouTube\'s Terms of Service', () => {
    render(<TermsPage />)
    headings([/^youtube$/i])
    expect(screen.getByText(/agree to be bound by the YouTube Terms of Service/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'YouTube Terms of Service' })).toHaveAttribute('target', '_blank')
  })
})
