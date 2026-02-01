import { test, expect } from '@playwright/test';
import { setupMinimaxMocks } from './fixtures/minimax-mocks';

/**
 * E2E tests for Segment Management workflow
 * 
 * Tests the Human-in-the-Loop (HITL) segment approval flow:
 * 1. Reviewing AI-generated segments
 * 2. Editing segment prompts and narration
 * 3. Approving a segment
 * 
 * NOTE: All MiniMax API calls are mocked using real captured responses
 */

test.describe('Segment Management', () => {
  test.beforeEach(async ({ page }) => {
    // Setup all mocks before starting
    const mocks = setupMinimaxMocks(page);
    await mocks.mockAll();

    // Create a project
    await page.goto('/projects/new');
    await page.fill('[data-testid="project-name"]', 'Segment Test Project');
    await page.fill('[data-testid="story-prompt"]', 'A mountain adventure');
    await page.click('[data-testid="create-button"]');
    await page.waitForURL(/\/projects\/[\w-]+$/);

    // Upload first frame and audio
    await page.locator('[data-testid="file-input-image"]').setInputFiles(
      './e2e/fixtures/test-image.jpg'
    );
    await expect(page.locator('img[alt="Preview"]')).toBeVisible({
      timeout: 30000,
    });

    await page.locator('[data-testid="file-input-audio"]').setInputFiles(
      './e2e/fixtures/test-audio.mp3'
    );
    await expect(page.locator('audio')).toBeVisible({ timeout: 30000 });

    // Clone voice and generate plan (use force for mobile compatibility)
    await page.click('[data-testid="clone-voice-button"]', { force: true });
    await expect(page.locator('[data-testid="generate-plan-button"]')).toBeEnabled({
      timeout: 60000,
    });
    await page.click('[data-testid="generate-plan-button"]', { force: true });

    // Wait for segments to appear
    await expect(page.locator('[data-testid="segment-card-0"]')).toBeVisible({
      timeout: 60000,
    });
  });

  test('should display generated segments', async ({ page }) => {
    const segments = page.locator('[data-testid^="segment-card-"]');
    const count = await segments.count();

    expect(count).toBeGreaterThan(0);
    expect(count).toBeLessThanOrEqual(10);

    const firstSegment = segments.first();
    await expect(firstSegment.getByText('Video Prompt')).toBeVisible();
    await expect(firstSegment.getByText('Narration')).toBeVisible();
  });

  test('should edit segment prompt and narration', async ({ page }) => {
    const firstSegment = page.locator('[data-testid="segment-card-0"]');

    await firstSegment.locator('[data-testid="edit-button"]').click();

    const promptInput = firstSegment.locator('textarea').nth(0);
    const narrationInput = firstSegment.locator('textarea').nth(1);

    await promptInput.fill('Edited prompt: A climber reaches the summit');
    await narrationInput.fill('Edited narration for the segment.');

    await firstSegment.getByRole('button', { name: 'Save' }).click();

    await expect(firstSegment).toContainText('Edited prompt: A climber reaches the summit');
    await expect(firstSegment).toContainText('Edited narration for the segment.');
  });

  test('should approve a segment', async ({ page }) => {
    const firstSegment = page.locator('[data-testid="segment-card-0"]');

    await firstSegment.locator('[data-testid="approve-button"]').click();

    // After approval, the Generate button should appear
    await expect(firstSegment.locator('[data-testid="generate-button"]')).toBeVisible({
      timeout: 30000,
    });
  });
});
