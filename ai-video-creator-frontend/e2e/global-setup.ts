import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { chromium, type FullConfig } from '@playwright/test';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const authFile = path.join(__dirname, '../.auth/user.json');

async function globalSetup(config: FullConfig): Promise<void> {
  const baseURL =
    config.projects[0]?.use?.baseURL ||
    process.env.BASE_URL ||
    'http://localhost:5173';

  await fs.mkdir(path.dirname(authFile), { recursive: true });

  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  const useMockAuth = process.env.E2E_MOCK_AUTH !== 'false';

  if (useMockAuth) {
    await page.goto(baseURL, { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => {
      // Use the backend's development token which bypasses JWT validation
      const devToken = 'dev-token';
      localStorage.setItem('access_token', devToken);
    });
  } else {
    const testEmail = process.env.E2E_TEST_EMAIL;
    const testPassword = process.env.E2E_TEST_PASSWORD;

    if (!testEmail || !testPassword) {
      throw new Error(
        'E2E_TEST_EMAIL and E2E_TEST_PASSWORD must be set for real authentication'
      );
    }

    await page.goto(`${baseURL}/login`, { waitUntil: 'domcontentloaded' });
    await page.fill('[data-testid="email-input"]', testEmail);
    await page.fill('[data-testid="password-input"]', testPassword);
    await page.click('[data-testid="login-button"]');
    await page.waitForURL(`${baseURL}/dashboard`, { timeout: 10000 });
  }

  await context.storageState({ path: authFile });
  await browser.close();
}

export default globalSetup;
