'use client'

/** The root layout itself failed: plain inline styles, since the site's CSS may not be there. */
export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: 'system-ui, sans-serif', background: '#fff', color: '#0f172a' }}>
        <div style={{ background: '#0f2340', color: '#fff', padding: '14px 16px', fontWeight: 700, fontSize: 18 }}>Avasetu</div>
        <div style={{ maxWidth: 640, margin: '0 auto', padding: '48px 16px' }}>
          <h1 style={{ fontSize: 28, margin: 0 }}>This page did not load</h1>
          <p style={{ fontSize: 18, lineHeight: 1.6, color: '#334155' }}>Our server was busy for a moment. Trying again usually works within a few seconds.</p>
          <button type="button" onClick={() => { reset(); window.location.reload() }}
            style={{ minHeight: 48, padding: '0 24px', borderRadius: 12, border: 0, background: '#f0b440', color: '#0f2340', fontWeight: 700, fontSize: 16, cursor: 'pointer' }}>
            Try again
          </button>{' '}
          <a href="/" style={{ display: 'inline-block', marginLeft: 12, color: '#0f2340', fontWeight: 700 }}>Home page</a>
        </div>
      </body>
    </html>
  )
}
