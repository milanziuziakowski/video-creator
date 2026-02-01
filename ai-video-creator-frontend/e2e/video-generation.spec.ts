import { test, expect, Page } from '@playwright/test';
import { setupMinimaxMocks, MINIMAX_MOCK_RESPONSES, BACKEND_MOCK_RESPONSES } from './fixtures/minimax-mocks';

/**
 * E2E tests for Video Generation and Playback
 * 
 * Tests the complete flow:
 * 1. Viewing uploaded images (first frame)
 * 2. Seeing generation status updates
 * 3. Playing generated videos in segments
 * 4. Playing final video
 * 
 * NOTE: All MiniMax API calls are mocked using REAL captured responses
 */

test.describe('Video Generation and Playback', () => {
  let mocks: ReturnType<typeof setupMinimaxMocks>;

  test.beforeEach(async ({ page }) => {
    mocks = setupMinimaxMocks(page);
  });

  test('should display uploaded first frame image', async ({ page }) => {
    await mocks.mockAll();

    // Create project and upload image
    await page.goto('/projects/new');
    await page.fill('[data-testid="project-name"]', 'Image Preview Test');
    await page.fill('[data-testid="story-prompt"]', 'Test story');
    await page.click('[data-testid="create-button"]');
    await page.waitForURL(/\/projects\/[\w-]+$/);

    // Upload first frame image
    await page.locator('[data-testid="file-input-image"]').setInputFiles(
      './e2e/fixtures/first-frame.jpg'
    );

    // Verify image preview is displayed
    const imagePreview = page.locator('img[alt="Preview"]');
    await expect(imagePreview).toBeVisible({ timeout: 30000 });
    
    // Verify image has a valid src attribute
    const imgSrc = await imagePreview.getAttribute('src');
    expect(imgSrc).toBeTruthy();
    expect(imgSrc!.length).toBeGreaterThan(0);
  });





  test('should display final video after project finalization', async ({ page }) => {
    // Setup mocks
    await mocks.mockVoiceClone();
    await mocks.mockGeneratePlan();
    await mocks.mockUpdateSegment();
    await mocks.mockApproveSegment();

    // Mock segments - all approved
    await page.route('**/api/v1/segments/project/*', async (route) => {
      const allApprovedSegments = BACKEND_MOCK_RESPONSES.generatePlan.segments.map((seg, idx) => ({
        id: `seg-${idx + 1}`,
        projectId: 'project-123',
        index: idx,
        videoPrompt: seg.videoPrompt,
        narrationText: seg.narrationText,
        endFramePrompt: seg.endFramePrompt,
        durationSec: 6,
        status: 'segment_approved',
        approved: true,
        firstFrameUrl: null,
        lastFrameUrl: null,
        videoUrl: MINIMAX_MOCK_RESPONSES.chainedVideoGeneration[`segment${idx + 1}` as keyof typeof MINIMAX_MOCK_RESPONSES.chainedVideoGeneration]?.download_url || null,
        audioUrl: `https://storage.example.com/audio/segment-${idx + 1}.mp3`,
        videoTaskId: MINIMAX_MOCK_RESPONSES.chainedVideoGeneration[`segment${idx + 1}` as keyof typeof MINIMAX_MOCK_RESPONSES.chainedVideoGeneration]?.task_id || null,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }));

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(allApprovedSegments),
      });
    });

    // Mock project with final video URL
    await page.route('**/api/v1/projects/*', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'project-123',
            name: 'Final Video Test',
            storyPrompt: 'A mountain adventure',
            status: 'completed',
            firstFrameUrl: '/uploads/first-frame.jpg',
            audioSampleUrl: '/uploads/audio.mp3',
            voiceId: 'test-voice-20260201133125',
            finalVideoUrl: 'https://video-product.cdn.minimax.io/final/project-123.mp4',
            segmentCount: 3,
            targetDurationSec: 18,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Navigate directly to project detail
    await page.goto('/projects/project-123');

    // Wait for final video to be visible
    const finalVideo = page.locator('[data-testid="final-video"]');
    await expect(finalVideo).toBeVisible({ timeout: 30000 });

    // Verify video has the correct source
    const videoSrc = await finalVideo.getAttribute('src');
    expect(videoSrc).toBe('https://video-product.cdn.minimax.io/final/project-123.mp4');

    // Verify download button is visible
    await expect(page.locator('[data-testid="download-button"]')).toBeVisible();
  });




});
