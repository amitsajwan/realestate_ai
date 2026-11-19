import { ServerResponse, IncomingMessage } from 'node:http'
import { Socket } from 'node:net'
import { keepOneLocation } from '@/lib/site/singleLocation'

// Search Console "Redirect error", 2026-11-19: a freshly rendered redirect carried Location twice (Next set it, then appended the
// rendered result's headers again)
function response(): ServerResponse {
  return new ServerResponse(new IncomingMessage(new Socket()))
}

describe('one Location header per response', () => {
  beforeAll(() => keepOneLocation(ServerResponse.prototype))

  it('a redirect whose Location is set and then appended goes out with one Location', () => {
    const res = response()
    res.setHeader('location', 'https://avasetu.in/projects/lodha-camelot')
    res.appendHeader('Location', '/projects/lodha-camelot')
    expect(res.getHeader('location')).toBe('/projects/lodha-camelot')
  })

  it('other headers still append', () => {
    const res = response()
    res.appendHeader('set-cookie', 'a=1')
    res.appendHeader('set-cookie', 'b=2')
    expect(res.getHeader('set-cookie')).toEqual(['a=1', 'b=2'])
  })

  it('patching twice is harmless', () => {
    keepOneLocation(ServerResponse.prototype)
    const res = response()
    res.appendHeader('location', '/a')
    res.appendHeader('location', ['/b'])
    expect(res.getHeader('location')).toBe('/b')
  })
})
