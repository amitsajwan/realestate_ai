import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { renderHook } from '@testing-library/react'
import React from 'react'
import { BrochureCard } from '@/components/app/BrochureCard'
import { ApiError } from '@/lib/app/api'
import { createFixtureBrochureApi, sampleKit } from '@/lib/app/brochure'
import type { BrochureApi, BrochureKit } from '@/lib/app/brochure'
import { useBrochure } from '@/lib/app/useBrochure'

jest.mock('@/lib/app/client', () => ({ isFixtureMode: () => false }))

/** The fixture fake behind jest.fn spies, optionally starting with a kit already read. */
function fakeClient(start?: BrochureKit) {
  const fx = createFixtureBrochureApi()
  let seeded = !start
  const c = {
    get: jest.fn(async (lid: string) => {
      if (!seeded) {
        seeded = true
        await fx.upload(lid, new File(['%PDF'], start!.filename, { type: 'application/pdf' }))
        for (const f of start!.facts) await fx.setFact(lid, f.id, f.state)
        for (const i of start!.images ?? []) await fx.setImage(lid, i.id, i.state)
      }
      const k = await fx.get(lid)
      return k && start ? { ...k, image_only_pages: start.image_only_pages, registration: start.registration } : k
    }),
    upload: jest.fn(fx.upload),
    setFact: jest.fn(fx.setFact),
    setRegistration: jest.fn(fx.setRegistration),
    pageImage: jest.fn(async (_l: string, n: number) => `blob:page-${n}`),
    setImage: jest.fn(fx.setImage),
    image: jest.fn(async (_l: string, id: string) => `blob:image-${id}`),
  }
  return c as typeof c & BrochureApi
}

const pdf = (size = 2048, name = 'gulmohar.pdf', type = 'application/pdf') => {
  const f = new File(['%PDF'], name, { type })
  Object.defineProperty(f, 'size', { value: size })
  return f
}

async function choose(file: File) {
  await act(async () => {
    fireEvent.change(screen.getByTestId('brochure-file'), { target: { files: [file] } })
  })
}

test('no brochure yet: explains, uploads a PDF, then shows the facts to confirm', async () => {
  const c = fakeClient()
  render(<BrochureCard listingId="L1" client={c} />)
  expect(await screen.findByRole('button', { name: 'Upload brochure PDF' })).toBeInTheDocument()
  expect(screen.getByText(/30 MB and 40 pages/)).toBeInTheDocument()
  await choose(pdf())
  expect(c.upload).toHaveBeenCalledWith('L1', expect.any(File), expect.any(Function))
  const kit = screen.getByTestId('brochure-kit')
  expect(within(kit).getByText('Confirm the kit')).toBeInTheDocument()
  expect(within(kit).getByText(/as per the builder's brochure/)).toBeInTheDocument()
  expect(screen.getByTestId('image-only')).toHaveTextContent('3 pages are images only and were not read yet.')
  expect(screen.getByText('4 left to check')).toBeInTheDocument()
  // a fact: label, value, quote with its page, and the page thumbnail
  const flooring = screen.getByTestId('fact-f4')
  expect(flooring).toHaveTextContent('Flooring')
  expect(flooring).toHaveTextContent('Vitrified tiles in all rooms')
  expect(flooring).toHaveTextContent('“2x2 vitrified tiles in all rooms”')
  expect(flooring).toHaveTextContent('(page 8)')
  await waitFor(() => expect(within(flooring).getByRole('button', { name: 'Enlarge page 8' })).toBeEnabled())
  // lists are chips
  const amenities = screen.getByTestId('fact-f2')
  expect(within(amenities).getAllByRole('listitem').map((li) => li.textContent)).toEqual(['Clubhouse', 'Swimming pool', 'Gym', "Children's play area"])
})

test('too big or not a PDF: refused on the phone, nothing is sent', async () => {
  const c = fakeClient()
  render(<BrochureCard listingId="L1" client={c} />)
  await screen.findByRole('button', { name: 'Upload brochure PDF' })
  await choose(pdf(31 * 1024 * 1024))
  expect(screen.getByRole('alert')).toHaveTextContent('This PDF is 31.0 MB. The limit is 30 MB.')
  await choose(pdf(100, 'photo.jpg', 'image/jpeg'))
  expect(screen.getByRole('alert')).toHaveTextContent('Choose a PDF file')
  expect(c.upload).not.toHaveBeenCalled()
})

test('upload progress, then reading, then an error from the server is shown', async () => {
  const c = fakeClient()
  let progress: (f: number) => void = () => undefined
  let fail: (e: Error) => void = () => undefined
  c.upload.mockImplementation((_l, _f, onP) => new Promise((_res, rej) => { progress = onP!; fail = rej }))
  render(<BrochureCard listingId="L1" client={c} />)
  await screen.findByRole('button', { name: 'Upload brochure PDF' })
  await choose(pdf())
  act(() => progress(0.42))
  expect(screen.getByTestId('brochure-progress')).toHaveTextContent('Uploading 42%')
  act(() => progress(1))
  expect(screen.getByTestId('brochure-progress')).toHaveTextContent('Reading the brochure')
  await act(async () => fail(new ApiError(422, 'This PDF has 52 pages. The limit is 40.')))
  expect(screen.queryByTestId('brochure-progress')).toBeNull()
  expect(screen.getByRole('alert')).toHaveTextContent('This PDF has 52 pages. The limit is 40.')
  expect(screen.getByRole('button', { name: 'Upload brochure PDF' })).toBeInTheDocument()
})

test('one tap confirms or drops; tapping again sets it back to pending', async () => {
  const c = fakeClient(sampleKit('L1'))
  render(<BrochureCard listingId="L1" client={c} />)
  const row = await screen.findByTestId('fact-f1')
  await act(async () => { fireEvent.click(within(row).getByRole('button', { name: 'Confirm' })) })
  expect(c.setFact).toHaveBeenLastCalledWith('L1', 'f1', 'confirmed', undefined)
  expect(screen.getByTestId('fact-f1')).toHaveAttribute('data-state', 'confirmed')
  expect(within(screen.getByTestId('fact-f1')).getByRole('button', { name: '✓ Confirm' })).toHaveAttribute('aria-pressed', 'true')
  expect(screen.getByText('3 left to check')).toBeInTheDocument()
  await act(async () => { fireEvent.click(within(screen.getByTestId('fact-f1')).getByRole('button', { name: '✓ Confirm' })) })
  expect(c.setFact).toHaveBeenLastCalledWith('L1', 'f1', 'pending', undefined)
  await act(async () => { fireEvent.click(within(screen.getByTestId('fact-f3')).getByRole('button', { name: 'Drop' })) })
  expect(c.setFact).toHaveBeenLastCalledWith('L1', 'f3', 'dropped', undefined)
  expect(screen.getByTestId('fact-f3')).toHaveAttribute('data-state', 'dropped')
})

test('a refused tap puts the fact back and says why', async () => {
  const c = fakeClient(sampleKit('L1'))
  c.setFact.mockRejectedValueOnce(new ApiError(409, 'The brochure was replaced. Refresh.'))
  render(<BrochureCard listingId="L1" client={c} />)
  const row = await screen.findByTestId('fact-f1')
  await act(async () => { fireEvent.click(within(row).getByRole('button', { name: 'Confirm' })) })
  expect(screen.getByTestId('fact-f1')).toHaveAttribute('data-state', 'pending')
  expect(screen.getByRole('alert')).toHaveTextContent('The brochure was replaced. Refresh.')
})

test('Confirm all confirms the facts still pending, leaving dropped ones alone', async () => {
  const k = sampleKit('L1')
  k.facts[2].state = 'dropped'
  const c = fakeClient(k)
  render(<BrochureCard listingId="L1" client={c} />)
  await screen.findByText('3 left to check')
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Confirm all (3)' })) })
  expect(c.setFact.mock.calls.slice(-3).map((a) => [a[1], a[2]])).toEqual([['f1', 'confirmed'], ['f2', 'confirmed'], ['f4', 'confirmed']])
  expect(screen.getByText('All facts checked.')).toBeInTheDocument()
  expect(screen.getByTestId('fact-f3')).toHaveAttribute('data-state', 'dropped')
  expect(screen.queryByRole('button', { name: /Confirm all/ })).toBeNull()
})

test('Fix: edit a text value inline (Enter saves and confirms); edit a list as chips', async () => {
  const c = fakeClient(sampleKit('L1'))
  render(<BrochureCard listingId="L1" client={c} />)
  const row = await screen.findByTestId('fact-f4')
  fireEvent.click(within(row).getByRole('button', { name: 'Fix' }))
  const box = within(row).getByLabelText('Flooring')
  fireEvent.change(box, { target: { value: 'Italian marble in living room' } })
  await act(async () => { fireEvent.keyDown(box, { key: 'Enter' }) })
  expect(c.setFact).toHaveBeenLastCalledWith('L1', 'f4', 'confirmed', 'Italian marble in living room')
  expect(screen.getByTestId('fact-f4')).toHaveTextContent('Italian marble in living room')
  expect(screen.getByTestId('fact-f4')).toHaveTextContent('Edited')

  const am = screen.getByTestId('fact-f2')
  fireEvent.click(within(am).getByRole('button', { name: 'Fix' }))
  fireEvent.click(within(am).getByRole('button', { name: 'Remove Gym' }))
  fireEvent.change(within(am).getByLabelText('Add: Amenities'), { target: { value: 'Jogging track' } })
  fireEvent.click(within(am).getByRole('button', { name: 'Add' }))
  await act(async () => { fireEvent.click(within(am).getByRole('button', { name: 'Save and confirm' })) })
  expect(c.setFact).toHaveBeenLastCalledWith('L1', 'f2', 'confirmed', ['Clubhouse', 'Swimming pool', "Children's play area", 'Jogging track'])
})

test('page thumbnail opens large; Escape closes it', async () => {
  const c = fakeClient(sampleKit('L1'))
  render(<BrochureCard listingId="L1" client={c} />)
  const row = await screen.findByTestId('fact-f2')
  const thumb = within(row).getByRole('button', { name: 'Enlarge page 4' })
  await waitFor(() => expect(thumb).toBeEnabled())
  fireEvent.click(thumb)
  const dialog = screen.getByRole('dialog', { name: 'Page 4' })
  expect(within(dialog).getByRole('img', { name: 'Page 4' })).toHaveAttribute('src', 'blob:page-4')
  expect(within(dialog).getByRole('button', { name: 'Close' })).toHaveFocus()
  fireEvent.keyDown(document, { key: 'Escape' })
  expect(screen.queryByRole('dialog')).toBeNull()
})

test('plans and images: thumbnails with what they are; Use and Don\'t use call the API and toggle back', async () => {
  const c = fakeClient(sampleKit('L1'))
  render(<BrochureCard listingId="L1" client={c} />)
  const row = await screen.findByTestId('brochure-images')
  expect(within(row).getByRole('heading', { name: 'Plans and images from the brochure' })).toBeInTheDocument()
  expect(row).toHaveTextContent('never go in the walkthrough video')
  const render1 = screen.getByTestId('image-i1')
  expect(render1).toHaveTextContent("Render · Artist's impression")
  expect(render1).toHaveTextContent('Page 1')
  const plan = screen.getByTestId('image-i7')
  expect(plan).toHaveTextContent('Floor plan')
  await waitFor(() => expect(c.image).toHaveBeenCalledWith('L1', 'i7'))

  await act(async () => { fireEvent.click(within(plan).getByRole('button', { name: 'Use' })) })
  expect(c.setImage).toHaveBeenLastCalledWith('L1', 'i7', 'confirmed')
  expect(screen.getByTestId('image-i7')).toHaveAttribute('data-state', 'confirmed')
  expect(within(screen.getByTestId('image-i7')).getByRole('button', { name: '✓ Use' })).toHaveAttribute('aria-pressed', 'true')
  await act(async () => { fireEvent.click(within(screen.getByTestId('image-i7')).getByRole('button', { name: '✓ Use' })) })
  expect(c.setImage).toHaveBeenLastCalledWith('L1', 'i7', 'pending')
  await act(async () => { fireEvent.click(within(render1).getByRole('button', { name: "Don't use" })) })
  expect(c.setImage).toHaveBeenLastCalledWith('L1', 'i1', 'dropped')
  expect(screen.getByTestId('image-i1')).toHaveAttribute('data-state', 'dropped')
  expect(c.setFact).not.toHaveBeenCalled()
})

test('a refused image tap puts it back and says why', async () => {
  const c = fakeClient(sampleKit('L1'))
  c.setImage.mockRejectedValueOnce(new ApiError(404, 'No such image in this brochure.'))
  render(<BrochureCard listingId="L1" client={c} />)
  const plan = await screen.findByTestId('image-i7')
  await act(async () => { fireEvent.click(within(plan).getByRole('button', { name: 'Use' })) })
  expect(screen.getByTestId('image-i7')).toHaveAttribute('data-state', 'pending')
  expect(screen.getByRole('alert')).toHaveTextContent('This listing or brochure was not found')
})

test('an image opens large in the same viewer; Close shuts it', async () => {
  const c = fakeClient(sampleKit('L1'))
  render(<BrochureCard listingId="L1" client={c} />)
  const plan = await screen.findByTestId('image-i7')
  const thumb = within(plan).getByRole('button', { name: 'Enlarge: Floor plan, page 7' })
  await waitFor(() => expect(thumb).toBeEnabled())
  fireEvent.click(thumb)
  const dialog = screen.getByRole('dialog', { name: 'Floor plan' })
  expect(within(dialog).getByRole('img', { name: 'Floor plan' })).toHaveAttribute('src', 'blob:image-i7')
  fireEvent.click(within(dialog).getByRole('button', { name: 'Close' }))
  expect(screen.queryByRole('dialog')).toBeNull()
})

test('a kit without images shows no images row', async () => {
  const k = sampleKit('L1')
  const c = fakeClient(k)
  c.get.mockImplementationOnce(async () => ({ ...k, images: undefined }))
  render(<BrochureCard listingId="L1" client={c} />)
  await screen.findByTestId('brochure-kit')
  expect(screen.queryByTestId('brochure-images')).toBeNull()
})

test('registration: unknown asks the question; a bad number is refused, a good one is saved', async () => {
  const c = fakeClient(sampleKit('L1'))
  render(<BrochureCard listingId="L1" client={c} />)
  const q = await screen.findByTestId('reg-question')
  expect(within(q).getByText('Is this project registered with MahaRERA, or exempt?')).toBeInTheDocument()
  expect(within(q).getByText(/more than 500 sq m of land or with more than 8 units/)).toBeInTheDocument()
  fireEvent.click(within(q).getByLabelText('Registered with MahaRERA'))
  const num = within(q).getByLabelText('MahaRERA number')
  fireEvent.change(num, { target: { value: 'ABC123' } })
  await act(async () => { fireEvent.click(within(q).getByRole('button', { name: 'Save answer' })) })
  expect(c.setRegistration).not.toHaveBeenCalled()
  expect(num).toHaveAttribute('aria-invalid', 'true')
  expect(within(q).getByRole('alert')).toHaveTextContent('PR and 13 digits')
  fireEvent.change(num, { target: { value: 'p5210 0076768' } })
  await act(async () => { fireEvent.click(within(q).getByRole('button', { name: 'Save answer' })) })
  expect(c.setRegistration).toHaveBeenCalledWith('L1', { status: 'registered', rera_no: 'P52100076768' })
})

test('registration: exempt is saved and shown with a way to change it', async () => {
  const k = sampleKit('L1')
  const c = fakeClient(k)
  c.setRegistration.mockResolvedValueOnce({ ...k, registration: { status: 'exempt', rera_no: null, note: '' } })
  render(<BrochureCard listingId="L1" client={c} />)
  const q = await screen.findByTestId('reg-question')
  fireEvent.click(within(q).getByLabelText('Exempt (small project or resale)'))
  await act(async () => { fireEvent.click(within(q).getByRole('button', { name: 'Save answer' })) })
  expect(c.setRegistration).toHaveBeenCalledWith('L1', { status: 'exempt' })
  expect(screen.queryByTestId('reg-question')).toBeNull()
  expect(screen.getByTestId('reg-status')).toHaveTextContent('Exempt from MahaRERA registration')
  fireEvent.click(screen.getByRole('button', { name: 'Change' }))
  expect(screen.getByTestId('reg-question')).toBeInTheDocument()
})

test('registration: verified is shown, not asked', async () => {
  const c = fakeClient({ ...sampleKit('L1'), registration: { status: 'verified', rera_no: 'P52100076768', note: '' } })
  render(<BrochureCard listingId="L1" client={c} />)
  expect(await screen.findByTestId('reg-status')).toHaveTextContent('MahaRERA: verified P52100076768')
  expect(screen.queryByTestId('reg-question')).toBeNull()
})

test('a failed read shows the reason and lets the agent upload again', async () => {
  const c = fakeClient()
  c.get.mockResolvedValueOnce({ ...sampleKit('L1'), status: 'failed', error: 'The PDF is password protected.', facts: [] })
  render(<BrochureCard listingId="L1" client={c} />)
  expect(await screen.findByRole('alert')).toHaveTextContent('The brochure could not be read. The PDF is password protected.')
  expect(screen.getByRole('button', { name: 'Upload a different brochure' })).toBeInTheDocument()
})

test('useBrochure: loading, then null when there is no brochure; a load error is kept', async () => {
  const c = fakeClient()
  const { result } = renderHook(() => useBrochure('L1', c))
  expect(result.current.loading).toBe(true)
  await waitFor(() => expect(result.current.loading).toBe(false))
  expect(result.current.kit).toBeNull()
  c.get.mockRejectedValueOnce(new ApiError(0, 'Cannot reach the server. Check your internet.'))
  await act(async () => { await result.current.reload() })
  expect(result.current.error).toBe('Cannot reach the server. Check your internet.')
})
