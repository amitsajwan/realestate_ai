/** When a server-side fetch fails, tell Next.js not to keep this render, so an error page is never cached and the next visit retries. */
export async function dontCacheThisRender(): Promise<void> {
  try {
    const { unstable_noStore } = await import('next/cache')
    unstable_noStore()
  } catch {
    // outside a Next.js render (tests): nothing to do
  }
}
