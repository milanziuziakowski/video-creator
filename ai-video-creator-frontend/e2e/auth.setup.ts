import { test as setup, expect } from '@playwright/test';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const authFile = path.join(__dirname, '../.auth/user.json');

/**
 * Authentication setup for E2E tests.
 * 
 * Since this app uses JWT token-based authentication,
 * we'll create a mock login flow for testing purposes.
 * 
 * In a real scenario, you would:
 * 1. Call the /auth/login endpoint with test credentials
 * 2. Store the returned JWT token in localStorage
 * 3. Save the authenticated state for reuse in tests
 */

setup('authenticate', async ({ page, request }) => {
  // Check if we should use mock authentication
  const useMockAuth = process.env.E2E_MOCK_AUTH !== 'false';

  if (useMockAuth) {
    console.log('Using mock authentication for E2E tests');
    
    // Navigate to the app
    await page.goto('/');
    
    // Set mock JWT token in localStorage
    await page.evaluate(() => {
      const mockToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItaWQiLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIiwiZXhwIjo5OTk5OTk5OTk5fQ.mock_signature';
      localStorage.setItem('access_token', mockToken);
    });
    
    // Verify we can access protected routes
    await page.goto('/dashboard');
    await expect(page).toHaveURL('/dashboard');
    
  } else {
    console.log('Using real authentication for E2E tests');
    
    // Real authentication flow
    const testEmail = process.env.E2E_TEST_EMAIL;
    const testPassword = process.env.E2E_TEST_PASSWORD;
    
    if (!testEmail || !testPassword) {
      throw new Error(
        'E2E_TEST_EMAIL and E2E_TEST_PASSWORD must be set for real authentication'
      );
    }
    
    // Navigate to login page
    await page.goto('/login');
    
    // Fill in credentials
    await page.fill('[data-testid="email-input"]', testEmail);
    await page.fill('[data-testid="password-input"]', testPassword);
    
    // Submit login form
    await page.click('[data-testid="login-button"]');
    
    // Wait for redirect to dashboard
    await page.waitForURL('/dashboard', { timeout: 10000 });
    
    // Verify we're logged in
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  }
  
  // Save authentication state for reuse
  await fs.mkdir(path.dirname(authFile), { recursive: true });
  await page.context().storageState({ path: authFile });
  
  console.log('Authentication setup complete');
});
