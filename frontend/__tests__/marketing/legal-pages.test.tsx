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
  for (const [name, href] of [['Privacy', '/privacy'], ['Terms', '/terms'], ['Data deletion', '/data-deletion'], ['Request an invite', '/request-invite'], ['Sign in', '/studio']]) {
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
    expect(screen.getByText(/RERA/)).toBeInTheDocument()
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
