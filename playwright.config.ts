import { defineConfig, devices } from '@playwright/test';

// Allow env-driven baseURL and optional webServer (so we can target a real running app)
const baseURL = process.env.BASE_URL || 'http://127.0.0.1:8004';
const disableWebServer = process.env.PW_NO_SERVER === '1';

// Default local server command (kept for compatibility). Can be overridden by setting PW_NO_SERVER=1
const defaultWebServer = {
  command: `C:\\Users\\code\\realestate_ai\\.venv\\Scripts\\python.exe complete_production_crm.py`,
  url: 'http://127.0.0.1:8004',
  timeout: 120_000,
  reuseExistingServer: true,
  cwd: 'C:\\Users\\code\\realestate_ai',
} as const;

export default defineConfig({
  testDir: './tests/ui',
  timeout: 60_000,
  retries: 0,
  reporter: [
    ['list'],
    [require.resolve('./tests/ui/reporters/telemetry-reporter')],
  ],
  use: {
    baseURL,
    headless: true,
    trace: 'on-first-retry',
    // Inject Authorization header automatically when AUTH_TOKEN is provided
    extraHTTPHeaders: process.env.AUTH_TOKEN
      ? { Authorization: `Bearer ${process.env.AUTH_TOKEN}` }
      : undefined,
  },
  // If PW_NO_SERVER=1, Playwright won't try to start any server (assumes real app is already running)
  webServer: disableWebServer ? undefined : defaultWebServer,
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
