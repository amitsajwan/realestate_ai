// jsdom has no Response: a minimal stand-in is enough to read the status and Location
(global as any).Response = class { status: number; headers: Headers; constructor(_b: unknown, init: any) { this.status = init.status; this.headers = new Headers(init.headers) } }

// eslint-disable-next-line @typescript-eslint/no-var-requires
const { POST } = require('@/app/i/[code]/tap/route')

describe('/i/[code]/tap (no-JS post)', () => {
  const post = (fields: Record<string, string>) => {
    const fd = new FormData()
    Object.entries(fields).forEach(([k, v]) => fd.append(k, v))
    return POST({ formData: async () => fd, headers: new Headers() } as any, { params: Promise.resolve({ code: 'abc2345' }) })
  }
  it('calls the API and redirects back with only a status flag in the URL', async () => {
    ;(global as any).fetch = jest.fn().mockResolvedValue({ ok: true, status: 200 })
    const res = await post({ step: 'details', name: 'Asha', phone: '9876543210', consent: 'on' })
    expect(res.status).toBe(303)
    expect(res.headers.get('Location')).toBe('/i/abc2345?done=2')
    expect(JSON.parse((global.fetch as jest.Mock).mock.calls[0][1].body)).toMatchObject({ phone: '9876543210', consent: true })
    expect((await post({})).headers.get('Location')).toBe('/i/abc2345?done=1')
  })
  it('turns an API consent error into a message flag, never echoing personal data', async () => {
    ;(global as any).fetch = jest.fn().mockResolvedValue({ ok: false, status: 400 })
    const loc = (await post({ step: 'details', phone: '9876543210' })).headers.get('Location')!
    expect(loc).toBe('/i/abc2345?done=1&e=consent')
    expect(loc).not.toContain('9876543210')
  })
})

