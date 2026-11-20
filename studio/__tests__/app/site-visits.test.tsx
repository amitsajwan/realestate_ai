/** Studio > Site > On the ground (backend areastats/sitevisits.py): the owner writes what was seen at a project's site. */
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { SiteVisits } from '@/components/app/admin/SiteVisits'
import { ApiError } from '@/lib/app/api'
import type { SiteVisit, SiteVisitIn } from '@/lib/app/admin'

const SAVED: SiteVisit = { regno: 'PR1260002502426', slug: 'godrej-ivara-pune', project: 'Godrej Ivara', visited_on: '2026-11-19',
  by: 'House Deal', text: 'Tower A has its slab up to the 21st floor.', at: '2026-11-20T09:00:00+00:00', withdrawn: false }
const mockAdd = jest.fn<Promise<SiteVisit[]>, [SiteVisitIn]>()
const mockWithdraw = jest.fn<Promise<SiteVisit[]>, [string, string]>()
jest.mock('@/lib/app/admin', () => ({
  adminApi: {
    siteVisits: async () => [],
    addSiteVisit: (b: SiteVisitIn) => mockAdd(b),
    withdrawSiteVisit: (p: string, at: string) => mockWithdraw(p, at),
  },
}))

beforeEach(() => { mockAdd.mockReset(); mockWithdraw.mockReset() })

async function fill() {
  render(<SiteVisits />)
  await screen.findByTestId('site-visits')
  fireEvent.change(screen.getByLabelText('Project: page address or MahaRERA number'), { target: { value: 'godrej-ivara-pune' } })
  fireEvent.change(screen.getByLabelText(/What you saw/), { target: { value: 'Tower A has its slab up to the 21st floor.' } })
}

it('sends the note with the day and shows it in the list, ready to take off the page', async () => {
  mockAdd.mockResolvedValue([SAVED])
  mockWithdraw.mockResolvedValue([{ ...SAVED, withdrawn: true }])
  await fill()
  expect(screen.getByLabelText(/What you saw \(10 words; 60 to 250\)/)).toBeInTheDocument()
  fireEvent.click(screen.getByTestId('visit-save'))
  await screen.findByTestId('visit-saved')
  expect(mockAdd).toHaveBeenCalledWith(expect.objectContaining({ project: 'godrej-ivara-pune', text: 'Tower A has its slab up to the 21st floor.' }))
  expect(screen.getByTestId('visit')).toHaveTextContent('Visited 2026-11-19 by House Deal')
  fireEvent.click(screen.getByTestId('visit-withdraw'))
  await waitFor(() => expect(screen.getByTestId('visit')).toHaveTextContent('taken off the page'))
  expect(mockWithdraw).toHaveBeenCalledWith('PR1260002502426', SAVED.at)
})

it("shows the server's reason when the rules refuse a note, and keeps what was written", async () => {
  mockAdd.mockRejectedValue(new ApiError(422, 'Write at least 60 words about what you saw (9 now)'))
  await fill()
  fireEvent.click(screen.getByTestId('visit-save'))
  expect(await screen.findByText(/Write at least 60 words/)).toBeInTheDocument()
  expect(screen.getByLabelText(/What you saw/)).toHaveValue('Tower A has its slab up to the 21st floor.')
})
