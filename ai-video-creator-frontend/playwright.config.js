var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
import { defineConfig, devices } from '@playwright/test';
/**
 * Playwright Configuration for AI Video Creator E2E Tests
 *
 * See https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
    testDir: './e2e',
    globalSetup: './e2e/global-setup.ts',
    // Run tests in files in parallel
    fullyParallel: true,
    // Fail the build on CI if you accidentally left test.only in the source code
    forbidOnly: !!process.env.CI,
    // Retry on CI only
    retries: process.env.CI ? 2 : 0,
    // Opt out of parallel tests on CI
    workers: process.env.CI ? 1 : undefined,
    // Reporter configuration
    reporter: [
        ['html', { open: 'never' }],
        ['json', { outputFile: 'test-results/results.json' }],
        process.env.CI ? ['github'] : ['list'],
    ],
    // Shared settings for all tests
    use: {
        // Base URL for navigation
        baseURL: process.env.BASE_URL || 'http://localhost:5173',
        // Use authenticated state created in global setup
        storageState: '.auth/user.json',
        // Collect trace on first retry
        trace: 'on-first-retry',
        // Screenshot on failure
        screenshot: 'only-on-failure',
        // Video on failure
        video: 'retain-on-failure',
        // Timeout for each action (e.g., click, fill)
        actionTimeout: 10000,
    },
    // Test projects for different browsers
    projects: [
        // Desktop Chrome
        {
            name: 'chromium',
            use: __assign({}, devices['Desktop Chrome']),
        },
        // Desktop Firefox
        {
            name: 'firefox',
            use: __assign({}, devices['Desktop Firefox']),
        },
        // Desktop Safari
        {
            name: 'webkit',
            use: __assign({}, devices['Desktop Safari']),
        },
        // Mobile Chrome
        {
            name: 'mobile-chrome',
            use: __assign({}, devices['Pixel 5']),
        },
        // Mobile Safari
        {
            name: 'mobile-safari',
            use: __assign({}, devices['iPhone 13']),
        },
    ],
    // Web server configuration - starts dev server for tests
    webServer: {
        command: 'npm run dev',
        url: 'http://localhost:5173',
        reuseExistingServer: !process.env.CI,
        timeout: 120000,
    },
});
