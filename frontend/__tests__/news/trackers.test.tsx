import { render, screen, within } from '@testing-library/react'
import React from 'react'
import { AreaTrackers, TrackerPage } from '@/components/news/Trackers'
import { cleanTracker, trackerDate, type Tracker } from '@/lib/news/trackers'

const RAW = {
  slug: 'purandar-airport', name: 'Purandar airport', title: 'Purandar airport: status and timeline', summary: 'The planned second airport.',
  kind: 'project', areas: [], stages: ['Site chosen', 'Land acquisition', 'Feasibility and design', 'Construction', 'Open'], stage: 2,
  status: 'Land acquisition is nearly done.', status_date: '2026-10-23', status_sources: ['Punekar News', 'Pune Mirror'],
  means: 'A new airport is years away.', updated: '2026-10-24', report_count: 3, newer_reports: 1,
  latest: null,
  history: [{ date: '2026-10-23', stage: 2, status: 'Land acquisition is nearly done.', sources: ['Punekar News'] },
    { date: '2026-09-24', stage: 1, status: 'The High Court dismissed the plea.', sources: [] }],
  timeline: [
    { date: '2026-10-24', headline: 'Maharashtra Revives Purandar Airport Project', source: 'Swarajya', url: 'https://news.google.com/x', is_redirect: true, also: [] },
    { date: '2026-10-21', headline: 'Administration to Acquire Remaining 40 Hectares', source: 'Punekar News', url: 'https://punekarnews.in/a', is_redirect: false,
      also: [{ name: 'Pune Mirror', url: 'javascript:alert(1)', is_redirect: false }] },
  ],
}

const tracker = (over: Record<string, unknown> = {}): Tracker => cleanTracker({ ...RAW, ...over }) as Tracker

it('keeps only well-formed trackers, and never a stage outside the list or an unsafe link', () => {
  expect(cleanTracker({ ...RAW, slug: 'Bad Slug' })).toBeNull()
  expect(cleanTracker({ ...RAW, status: '' })).toBeNull()
  expect(tracker({ stage: 7 }).stage).toBeNull()
  expect(tracker().timeline[1].also[0].url).toBeNull()
  expect(trackerDate('2026-10-23')).toBe('23 Oct 2026')
})

it('shows where it stands, the stage, a note about newer reports, the reports and how the status changed', () => {
  render(<TrackerPage t={tracker()} />)
  expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Purandar airport: status and timeline')
  expect(screen.getByTestId('tracker-status')).toHaveTextContent('Land acquisition is nearly done.')
  expect(screen.getByLabelText('Stage 3 of 5: Feasibility and design')).toBeInTheDocument()
  expect(screen.getByText(/A newer report is below/)).toBeInTheDocument()
  const tl = within(screen.getByTestId('tracker-timeline'))
  expect(tl.getByRole('link', { name: 'Maharashtra Revives Purandar Airport Project' })).toHaveAttribute('href', 'https://news.google.com/x')
  expect(tl.getByText(/Also reported by/)).toHaveTextContent('Pune Mirror')
  expect(tl.queryByRole('link', { name: 'Pune Mirror' })).toBeNull()
  expect(screen.getByText('The High Court dismissed the plea.')).toBeInTheDocument()
})

it('an area page block shows nothing when no tracker touches the area', () => {
  const { container } = render(<AreaTrackers name="Kharadi" items={[]} />)
  expect(container).toBeEmptyDOMElement()
})
