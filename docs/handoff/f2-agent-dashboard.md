# F2 handoff: agent dashboard, qualified leads, follow-up drafts

Contract: `docs/contracts/qualification.md` (frozen). Branch `v2/f2-agent-dashboard`.

## What shipped
- `lib/app/types.ts`, `api.ts`: `getToday()`, `createFollowupDraft(id, language?)`, `updateLead(id, stageOrPatch, note?)`
  (patch form `{stage?, note?, follow_up_at?}`; the old `(id, stage, note)` form still works). Lead list items carry
  `requirement_line`; lead detail carries `requirement`, `ai_summary`, `next_action`, `matches`, `follow_up` (all optional in
  the types so an older backend does not crash the UI).
- `lib/app/leads.ts` pure helpers: `budgetRange`, `requirementChips`, `requirementSourceNote`, `buildWhatsappUrl`,
  `followUpAt` (N days at 10:00 local), `dueLabel`.
- `lib/app/fixtures.ts`: every new method with 5 seeded leads (hot/warm/cold, different requirements), 4 live listings, rule-based
  matches, next_action, summary, follow-up dates and drafts (en, small hi template, mr falls back to en). Storage key bumped to `_v2`.
- `components/app/BusinessToday.tsx` (/studio home), `LeadPanels.tsx`, `LeadDetailView.tsx` (lead detail). All copy in `strings.ts`.
- `/studio/leads` shows `requirement_line`, and accepts `?filter=new|hot|site_visit|followups` (tile links). `followups` is
  resolved client-side from `GET /inbox/today` ids; `hot` is filtered client-side from the list (temperature hot, not won/lost).

## Behaviour notes
- Brand-new agent (no leads at all) sees the onboarding empty state: site card, then Add listing. With leads, the leads
  section comes first and the site card + Add listing sit below.
- "has leads" = `listLeads()` non-empty, or any count/list in `/inbox/today` non-zero.
- The app never sends anything: "Send on WhatsApp" is a plain `wa.me` link built from the (possibly edited) textarea text and the
  lead's phone (not from the server's `whatsapp_url`, so edits are honored). A short line says so.
- Switching language refetches the draft and replaces the text (edits are discarded). If the returned `language` differs from
  the chosen one, a small note says it is in English.
- Follow-up quick buttons send ISO `follow_up_at` = 10:00 local on day+1 / +3 / +7.

## Gaps / assumptions for the backend stream
- Lead list items have no follow-up or `requirement` fields per contract, hence the client-side `followups` filter via `/inbox/today`
  (capped at 10 by the contract; a lead beyond the cap will not appear in that filtered view).
- The `new` tile links to stage=new although the count is "new in last 24h" (contract has no 24h filter on the list).
- `next_action: schedule_visit` is implemented as `PATCH {stage: "site_visit"}` (no visit date/time is captured).

## Verify
`cd frontend && npx tsc --noEmit` (0 errors); `npx jest --testMatch "**/__tests__/app/**/*.test.{ts,tsx}"` (9 suites, 77 tests).
