// Runs once when the server starts (Next's instrumentation hook). Node only: the Edge runtime has no ServerResponse.
export async function register() {
  if (process.env.NEXT_RUNTIME !== 'nodejs') return
  const [{ ServerResponse }, { keepOneLocation }] = await Promise.all([import('node:http'), import('./lib/site/singleLocation')])
  keepOneLocation(ServerResponse.prototype)   // a fresh redirect sent two Location headers: Search Console's "Redirect error"
}
