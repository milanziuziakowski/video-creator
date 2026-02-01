import { test, expect } from '@playwright/test';
import { setupMinimaxMocks } from './fixtures/minimax-mocks';

/**
 * E2E tests for Complete Video Generation workflow
 * 
 * Tests the end-to-end flow that exists in the current UI:
 * 1. Creating project
 * 2. Uploading media
 * 3. Cloning voice
 * 4. Generating plan
 * 5. Verifying segments appear
 * 
 * NOTE: All MiniMax API calls are mocked using real captured responses
 */

test.describe('Complete Video Generation Workflow', () => {
  test('should complete the core workflow', async ({ page }) => {
    // Setup all mocks before starting
    const mocks = setupMinimaxMocks(page);
    await mocks.mockAll();

    // Step 1: Create project
    await page.goto('/dashboard');
    await page.click('[data-testid="create-project-button"]');

    await page.fill('[data-testid="project-name"]', 'Full Workflow Test');
    await page.fill(
      '[data-testid="story-prompt"]',
      'A time-lapse of a blooming flower'
    );
    await page.selectOption('[data-testid="target-duration"]', '30');
    await page.click('[data-testid="create-button"]');

    await page.waitForURL(/\/projects\/[\w-]+$/);

    // Step 2: Upload first frame
    await page.locator('[data-testid="file-input-image"]').setInputFiles(
      './e2e/fixtures/test-image.jpg'
    );
    await expect(page.locator('img[alt="Preview"]')).toBeVisible({
      timeout: 30000,
    });

    // Step 3: Upload audio sample
    await page.locator('[data-testid="file-input-audio"]').setInputFiles(
      './e2e/fixtures/test-audio.mp3'
    );
    await expect(page.locator('audio')).toBeVisible({ timeout: 30000 });

    // Step 4: Clone voice (using mocked response)
    await page.click('[data-testid="clone-voice-button"]');
    await expect(page.locator('[data-testid="generate-plan-button"]')).toBeEnabled({
      timeout: 60000,
    });

    // Step 5: Generate plan (using mocked response)
    await page.click('[data-testid="generate-plan-button"]');
    await expect(page.locator('[data-testid="segment-card-0"]')).toBeVisible({
      timeout: 60000,
    });
    
    // Verify we got the expected number of segments (5 segments for 30 seconds)
    const segmentCards = page.locator('[data-testid^="segment-card-"]');
    await expect(segmentCards).toHaveCount(5);
  });

  test('should save progress and resume later', async ({ page }) => {
    // Create a project
    await page.goto('/projects/new');
    await page.fill('[data-testid="project-name"]', 'Resume Test');
    await page.fill('[data-testid="story-prompt"]', 'A short story');
    await page.click('[data-testid="create-button"]');

    const url = page.url();
    const projectId = url.split('/').pop();

    // Navigate away
    await page.goto('/projects');

    // Come back to the project
    await page.goto(`/projects/${projectId}`);

    // Verify project header is visible
    await expect(page.locator('h1')).toBeVisible();
  });
});
