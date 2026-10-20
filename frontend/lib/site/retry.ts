/**
 * Retries for the server-side API reads (./api, ./register, ./facets).
 *
 * `down`: the API is not there at all (connection refused, its name not resolving yet, 502/503): a deploy restarting it, ~10-60 s.
 * Those answer at once, so waiting for it costs nothing: try every second for up to ~10 s, and a page rendered just after a deploy
 * is slow instead of an error. Anything else (a timeout, a 500) gets one retry half a second later: retrying a timeout again and
 * again would only add load to an API that is already busy. A 404 is final.
 */
export type Got<T> = { ok: true; data: T } | { ok: false; notFound: boolean; down?: boolean }

const DOWN_TRIES = 10
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

export async function withRetry<T>(once: () => Promise<Got<T>>): Promise<Got<T>> {
  let r = await once()
  for (let i = 0; i < DOWN_TRIES && !r.ok && r.down; i++) {
    await sleep(1000)
    r = await once()
  }
  if (r.ok || r.notFound || r.down) return r
  await sleep(500)
  return once()
}

/** The failure of one fetch: `down` unless it was our own timeout (an abort). */
export function failed(e: unknown): { ok: false; notFound: false; down: boolean } {
  return { ok: false, notFound: false, down: !(e instanceof Error && e.name === 'AbortError') }
}

/** A non-OK answer that is not a 404: 502/503 mean the API is not up yet. */
export function badStatus(status: number): { ok: false; notFound: false; down: boolean } {
  return { ok: false, notFound: false, down: status === 502 || status === 503 }
}
