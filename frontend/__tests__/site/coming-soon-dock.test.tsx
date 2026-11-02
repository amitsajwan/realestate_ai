import React from 'react'
import { act, fireEvent, render, screen } from '@testing-library/react'
import ComingSoonDock, { FOLD_MS, SHOW_AFTER_MS, TURN_MS } from '@/components/site/ComingSoonDock'
import type { UpcomingBrief } from '@/lib/site/hubs'

const u = (slug: string): UpcomingBrief => ({ slug, name: slug, builder: 'A builder', logo: '', area: 'wagholi', area_name: 'Wagholi', area_slug: 'wagholi', note: '2 & 3 BHK · coming soon' })
const ITEMS = [u('one'), u('two'), u('three')]
const NOW = new Date('2026-11-02T10:00:00Z').getTime()

const pass = (ms: number) => act(() => { jest.advanceTimersByTime(ms) })
const link = () => screen.getByTestId('coming-soon-link').getAttribute('href')

describe('coming-soon corner card', () => {
  beforeEach(() => { jest.useFakeTimers({ now: NOW }); window.localStorage.clear() })
  afterEach(() => { jest.useRealTimers(); delete (window as { matchMedia?: unknown }).matchMedia })

  it('slides in after a moment, says not registered, and takes its turns', () => {
    render(<ComingSoonDock items={ITEMS} />)
    expect(screen.queryByTestId('coming-soon-dock')).toBeNull()
    pass(SHOW_AFTER_MS)
    expect(screen.getByTestId('coming-soon-dock')).toHaveTextContent('Not yet MahaRERA registered')
    expect(link()).toBe('/projects/upcoming/one#enquire')
    pass(TURN_MS)
    expect(link()).toBe('/projects/upcoming/two#enquire')
    pass(TURN_MS * 2)
    expect(link()).toBe('/projects/upcoming/one#enquire')
  })

  it('stops turning while the pointer is on it', () => {
    render(<ComingSoonDock items={ITEMS} />)
    pass(SHOW_AFTER_MS)
    fireEvent.mouseEnter(screen.getByTestId('coming-soon-dock'))
    pass(TURN_MS * 3)
    expect(link()).toBe('/projects/upcoming/one#enquire')
  })

  it('stands still for people who ask for reduced motion', () => {
    window.matchMedia = jest.fn(() => ({ matches: true })) as unknown as typeof window.matchMedia
    render(<ComingSoonDock items={ITEMS} />)
    pass(SHOW_AFTER_MS + TURN_MS * 3)
    expect(link()).toBe('/projects/upcoming/one#enquire')
  })

  it('leaves while someone types in a form, and comes back after', () => {
    render(<><input aria-label="Name" /><ComingSoonDock items={ITEMS} /></>)
    pass(SHOW_AFTER_MS)
    fireEvent.focusIn(screen.getByLabelText('Name'))
    expect(screen.queryByTestId('coming-soon-dock')).toBeNull()
    fireEvent.focusOut(screen.getByLabelText('Name'))
    expect(screen.getByTestId('coming-soon-dock')).toBeInTheDocument()
  })

  it('folds to a tab that stays for a day, and the tab opens it again', () => {
    const first = render(<ComingSoonDock items={ITEMS} />)
    pass(SHOW_AFTER_MS)
    fireEvent.click(screen.getByTestId('coming-soon-fold'))
    expect(screen.getByTestId('coming-soon-tab')).toHaveTextContent('3 launching soon')
    first.unmount()

    const later = render(<ComingSoonDock items={ITEMS} />)
    pass(SHOW_AFTER_MS)
    expect(screen.getByTestId('coming-soon-tab')).toBeInTheDocument()
    later.unmount()

    jest.setSystemTime(NOW + FOLD_MS + SHOW_AFTER_MS * 2)
    const nextDay = render(<ComingSoonDock items={ITEMS} />)
    pass(SHOW_AFTER_MS)
    expect(screen.getByTestId('coming-soon-dock')).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('coming-soon-fold'))
    fireEvent.click(screen.getByTestId('coming-soon-tab'))
    expect(screen.getByTestId('coming-soon-dock')).toBeInTheDocument()
    nextDay.unmount()
  })

  it('shows nothing when no project is coming', () => {
    const { container } = render(<ComingSoonDock items={[]} />)
    pass(SHOW_AFTER_MS)
    expect(container).toBeEmptyDOMElement()
  })
})
