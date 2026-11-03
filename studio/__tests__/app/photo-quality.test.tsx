import React from 'react'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { BrandEditor } from '@/components/app/BrandEditor'
import { PhotoPicker } from '@/components/app/PhotoPicker'
import { ListingPhotos } from '@/components/app/quality/ListingPhotos'
import { EnhanceToggle, QualityBadge } from '@/components/app/quality/QualityBadge'
import { ReviewChip } from '@/components/app/quality/ReviewChip'
import type { BrandingDoc } from '@/lib/app/branding'
import {
  analyzePixels, badgeFor, createQualityApi, displayUrl, normalizeReview, qualityFields, reviewSummary,
} from '@/lib/app/quality'
import type { PhotoQuality, QualityApi, QualityReview } from '@/lib/app/quality'
import type { Media } from '@/lib/app/types'

function pixels(w: number, h: number, f: (x: number, y: number) => number): Uint8ClampedArray {
  const d = new Uint8ClampedArray(w * h * 4)
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const v = f(x, y)
    const p = (y * w + x) * 4
    d[p] = d[p + 1] = d[p + 2] = v
    d[p + 3] = 255
  }
  return d
}

const checker = (x: number, y: number) => (((x >> 3) + (y >> 3)) % 2 ? 210 : 70)

describe('quality lib', () => {
  it('analyzePixels flags dark, blurry and small photos like the backend', () => {
    const big = { width: 1600, height: 1200 }
    expect(analyzePixels(pixels(160, 120, checker), 160, 120, big)).toMatchObject({ issues: [], score: 100 })
    expect(analyzePixels(pixels(160, 120, (x, y) => checker(x, y) * 0.3), 160, 120, big).issues).toContain('dark')
    expect(analyzePixels(pixels(160, 120, () => 140), 160, 120, big).issues).toEqual(['blurry'])
    const small = analyzePixels(pixels(160, 120, checker), 160, 120, { width: 640, height: 480 })
    expect(small.issues).toEqual(['small'])
    expect(small.tips).toEqual(['Send the original photo, not a forwarded one'])
  })

  it('badge text and tips', () => {
    expect(badgeFor({ issues: [] })).toEqual({ tone: 'good', text: 'Good', tip: null })
    expect(badgeFor({ issues: ['dark', 'blurry', 'tilted'] })).toEqual({ tone: 'check', text: 'Check: too dark, blurry', tip: 'Take it again with lights on' })
    expect(badgeFor({ issues: ['tilted'] })?.tip).toBe('Hold the phone straight')
    expect(badgeFor(null)).toBeNull()
  })

  it('displayUrl and qualityFields', () => {
    expect(displayUrl({ url: '/a.jpg', enhanced_url: '/a-enh.jpg', use_enhanced: true })).toBe('/a-enh.jpg')
    expect(displayUrl({ url: '/a.jpg', enhanced_url: '/a-enh.jpg', use_enhanced: false })).toBe('/a.jpg')
    expect(qualityFields({ url: '/a.jpg' })).toEqual({})
    expect(qualityFields({ url: '/a.jpg', quality: { score: 60, issues: ['dark'], tips: ['x'], enhanced_score: 90, width: 9 }, enhanced_url: '/a-enh.jpg', use_enhanced: true }))
      .toEqual({ quality: { score: 60, issues: ['dark'], tips: ['x'], enhanced_score: 90 }, enhanced_url: '/a-enh.jpg', use_enhanced: true })
  })

  it('review summary wording', () => {
    expect(reviewSummary({ score: 82, verdict: 'good', notes: [], source: 'ai', ai_available: true })).toBe('Quality 82/100 · Good')
    expect(reviewSummary({ score: 54, verdict: 'fix', notes: ['AI review unavailable', 'text cut at the bottom'], source: 'rules', ai_available: false }))
      .toBe('Quality 54 · Check: text cut at the bottom')
    expect(reviewSummary(normalizeReview({ score: null }))).toBe('Quality: no image yet')
  })

  it('review client posts kind and id with the token', async () => {
    const body = JSON.stringify({ score: 77.4, verdict: 'good', notes: ['ok'], source: 'ai', ai_available: true })
    const fetchImpl = jest.fn().mockResolvedValue({ ok: true, status: 200, text: async () => body })
    const client = createQualityApi({ getToken: () => 'tok', baseUrl: 'http://api', fetchImpl })
    const r = await client.review('news', 'n1')
    expect(r).toEqual({ score: 77, verdict: 'good', notes: ['ok'], source: 'ai', ai_available: true })
    const [url, init] = fetchImpl.mock.calls[0]
    expect(url).toBe('http://api/api/v1/quality/review')
    expect(JSON.parse(init.body)).toEqual({ kind: 'news', id: 'n1', refresh: false })
    expect(init.headers.Authorization).toBe('Bearer tok')
  })
})

describe('photo badges and the enhanced toggle', () => {
  it('PhotoPicker shows a badge per photo and a tip for the one to retake', async () => {
    const files = [new File(['a'], 'good.jpg', { type: 'image/jpeg' }), new File(['b'], 'dark.jpg', { type: 'image/jpeg' })]
    const analyze = jest.fn(async (f: File): Promise<PhotoQuality> => (f.name === 'dark.jpg' ? { score: 70, issues: ['dark'] } : { score: 100, issues: [] }))
    global.URL.createObjectURL = jest.fn(() => 'blob:x')
    global.URL.revokeObjectURL = jest.fn()
    render(<PhotoPicker files={files} onChange={() => {}} analyze={analyze} />)
    await waitFor(() => expect(screen.getAllByTestId('quality-badge')).toHaveLength(2))
    expect(screen.getAllByTestId('quality-badge').map((b) => b.textContent)).toEqual(['Good', 'Check: too dark'])
    expect(screen.getByTestId('photo-tips')).toHaveTextContent('Photo 2: Take it again with lights on')
  })

  it('QualityBadge renders nothing without an analysis', () => {
    const { container } = render(<QualityBadge quality={null} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('EnhanceToggle switches and peeks before/after', () => {
    const onChange = jest.fn()
    render(<EnhanceToggle original="/a.jpg" enhanced="/a-enh.jpg" value={true} onChange={onChange} scores={{ before: 61, after: 88 }} />)
    expect(screen.getByRole('switch')).toBeChecked()
    fireEvent.click(screen.getByRole('switch'))
    expect(onChange).toHaveBeenCalledWith(false)
    expect(screen.queryByTestId('before-after')).toBeNull()
    fireEvent.click(screen.getByText('Before / after'))
    expect(screen.getByAltText('Before enhancement')).toHaveAttribute('src', '/a.jpg')
    expect(screen.getByAltText('After enhancement')).toHaveAttribute('src', '/a-enh.jpg')
    expect(screen.getByTestId('before-after')).toHaveTextContent('After · 88/100')
  })

  it('ListingPhotos shows the chosen copy and toggles per photo', () => {
    const media: Media[] = [
      { url: '/a.jpg', kind: 'image', order: 0, quality: { score: 60, issues: ['tilted'], enhanced_score: 85 }, enhanced_url: '/a-enh.jpg', use_enhanced: true },
      { url: '/b.jpg', kind: 'image', order: 1, quality: { score: 100, issues: [] } },
    ]
    const onToggle = jest.fn()
    render(<ListingPhotos media={media} onToggle={onToggle} />)
    expect(screen.getByAltText('Photo 1')).toHaveAttribute('src', '/a-enh.jpg')
    expect(screen.getByAltText('Photo 2')).toHaveAttribute('src', '/b.jpg')
    expect(screen.getByTestId('quality-tip')).toHaveTextContent('Hold the phone straight')
    expect(screen.getAllByTestId('enhance-toggle')).toHaveLength(1)
    fireEvent.click(screen.getByRole('switch'))
    expect(onToggle).toHaveBeenCalledWith(0, false)
  })

  it('brand banner: shows quality and switches between the original and the enhanced copy', async () => {
    const doc = (b: BrandingDoc['branding_data'] = {}): BrandingDoc => ({ slug: 'p', agent_name: 'Priya', branding_data: b })
    const save = jest.fn().mockImplementation(async (patch) => doc(patch))
    const upload = jest.fn().mockResolvedValue({ id: '1', url: '/uploads/images/b.jpg', enhanced_url: '/uploads/images/b-enh.jpg', use_enhanced: true,
      quality: { score: 62, issues: ['dark'], enhanced_score: 90 } })
    render(<BrandEditor loadBranding={jest.fn().mockResolvedValue(doc())} saveBranding={save} uploadImage={upload} />)
    await screen.findByTestId('brand-editor')
    const input = screen.getByTestId('brand-banner') as HTMLInputElement
    await act(async () => { fireEvent.change(input, { target: { files: [new File(['x'], 'b.jpg', { type: 'image/jpeg' })] } }) })
    const box = await screen.findByTestId('picked-quality')
    expect(box).toHaveTextContent('Check: too dark')
    expect(box).toHaveTextContent('Take it again with lights on')
    const sw = screen.getByRole('switch')
    expect(sw).toBeChecked()
    fireEvent.click(sw)
    fireEvent.click(screen.getByRole('button', { name: /save/i }))
    await waitFor(() => expect(save).toHaveBeenCalled())
    expect(save.mock.calls[0][0].banner).toBe('/uploads/images/b.jpg')
  })
})

describe('ReviewChip', () => {
  const fake = (r: QualityReview | Error): QualityApi => ({ review: jest.fn(() => (r instanceof Error ? Promise.reject(r) : Promise.resolve(r))) })

  it('shows the score and keeps notes collapsed', async () => {
    const client = fake({ score: 54, verdict: 'fix', notes: ['text cut at the bottom', 'busy background'], source: 'ai', ai_available: true })
    render(<ReviewChip kind="calendar" id="c1" client={client} />)
    const chip = await screen.findByTestId('review-chip')
    expect(chip).toHaveTextContent('Quality 54 · Check: text cut at the bottom')
    expect(chip).not.toHaveAttribute('open')
    expect(screen.getByTestId('review-notes')).toHaveTextContent('busy background')
    expect(client.review).toHaveBeenCalledWith('calendar', 'c1')
  })

  it('good review and the AI-unavailable note', async () => {
    render(<ReviewChip kind="news" id="n1" client={fake({ score: 81, verdict: 'good', notes: ['AI review unavailable'], source: 'rules', ai_available: false })} />)
    const chip = await screen.findByTestId('review-chip')
    expect(chip).toHaveTextContent('Quality 81/100 · Good')
    expect(chip).toHaveTextContent('AI review unavailable: this score comes from automatic checks only.')
  })

  it('a failed review hides the chip and never blocks', async () => {
    const { container } = render(<ReviewChip kind="listing" id="l1" client={fake(new Error('x'))} />)
    await waitFor(() => expect(container).toBeEmptyDOMElement())
  })
})
