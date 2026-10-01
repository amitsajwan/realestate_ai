import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import { AboutStep } from '@/components/app/AboutStep'
import { ReviewForm } from '@/components/app/ReviewForm'
import ListingAbout from '@/components/site/ListingAbout'
import { aboutProblem, aboutSummaryLines, compactAbout } from '@/lib/app/about'
import { createApiClient } from '@/lib/app/api'
import type { About, AboutSuggestion } from '@/lib/app/types'

const SUGGESTION: AboutSuggestion = {
  highlights: [{ text: 'East facing', source: 'agent' }],
  amenities: [{ text: 'Lift', source: 'agent' }],
  nearby: [{ type: 'office', name: 'EON Free Zone', source: 'area_guide' }],
  connectivity: [{ text: 'Metro Line 4 (Kharadi to Khadakwasla) is approved, not running yet. Check the latest status with Maha-Metro.', source: 'area_guide' }],
  fields: { parking: { text: '1 covered parking', source: 'agent' } },
  project_name: 'Rohan Heights',
  area_known: true,
  area_name: 'Kharadi',
}

const mockFetch = jest.fn()
jest.mock('@/lib/app/client', () => {
  const { createApiClient: make } = jest.requireActual('@/lib/app/api')
  return {
    api: make({ baseUrl: '', getToken: () => 'tok', fetchImpl: (...a: unknown[]) => mockFetch(...a) }),
    errorMessage: (e: Error) => e.message,
    isFixtureMode: () => false,
  }
})

function ok(body: unknown) {
  return { ok: true, status: 200, text: async () => JSON.stringify(body) }
}

function Harness({ initial = {}, onDone = jest.fn(), onSkip = jest.fn(), spy }: { initial?: About; onDone?: () => void; onSkip?: () => void; spy?: (a: About) => void }) {
  const [v, setV] = React.useState<About>(initial)
  return (
    <AboutStep
      value={v}
      onChange={(a) => { setV(a); spy?.(a) }}
      context={{ locality: 'Kharadi', bhk: 2, description: '2 BHK east facing, lift, 1 covered parking' }}
      onDone={onDone}
      onSkip={onSkip}
    />
  )
}

beforeEach(() => mockFetch.mockReset())

describe('AboutStep', () => {
  it('explains why it matters and is skippable', () => {
    const onSkip = jest.fn()
    render(<Harness onSkip={onSkip} />)
    expect(screen.getByText(/answer the questions buyers ask, on your behalf/i)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /skip for now/i }))
    expect(onSkip).toHaveBeenCalled()
  })

  it('amenity and nearby chips toggle and land in the value', () => {
    const spy = jest.fn()
    render(<Harness spy={spy} />)
    const lift = screen.getByRole('button', { name: 'Lift' })
    fireEvent.click(lift)
    expect(lift).toHaveAttribute('aria-pressed', 'true')
    fireEvent.click(screen.getByRole('button', { name: 'School nearby' }))
    expect(spy).toHaveBeenLastCalledWith({ amenities: ['Lift'], nearby: [{ type: 'school', name: 'School nearby' }] })
    fireEvent.click(lift)
    expect(lift).toHaveAttribute('aria-pressed', 'false')
  })

  it('text inputs and a buyer question with an answer are saved; unanswered questions are dropped on continue', () => {
    const spy = jest.fn()
    const onDone = jest.fn()
    render(<Harness spy={spy} onDone={onDone} />)
    fireEvent.change(screen.getByLabelText('Water'), { target: { value: '24x7 water supply' } })
    fireEvent.change(screen.getByLabelText('Your answer 1'), { target: { value: 'Yes, one covered slot.' } })
    fireEvent.click(screen.getByRole('button', { name: /^continue$/i }))
    const last = spy.mock.calls[spy.mock.calls.length - 1][0] as About
    expect(last.water).toBe('24x7 water supply')
    expect(last.faq).toEqual([{ q: 'Is parking included?', a: 'Yes, one covered slot.' }])
    expect(onDone).toHaveBeenCalled()
  })

  it('suggest flow: calls the endpoint, shows source tags, nothing is kept until the agent taps Keep', async () => {
    mockFetch.mockResolvedValue(ok(SUGGESTION))
    const spy = jest.fn()
    render(<Harness spy={spy} />)
    fireEvent.click(screen.getByRole('button', { name: /suggest from my description and the area guide/i }))
    const list = await screen.findByRole('list', { name: 'Suggestions' })
    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/v1/listings/ai/about-suggest')
    expect(JSON.parse(init.body as string)).toMatchObject({ locality: 'Kharadi', bhk: 2 })
    // tags
    const guideTags = list.querySelectorAll('[data-source="area_guide"]')
    const agentTags = list.querySelectorAll('[data-source="agent"]')
    expect(guideTags.length).toBe(2) // EON Free Zone + metro line
    expect(agentTags.length).toBe(3) // highlight, amenity, parking
    expect(within(list).getAllByText('You said').length).toBe(3)
    expect(within(list).getAllByText('Area guide').length).toBe(2)
    // project name is prefilled from the suggestion, but no item is kept yet
    expect(screen.getByLabelText(/project or society name/i)).toHaveValue('Rohan Heights')
    fireEvent.click(screen.getByRole('button', { name: /Keep: East facing/ }))
    fireEvent.click(screen.getByRole('button', { name: /Keep: EON Free Zone/ }))
    fireEvent.click(screen.getByRole('button', { name: /Keep: Parking: 1 covered parking/ }))
    const last = spy.mock.calls[spy.mock.calls.length - 1][0] as About
    expect(last.highlights).toEqual(['East facing'])
    expect(last.nearby).toEqual([{ type: 'office', name: 'EON Free Zone' }])
    expect(last.parking).toBe('1 covered parking')
    expect(last.connectivity).toBeUndefined()
    // remove again
    fireEvent.click(screen.getByRole('button', { name: /Remove: East facing/ }))
    expect((spy.mock.calls[spy.mock.calls.length - 1][0] as About).highlights).toEqual([])
  })

  it('Keep all keeps every suggestion; the metro line keeps the approved-not-running wording', async () => {
    mockFetch.mockResolvedValue(ok(SUGGESTION))
    const spy = jest.fn()
    render(<Harness spy={spy} />)
    fireEvent.click(screen.getByRole('button', { name: /suggest from my description/i }))
    await screen.findByRole('list', { name: 'Suggestions' })
    fireEvent.click(screen.getByRole('button', { name: /keep all/i }))
    const last = spy.mock.calls[spy.mock.calls.length - 1][0] as About
    expect(last.connectivity?.[0]).toMatch(/approved, not running/)
    expect(last.amenities).toContain('Lift')
  })

  it('shows an error when the suggestion call fails, and the form still works', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 500, text: async () => JSON.stringify({ detail: 'Try again later' }) })
    render(<Harness />)
    fireEvent.click(screen.getByRole('button', { name: /suggest from my description/i }))
    await waitFor(() => expect(screen.getByText(/try again later/i)).toBeInTheDocument())
    expect(screen.getByRole('button', { name: 'Lift' })).toBeEnabled()
  })

  it('refuses phone numbers and links before they reach the server', () => {
    const onDone = jest.fn()
    render(<Harness onDone={onDone} />)
    fireEvent.change(screen.getByLabelText('Water'), { target: { value: 'call 98765 43210' } })
    expect(screen.getByRole('alert')).toHaveTextContent(/phone numbers/i)
    expect(screen.getByRole('button', { name: /^continue$/i })).toBeDisabled()
    fireEvent.change(screen.getByLabelText('Water'), { target: { value: 'see www.mysite.com' } })
    expect(screen.getByRole('alert')).toHaveTextContent(/links/i)
    fireEvent.change(screen.getByLabelText('Water'), { target: { value: 'Borewell' } })
    expect(screen.queryByRole('alert')).toBeNull()
    expect(screen.getByRole('button', { name: /^continue$/i })).toBeEnabled()
  })

  it('adds up to 6 highlights', () => {
    const spy = jest.fn()
    render(<Harness spy={spy} initial={{ highlights: ['a1', 'b2', 'c3', 'd4', 'e5'] }} />)
    fireEvent.change(screen.getByLabelText(/add a highlight/i), { target: { value: 'f6' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add' }))
    expect((spy.mock.calls[0][0] as About).highlights).toHaveLength(6)
    expect(screen.getByLabelText(/add a highlight/i)).toBeDisabled()
  })
})

describe('about helpers', () => {
  it('compactAbout drops empties and half-filled questions', () => {
    expect(compactAbout({ water: '  ', highlights: [' ', 'x'], faq: [{ q: 'q', a: '' }] })).toEqual({ highlights: ['x'] })
    expect(compactAbout({})).toBeUndefined()
  })
  it('aboutProblem mirrors the server rules', () => {
    expect(aboutProblem({ highlights: ['fine, 1100 sq ft'] })).toBeNull()
    expect(aboutProblem({ parking: '+91 98765-43210' })).toMatch(/phone/)
    expect(aboutProblem({ nearby: [{ type: 'other', name: 'https://x.com' }] })).toMatch(/links/)
    expect(aboutProblem({ water: 'x'.repeat(301) })).toMatch(/300/)
  })
  it('suggestAbout posts to the listings AI route', async () => {
    const f = jest.fn(async () => ok(SUGGESTION)) as unknown as typeof fetch
    const api = createApiClient({ baseUrl: 'http://x', getToken: () => 't', fetchImpl: f })
    await api.suggestAbout({ locality: 'Wagholi', description: 'lift' })
    expect((f as unknown as jest.Mock).mock.calls[0][0]).toBe('http://x/api/v1/listings/ai/about-suggest')
  })
})

describe('ReviewForm about summary', () => {
  it('shows a summary and an edit link', () => {
    const onEdit = jest.fn()
    render(<ReviewForm value={{}} onChange={() => undefined} about={{ project_name: 'Rohan Heights', amenities: ['Lift', 'Gym'], parking: '1 covered parking' }} onEditAbout={onEdit} />)
    expect(screen.getByText('Rohan Heights')).toBeInTheDocument()
    expect(screen.getByText('Lift, Gym')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Edit' }))
    expect(onEdit).toHaveBeenCalled()
  })
  it('offers to add it when skipped', () => {
    render(<ReviewForm value={{}} onChange={() => undefined} about={{}} onEditAbout={() => undefined} />)
    expect(screen.getByText(/not added/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Add' })).toBeInTheDocument()
    expect(aboutSummaryLines({})).toEqual([])
  })
})

describe('public listing about section', () => {
  const about = {
    project_name: 'Riverfront Residences', highlights: ['East facing'], amenities: ['Lift', 'Gym'],
    nearby: [{ type: 'school', name: 'School nearby' }, { type: 'office', name: 'EON Free Zone', minutes: 10 }],
    connectivity: ['Metro Line 4 is approved, not running yet.'], water: '24x7 water supply',
  }
  it('renders highlights, amenities, facts and nearby; hides amenities already shown above', () => {
    render(<ListingAbout about={about} listingAmenities={['Gym']} />)
    const sec = screen.getByTestId('listing-about')
    expect(within(sec).getByText('About the project: Riverfront Residences')).toBeInTheDocument()
    expect(within(sec).getByText('East facing')).toBeInTheDocument()
    expect(within(sec).getByText('Lift')).toBeInTheDocument()
    expect(within(sec).queryByText('Gym')).toBeNull()
    expect(within(sec).getByText('24x7 water supply')).toBeInTheDocument()
    expect(within(sec).getByText('School nearby')).toBeInTheDocument()
    expect(within(sec).getByText(/about 10 min/)).toBeInTheDocument()
    expect(within(sec).getByText(/approved, not running/)).toBeInTheDocument()
  })
  it('renders nothing without about', () => {
    const { container, rerender } = render(<ListingAbout about={null} />)
    expect(container).toBeEmptyDOMElement()
    rerender(<ListingAbout about={{}} />)
    expect(container).toBeEmptyDOMElement()
  })
})
