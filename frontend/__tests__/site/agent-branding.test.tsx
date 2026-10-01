import React from 'react'
import fs from 'fs'
import path from 'path'
import { render, screen } from '@testing-library/react'
import AboutAgent from '@/components/site/AboutAgent'
import Hero from '@/components/site/Hero'
import SiteShell from '@/components/site/SiteShell'
import { FIXTURE_AGENT, FIXTURE_BRAND_AGENTS } from '@/lib/site/fixtures'
import { PRESETS } from '@/lib/site/presets'
import { monogram, safeImage, safeRera } from '@/lib/site/theme'
import type { AgentProfile } from '@/lib/site/types'

jest.mock('@/components/site/ChatWidget', () => ({ __esModule: true, default: () => null }))

const kulkarni = FIXTURE_BRAND_AGENTS['rohan-kulkarni-aundh']
const joshi = FIXTURE_BRAND_AGENTS['meera-joshi-kothrud']

describe('themed agent site', () => {
  it('header shows the agent business name and monogram, not the Avasetu brand', () => {
    const { container } = render(<SiteShell agent={joshi}><p>body</p></SiteShell>)
    const header = container.querySelector('header')!
    expect(header).toHaveTextContent('Joshi & Associates')
    expect(header).not.toHaveTextContent('Avasetu')
    expect(header).toHaveTextContent('JA')
    expect(container.querySelector('[data-surface="v2"]')!.getAttribute('style')).toContain(PRESETS.terracotta.primary)
    expect(container.querySelector('img[src="/brand/mark.svg"]')).toBeNull()
  })

  it('footer says Powered by Avasetu, shows the RERA agent number with a MahaRERA link, never "Verified"', () => {
    const { container } = render(<SiteShell agent={joshi}><p>body</p></SiteShell>)
    const footer = container.querySelector('footer')!
    expect(footer).toHaveTextContent('Powered by Avasetu')
    expect(footer).toHaveTextContent('RERA agent registration: A52100031122')
    expect(footer).toHaveTextContent(/not verified by Avasetu/)
    const link = screen.getByRole('link', { name: /check on maharera/i })
    expect(link).toHaveAttribute('href', 'https://maharera.maharashtra.gov.in')
    expect(container.textContent).not.toMatch(/(?<!not )verified by avasetu/i)
  })

  it('uses the logo image when one is uploaded', () => {
    const a: AgentProfile = { ...joshi, branding_data: { ...joshi.branding_data, logo: '/uploads/images/logo1.png' } }
    const { container } = render(<SiteShell agent={a}><p /></SiteShell>)
    expect(container.querySelector('header img')).toHaveAttribute('src', '/uploads/images/logo1.png')
  })

  it('hero with a banner overlays the photo; without one it uses the preset gradient and skyline', () => {
    const withBanner = render(<Hero agent={kulkarni} city="Pune" />)
    expect(withBanner.container.querySelector('section')!.getAttribute('data-hero')).toBe('banner')
    expect(withBanner.container.querySelector('img[src="/uploads/images/fx-banner-aundh.jpg"]')).not.toBeNull()
    expect(withBanner.container.querySelector('svg')).toBeNull()
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Aundh and Baner homes, explained properly')
    withBanner.unmount()
    const plain = render(<Hero agent={joshi} city="Pune" />)
    expect(plain.container.querySelector('section')!.getAttribute('data-hero')).toBe('sun')
    expect(plain.container.querySelector('svg')).not.toBeNull()
  })

  it('an agent with no branding keeps working: navy-gold, default headline, own name in header', () => {
    const bare: AgentProfile = { ...FIXTURE_AGENT, branding_data: null }
    const { container } = render(<><SiteShell agent={bare}><Hero agent={bare} city="Pune" /></SiteShell></>)
    expect(container.querySelector('[data-preset]')!.getAttribute('data-preset')).toBe('navy-gold')
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Homes in Pune, shared clearly')
    expect(container.querySelector('header')).toHaveTextContent('Priya Deshmukh')
  })

  it('about section shows areas as chips, languages, experience and the self-declared RERA number', () => {
    render(<AboutAgent agent={kulkarni} />)
    expect(screen.getByRole('heading', { name: 'About Kulkarni Homes' })).toBeInTheDocument()
    const chips = screen.getByRole('list', { name: 'Areas we cover' })
    expect(chips).toHaveTextContent('Aundh')
    expect(chips.querySelectorAll('li')).toHaveLength(4)
    expect(screen.getByText(/12 years/)).toBeInTheDocument()
    expect(screen.getByTestId('rera-agent')).toHaveTextContent('A52100023456')
    expect(screen.getByTestId('rera-agent')).toHaveTextContent(/has not verified it/)
  })

  it('without a RERA number nothing is claimed', () => {
    render(<AboutAgent agent={{ ...kulkarni, branding_data: { ...kulkarni.branding_data, rera_agent_no: null } }} />)
    expect(screen.queryByTestId('rera-agent')).toBeNull()
  })

  it('never renders unsafe stored values', () => {
    expect(safeImage('javascript:alert(1)')).toBeNull()
    expect(safeImage('https://evil.test/x.jpg')).toBeNull()
    expect(safeImage('/uploads/images/a.jpg')).toBe('/uploads/images/a.jpg')
    expect(safeRera('A52100012345')).toBe('A52100012345')
    expect(safeRera('<script>')).toBeNull()
    const { container } = render(<SiteShell agent={{ ...joshi, branding_data: { ...joshi.branding_data, logo: 'https://evil.test/x.png', rera_agent_no: 'bad' } }}><p /></SiteShell>)
    expect(container.querySelector('header img')).toBeNull()
    expect(container.querySelector('footer')).not.toHaveTextContent('RERA agent registration')
  })

  it('monogram', () => {
    expect(monogram('Deshmukh Realty')).toBe('DR')
    expect(monogram('Studio')).toBe('ST')
  })

  it('frontend preset colours match the backend list', () => {
    const py = fs.readFileSync(path.join(__dirname, '../../../backend/app/modules/onboarding/branding.py'), 'utf8')
    for (const p of Object.values(PRESETS)) {
      const m = py.match(new RegExp(`"${p.id}": \\{"primary": "(#[0-9a-f]{6})", "secondary": "(#[0-9a-f]{6})", "accent": "(#[0-9a-f]{6})"`, 'i'))
      expect(m && m.slice(1)).toEqual([p.primary, p.secondary, p.accent])
    }
  })
})
