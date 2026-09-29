# F1 handoff: qualification enquiry form

- `frontend/lib/site/qualification.ts`: pure option lists, budget -> min/max mapping, `toggleChoice`, `buildQualificationFields` (omits unset fields; `2Cr+` gives `budget_max_inr: null`; 4+ BHK sends 4).
- `frontend/lib/site/strings.ts`: all copy for the optional block.
- `EnquiryForm.tsx`: optional fieldset "Help {first name} find the right property (optional)" with chip groups (44px targets, `aria-pressed`, tap again to clear). Untouched block sends the exact old payload.
- `InquiryInput` in `tracking.ts` gained optional `bhk, budget_min_inr, budget_max_inr, timeline, financing`.
- BHK is asked only when no `listingId` prop (agent home page). Listing pages skip it; backend fills bhk from the listing.
- Success state adds a one-line note when any optional data was sent.
- Tests: `__tests__/site/qualification.test.ts`, extended `components.test.tsx`.
- Fixture mode: form has no fixture data of its own; nothing changed.
