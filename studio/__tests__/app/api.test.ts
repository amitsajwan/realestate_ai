import { ApiError, createApiClient, parseErrorBody } from '@/lib/app/api'

function fakeFetch(status: number, body: unknown) {
  return jest.fn(async () => ({
    ok: status >= 200 && status < 300,
    status,
    text: async () => (body === undefined ? '' : JSON.stringify(body)),
  })) as unknown as jest.MockedFunction<typeof fetch>
}

describe('api client', () => {
  it('adds the bearer header and hits /api/v1', async () => {
    const f = fakeFetch(200, { items: [{ id: 'a' }] })
    const api = createApiClient({ baseUrl: 'http://x', getToken: () => 'tok', fetchImpl: f })
    const items = await api.listListings('live')
    expect(items).toEqual([{ id: 'a' }])
    const [url, init] = f.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toBe('http://x/api/v1/listings?status=live&limit=100')
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer tok')
  })

  it('sends no auth header without a token and posts JSON', async () => {
    const f = fakeFetch(200, { sent: true, dev_code: '123456' })
    const api = createApiClient({ baseUrl: '', getToken: () => null, fetchImpl: f })
    await api.requestOtp('+919876543210')
    const [url, init] = f.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toBe('/api/v1/join/otp/request')
    expect((init.headers as Record<string, string>).Authorization).toBeUndefined()
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body as string)).toEqual({ phone: '+919876543210' })
  })

  it('calls onUnauthorized on 401 with a token and throws ApiError', async () => {
    const onUnauthorized = jest.fn()
    const api = createApiClient({ getToken: () => 'tok', onUnauthorized, fetchImpl: fakeFetch(401, { detail: 'Unauthorized' }) })
    await expect(api.getListing('x')).rejects.toMatchObject({ status: 401, detail: 'Unauthorized' })
    expect(onUnauthorized).toHaveBeenCalledTimes(1)
  })

  it('does not treat a 401 from login (no token) as session expiry', async () => {
    const onUnauthorized = jest.fn()
    const api = createApiClient({ getToken: () => null, onUnauthorized, fetchImpl: fakeFetch(401, { detail: 'Bad OTP' }) })
    await expect(api.verifyOtp('+919876543210', '000000')).rejects.toBeInstanceOf(ApiError)
    expect(onUnauthorized).not.toHaveBeenCalled()
  })

  it('maps network failures to status 0', async () => {
    const f = jest.fn().mockRejectedValue(new TypeError('failed')) as unknown as typeof fetch
    const api = createApiClient({ getToken: () => null, fetchImpl: f })
    const e = await api.requestOtp('+919876543210').catch((x) => x)
    expect(e.isNetwork).toBe(true)
  })

  it('maps publish 422 missing-field lists to form errors', async () => {
    const api = createApiClient({ getToken: () => 't', fetchImpl: fakeFetch(422, { detail: { missing: ['price_inr', 'media'] } }) })
    const e = (await api.publishListing('1').catch((x) => x)) as ApiError
    expect(e.status).toBe(422)
    expect(e.missing).toEqual(['price_inr', 'media'])
    expect(e.fields).toEqual({ price_inr: 'Required', media: 'Required' })
  })

  it('sends ai/draft as multipart with image_count', async () => {
    const f = fakeFetch(200, { draft: {}, confidence: {}, missing: [], warnings: [] })
    const api = createApiClient({ getToken: () => 't', fetchImpl: f })
    await api.aiDraft({ text: ' 2 bhk baner ', audio: new Blob(['x'], { type: 'audio/webm' }), image_count: 2 })
    const init = (f.mock.calls[0] as unknown as [string, RequestInit])[1]
    const form = init.body as FormData
    expect(form.get('text')).toBe('2 bhk baner')
    expect(form.get('image_count')).toBe('2')
    expect((form.get('audio') as File).name).toBe('voice.webm')
    expect((init.headers as Record<string, string>)['Content-Type']).toBeUndefined()
  })

  it('uploads images to /uploads/images and fails when the server dropped files', async () => {
    const f = fakeFetch(200, { success: true, files: [{ id: '1', url: 'http://h/u/1.jpg' }] })
    const api = createApiClient({ getToken: () => 't', fetchImpl: f })
    const a = new File(['a'], 'a.jpg', { type: 'image/jpeg' })
    const b = new File(['b'], 'b.jpg', { type: 'image/jpeg' })
    expect((await api.uploadImages([a]))[0].url).toBe('http://h/u/1.jpg')
    expect((f.mock.calls[0] as unknown as [string])[0]).toBe('/api/v1/uploads/images')
    await expect(api.uploadImages([a, b])).rejects.toMatchObject({ status: 422 })
  })

  it('unwraps the inbox and PATCHes stage with optional note', async () => {
    const f = fakeFetch(200, { leads: [{ id: 'c1' }] })
    const api = createApiClient({ getToken: () => 't', fetchImpl: f })
    expect(await api.listLeads('new')).toEqual([{ id: 'c1' }])
    await api.updateLead('c1', 'contacted', 'called')
    const init = (f.mock.calls[1] as unknown as [string, RequestInit])[1]
    expect(init.method).toBe('PATCH')
    expect(JSON.parse(init.body as string)).toEqual({ stage: 'contacted', note: 'called' })
  })
})

describe('parseErrorBody', () => {
  it('handles FastAPI validation arrays', () => {
    const e = parseErrorBody({ detail: [{ loc: ['body', 'price_inr'], msg: 'must be > 0' }] }, 422)
    expect(e.fields.price_inr).toBe('must be > 0')
    expect(e.detail).toBe('must be > 0')
  })
  it('handles string details and empty bodies', () => {
    expect(parseErrorBody({ detail: 'Incorrect OTP' }, 400).detail).toBe('Incorrect OTP')
    expect(parseErrorBody(null, 500).detail).toContain('500')
  })
  it('unwraps the server envelope {error: {message}} (live guide run showed "Request failed (409)")', () => {
    const e = parseErrorBody({ error: { message: 'Create the marketing pack for this listing first', code: 'HTTP_ERROR', status_code: 409 } }, 409)
    expect(e.detail).toBe('Create the marketing pack for this listing first')
    expect(parseErrorBody({ error: { message: 'Incorrect code', code: 'HTTP_ERROR' } }, 400).detail).toBe('Incorrect code')
    const m = parseErrorBody({ error: { message: { missing: ['price_inr'] }, code: 'HTTP_ERROR' } }, 422)
    expect(m.missing).toEqual(['price_inr'])
    const v = parseErrorBody({ error: { message: 'Validation failed', details: { validation_errors: [{ field: 'body -> price_inr', message: 'must be > 0' }] } } }, 422)
    expect(v.fields.price_inr).toBe('must be > 0')
    expect(v.detail).toBe('must be > 0')
  })
})
