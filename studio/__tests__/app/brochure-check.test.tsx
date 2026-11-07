import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { BrochureCheck } from '@/components/app/BrochureCheck'
import { createFixtureBrochureApi } from '@/lib/app/brochure'
import type { BrochureApi, BrochureKit, BrochureReading } from '@/lib/app/brochure'

const FILE = new File(['x'], 'b.pdf', { type: 'application/pdf' })

function withReading(api: BrochureApi, reading: () => BrochureReading): BrochureApi {
  return { ...api, reading: async () => reading() }
}

function verified(api: BrochureApi): BrochureApi {
  return {
    ...api,
    get: async (lid) => {
      const k = await api.get(lid)
      return k ? ({ ...k, registration: { status: 'verified', rera_no: 'PM1260002501030', note: '' } } as BrochureKit) : null
    },
  }
}

test('a brochure being read says so and shows nothing to tick', async () => {
  render(<BrochureCheck listingId="l1" client={withReading(createFixtureBrochureApi(), () => ({ status: 'reading', note: null }))} />)
  expect(await screen.findByText(/reading your brochure/)).toBeInTheDocument()
})

test('a listing with no brochure shows nothing', async () => {
  const { container } = render(<BrochureCheck listingId="l1" client={withReading(createFixtureBrochureApi(), () => ({ status: 'none', note: null }))} />)
  await waitFor(() => expect(container.querySelector('[aria-label="What we read from your brochure"]')).toBeNull())
  expect(screen.queryByText(/brochure/)).toBeNull()
})

test('a file that could not be read gives the reason', async () => {
  render(<BrochureCheck listingId="l1" client={withReading(createFixtureBrochureApi(), () => ({ status: 'failed', note: 'We could not read this brochure.' }))} />)
  expect(await screen.findByText(/could not read/)).toBeInTheDocument()
})

test('a verified brochure offers its plans and facts', async () => {
  const api = createFixtureBrochureApi()
  await api.upload('l1', FILE)
  render(<BrochureCheck listingId="l1" client={withReading(verified(api), () => ({ status: 'done', note: null }))} />)
  expect(await screen.findByText(/matches this project/)).toBeInTheDocument()
  const right = await screen.findAllByRole('button', { name: 'Right' })
  fireEvent.click(right[0])
  expect(await screen.findByText('Ticked')).toBeInTheDocument()
})

test('a brochure that is not checked says nothing from it goes on the page', async () => {
  const api = createFixtureBrochureApi()
  await api.upload('l1', FILE)
  render(<BrochureCheck listingId="l1" client={withReading(api, () => ({ status: 'done', note: null }))} />)
  expect(await screen.findByRole('alert')).toHaveTextContent('Nothing from it goes on the project page')
})
