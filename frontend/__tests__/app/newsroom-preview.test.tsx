import { act, fireEvent, render, screen, within } from '@testing-library/react'
import React from 'react'
import { QueueCard } from '@/components/app/newsroom/QueueCard'
import { createFixtureNewsroomApi, createNewsroomApi, FIXTURE_QUEUE, mediaUrl, normalizeItem, normalizePreview } from '@/lib/app/newsroom'
import type { NewsroomItem } from '@/lib/app/newsroom'

jest.mock('@/lib/app/client', () => ({ errorMessage: (e: Error) => e.message, isFixtureMode: () => false }))
jest.mock('@/lib/app/session', () => ({ getToken: () => 'tok' }))

const item = (over: Partial<NewsroomItem> = {}): NewsroomItem => ({ ...FIXTURE_QUEUE[0], ...over })
const noop = jest.fn().mockResolvedValue(undefined)

describe('Studio preview before Approve', () => {
  it('shows the card, the channels it goes to and the exact captions', () => {
    render(<QueueCard item={item()} onApprove={noop} onReject={noop} />)
    const pv = screen.getByTestId('post-preview')
    const ch = within(screen.getByTestId('preview-channels'))
    expect(ch.getByText(/Facebook Page/)).toBeInTheDocument()
    expect(ch.getByText(/Instagram/)).toBeInTheDocument()
    expect(within(pv).getByAltText(/Instagram card/)).toHaveAttribute('src', expect.stringContaining('gn-metro-hinjewadi-1-ig.jpg'))
    expect(within(pv).getByAltText(/Facebook card/)).toHaveAttribute('src', expect.stringContaining('-fb.jpg'))
    expect(screen.getByTestId('caption-facebook').textContent).toBe(FIXTURE_QUEUE[0].captions.facebook)
    expect(screen.getByTestId('caption-facebook').textContent).toContain('Read more: https://34-180-39-243.sslip.io/news/gn-metro-hinjewadi-1')
    expect(screen.getByTestId('caption-instagram').textContent).not.toMatch(/https?:\/\//)
    expect(screen.getByTestId('caption-instagram').textContent).toContain('link in our bio')
    expect(screen.getByTestId('preview-dry-run')).toHaveTextContent('will not post anything for real')
  })

  it('lists only the channels that will be used and says when the card is not drawn yet', () => {
    render(<QueueCard item={FIXTURE_QUEUE[1]} onApprove={noop} onReject={noop} />)
    expect(within(screen.getByTestId('preview-channels')).queryByText(/Instagram/)).toBeNull()
    expect(screen.getByTestId('preview-no-card')).toBeInTheDocument()
    expect(screen.queryByTestId('preview-dry-run')).toBeNull()
  })

  it('shows nothing extra for an old server that sends no preview fields', () => {
    render(<QueueCard item={normalizeItem({ id: 'x', title: 'T', draft: 'body', check: { ok: true, problems: [] } })} onApprove={noop} onReject={noop} />)
    expect(screen.queryByTestId('post-preview')).toBeNull()
    expect(screen.getByRole('button', { name: 'Approve' })).toBeEnabled()
  })

  it('blocks Approve and shows the reason when a caption fails the checks', () => {
    render(<QueueCard item={item({ captionProblems: { instagram: ['Copies more than 15 words in a row from the source: reword it'] } })} onApprove={noop} onReject={noop} />)
    expect(screen.getByTestId('caption-problems-instagram')).toHaveTextContent('Copies more than 15 words')
    expect(screen.getByTestId('approve-blocked')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Approve' })).toBeDisabled()
  })

  describe('after an edit', () => {
    beforeEach(() => jest.useFakeTimers())
    afterEach(() => jest.useRealTimers())

    it('asks the server for the captions of the edited text, after a pause, and shows them', async () => {
      const onPreview = jest.fn().mockResolvedValue({ card: null, channels: [], captions: { facebook: 'EDITED FB CAPTION', instagram: 'EDITED IG CAPTION' }, captionProblems: {}, dryRun: true })
      render(<QueueCard item={item()} onApprove={noop} onReject={noop} onPreview={onPreview} />)
      fireEvent.change(screen.getByLabelText('Post text'), { target: { value: 'My own words. Thoughts?' } })
      expect(onPreview).not.toHaveBeenCalled() // debounced
      expect(screen.getAllByText('Updating...').length).toBeGreaterThan(0)
      await act(async () => { jest.advanceTimersByTime(700) })
      expect(onPreview).toHaveBeenCalledTimes(1)
      expect(onPreview).toHaveBeenCalledWith('gn-metro-hinjewadi-1', 'My own words. Thoughts?')
      expect(screen.getByTestId('caption-facebook')).toHaveTextContent('EDITED FB CAPTION')
      expect(screen.getByTestId('caption-instagram')).toHaveTextContent('EDITED IG CAPTION')
    })

    it('blocks Approve when the edited text produces a caption that fails, and frees it when fixed', async () => {
      const onPreview = jest.fn()
        .mockResolvedValueOnce({ card: null, channels: [], captions: { facebook: 'a', instagram: 'b' }, captionProblems: { facebook: ['Figures not found in the source: 99'] }, dryRun: false })
        .mockResolvedValueOnce({ card: null, channels: [], captions: { facebook: 'c', instagram: 'd' }, captionProblems: {}, dryRun: false })
      render(<QueueCard item={item()} onApprove={noop} onReject={noop} onPreview={onPreview} />)
      const box = screen.getByLabelText('Post text')
      fireEvent.change(box, { target: { value: 'Costs 99 crore. Thoughts?' } })
      await act(async () => { jest.advanceTimersByTime(700) })
      expect(screen.getByRole('button', { name: 'Approve' })).toBeDisabled()
      expect(screen.getByTestId('caption-problems-facebook')).toHaveTextContent('Figures not found')
      fireEvent.change(box, { target: { value: 'Costs less. Thoughts?' } })
      await act(async () => { jest.advanceTimersByTime(700) })
      expect(screen.getByRole('button', { name: 'Approve' })).toBeEnabled()
    })

    it('keeps the current captions when the preview cannot be loaded, and returns to the stored ones when the edit is undone', async () => {
      const onPreview = jest.fn().mockRejectedValue(new Error('down'))
      render(<QueueCard item={item()} onApprove={noop} onReject={noop} onPreview={onPreview} />)
      const box = screen.getByLabelText('Post text')
      fireEvent.change(box, { target: { value: 'Changed. Thoughts?' } })
      await act(async () => { jest.advanceTimersByTime(700) })
      expect(screen.getByTestId('caption-facebook').textContent).toBe(FIXTURE_QUEUE[0].captions.facebook)
      expect(screen.queryByText('Updating...')).toBeNull()
      fireEvent.change(box, { target: { value: FIXTURE_QUEUE[0].draft } })
      expect(onPreview).toHaveBeenCalledTimes(1)
    })
  })
})

describe('preview client and normalising', () => {
  it('resolves media addresses and tolerates anything', () => {
    expect(mediaUrl('https://m.test/a.jpg')).toBe('https://m.test/a.jpg')
    expect(mediaUrl('/uploads/a.jpg', 'http://api.test/')).toBe('http://api.test/uploads/a.jpg')
    expect(mediaUrl('a.jpg')).toBeNull()
    expect(mediaUrl(null)).toBeNull()
    const p = normalizePreview({ card: { fb: '/uploads/n/x-fb.jpg', ig: 'https://m.test/x-ig.jpg', variant: 'photo' }, channels: [{ id: 'instagram' }, { id: 'tiktok' }],
      captions: { facebook: 'hi', bad: 3 }, caption_problems: { facebook: ['x'], instagram: [] }, dry_run: true })
    expect(p.card?.ig).toBe('https://m.test/x-ig.jpg')
    expect(p.card?.slides).toEqual(['https://m.test/x-ig.jpg'])
    expect(p.channels).toEqual([{ id: 'instagram', label: 'Instagram', post: '' }])
    expect(p.captions).toEqual({ facebook: 'hi' })
    expect(p.captionProblems).toEqual({ facebook: ['x'] })
    expect(p.dryRun).toBe(true)
    expect(normalizePreview(null)).toEqual({ card: null, channels: [], captions: {}, captionProblems: {}, dryRun: false })
  })

  it('posts the edited text to the preview endpoint', async () => {
    const f = jest.fn().mockResolvedValue({ ok: true, status: 200, text: async () => JSON.stringify({ captions: { facebook: 'x' }, channels: [], card: null }) } as unknown as Response)
    const api = createNewsroomApi({ getToken: () => 'abc', baseUrl: 'http://x', fetchImpl: f as unknown as typeof fetch })
    expect((await api.preview('i 1', 'new text')).captions.facebook).toBe('x')
    await api.preview('i2')
    expect(f.mock.calls.map((c) => [c[0], c[1].method, c[1].body])).toEqual([
      ['http://x/api/v1/newsroom/items/i%201/preview', 'POST', JSON.stringify({ text: 'new text' })],
      ['http://x/api/v1/newsroom/items/i2/preview', 'POST', '{}'],
    ])
  })

  it('the fixture api previews edited text and refuses unknown items', async () => {
    const f = createFixtureNewsroomApi()
    const p = await f.preview('gn-metro-hinjewadi-1', 'Fresh line.')
    expect(p.captions.facebook.startsWith('Fresh line.')).toBe(true)
    expect(p.captions.facebook.endsWith('PUNE Property · https://34-180-39-243.sslip.io')).toBe(true)
    await expect(f.preview('gone')).rejects.toMatchObject({ status: 404 })
  })
})
