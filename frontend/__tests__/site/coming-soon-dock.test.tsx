import React from 'react'
import { act, fireEvent, render, screen } from '@testing-library/react'
import ComingSoonDock, { FOLD_MS, SHOW_AFTER_MS, STILL_TURN_MS, TURN_MS } from '@/components/site/ComingSoonDock'
import type { UpcomingBrief } from '@/lib/site/hubs'

const u = (slug: string): UpcomingBrief => ({ slug, name: slug, builder: 'A builder', logo: '', area: 'wagholi', area_name: 'Wagholi', area_slug: 'wagholi', note: '2 & 3 BHK · coming soon' })
const ITEMS = [u('one'), u('two'), u('three')]
const NOW = new Date('2026-11-02T10:00:00Z').getTime()

const pass = (ms: number) => act(() => { jest.advanceTimersByTime(ms) })
const link = () => screen.getByTestId('coming-soon-link').getAttribute('href')

describe('coming-soon corner card', () => {
  beforeEach(() => { jest.useFakeTimers({ now: NOW }); window.localStorage.clear() })
  // the test setup may define matchMedia as a property that cannot be deleted: put the original back
  const original = window.matchMedia
  afterEach(() => { jest.useRealTimers(); window.matchMedia = original })

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

  it('still turns, more slowly, when animations are turned off', () => {
    window.matchMedia = jest.fn(() => ({ matches: true })) as unknown as typeof window.matchMedia
    render(<ComingSoonDock items={ITEMS} />)
    pass(SHOW_AFTER_MS)
    pass(TURN_MS)
    expect(link()).toBe('/projects/upcoming/one#enquire')
    pass(STILL_TURN_MS - TURN_MS)
    expect(link()).toBe('/projects/upcoming/two#enquire')
  })

  it('keeps turning after a tap on a phone', () => {
    render(<ComingSoonDock items={ITEMS} />)
    pass(SHOW_AFTER_MS)
    const dock = screen.getByTestId('coming-soon-dock')
    fireEvent.touchStart(dock)
    fireEvent.mouseEnter(dock)
    pass(TURN_MS)
    expect(link()).toBe('/projects/upcoming/two#enquire')
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
