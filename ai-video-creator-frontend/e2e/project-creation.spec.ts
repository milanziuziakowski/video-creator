import { test, expect } from '@playwright/test';
import { setupMinimaxMocks } from './fixtures/minimax-mocks';

/**
 * E2E tests for Project Creation workflow
 * 
 * Tests the complete flow:
 * 1. Creating a new project
 * 2. Uploading first frame image
 * 3. Uploading audio sample
 * 4. Generating story plan with AI
 * 
 * NOTE: All MiniMax API calls are mocked using real captured responses
 */

test.describe('Project Creation', () => {
  test('should create a new project successfully', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/dashboard');
    
    // Click "Create New Project" button
    await page.click('[data-testid="create-project-button"]');
    
    // Verify we're on the new project page
    await expect(page).toHaveURL('/projects/new');
    await expect(page.locator('h1')).toContainText('Create New Project');
    
    // Fill in project details
    await page.fill('[data-testid="project-name"]', 'E2E Test Project');
    await page.fill(
      '[data-testid="story-prompt"]',
      'A peaceful journey through the mountains at sunrise'
    );
    
    // Select target duration
    await page.selectOption('[data-testid="target-duration"]', '30');
    
    // Submit form
    await page.click('[data-testid="create-button"]');
    
    // Wait for redirect to project detail page
    await page.waitForURL(/\/projects\/[\w-]+$/, { timeout: 10000 });
    
    // Verify project was created
    await expect(page.locator('h1')).toContainText('E2E Test Project');
  });

  test('should require project name', async ({ page }) => {
    await page.goto('/projects/new');
    
    // Submit should be disabled until name is provided
    await expect(page.locator('[data-testid="create-button"]')).toBeDisabled();
    
    await page.fill('[data-testid="project-name"]', 'Required Name');
    await expect(page.locator('[data-testid="create-button"]')).toBeEnabled();
  });

  test('should upload first frame image', async ({ page }) => {
    // Create a project first
    await page.goto('/projects/new');
    await page.fill('[data-testid="project-name"]', 'Image Upload Test');
    await page.click('[data-testid="create-button"]');
    await page.waitForURL(/\/projects\/[\w-]+$/);
    
    // Upload first frame image (first file input)
    const fileInput = page.locator('[data-testid="file-input-image"]');
    
    // Upload test image
    await fileInput.setInputFiles('./e2e/fixtures/test-image.jpg');
    
    // Verify image preview is shown
    await expect(page.locator('img[alt="Preview"]')).toBeVisible({
      timeout: 30000,
    });
  });

  test('should upload audio sample', async ({ page }) => {
    // Create a project first
    await page.goto('/projects/new');
    await page.fill('[data-testid="project-name"]', 'Audio Upload Test');
    await page.click('[data-testid="create-button"]');
    await page.waitForURL(/\/projects\/[\w-]+$/);
    
    // Upload audio file
    const audioInput = page.locator('[data-testid="file-input-audio"]');
    await audioInput.setInputFiles('./e2e/fixtures/test-audio.mp3');
    
    // Verify audio player is shown
    await expect(page.locator('audio')).toBeVisible({ timeout: 30000 });
  });

  test('should generate story plan with AI', async ({ page }) => {
    // Setup mocks for voice cloning and plan generation
    const mocks = setupMinimaxMocks(page);
    await mocks.mockVoiceClone();
    await mocks.mockGeneratePlan();

    // Create a project first
    await page.goto('/projects/new');
    await page.fill('[data-testid="project-name"]', 'AI Story Test');
    await page.fill(
      '[data-testid="story-prompt"]',
      'A futuristic city at night'
    );
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

    // Clone voice (mocked - no real API call)
    await page.click('[data-testid="clone-voice-button"]');
    await expect(page.locator('[data-testid="generate-plan-button"]')).toBeEnabled({
      timeout: 60000,
    });

    // Generate plan (mocked - no real API call)
    await page.click('[data-testid="generate-plan-button"]');

    // Verify segments were created (from mocked response)
    await expect(page.locator('[data-testid="segment-card-0"]')).toBeVisible({
      timeout: 60000,
    });
  });
});
