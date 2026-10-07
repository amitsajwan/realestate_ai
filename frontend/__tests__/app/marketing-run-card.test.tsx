import { act, fireEvent, render, screen } from '@testing-library/react'
import React from 'react'
import { MarketingRunCard } from '@/components/app/MarketingRunCard'
import type { MarketingRun } from '@/lib/app/types'

const getMarketingRun = jest.fn()
const startMarketingRun = jest.fn()
const sendRunToCalendar = jest.fn()
const editRunPost = jest.fn()
const redoRunPost = jest.fn()
jest.mock('@/lib/app/client', () => ({
  api: {
    getMarketingRun: (...a: unknown[]) => getMarketingRun(...a),
    startMarketingRun: (...a: unknown[]) => startMarketingRun(...a),
    sendRunToCalendar: (...a: unknown[]) => sendRunToCalendar(...a),
    editRunPost: (...a: unknown[]) => editRunPost(...a),
    redoRunPost: (...a: unknown[]) => redoRunPost(...a),
  },
  errorMessage: (e: Error) => e.message,
}))

const base: MarketingRun = { id: 'r1', listing_id: 'L1', status: 'queued', posts: [], facts: null }
const factsDone: MarketingRun = {
  ...base, status: 'posts', facts_done_at: '2026-10-06T12:00:00Z', page_url: 'https://avasetu.in/agent/priya/listings/L1',
  facts: { usable: 28, held: 0, maharera: 'P52100076768', how: 'name and taluka (Shirur)', nearby: 2, notes: ['no named school mapped within 10 km'] },
}
const done: MarketingRun = {
  ...factsDone, status: 'done',
  posts: [{ angle: 'price_reveal', images: ['https://api/uploads/campaigns/L1/a.png'], caption: '₹32.3 lakh for a plot in Gulmohar City.\n\nMore' }],
}

beforeEach(() => {
  jest.useFakeTimers()
  getMarketingRun.mockReset()
  startMarketingRun.mockReset()
})
afterEach(() => jest.useRealTimers())

it('offers Start marketing when nothing ran yet, then shows step 1 working', async () => {
  getMarketingRun.mockResolvedValue(null)
  startMarketingRun.mockResolvedValue(base)
  render(<MarketingRunCard listingId="L1" />)
  fireEvent.click(await screen.findByRole('button', { name: 'Start marketing' }))
  expect(startMarketingRun).toHaveBeenCalledWith('L1', false, 'en')
  expect(await screen.findByText(/Project facts and listing page/)).toBeInTheDocument()
  expect(screen.getAllByText(/Working/)).toHaveLength(1)   // step 2 waits for step 1
})

it('polls: facts first (with the page link), then the posts', async () => {
  getMarketingRun.mockResolvedValueOnce(factsDone).mockResolvedValueOnce(done)
  render(<MarketingRunCard listingId="L1" />)
  expect(await screen.findByText(/28 facts checked · MahaRERA P52100076768 · 2 nearby places/)).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'See the listing page' })).toHaveAttribute('href', factsDone.page_url)
  await act(async () => {
    jest.advanceTimersByTime(3000)
  })
  expect(await screen.findByText('1 post ready for your approval')).toBeInTheDocument()
  expect(screen.getByRole('img', { name: '₹32.3 lakh for a plot in Gulmohar City.' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Check again and remake' })).toBeInTheDocument()
})

it('a failed posts step keeps the facts and offers a retry', async () => {
  getMarketingRun.mockResolvedValue({ ...factsDone, status: 'failed', error: 'The facts are saved, but the posts could not be made.' })
  render(<MarketingRunCard listingId="L1" />)
  expect(await screen.findByText(/The facts are saved/)).toBeInTheDocument()
  expect(screen.getByText(/28 facts checked/)).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
})

it('sends the finished posts to the calendar for approval', async () => {
  jest.useRealTimers()
  getMarketingRun.mockResolvedValue(done)
  sendRunToCalendar.mockResolvedValue({
    ...done, calendar: [{ angle: 'price_reveal', channel: 'instagram', row_id: 'r1', due_at: '2026-10-07T13:30:00Z' },
                        { angle: 'price_reveal', channel: 'facebook_page', row_id: 'r2', due_at: '2026-10-07T13:30:00Z' }],
  })
  render(<MarketingRunCard listingId="L1" />)
  fireEvent.click(await screen.findByRole('button', { name: 'Send to calendar for approval' }))
  expect(sendRunToCalendar).toHaveBeenCalledWith('L1')
  expect(await screen.findByText(/2 planned in the calendar, one a day from 7 Oct/)).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Approve them in Content' })).toHaveAttribute('href', '/studio/content')
  expect(screen.queryByRole('button', { name: 'Send to calendar for approval' })).not.toBeInTheDocument()
})

it('shows the slides reels and says when the walkthrough is still being made', async () => {
  jest.useRealTimers()
  getMarketingRun.mockResolvedValue({
    ...done,
    reels: [{ kind: 'slides', angle: 'nearby', video: 'https://api/uploads/campaigns/L1/x/reels/nearby.mp4' },
            { kind: 'walkthrough', status: 'queued', video: null }],
  })
  render(<MarketingRunCard listingId="L1" />)
  expect(await screen.findByLabelText('nearby')).toHaveAttribute('src', 'https://api/uploads/campaigns/L1/x/reels/nearby.mp4')
  expect(screen.getByText(/Walkthrough reel: being made/)).toBeInTheDocument()
})

it('edits a caption (showing the checks as warnings) and improves a post with a note', async () => {
  jest.useRealTimers()
  getMarketingRun.mockResolvedValue(done)
  render(<MarketingRunCard listingId="L1" />)
  fireEvent.click(await screen.findByRole('button', { name: /₹32.3 lakh for a plot in Gulmohar City/ }))
  const box = screen.getByLabelText('Caption')
  expect(box).toHaveValue(done.posts[0].caption)
  const edited = 'Only ₹25 lakh, call now'
  editRunPost.mockResolvedValue({ run: { ...done, posts: [{ ...done.posts[0], caption: edited, edited: true }] },
                                  problems: ['number not in facts: 25'] })
  fireEvent.change(box, { target: { value: edited } })
  fireEvent.click(screen.getByRole('button', { name: 'Save caption' }))
  expect(editRunPost).toHaveBeenCalledWith('L1', 'price_reveal', edited)
  expect(await screen.findByText(/Saved. Please check: number not in facts: 25/)).toBeInTheDocument()

  redoRunPost.mockResolvedValue({ ...done, posts: [{ ...done.posts[0], caption: 'Near MIDC: ₹32.3 lakh plot.', redos: 1 }] })
  fireEvent.change(screen.getByLabelText('What should change?'), { target: { value: 'mention MIDC' } })
  fireEvent.click(screen.getByRole('button', { name: 'Make it again with this note' }))
  expect(redoRunPost).toHaveBeenCalledWith('L1', 'price_reveal', 'mention MIDC')
  expect(await screen.findByDisplayValue('Near MIDC: ₹32.3 lakh plot.')).toBeInTheDocument()
})

it('makes the posts in the language picked, and keeps that language for a remake', async () => {
  getMarketingRun.mockResolvedValue(null)
  startMarketingRun.mockResolvedValue({ ...done, language: 'mr' })
  render(<MarketingRunCard listingId="L1" />)
  fireEvent.click(await screen.findByRole('radio', { name: 'मराठी' }))
  expect(screen.getByRole('radio', { name: 'मराठी' })).toHaveAttribute('aria-checked', 'true')
  fireEvent.click(screen.getByRole('button', { name: 'Start marketing' }))
  expect(startMarketingRun).toHaveBeenCalledWith('L1', false, 'mr')
  fireEvent.click(await screen.findByRole('button', { name: 'Check again and remake' }))
  expect(startMarketingRun).toHaveBeenLastCalledWith('L1', true, 'mr')
})
