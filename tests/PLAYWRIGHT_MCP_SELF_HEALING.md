# Playwright + MCP: AI-assisted, self-healing UI tests

This repo uses a lightweight MCP-style fixture (`tests/ui/fixtures/mcp.ts`) and a small self-healing utility (`tests/ui/utils/self_heal.ts`) to let AI agents adapt tests when selectors change.

## What you get
- MCP-style hooks for before/after auth, beforeNavigate, and onApiResponse
- AI-friendly selector utilities that:
  - Try multiple candidate selectors in order
  - Fall back to nearby elements when not found
  - Emit suggestions to `test_reports/self_heal_suggestions.json` for automated repair PRs

## How to use in a test
```ts
import { test, expect } from './fixtures/mcp';
import { clickSmart, fillSmart, ensureVisible } from './utils/self_heal';

test('example self-heal flow', async ({ page }) => {
  await page.goto('/dashboard');

  // Click Smart Properties nav with multiple candidates
  const clicked = await clickSmart(page, [
    { description: 'emoji nav', text: '🤖 Smart Properties' },
    { description: 'emoji only', text: '🤖' },
    { description: 'role link', role: 'link', name: /smart properties/i },
    { description: 'css backup', css: 'a.nav-item[href="#smart-properties"]' },
  ], 'open-smart-properties');
  expect(clicked).toBeTruthy();

  // Ensure modal is visible using candidates
  const modal = await ensureVisible(page, [
    { description: 'smart modal by id', css: '#smartPropertyModal' },
    { description: 'any modal', css: '.modal[style*="display: flex"]' },
  ], 'smart-modal');
  expect(modal).not.toBeNull();
});
```

## How MCP fits in
- Agents (via MCP) can parse `self_heal_suggestions.json` and open a PR that updates flaky selectors.
- Hooks in `mcp.ts` can be extended to report failures back to your agent for auto-triage.

## Tips
- Keep candidates ordered by confidence (best selector first).
- Prefer role-based and text selectors before brittle CSS.
- Use the suggestions file to evolve selectors safely.
