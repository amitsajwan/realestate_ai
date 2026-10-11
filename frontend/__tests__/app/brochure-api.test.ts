import { ApiError } from '@/lib/app/api'
import {
  BROCHURE_MAX_BYTES,
  brochureFileError,
  createBrochureApi,
  createFixtureBrochureApi,
  friendlyBrochureError,
  isReraNo,
  needsRegistrationAnswer,
  pendingFacts,
  sampleKit,
} from '@/lib/app/brochure'

jest.mock('@/lib/app/client', () => ({ isFixtureMode: () => false }))

const kit = sampleKit('L1')
const ok = (body: unknown, status = 200) =>
  ({ ok: status < 400, status, text: async () => (body === undefined ? '' : JSON.stringify(body)), blob: async () => new Blob(['x']) }) as unknown as Response

function client(responses: Response[]) {
  const calls: Array<{ url: string; init: RequestInit }> = []
  let i = 0
  const fetchImpl = jest.fn(async (url: string, init: RequestInit) => {
    calls.push({ url, init })
    return responses[Math.min(i++, responses.length - 1)]
  })
  const api = createBrochureApi({ getToken: () => 'tok', baseUrl: 'https://api.test', fetchImpl: fetchImpl as unknown as typeof fetch })
  return { api, calls, fetchImpl }
}

class FakeXhr {
  static last: FakeXhr
  method = ''
  url = ''
  headers: Record<string, string> = {}
  body: FormData | null = null
  status = 0
  responseText = ''
  upload: { onprogress: ((ev: { lengthComputable: boolean; loaded: number; total: number }) => void) | null } = { onprogress: null }
  onload: (() => void) | null = null
  onerror: (() => void) | null = null
  onabort: (() => void) | null = null
  constructor() {
    FakeXhr.last = this
  }
  open(m: string, u: string) {
    this.method = m
    this.url = u
  }
  setRequestHeader(k: string, v: string) {
    this.headers[k] = v
  }
  send(b: FormData) {
    this.body = b
  }
  respond(status: number, body: unknown) {
    this.status = status
    this.responseText = JSON.stringify(body)
    this.onload?.()
  }
}

const pdf = (size = 1000, name = 'brochure.pdf', type = 'application/pdf') => {
  const f = new File(['%PDF'], name, { type })
  Object.defineProperty(f, 'size', { value: size })
  return f
}

test('get: the kit, or null when there is no brochure (404); other errors are thrown', async () => {
  const { api, calls } = client([ok(kit), ok({ detail: 'No brochure' }, 404), ok({ detail: 'Boom' }, 500)])
  expect(await api.get('L 1')).toEqual(kit)
  expect(calls[0].url).toBe('https://api.test/api/v1/listings/L%201/brochure')
  expect((calls[0].init.headers as Record<string, string>).Authorization).toBe('Bearer tok')
  expect(await api.get('L1')).toBeNull()
  await expect(api.get('L1')).rejects.toMatchObject({ status: 500, detail: 'Boom' })
})

test('setFact and setRegistration send the contract bodies', async () => {
  const { api, calls } = client([ok(kit)])
  await api.setFact('L1', 'f2', 'confirmed')
  await api.setFact('L1', 'f2', 'confirmed', ['Gym', 'Pool'])
  await api.setRegistration('L1', { status: 'registered', rera_no: ' p521 0007 6768 ' })
  await api.setRegistration('L1', { status: 'exempt' })
  expect(calls.map((c) => `${c.init.method} ${c.url}`)).toEqual([
    'PATCH https://api.test/api/v1/listings/L1/brochure/facts/f2',
    'PATCH https://api.test/api/v1/listings/L1/brochure/facts/f2',
    'POST https://api.test/api/v1/listings/L1/brochure/registration',
    'POST https://api.test/api/v1/listings/L1/brochure/registration',
  ])
  expect(calls.map((c) => JSON.parse(c.init.body as string))).toEqual([
    { state: 'confirmed' },
    { state: 'confirmed', value: ['Gym', 'Pool'] },
    { status: 'registered', rera_no: 'P52100076768' },
    { status: 'exempt' },
  ])
})

test('server refusals come back as ApiError with the detail', async () => {
  const { api } = client([ok({ detail: 'RERA number not in the MahaRERA format' }, 422)])
  const e = await api.setRegistration('L1', { status: 'registered', rera_no: 'P5' }).catch((x) => x)
  expect(e).toBeInstanceOf(ApiError)
  expect(friendlyBrochureError(e)).toBe('RERA number not in the MahaRERA format')
  expect(friendlyBrochureError(new ApiError(413, 'too big'))).toMatch(/30 MB and 40 pages/)
})

test('network failure reads as a connection message', async () => {
  const fetchImpl = jest.fn(async () => { throw new TypeError('Failed to fetch') })
  const api = createBrochureApi({ getToken: () => null, baseUrl: '', fetchImpl: fetchImpl as unknown as typeof fetch })
  await expect(api.get('L1')).rejects.toMatchObject({ status: 0, detail: 'Cannot reach the server. Check your internet.' })
})

test('upload: multipart field "file", bearer header, progress, then the kit', async () => {
  const api = createBrochureApi({ getToken: () => 'tok', baseUrl: 'https://api.test', xhr: () => new FakeXhr() as never })
  const progress: number[] = []
  const p = api.upload('L1', pdf(), (f) => progress.push(f))
  const x = FakeXhr.last
  expect(`${x.method} ${x.url}`).toBe('POST https://api.test/api/v1/listings/L1/brochure')
  expect(x.headers.Authorization).toBe('Bearer tok')
  expect((x.body!.get('file') as File).name).toBe('brochure.pdf')
  x.upload.onprogress!({ lengthComputable: true, loaded: 50, total: 100 })
  x.respond(200, kit)
  await expect(p).resolves.toEqual(kit)
  expect(progress).toEqual([0.5, 1])
})

test('upload: refusal and dropped connection', async () => {
  const api = createBrochureApi({ getToken: () => 'tok', baseUrl: '', xhr: () => new FakeXhr() as never })
  const p1 = api.upload('L1', pdf())
  FakeXhr.last.respond(422, { detail: 'This PDF has 52 pages. The limit is 40.' })
  await expect(p1).rejects.toMatchObject({ status: 422, detail: 'This PDF has 52 pages. The limit is 40.' })
  const p2 = api.upload('L1', pdf())
  FakeXhr.last.onerror!()
  await expect(p2).rejects.toMatchObject({ status: 0 })
})

test('page thumbnails are fetched once with the token and kept', async () => {
  const created = jest.fn(() => 'blob:page-4')
  const orig = URL.createObjectURL
  ;(URL as unknown as { createObjectURL: unknown }).createObjectURL = created
  try {
    const { api, calls } = client([ok(undefined)])
    expect(await api.pageImage('L1', 4)).toBe('blob:page-4')
    expect(await api.pageImage('L1', 4)).toBe('blob:page-4')
    expect(calls).toHaveLength(1)
    expect(calls[0].url).toBe('https://api.test/api/v1/listings/L1/brochure/pages/4.jpg')
    expect((calls[0].init.headers as Record<string, string>).Authorization).toBe('Bearer tok')
  } finally {
    ;(URL as unknown as { createObjectURL: unknown }).createObjectURL = orig
  }
})

test('images: PATCH the state, GET the JPEG once with the token', async () => {
  const created = jest.fn(() => 'blob:image-i3')
  const orig = URL.createObjectURL
  ;(URL as unknown as { createObjectURL: unknown }).createObjectURL = created
  try {
    const { api, calls } = client([ok(kit), ok(undefined)])
    const k = await api.setImage('L1', 'i3', 'confirmed')
    expect(k.images?.map((i) => i.id)).toEqual(['i1', 'i7'])
    expect(calls[0].init.method).toBe('PATCH')
    expect(calls[0].url).toBe('https://api.test/api/v1/listings/L1/brochure/images/i3')
    expect(JSON.parse(calls[0].init.body as string)).toEqual({ state: 'confirmed' })
    expect(await api.image('L1', 'i3')).toBe('blob:image-i3')
    expect(await api.image('L1', 'i3')).toBe('blob:image-i3')
    expect(calls).toHaveLength(2)
    expect(calls[1].url).toBe('https://api.test/api/v1/listings/L1/brochure/images/i3.jpg')
    expect((calls[1].init.headers as Record<string, string>).Authorization).toBe('Bearer tok')
  } finally {
    ;(URL as unknown as { createObjectURL: unknown }).createObjectURL = orig
  }
})

test('a missing image is an ApiError and is fetched again next time', async () => {
  const { api, calls } = client([ok({ detail: 'No such image.' }, 404)])
  await expect(api.image('L1', 'i9')).rejects.toMatchObject({ status: 404 })
  await expect(api.image('L1', 'i9')).rejects.toBeInstanceOf(ApiError)
  expect(calls).toHaveLength(2)
})

test('fixture fake: images can be used and dropped', async () => {
  const fx = createFixtureBrochureApi()
  await fx.upload('L1', pdf())
  const k = await fx.setImage('L1', 'i7', 'confirmed')
  expect(k.images?.find((i) => i.id === 'i7')?.state).toBe('confirmed')
  expect(k.images?.find((i) => i.id === 'i1')?.label).toBe("Artist's impression")
  await expect(fx.setImage('L1', 'nope', 'confirmed')).rejects.toBeInstanceOf(ApiError)
})

test('file checks before upload: PDF only, not empty, 30 MB at most', () => {
  expect(brochureFileError(pdf())).toBeNull()
  expect(brochureFileError(pdf(1000, 'b.PDF', ''))).toBeNull()
  expect(brochureFileError(pdf(1000, 'b.jpg', 'image/jpeg'))).toMatch(/PDF/)
  expect(brochureFileError(pdf(0))).toMatch(/empty/)
  expect(brochureFileError(pdf(BROCHURE_MAX_BYTES))).toBeNull()
  expect(brochureFileError(pdf(BROCHURE_MAX_BYTES + 1))).toMatch(/limit is 30 MB/)
})

test('MahaRERA number format and kit helpers', () => {
  expect(isReraNo('P52100076768')).toBe(true)
  expect(isReraNo('p5210 0076768')).toBe(true)
  expect(isReraNo('P42100076768')).toBe(false)
  expect(isReraNo('P5')).toBe(false)
  expect(isReraNo('PR1234567')).toBe(false)
  expect(pendingFacts(kit)).toHaveLength(4)
  expect(needsRegistrationAnswer(kit)).toBe(true)
  expect(needsRegistrationAnswer({ ...kit, registration: { status: 'verified', rera_no: 'P52100076768', note: '' } })).toBe(false)
  expect(needsRegistrationAnswer(null)).toBe(false)
})

test('fixture fake: upload, fix a fact, answer the registration question', async () => {
  const fx = createFixtureBrochureApi()
  expect(await fx.get('L9')).toBeNull()
  await fx.upload('L9', pdf())
  const k = await fx.setFact('L9', 'f4', 'confirmed', 'Italian marble')
  expect(k.facts.find((f) => f.id === 'f4')).toMatchObject({ state: 'confirmed', value: 'Italian marble', edited: true })
  expect((await fx.setRegistration('L9', { status: 'exempt' })).registration.status).toBe('exempt')
})
