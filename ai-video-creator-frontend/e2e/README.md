# Playwright E2E Testing Setup

This directory contains end-to-end tests for the AI Video Creator frontend using Playwright.

## Prerequisites

```bash
# Install dependencies (includes Playwright)
npm install

# Install Playwright browsers
npx playwright install
```

## Running Tests

```bash
# Run all tests in headless mode
npm run test:e2e

# Run tests with UI mode (interactive)
npm run test:e2e:ui

# Run tests in headed mode (see the browser)
npm run test:e2e:headed

# Debug tests
npm run test:e2e:debug

# Show last test report
npm run test:e2e:report
```

## Test Structure

```
e2e/
├── auth.setup.ts                 # Authentication setup (runs before all tests)
├── project-creation.spec.ts      # Project creation workflow tests
├── segment-management.spec.ts    # Segment HITL approval tests
├── complete-workflow.spec.ts     # Full end-to-end workflow tests
└── fixtures/                     # Test files (images, audio)
    ├── test-image.jpg
    └── test-audio.mp3
```

## Configuration

Configuration is in [playwright.config.ts](../playwright.config.ts):

- **Browsers:** Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari
- **Base URL:** `http://localhost:5173` (Vite dev server)
- **Retries:** 2 retries on CI, 0 locally
- **Screenshots:** On failure only
- **Videos:** Retained on failure only

## Authentication

Tests use mock authentication by default:
- Set `E2E_MOCK_AUTH=true` (default) for mock JWT tokens
- Set `E2E_MOCK_AUTH=false` to use real authentication

For real authentication, provide:
```bash
E2E_TEST_EMAIL=your@email.com
E2E_TEST_PASSWORD=yourpassword
```

## Test Fixtures

Test files are stored in `e2e/fixtures/`:

**To add fixtures:**
```bash
cd e2e/fixtures
bash download-fixtures.sh
```

Or manually add:
- `test-image.jpg` - 1280x720 image for first frame tests
- `test-audio.mp3` - 5-10 second audio sample for voice cloning tests

## CI Integration

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

CI workflow runs:
1. Lint & Type check
2. **E2E Tests** (Chromium only on CI)
3. Build
4. Lighthouse audit (PRs only)

Test results and traces are uploaded as artifacts on failure.

## Writing New Tests

Follow these patterns:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test('should do something', async ({ page }) => {
    // Navigate
    await page.goto('/some-page');
    
    // Interact with data-testid attributes
    await page.fill('[data-testid="input-field"]', 'value');
    await page.click('[data-testid="submit-button"]');
    
    // Assert
    await expect(page.locator('[data-testid="result"]')).toBeVisible();
  });
});
```

### Best Practices

1. **Use data-testid** - All interactive elements should have `data-testid` attributes
2. **Wait for elements** - Use `waitForURL`, `waitForSelector`, or `expect().toBeVisible()`
3. **Isolate tests** - Each test should be independent and can run in any order
4. **Mock external APIs** - Don't rely on real MiniMax/OpenAI APIs in tests
5. **Keep tests fast** - Use shorter timeouts, mock slow operations
6. **Test user flows** - Test complete workflows, not just individual actions

## Debugging

```bash
# Run with debug inspector
npm run test:e2e:debug

# Run specific test file
npx playwright test e2e/project-creation.spec.ts

# Run specific test by name
npx playwright test -g "should create a new project"

# Generate test code (Codegen)
npx playwright codegen http://localhost:5173
```

## Troubleshooting

**Tests timing out:**
- Increase timeout in `playwright.config.ts`
- Check if dev server is running (`npm run dev`)
- Verify `BASE_URL` environment variable

**Authentication failing:**
- Check `.auth/user.json` exists after setup
- Verify mock token in `auth.setup.ts`
- Clear browser state: `rm -rf .auth/`

**Flaky tests:**
- Add explicit waits for dynamic content
- Use `waitForLoadState('networkidle')`
- Increase retry count for specific tests

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [API Reference](https://playwright.dev/docs/api/class-test)
- [VS Code Extension](https://marketplace.visualstudio.com/items?itemName=ms-playwright.playwright)
