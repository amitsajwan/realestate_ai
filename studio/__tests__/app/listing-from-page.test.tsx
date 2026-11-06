import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import React from 'react'
import { NewListingFlow } from '@/components/app/NewListingFlow'

const mock: Record<string, jest.Mock> = {}
;['searchProjects', 'aiDraftProject', 'aiDraft', 'createListing', 'publishListing', 'updateListing', 'uploadImages'].forEach((n) => (mock[n] = jest.fn()))

jest.mock('next/navigation', () => ({ useParams: () => ({}), usePathname: () => '/studio/listings/new' }))
jest.mock('@/lib/app/session', () => ({ getToken: () => 'tok', getSiteUrl: () => 'https://site.test', useSession: () => ({ ready: true }) }))
jest.mock('@/lib/app/client', () => ({
  errorMessage: (e: Error) => e.message,
  isFixtureMode: () => false,
  api: new Proxy({}, { get: (_t, k: string) => (...a: unknown[]) => mock[k](...a) }),
}))

const HIT = { regno: 'P52100000001', slug: 'godrej-ivara', marketed_name: 'Godrej Ivara', place_name: 'Upper Kharadi', promoter: 'Godrej Properties' }
const PAGE = { slug: 'godrej-ivara', name: 'Godrej Ivara', photos: [{ url: '/uploads/a.jpg', alt: 'Tower' }, { url: '/uploads/b.jpg', alt: 'Lobby' }], mine: null, others: 0 }
const DRAFT = {
  draft: { transaction: 'sale', property_type: 'apartment', title: 'Godrej Ivara: 2 BHK and up', price_inr: 9000000, city: 'Pune', locality: 'Upper Kharadi', bhk: 2,
    listing_scope: 'layout', rera_no: HIT.regno, description: { en: 'Homes' } },
  confidence: {}, missing: [], warnings: [], page: PAGE,
}

beforeEach(() => {
  Object.values(mock).forEach((m) => m.mockReset())
  window.history.pushState({}, '', '/studio/listings/new')
  mock.searchProjects.mockResolvedValue([HIT])
  mock.aiDraftProject.mockResolvedValue(DRAFT)
  mock.createListing.mockResolvedValue({ id: 'L1', title: 't' })
  mock.publishListing.mockResolvedValue({ id: 'L1', title: 't', status: 'live' })
})

async function pick() {
  fireEvent.change(screen.getByLabelText('Which project are you selling?'), { target: { value: 'ivara' } })
  fireEvent.click(await screen.findByRole('button', { name: /Godrej Ivara/ }))
}

describe('a new listing starts from the project', () => {
  it('asks which project first, and describing is the other door', () => {
    render(<NewListingFlow />)
    expect(screen.getByTestId('project-pick')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: /Resale or rent flat/ }))
    expect(screen.queryByTestId('project-pick')).not.toBeInTheDocument()
    expect(screen.getByLabelText(/Describe the property/)).toBeVisible()
  })

  it('finds a project and goes straight to the check', async () => {
    render(<NewListingFlow />)
    await pick()
    await screen.findByTestId('page-photos')
    expect(mock.searchProjects).toHaveBeenCalledWith('ivara')
    expect(mock.aiDraftProject).toHaveBeenCalledWith(HIT.regno)
    expect(mock.aiDraft).not.toHaveBeenCalled()
  })

  it('says so when nothing is found, and keeps the way out', async () => {
    mock.searchProjects.mockResolvedValue([])
    render(<NewListingFlow />)
    fireEvent.change(screen.getByLabelText('Which project are you selling?'), { target: { value: 'nothing here' } })
    await screen.findByText(/could not find that project/)
    expect(screen.getByRole('button', { name: /Resale or rent flat/ })).toBeInTheDocument()
  })

  it('starts by itself from a project page\'s button', async () => {
    window.history.pushState({}, '', `/studio/listings/new?project=${HIT.regno}`)
    render(<NewListingFlow />)
    await screen.findByTestId('page-photos')
    expect(mock.aiDraftProject).toHaveBeenCalledWith(HIT.regno)
  })

  it('tells the agent when the project cannot be opened, and stays on the search', async () => {
    mock.aiDraftProject.mockRejectedValue(new Error('We could not find this project.'))
    render(<NewListingFlow />)
    await pick()
    expect((await screen.findAllByText('We could not find this project.')).length).toBeGreaterThan(0)
    expect(screen.getByTestId('project-pick')).toBeVisible()
  })
})

describe('the page\'s photos', () => {
  it('are all ticked and go on the listing', async () => {
    render(<NewListingFlow />)
    await pick()
    await screen.findByTestId('page-photos')
    fireEvent.click(screen.getByRole('button', { name: /confirm/i }))
    await waitFor(() => expect(mock.createListing).toHaveBeenCalled())
    expect(mock.createListing.mock.calls[0][0].media.map((m: { url: string }) => m.url)).toEqual(['/uploads/a.jpg', '/uploads/b.jpg'])
    expect(mock.uploadImages).not.toHaveBeenCalled()
  })

  it('can be dropped one by one', async () => {
    render(<NewListingFlow />)
    await pick()
    const box = await screen.findByTestId('page-photos')
    fireEvent.click(within(box).getByRole('checkbox', { name: 'Use photo 1' }))
    fireEvent.click(screen.getByRole('button', { name: /confirm/i }))
    await waitFor(() => expect(mock.createListing).toHaveBeenCalled())
    expect(mock.createListing.mock.calls[0][0].media.map((m: { url: string }) => m.url)).toEqual(['/uploads/b.jpg'])
  })
})

describe('a project already listed', () => {
  it('sends the agent to their own listing', async () => {
    mock.aiDraftProject.mockResolvedValue({ ...DRAFT, page: { ...PAGE, mine: 'L7' } })
    render(<NewListingFlow />)
    await pick()
    const note = await screen.findByTestId('already-listed')
    expect(within(note).getByRole('link', { name: 'Open your listing' })).toHaveAttribute('href', '/studio/listings/L7')
  })

  it('tells the agent others list it and what decides the page', async () => {
    mock.aiDraftProject.mockResolvedValue({ ...DRAFT, page: { ...PAGE, others: 2 } })
    render(<NewListingFlow />)
    await pick()
    expect(await screen.findByTestId('also-listed')).toHaveTextContent('most complete listing')
  })
})

describe('after posting', () => {
  it('links to the project page', async () => {
    render(<NewListingFlow />)
    await pick()
    await screen.findByTestId('page-photos')
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /confirm/i })) })
    const link = await screen.findByRole('link', { name: 'See it on the project page' })
    expect(link).toHaveAttribute('href', '/projects/godrej-ivara')
  })
})
