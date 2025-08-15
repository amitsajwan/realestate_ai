import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/ui',
  timeout: 60_000,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: process.env.BASE_URL || 'http://127.0.0.1:8004',
    headless: true,
    trace: 'on-first-retry',
  },
  webServer: {
    command: `C:\\Users\\code\\realestate_ai\\.venv\\Scripts\\python.exe complete_production_crm.py`,
    url: 'http://127.0.0.1:8004',
    timeout: 120_000,
    reuseExistingServer: true,
    cwd: 'C:\\Users\\code\\realestate_ai',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
