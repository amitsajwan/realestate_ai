# PropertyAI E2E Tests

This directory contains comprehensive end-to-end tests for the PropertyAI platform using Playwright.

## Test Coverage

### 1. Authentication System (`01-auth.spec.ts`)
- Login form validation
- Registration process
- Password strength indicators
- Social login integration
- Form validation and error handling
- Mobile responsiveness

### 2. Onboarding Process (`02-onboarding.spec.ts`)
- 6-step onboarding flow
- AI branding generation
- Form validation and progress tracking
- Data persistence between steps
- Error handling and recovery
- Mobile responsiveness

### 3. Property Management (`03-property-management.spec.ts`)
- Smart property form
- AI suggestions integration
- Image upload and management
- Property creation and editing
- Property listing and filtering
- Analytics and performance tracking
- Mobile responsiveness

### 4. Post Management (`04-post-management.spec.ts`)
- Post creation and editing
- AI content generation
- Multi-channel preview
- Post scheduling and publishing
- Post analytics and performance
- Error handling and recovery
- Mobile responsiveness

### 5. Agent Website (`05-agent-website.spec.ts`)
- Public profile display
- Property showcase
- Contact information
- Social proof and testimonials
- Performance metrics
- Error handling
- Mobile responsiveness

### 6. Analytics Dashboard (`06-analytics-dashboard.spec.ts`)
- Key metrics display
- Performance charts
- Property performance tracking
- Lead conversion metrics
- Social media analytics
- Data export functionality
- Error handling and retry
- Mobile responsiveness

### 7. CRM System (`07-crm-system.spec.ts`)
- Lead management
- Lead creation and editing
- Activity tracking
- Lead status updates
- Lead assignment
- Lead analytics and reporting
- Error handling
- Mobile responsiveness

### 8. Team Management (`08-team-management.spec.ts`)
- Team member management
- Invitation system
- Role and permission management
- Team analytics
- Member performance tracking
- Error handling
- Mobile responsiveness

### 9. AI Content Generation (`09-ai-content-generation.spec.ts`)
- AI content generation
- Content editing and customization
- Content templates
- Content quality scoring
- Content history and management
- Error handling and retry
- Mobile responsiveness

### 10. Multi-Channel Publishing (`10-multi-channel-publishing.spec.ts`)
- Channel configuration
- Multi-channel publishing
- Post preview and scheduling
- Publishing analytics
- Error handling and retry
- Mobile responsiveness

### 11. Integration Tests (`00-integration.spec.ts`)
- Full user journey tests
- Cross-component data flow
- Error recovery scenarios
- State management
- Concurrent user actions

## Running Tests

### Prerequisites
- Node.js 18+
- Playwright browsers installed
- Backend and frontend servers running

### Installation
```bash
cd e2e
npm install
npx playwright install
```

### Running Tests

#### Run all tests
```bash
npm test
```

#### Run tests in headed mode (visible browser)
```bash
npm run test:headed
```

#### Run tests with UI mode
```bash
npm run test:ui
```

#### Run specific test file
```bash
npx playwright test 01-auth.spec.ts
```

#### Run tests in debug mode
```bash
npm run test:debug
```

#### Generate test report
```bash
npm run test:report
```

### Test Configuration

The tests are configured in `playwright.config.ts` with:
- Multiple browser support (Chrome, Firefox, Safari)
- Mobile viewport testing
- Automatic server startup
- Screenshot and video capture on failure
- Parallel test execution
- Retry logic for flaky tests

### Test Data

Tests use mocked API responses to ensure:
- Consistent test results
- Fast execution
- No dependency on external services
- Easy maintenance

### Best Practices

1. **Test Isolation**: Each test is independent and can run in any order
2. **Page Object Pattern**: Reusable page objects for common interactions
3. **Data-Driven Tests**: Parameterized tests for different scenarios
4. **Error Scenarios**: Comprehensive error handling tests
5. **Mobile Testing**: Responsive design validation
6. **Performance**: Tests include performance considerations
7. **Accessibility**: Basic accessibility testing included

### Continuous Integration

Tests are designed to run in CI/CD pipelines with:
- Headless browser execution
- Parallel test execution
- Test result reporting
- Screenshot and video artifacts on failure
- Retry logic for flaky tests

### Maintenance

- Update tests when UI changes
- Add new tests for new features
- Remove obsolete tests
- Keep test data up to date
- Monitor test performance and flakiness

## Test Results

Test results are generated in:
- HTML report: `playwright-report/index.html`
- JSON results: `e2e-results.json`
- JUnit results: `e2e-results.xml`

## Troubleshooting

### Common Issues

1. **Tests failing due to server not running**
   - Ensure backend and frontend servers are started
   - Check server URLs in configuration

2. **Flaky tests**
   - Increase timeouts for slow operations
   - Add proper wait conditions
   - Use retry logic for network operations

3. **Mobile tests failing**
   - Check viewport size settings
   - Verify mobile-specific selectors
   - Test on actual mobile devices

4. **API mocking issues**
   - Verify mock routes are correct
   - Check response format matches expected structure
   - Ensure mocks are set up before test execution

### Debug Mode

Use debug mode to step through tests:
```bash
npx playwright test --debug
```

This opens the Playwright Inspector where you can:
- Step through test execution
- Inspect elements
- View network requests
- Take screenshots
- Modify test code on the fly