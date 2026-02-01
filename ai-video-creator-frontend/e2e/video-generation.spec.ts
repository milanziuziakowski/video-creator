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

  test('should show generation status during video creation', async ({ page }) => {
    // Setup mocks with delayed status transitions
    await mocks.mockVoiceClone();
    await mocks.mockGeneratePlan();
    await mocks.mockUpdateSegment();
    await mocks.mockApproveSegment();

    // Track segment status - starts as prompt_ready, changes to generating after generate click
    let segmentStatus = 'prompt_ready';
    let segmentApproved = false;

    // Mock segments endpoint - returns current status
    await page.route('**/api/v1/segments/project/*', async (route) => {
      const segments = BACKEND_MOCK_RESPONSES.generatePlan.segments.map((seg, idx) => ({
        id: `seg-${idx + 1}`,
        projectId: 'project-123',
        index: idx,
        videoPrompt: seg.videoPrompt,
        narrationText: seg.narrationText,
        endFramePrompt: seg.endFramePrompt,
        durationSec: 6,
        status: idx === 0 ? segmentStatus : 'prompt_ready',
        approved: idx === 0 ? segmentApproved : false,
        videoUrl: null,
        audioUrl: null,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }));

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(segments),
      });
    });

    // Mock approve segment - updates status
    await page.route('**/api/v1/segments/*/approve', async (route) => {
      segmentStatus = 'approved';
      segmentApproved = true;
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'seg-1',
          status: 'approved',
          approved: true,
        }),
      });
    });

    // Mock generate segment - changes status to generating_video
    await page.route('**/api/v1/generation/segment/*', async (route) => {
      segmentStatus = 'generating_video';
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          segmentId: 'seg-1',
          status: 'generating',
          videoTaskId: MINIMAX_MOCK_RESPONSES.chainedVideoGeneration.segment1.task_id,
          message: 'Segment generation started',
        }),
      });
    });

    // Create project and setup
    await page.goto('/projects/new');
    await page.fill('[data-testid="project-name"]', 'Status Test Project');
    await page.fill('[data-testid="story-prompt"]', 'A mountain adventure');
    await page.click('[data-testid="create-button"]');
    await page.waitForURL(/\/projects\/[\w-]+$/);

    // Upload media
    await page.locator('[data-testid="file-input-image"]').setInputFiles(
      './e2e/fixtures/first-frame.jpg'
    );
    await expect(page.locator('img[alt="Preview"]')).toBeVisible({ timeout: 30000 });

    await page.locator('[data-testid="file-input-audio"]').setInputFiles(
      './e2e/fixtures/test-audio.mp3'
    );
    await expect(page.locator('audio')).toBeVisible({ timeout: 30000 });

    // Clone voice and generate plan
    await page.click('[data-testid="clone-voice-button"]');
    await expect(page.locator('[data-testid="generate-plan-button"]')).toBeEnabled({
      timeout: 60000,
    });
    await page.click('[data-testid="generate-plan-button"]');

    // Wait for segments
    await expect(page.locator('[data-testid="segment-card-0"]')).toBeVisible({
      timeout: 60000,
    });

    // Approve first segment
    const firstSegment = page.locator('[data-testid="segment-card-0"]');
    await firstSegment.locator('[data-testid="approve-button"]').click();

    // Wait for generate button to appear after approval
    await expect(firstSegment.locator('[data-testid="generate-button"]')).toBeVisible({
      timeout: 30000,
    });

    // Start generation
    await firstSegment.locator('[data-testid="generate-button"]').click();

    // Verify "Generating..." spinner text is shown (specific to generating state)
    await expect(firstSegment.getByText('Generating...')).toBeVisible({
      timeout: 10000,
    });

    // Also verify the status badge shows "Generating Video"
    await expect(firstSegment.getByText('Generating Video')).toBeVisible();
  });

  test('should display video player when segment is generated', async ({ page }) => {
    // Setup mocks with completed segment
    await mocks.mockVoiceClone();
    await mocks.mockGeneratePlan();
    await mocks.mockUpdateSegment();
    await mocks.mockApproveSegment();

    // Mock segments with one already generated (has videoUrl)
    await page.route('**/api/v1/segments/project/*', async (route) => {
      const segmentsWithVideo = [
        {
          id: 'seg-1',
          projectId: 'project-123',
          index: 0,
          videoPrompt: BACKEND_MOCK_RESPONSES.generatePlan.segments[0].videoPrompt,
          narrationText: BACKEND_MOCK_RESPONSES.generatePlan.segments[0].narrationText,
          endFramePrompt: BACKEND_MOCK_RESPONSES.generatePlan.segments[0].endFramePrompt,
          durationSec: 6,
          status: 'generated',
          approved: true,
          firstFrameUrl: null,
          lastFrameUrl: null,
          videoUrl: MINIMAX_MOCK_RESPONSES.chainedVideoGeneration.segment1.download_url,
          audioUrl: 'https://storage.example.com/audio/segment-1.mp3',
          videoTaskId: MINIMAX_MOCK_RESPONSES.chainedVideoGeneration.segment1.task_id,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
        {
          id: 'seg-2',
          projectId: 'project-123',
          index: 1,
          videoPrompt: BACKEND_MOCK_RESPONSES.generatePlan.segments[1].videoPrompt,
          narrationText: BACKEND_MOCK_RESPONSES.generatePlan.segments[1].narrationText,
          endFramePrompt: BACKEND_MOCK_RESPONSES.generatePlan.segments[1].endFramePrompt,
          durationSec: 6,
          status: 'prompt_ready',
          approved: false,
          firstFrameUrl: null,
          lastFrameUrl: null,
          videoUrl: null,
          audioUrl: null,
          videoTaskId: null,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
        {
          id: 'seg-3',
          projectId: 'project-123',
          index: 2,
          videoPrompt: BACKEND_MOCK_RESPONSES.generatePlan.segments[2].videoPrompt,
          narrationText: BACKEND_MOCK_RESPONSES.generatePlan.segments[2].narrationText,
          endFramePrompt: BACKEND_MOCK_RESPONSES.generatePlan.segments[2].endFramePrompt,
          durationSec: 6,
          status: 'prompt_ready',
          approved: false,
          firstFrameUrl: null,
          lastFrameUrl: null,
          videoUrl: null,
          audioUrl: null,
          videoTaskId: null,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
      ];

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(segmentsWithVideo),
      });
    });

    // Create project and generate plan
    await page.goto('/projects/new');
    await page.fill('[data-testid="project-name"]', 'Video Playback Test');
    await page.fill('[data-testid="story-prompt"]', 'A mountain adventure');
    await page.click('[data-testid="create-button"]');
    await page.waitForURL(/\/projects\/[\w-]+$/);

    // Upload media
    await page.locator('[data-testid="file-input-image"]').setInputFiles(
      './e2e/fixtures/first-frame.jpg'
    );
    await expect(page.locator('img[alt="Preview"]')).toBeVisible({ timeout: 30000 });

    await page.locator('[data-testid="file-input-audio"]').setInputFiles(
      './e2e/fixtures/test-audio.mp3'
    );

    // Clone voice and generate plan
    await page.click('[data-testid="clone-voice-button"]');
    await expect(page.locator('[data-testid="generate-plan-button"]')).toBeEnabled({
      timeout: 60000,
    });
    await page.click('[data-testid="generate-plan-button"]');

    // Wait for segments
    await expect(page.locator('[data-testid="segment-card-0"]')).toBeVisible({
      timeout: 60000,
    });

    // Verify video player is visible in first segment (which has videoUrl)
    const firstSegment = page.locator('[data-testid="segment-card-0"]');
    const videoPlayer = firstSegment.locator('[data-testid="segment-video"]');
    
    await expect(videoPlayer).toBeVisible({ timeout: 10000 });
    
    // Verify video has the correct source URL
    const videoSrc = await videoPlayer.getAttribute('src');
    expect(videoSrc).toBe(MINIMAX_MOCK_RESPONSES.chainedVideoGeneration.segment1.download_url);

    // Verify video has controls
    await expect(videoPlayer).toHaveAttribute('controls', '');

    // Verify "Approve Video" button is visible for generated segment
    await expect(firstSegment.locator('[data-testid="approve-video-button"]')).toBeVisible();
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

    // Verify video has controls
    await expect(finalVideo).toHaveAttribute('controls', '');

    // Verify download button is visible
    await expect(page.locator('[data-testid="download-button"]')).toBeVisible();
  });

  test('should show all 3 segment videos with real MiniMax URLs', async ({ page }) => {
    await mocks.mockVoiceClone();
    await mocks.mockGeneratePlan();
    await mocks.mockUpdateSegment();
    await mocks.mockApproveSegment();

    // Mock segments with all 3 videos generated (using real captured URLs)
    await page.route('**/api/v1/segments/project/*', async (route) => {
      const segmentsWithAllVideos = [
        {
          id: 'seg-1',
          projectId: 'project-123',
          index: 0,
          videoPrompt: BACKEND_MOCK_RESPONSES.generatePlan.segments[0].videoPrompt,
          narrationText: BACKEND_MOCK_RESPONSES.generatePlan.segments[0].narrationText,
          endFramePrompt: BACKEND_MOCK_RESPONSES.generatePlan.segments[0].endFramePrompt,
          durationSec: 6,
          status: 'generated',
          approved: true,
          videoUrl: MINIMAX_MOCK_RESPONSES.chainedVideoGeneration.segment1.download_url,
          audioUrl: 'https://storage.example.com/audio/segment-1.mp3',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
        {
          id: 'seg-2',
          projectId: 'project-123',
          index: 1,
          videoPrompt: BACKEND_MOCK_RESPONSES.generatePlan.segments[1].videoPrompt,
          narrationText: BACKEND_MOCK_RESPONSES.generatePlan.segments[1].narrationText,
          endFramePrompt: BACKEND_MOCK_RESPONSES.generatePlan.segments[1].endFramePrompt,
          durationSec: 6,
          status: 'generated',
          approved: true,
          videoUrl: MINIMAX_MOCK_RESPONSES.chainedVideoGeneration.segment2.download_url,
          audioUrl: 'https://storage.example.com/audio/segment-2.mp3',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
        {
          id: 'seg-3',
          projectId: 'project-123',
          index: 2,
          videoPrompt: BACKEND_MOCK_RESPONSES.generatePlan.segments[2].videoPrompt,
          narrationText: BACKEND_MOCK_RESPONSES.generatePlan.segments[2].narrationText,
          endFramePrompt: BACKEND_MOCK_RESPONSES.generatePlan.segments[2].endFramePrompt,
          durationSec: 6,
          status: 'generated',
          approved: true,
          videoUrl: MINIMAX_MOCK_RESPONSES.chainedVideoGeneration.segment3.download_url,
          audioUrl: 'https://storage.example.com/audio/segment-3.mp3',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
      ];

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(segmentsWithAllVideos),
      });
    });

    // Create project
    await page.goto('/projects/new');
    await page.fill('[data-testid="project-name"]', 'All Videos Test');
    await page.fill('[data-testid="story-prompt"]', 'A mountain adventure');
    await page.click('[data-testid="create-button"]');
    await page.waitForURL(/\/projects\/[\w-]+$/);

    // Upload media
    await page.locator('[data-testid="file-input-image"]').setInputFiles(
      './e2e/fixtures/first-frame.jpg'
    );
    await expect(page.locator('img[alt="Preview"]')).toBeVisible({ timeout: 30000 });

    await page.locator('[data-testid="file-input-audio"]').setInputFiles(
      './e2e/fixtures/test-audio.mp3'
    );

    // Clone voice and generate plan
    await page.click('[data-testid="clone-voice-button"]');
    await expect(page.locator('[data-testid="generate-plan-button"]')).toBeEnabled({
      timeout: 60000,
    });
    await page.click('[data-testid="generate-plan-button"]');

    // Wait for segments
    await expect(page.locator('[data-testid="segment-card-0"]')).toBeVisible({
      timeout: 60000,
    });

    // Verify all 3 video players are visible with correct URLs
    const videoUrls = [
      MINIMAX_MOCK_RESPONSES.chainedVideoGeneration.segment1.download_url,
      MINIMAX_MOCK_RESPONSES.chainedVideoGeneration.segment2.download_url,
      MINIMAX_MOCK_RESPONSES.chainedVideoGeneration.segment3.download_url,
    ];

    for (let i = 0; i < 3; i++) {
      const segment = page.locator(`[data-testid="segment-card-${i}"]`);
      const video = segment.locator('[data-testid="segment-video"]');
      
      await expect(video).toBeVisible({ timeout: 10000 });
      
      const src = await video.getAttribute('src');
      expect(src).toBe(videoUrls[i]);
    }
  });

  test('should display status badges correctly', async ({ page }) => {
    await mocks.mockVoiceClone();
    await mocks.mockGeneratePlan();
    await mocks.mockUpdateSegment();
    await mocks.mockApproveSegment();

    // Mock segments with different statuses
    await page.route('**/api/v1/segments/project/*', async (route) => {
      const mixedStatusSegments = [
        {
          id: 'seg-1',
          projectId: 'project-123',
          index: 0,
          videoPrompt: 'Prompt 1',
          narrationText: 'Narration 1',
          endFramePrompt: 'End frame 1',
          durationSec: 6,
          status: 'segment_approved', // Green badge
          approved: true,
          videoUrl: MINIMAX_MOCK_RESPONSES.chainedVideoGeneration.segment1.download_url,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
        {
          id: 'seg-2',
          projectId: 'project-123',
          index: 1,
          videoPrompt: 'Prompt 2',
          narrationText: 'Narration 2',
          endFramePrompt: 'End frame 2',
          durationSec: 6,
          status: 'generating_video', // Purple badge with spinner
          approved: true,
          videoUrl: null,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
        {
          id: 'seg-3',
          projectId: 'project-123',
          index: 2,
          videoPrompt: 'Prompt 3',
          narrationText: 'Narration 3',
          endFramePrompt: 'End frame 3',
          durationSec: 6,
          status: 'prompt_ready', // Yellow badge
          approved: false,
          videoUrl: null,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
      ];

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mixedStatusSegments),
      });
    });

    // Create and setup project
    await page.goto('/projects/new');
    await page.fill('[data-testid="project-name"]', 'Status Badge Test');
    await page.fill('[data-testid="story-prompt"]', 'Test story');
    await page.click('[data-testid="create-button"]');
    await page.waitForURL(/\/projects\/[\w-]+$/);

    await page.locator('[data-testid="file-input-image"]').setInputFiles(
      './e2e/fixtures/first-frame.jpg'
    );
    await expect(page.locator('img[alt="Preview"]')).toBeVisible({ timeout: 30000 });

    await page.locator('[data-testid="file-input-audio"]').setInputFiles(
      './e2e/fixtures/test-audio.mp3'
    );

    await page.click('[data-testid="clone-voice-button"]');
    await expect(page.locator('[data-testid="generate-plan-button"]')).toBeEnabled({
      timeout: 60000,
    });
    await page.click('[data-testid="generate-plan-button"]');

    // Wait for segments
    await expect(page.locator('[data-testid="segment-card-0"]')).toBeVisible({
      timeout: 60000,
    });

    // Verify status badges
    // Segment 1: segment_approved (green)
    const segment1 = page.locator('[data-testid="segment-card-0"]');
    await expect(segment1.getByText('Approved')).toBeVisible();

    // Segment 2: generating_video (purple with spinner)
    const segment2 = page.locator('[data-testid="segment-card-1"]');
    await expect(segment2.getByText('Generating Video')).toBeVisible();
    await expect(segment2.getByText('Generating...')).toBeVisible(); // Spinner text

    // Segment 3: prompt_ready (yellow)
    const segment3 = page.locator('[data-testid="segment-card-2"]');
    await expect(segment3.getByText('Prompt Ready')).toBeVisible();
  });
});
