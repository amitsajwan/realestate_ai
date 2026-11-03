# shared

Plain TypeScript used by both Next.js apps: the public site (`../frontend/`) and Studio (`../studio/`). Each imports it as
`@shared/*`; the site also keeps shims at its old `lib/` paths.

Rules, so either app can build it:
- No React, no Next, no npm packages: functions, types and constants only.
- Files import only each other, by relative path (`./types`, `../brand`), never `@/...`, which means a different folder in
  each app.
- A change here is a change to both apps: run jest and the build in `frontend/` and in `studio/`.
