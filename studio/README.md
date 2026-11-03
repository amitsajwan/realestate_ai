# Studio

The agents' and the owner's phone app: `/studio/*` and its sign-in `/join` on avasetu.in. Studio is its own Next.js app, apart
from the public site (`../frontend/`), so it builds, tests and ships on its own. How it is laid out and why:
`docs/plan/studio-ux.md`. Where it sits: `docs/ARCHITECTURE.md` §9.

```bash
npm ci --no-audit --no-fund
npx jest --ci --silent        # unit tests (__tests__/)
npm run build                 # also the type check
npx next dev --webpack -p 3001
```

Locally, run the site too (`frontend/`, port 3000) and open http://localhost:3000/studio: the site forwards `/studio`, `/join`
and `/studio-static` here, so both share one address and the login. Demo data with no backend: in the browser console,
`localStorage.app_fixtures = 1`.

How it fits together:
- **Addresses.** Routes stay `/studio/...` and `/join`. Studio's scripts and styles are under `/studio-static` (`assetPrefix`).
  In production Caddy sends those three paths to the `studio` container and everything else to the site
  (`deploy/gcp/Caddyfile`).
- **Links to the public site are plain `<a>` tags**, never `<Link>`: Next's client-side navigation stays inside one app.
- **`@shared/*`** is `../shared/`: the plain TypeScript Studio and the site both use (brand, site types, strings, the login
  token). Change it with both apps' tests.
- **The API** is `/api/v1/...` on the same address (`lib/app/api.ts`).
- **Styles.** `styles/` and `app/globals.css` are the stylesheets the site gave Studio before it moved (2026-11-03); Studio owns
  them now and can trim them.
