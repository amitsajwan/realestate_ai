import { compressImage, fitWithin } from '@/lib/app/imageCompress'

describe('fitWithin', () => {
  it('scales the longer side down to the max, keeping the ratio', () => {
    expect(fitWithin(4000, 3000)).toEqual({ width: 1280, height: 960 })
    expect(fitWithin(3000, 4000)).toEqual({ width: 960, height: 1280 })
  })
  it('never upscales small images', () => {
    expect(fitWithin(800, 600)).toEqual({ width: 800, height: 600 })
  })
  it('never returns a zero side', () => {
    expect(fitWithin(10000, 1).height).toBeGreaterThanOrEqual(1)
  })
})

describe('compressImage', () => {
  it('returns non-images and gifs untouched', async () => {
    const pdf = new File(['x'], 'a.pdf', { type: 'application/pdf' })
    const gif = new File(['x'], 'a.gif', { type: 'image/gif' })
    expect(await compressImage(pdf)).toBe(pdf)
    expect(await compressImage(gif)).toBe(gif)
  })
  it('falls back to the original file when the browser cannot decode it', async () => {
    const bad = new File(['not really an image'], 'a.jpg', { type: 'image/jpeg' })
    expect(await compressImage(bad)).toBe(bad) // jsdom has no image decoding
  })
})
