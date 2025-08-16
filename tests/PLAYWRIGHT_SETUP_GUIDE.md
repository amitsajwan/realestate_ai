# Enhanced Playwright Test Configuration

## Installation and Setup

### 1. Install Playwright Dependencies
```bash
npm install -D @playwright/test
npx playwright install
```

### 2. Enhanced Playwright Config
```typescript
// playwright.config.ts (Enhanced)
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['junit', { outputFile: 'test-results/results.xml' }],
    ['json', { outputFile: 'test-results/results.json' }]
  ],
  
  use: {
    baseURL: 'http://127.0.0.1:8003',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  webServer: {
    command: '.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8003',
    port: 8003,
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
```

## Test Organization Structure

### E2E Test Files
```
tests/e2e/
├── dashboard/
│   ├── navigation.spec.ts
│   ├── widgets.spec.ts
│   ├── forms.spec.ts
│   └── integration.spec.ts
├── facebook/
│   ├── auth-flow.spec.ts
│   ├── posting.spec.ts
│   └── error-handling.spec.ts
├── ai/
│   ├── generation.spec.ts
│   ├── localization.spec.ts
│   └── templates.spec.ts
├── leads/
│   ├── crud-operations.spec.ts
│   ├── search-filter.spec.ts
│   └── status-management.spec.ts
└── utils/
    ├── test-data.ts
    ├── page-objects.ts
    └── fixtures.ts
```

## Page Object Models

### Dashboard Page Object
```typescript
// tests/e2e/utils/page-objects.ts
export class DashboardPage {
  constructor(private page: Page) {}

  async navigateToTab(tab: 'dashboard' | 'leads' | 'properties' | 'ai-tools' | 'settings') {
    await this.page.click(`[data-testid="${tab}-tab"]`);
    await this.page.waitForSelector(`[data-testid="${tab}-content"]`);
  }

  async createLead(leadData: {
    name: string;
    email: string;
    phone?: string;
    interest?: string;
  }) {
    await this.navigateToTab('leads');
    await this.page.click('[data-testid="new-lead-button"]');
    
    await this.page.fill('[data-testid="lead-name"]', leadData.name);
    await this.page.fill('[data-testid="lead-email"]', leadData.email);
    
    if (leadData.phone) {
      await this.page.fill('[data-testid="lead-phone"]', leadData.phone);
    }
    
    await this.page.click('[data-testid="save-lead"]');
    await this.page.waitForSelector('[data-testid="success-message"]');
  }

  async generateAIPost(propertyData: {
    address: string;
    price: string;
    template: string;
  }) {
    await this.navigateToTab('ai-tools');
    
    await this.page.fill('[data-testid="property-address"]', propertyData.address);
    await this.page.fill('[data-testid="property-price"]', propertyData.price);
    await this.page.selectOption('[data-testid="post-template"]', propertyData.template);
    
    await this.page.click('[data-testid="generate-post"]');
    await this.page.waitForSelector('[data-testid="generated-content"]', { timeout: 15000 });
    
    return await this.page.textContent('[data-testid="generated-content"]');
  }
}
```

## Test Data Management
```typescript
// tests/e2e/utils/test-data.ts
export const testLeads = {
  valid: {
    name: 'John Doe',
    email: 'john.doe@example.com',
    phone: '555-0123',
    interest: '3BR/2BA house'
  },
  minimal: {
    name: 'Jane Smith',
    email: 'jane@example.com'
  }
};

export const testProperties = {
  listing: {
    address: '123 Main Street',
    price: '500000',
    bedrooms: '3',
    bathrooms: '2',
    template: 'just_listed'
  },
  openHouse: {
    address: '456 Oak Avenue',
    price: '750000',
    bedrooms: '4',
    bathrooms: '3',
    template: 'open_house'
  }
};
```

## Running Tests

### NPM Scripts
```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:debug": "playwright test --debug",
    "test:e2e:headed": "playwright test --headed",
    "test:dashboard": "playwright test tests/e2e/dashboard",
    "test:facebook": "playwright test tests/e2e/facebook",
    "test:ai": "playwright test tests/e2e/ai",
    "test:leads": "playwright test tests/e2e/leads"
  }
}
```

### Test Execution Commands
```bash
# Run all E2E tests
npm run test:e2e

# Run specific feature tests
npm run test:dashboard
npm run test:facebook
npm run test:ai
npm run test:leads

# Debug mode
npm run test:e2e:debug

# UI mode for development
npm run test:e2e:ui

# Generate test report
npx playwright show-report
```

## CI/CD Integration
- GitHub Actions workflow for automated testing
- Test result reporting
- Screenshot/video artifacts on failure
- Cross-browser testing matrix
