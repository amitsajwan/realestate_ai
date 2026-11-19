/**
 * One Location header per response. Next 16 (checked to 16.4.6) renders a page that calls permanentRedirect() and sets Location
 * on the response, then appends the rendered result's headers again (build/templates/app-page-runtime.js, "cachedData.headers"),
 * so a freshly rendered redirect (a cache MISS) went out with two Location headers, one of them sometimes absolute. Browsers and
 * Googlebot refuse that: Search Console reported "Redirect error" on 2026-11-19 for the merged tower and builder addresses.
 * An appended Location now replaces the one already set. Plain Node, no Next: patched once at server start by ../../instrumentation.
 */
type Res = {
  setHeader(name: string, value: number | string | readonly string[]): unknown
  appendHeader(name: string, value: string | readonly string[]): unknown
}

const PATCHED = Symbol.for('avasetu.singleLocation')

export function keepOneLocation(proto: Res): void {
  const p = proto as Res & { [PATCHED]?: true }
  if (p[PATCHED]) return
  const append = p.appendHeader
  p.appendHeader = function (this: Res, name: string, value: string | readonly string[]) {
    if (typeof name === 'string' && name.toLowerCase() === 'location') {
      const last = Array.isArray(value) ? value[value.length - 1] : value
      if (last === undefined) return this
      this.setHeader(name, last as string)
      return this
    }
    return append.call(this, name, value)
  }
  p[PATCHED] = true
}
