import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import React from 'react'
import { ReelMaker } from '@/components/app/MarketingPackView'
import { PostSheet } from '@/components/app/agents/PostSheet'
import { ApiError } from '@/lib/app/api'
import { createFixtureReelsApi, createReelsApi, reelVideoUrl, whatsappReelUrl } from '@/lib/app/reels'
import type { ReelJob, ReelJobs, ReelSource } from '@/lib/app/reels'

jest.mock('@/lib/app/client', () => ({ isFixtureMode: () => false }))

const latestReels = jest.fn()
const postReel = jest.fn()
jest.mock('@/lib/app/reels', () => {
  const actual = jest.requireActual('@/lib/app/reels')
  return {
    ...actual,
    reelsApi: {
      forListing: () => ({ make: jest.fn(), latest: () => latestReels() }),
      forAgentListing: () => ({ make: jest.fn(), latest: () => latestReels() }),
      postReel: (...a: unknown[]) => postReel(...a),
    },
  }
})
jest.mock('@/lib/app/concierge', () => ({
  CHANNEL_LABEL: { facebook_page: 'Avasetu Facebook Page', instagram: 'Avasetu Instagram' },
  conciergeApi: { captions: () => Promise.resolve({ instagram: { text: 'Listed by Rahul Homes on Avasetu', image_urls: [], link: null } }) },
  firstName: (n: string) => n.split(' ')[0],
  friendlyConciergeError: (e: Error) => e.message,
}))

const job = (over: Partial<ReelJob> = {}): ReelJob => ({
  id: 'j1', listing_id: 'L1', lang: 'en', status: 'queued', video_path: null, video_url: null, audio: null, note: '', error: '',
  sample: false, created_at: '2026-10-01T09:00:00Z', finished_at: null, ...over,
})

function source(latest: ReelJobs[], made: ReelJob | Error = job()): ReelSource & { make: jest.Mock; latest: jest.Mock } {
  let i = 0
  return {
    make: jest.fn(async () => {
      if (made instanceof Error) throw made
      return made
    }),
    latest: jest.fn(async () => latest[Math.min(i++, latest.length - 1)]),
  }
}

afterEach(() => jest.useRealTimers())

test('idle: language picker and Make my reel, which starts a job in the chosen language', async () => {
  const s = source([{}])
  render(<ReelMaker source={s} caption="2 BHK in Kharadi" />)
  await waitFor(() => expect(s.latest).toHaveBeenCalled())
  const radios = screen.getAllByRole('radio')
  expect(radios.map((r) => r.textContent)).toEqual(['English', 'हिंदी', 'मराठी'])
  fireEvent.click(screen.getByRole('radio', { name: 'हिंदी' }))
  expect(screen.getByRole('radio', { name: 'हिंदी' })).toHaveAttribute('aria-checked', 'true')
  s.make.mockResolvedValueOnce(job({ lang: 'hi' }))
  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: 'Make my reel' }))
  })
  expect(s.make).toHaveBeenCalledWith('hi', false)
  expect(screen.getByTestId('reel-progress')).toHaveTextContent('Making your reel... this takes a few minutes')
})

test('queued and rendering: polls every 5 s until done, then shows the player, Download and WhatsApp', async () => {
  jest.useFakeTimers()
  const done = job({ status: 'done', video_path: '/uploads/reels/listing-L1-en-abcd1234.mp4', audio: 'music', note: 'Made without a voiceover. Music only.' })
  const s = source([{ en: job() }, { en: job({ status: 'rendering' }) }, { en: done }])
  render(<ReelMaker source={s} caption="2 BHK in Kharadi" />)
  await act(async () => { await Promise.resolve() })
  expect(screen.getByTestId('reel-progress')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Make my reel' })).not.toBeInTheDocument()
  await act(async () => { jest.advanceTimersByTime(5000) })
  expect(s.latest).toHaveBeenCalledTimes(2)
  expect(screen.getByTestId('reel-progress')).toBeInTheDocument()
  await act(async () => { jest.advanceTimersByTime(5000) })
  expect(s.latest).toHaveBeenCalledTimes(3)
  const video = screen.getByTestId('reel-video') as HTMLVideoElement
  expect(video.getAttribute('src')).toMatch(/\/uploads\/reels\/listing-L1-en-abcd1234\.mp4$/)
  const download = screen.getByRole('link', { name: 'Download' })
  expect(download).toHaveAttribute('download', 'reel-L1-en.mp4')
  expect(download.getAttribute('href')).toBe(video.getAttribute('src'))
  const wa = screen.getByRole('link', { name: 'Share on WhatsApp' })
  expect(wa.getAttribute('href')).toMatch(/^https:\/\/wa\.me\/\?text=/)
  expect(decodeURIComponent(wa.getAttribute('href')!)).toContain('2 BHK in Kharadi\n')
  expect(screen.getByText('Made without a voiceover. Music only.')).toBeInTheDocument()
  expect(screen.queryByTestId('reel-progress')).not.toBeInTheDocument()
  await act(async () => { jest.advanceTimersByTime(15000) })
  expect(s.latest).toHaveBeenCalledTimes(3) // polling stops once nothing is active
})

test('failed: shows the message and Try again asks for a fresh job', async () => {
  const s = source([{ en: job({ status: 'failed', error: 'Add at least 2 photos' }) }], job({ id: 'j2' }))
  render(<ReelMaker source={s} caption="x" />)
  expect(await screen.findByTestId('reel-failed')).toHaveTextContent('The reel could not be made. Add at least 2 photos')
  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
  })
  expect(s.make).toHaveBeenCalledWith('en', true)
  expect(screen.getByTestId('reel-progress')).toBeInTheDocument()
})

test('a refused request (daily limit, too few photos) is shown', async () => {
  const s = source([{}], new ApiError(429, 'You can make 5 reels a day. Try again tomorrow.'))
  render(<ReelMaker source={s} caption="x" />)
  await waitFor(() => expect(s.latest).toHaveBeenCalled())
  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: 'Make my reel' }))
  })
  expect(screen.getByRole('alert')).toHaveTextContent('5 reels a day')
})

test('helpers: absolute video url and the WhatsApp text', () => {
  expect(reelVideoUrl({ video_path: '/uploads/reels/a.mp4', video_url: null }, 'https://api.test/')).toBe('https://api.test/uploads/reels/a.mp4')
  expect(reelVideoUrl({ video_path: 'https://cdn.test/a.mp4', video_url: null }, 'https://api.test')).toBe('https://cdn.test/a.mp4')
  expect(decodeURIComponent(whatsappReelUrl('https://api.test/a.mp4', ' Home ').split('text=')[1])).toBe('Home\nhttps://api.test/a.mp4')
})

test('client: agent and concierge paths, and the fixture fake finishes a reel', async () => {
  const calls: Array<[string, RequestInit]> = []
  const fetchImpl = jest.fn(async (url: string, init: RequestInit) => {
    calls.push([url, init])
    return { ok: true, status: 200, text: async () => JSON.stringify({ job: job(), jobs: { en: job() }, publications: [] }) } as Response
  })
  const api = createReelsApi({ getToken: () => 't', baseUrl: 'https://api.test', fetchImpl: fetchImpl as unknown as typeof fetch })
  await api.forListing('L1').make('mr')
  await api.forAgentListing('a1', 'L1').latest()
  await api.postReel('a1', 'L1', 'hi')
  expect(calls.map(([u, i]) => `${i.method} ${u}`)).toEqual([
    'POST https://api.test/api/v1/listings/L1/reel',
    'GET https://api.test/api/v1/concierge/agents/a1/listings/L1/reel',
    'POST https://api.test/api/v1/concierge/agents/a1/listings/L1/reel/post',
  ])
  expect(JSON.parse(calls[0][1].body as string)).toEqual({ lang: 'mr' })

  const fx = createFixtureReelsApi().forListing('L9')
  await fx.make('en')
  let latest: ReelJobs = {}
  for (let k = 0; k < 4; k++) latest = await fx.latest()
  expect(latest.en?.status).toBe('done')
})

test('Post sheet: a finished reel can be posted as a Reel, only with consent', async () => {
  latestReels.mockResolvedValue({ en: job({ status: 'done', video_path: '/uploads/reels/x.mp4' }) })
  postReel.mockResolvedValue([{ channel: 'instagram', status: 'dry_run' }, { channel: 'facebook_page', status: 'dry_run' }])
  const { rerender } = render(<PostSheet agentId="a1" agentName="Rahul Sharma" listingId="L1" listingTitle="2 BHK" consentGiven={false} onClose={() => undefined} />)
  const btn = await screen.findByRole('button', { name: 'Post the reel for Rahul' })
  expect(btn).toBeDisabled()
  rerender(<PostSheet agentId="a1" agentName="Rahul Sharma" listingId="L1" listingTitle="2 BHK" consentGiven onClose={() => undefined} />)
  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: 'Post the reel for Rahul' }))
  })
  expect(postReel).toHaveBeenCalledWith('a1', 'L1', 'en')
  expect(screen.getByTestId('reel-results')).toHaveTextContent('Avasetu Instagram: checked (test mode, nothing was published)')
})
