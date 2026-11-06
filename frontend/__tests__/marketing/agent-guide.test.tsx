import React from 'react'
import { render, screen } from '@testing-library/react'
import AgentGuidePage, { metadata } from '@/app/for-agents/guide/page'

jest.mock('@/components/marketing/MarketingShell', () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => <main>{children}</main> }))

function text(): string {
  render(<AgentGuidePage />)
  return screen.getByRole('main').textContent ?? ''
}

describe('the guide for agents and channel partners', () => {
  it('says what they get, leads and the Lead Board among it', () => {
    const t = text()
    expect(screen.getByRole('heading', { name: 'What you get' })).toBeInTheDocument()
    for (const w of ['Lead cards', 'Lead Board', 'Your own page', 'Posts and a Reel', 'Results']) expect(t).toContain(w)
  })

  it('starts a listing from the project, with resale as the other way in', () => {
    const t = text()
    expect(t).toContain('Pick the project')
    expect(t).toContain('Change the prices to what you are selling at today')
    expect(t).toContain('List this project')
    expect(t).toContain('Resale or rent flat, or a project not listed here')
  })

  it('never promises posts on their own Facebook or Instagram', () => {
    const t = text()
    expect(t).toContain('Avasetu’s Facebook and Instagram with your name')
    expect(t).not.toMatch(/your own (Facebook|Instagram)/i)
  })

  it('is plain about whose lead is whose', () => {
    const t = text()
    expect(t).toContain('Always share your own link')
    expect(t).toContain('Avasetu’s lead. It may be passed to you, or appear on the Lead Board')
    expect(t).toContain('no agent’s number')
  })

  it('names no price beyond what we have decided, and no person', () => {
    const t = text()
    expect(t).toContain('we tell you the price before anything changes')
    expect(t).not.toMatch(/₹\s*\d/)
    expect(t).toContain('the Avasetu team')
  })

  it('stays out of search', () => {
    expect(JSON.stringify(metadata.robots)).toContain('false')
  })

  it('every picture it shows is there', () => {
    render(<AgentGuidePage />)
    const fs = jest.requireActual('fs') as typeof import('fs')
    const path = jest.requireActual('path') as typeof import('path')
    for (const img of Array.from(document.querySelectorAll('img'))) {
      expect(fs.existsSync(path.join(process.cwd(), 'public', img.getAttribute('src') as string))).toBe(true)
    }
  })
})
