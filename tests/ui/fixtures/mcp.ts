/*
MCP-style plugin bus for Playwright tests
- Provides hooks (beforeAuth, afterAuth, beforeNavigate, onApiResponse)
- Allows optional modules (facebook, pylance, db) to augment tests without tight coupling
*/
import { APIRequestContext, Page, test as base } from '@playwright/test';

export type MCPContext = {
  page: Page;
  request: APIRequestContext;
  // Optional shared state
  state: Record<string, unknown>;
  // Hooks for plugins
  hooks: {
    beforeAuth?: () => Promise<void> | void;
    afterAuth?: (token?: string) => Promise<void> | void;
    beforeNavigate?: (path: string) => Promise<void> | void;
    onApiResponse?: (url: string, status: number) => Promise<void> | void;
    onConsole?: (type: string, text: string) => Promise<void> | void;
    onPageError?: (message: string) => Promise<void> | void;
  };
};

export const test = base.extend<{ mcp: MCPContext }>({
  mcp: async ({ page, request }, use) => {
    const ctx: MCPContext = {
      page,
      request,
      state: {},
      hooks: {},
    };

    // Wire default network listener to fire onApiResponse
    page.on('response', async (resp) => {
      try {
        const url = resp.url();
        if (url.includes('/api/')) {
          await ctx.hooks.onApiResponse?.(url, resp.status());
          const tel = process.env.MCP_TELEMETRY_URL;
          if (tel) {
            try {
              await request.post(tel, {
                data: { kind: 'api', url, status: resp.status(), ts: Date.now() },
                headers: { 'content-type': 'application/json' },
              });
            } catch {}
          }
        }
      } catch {}
    });

    // Console telemetry
    page.on('console', async (msg) => {
      try {
        const type = msg.type();
        const text = msg.text();
        await ctx.hooks.onConsole?.(type, text);
        const tel = process.env.MCP_TELEMETRY_URL;
        if (tel && (type === 'error' || type === 'warning')) {
          try {
            await request.post(tel, {
              data: { kind: 'console', level: type, text, ts: Date.now() },
              headers: { 'content-type': 'application/json' },
            });
          } catch {}
        }
      } catch {}
    });

    // Page error telemetry
    page.on('pageerror', async (err) => {
      try {
        const message = err?.message || String(err);
        await ctx.hooks.onPageError?.(message);
        const tel = process.env.MCP_TELEMETRY_URL;
        if (tel) {
          try {
            await request.post(tel, {
              data: { kind: 'pageerror', message, ts: Date.now() },
              headers: { 'content-type': 'application/json' },
            });
          } catch {}
        }
      } catch {}
    });

    await use(ctx);
  },
});

export const expect = base.expect;
