/**
 * MiniMax API Mock Responses for E2E Tests
 * 
 * These are REAL responses captured from MiniMax API on 2026-02-01.
 * Use these to mock backend endpoints in Playwright tests.
 */

export const MINIMAX_MOCK_RESPONSES = {
  /**
   * File Upload Response
   * Endpoint: POST /v1/files/upload
   * REAL DATA captured 2026-02-01
   */
  filesUpload: {
    file_id: '362069085524212',
    status: 'success',
  },

  /**
   * Voice Clone Response
   * Endpoint: POST /v1/voice_clone
   * REAL DATA captured 2026-02-01
   */
  voiceClone: {
    voice_id: 'test-voice-20260201133125',
    status: 'success',
  },

  /**
   * Text-to-Audio Response
   * Endpoint: POST /v1/t2a_v2
   * REAL DATA captured 2026-02-01
   */
  textToAudio: {
    audio_size_bytes: 44160,
    status: 'success',
    voice_id: 'test-voice-20260201133125',
  },

  /**
   * Video Generation - Chained Segments (REAL DATA)
   * Captures real workflow: Segment 1 with FL2V, Segments 2-3 with extracted frames
   */
  chainedVideoGeneration: {
    segment1: {
      task_id: '362090061725888',
      file_id: '362088325627994',
      download_url: 'https://video-product.cdn.minimax.io/inference_output/video/2026-02-01/bbc3affb-5dab-42da-b50e-66052f2914d6/output.mp4',
      video_width: 864,
      video_height: 768,
      frame_source: 'first-frame.jpg + last-frame.jpg (FL2V)',
    },
    segment2: {
      task_id: '362088904257821',
      file_id: '362088836677797',
      download_url: 'https://video-product.cdn.minimax.io/inference_output/video/2026-02-01/c8de26fe-6951-472b-9c7d-81068aa0172e/output.mp4',
      video_width: 864,
      video_height: 768,
      frame_source: 'extracted last frame from segment 1',
    },
    segment3: {
      task_id: '362086435836151',
      file_id: '362090476376141',
      download_url: 'https://video-product.cdn.minimax.io/inference_output/video/2026-02-01/56578a0a-8a6d-45f4-82e7-de6b07af0692/output.mp4',
      video_width: 864,
      video_height: 768,
      frame_source: 'extracted last frame from segment 2',
    },
  },

  /**
   * Video Generation Start Response (default - uses segment 1)
   * Endpoint: POST /v1/video_generation
   * REAL DATA captured 2026-02-01
   */
  videoGeneration: {
    task_id: '362090061725888',
    status: 'submitted',
  },

  /**
   * Video Generation Status - Preparing
   * Endpoint: GET /v1/query/video_generation
   * REAL DATA captured 2026-02-01
   */
  videoStatusPreparing: {
    task_id: '362090061725888',
    status: 'Preparing',
    file_id: '',
    video_width: 0,
    video_height: 0,
  },

  /**
   * Video Generation Status - Processing
   * Endpoint: GET /v1/query/video_generation
   * REAL DATA captured 2026-02-01
   */
  videoStatusProcessing: {
    task_id: '362090061725888',
    status: 'Processing',
    file_id: '',
    video_width: 0,
    video_height: 0,
  },

  /**
   * Video Generation Status - Success
   * Endpoint: GET /v1/query/video_generation
   * REAL DATA captured 2026-02-01
   */
  videoStatusSuccess: {
    task_id: '362090061725888',
    status: 'Success',
    file_id: '362088325627994',
    video_width: 864,
    video_height: 768,
  },

  /**
   * File Retrieve Response
   * Endpoint: GET /v1/files/retrieve
   * REAL DATA captured 2026-02-01
   */
  fileRetrieve: {
    file_id: '362088325627994',
    download_url: 'https://video-product.cdn.minimax.io/inference_output/video/2026-02-01/bbc3affb-5dab-42da-b50e-66052f2914d6/output.mp4',
  },
};

/**
 * Backend API Mock Responses
 * These are the responses from YOUR backend that wrap MiniMax API calls
 */
export const BACKEND_MOCK_RESPONSES = {
  /**
   * POST /api/v1/generation/voice-clone
   */
  voiceClone: {
    voice_id: MINIMAX_MOCK_RESPONSES.voiceClone.voice_id,
    status: 'complete',
    message: 'Voice cloned successfully',
  },

  /**
   * POST /api/v1/generation/plan
   * REAL DATA from OpenAI GPT-4o structured output - captured 2026-02-01
   */
  generatePlan: {
    title: 'The Man Who Tried to Fly',
    segments: [
      {
        id: 'seg-1',
        index: 0,
        videoPrompt: 'The scene opens with a wide shot of a solitary man standing on a rugged mountain peak, surrounded by vast, snow-capped ranges. The sky is a brilliant blue with a few wispy clouds. [Zoom in] slowly towards the man as the wind gently rustles his hair and clothes, creating a sense of solitude and determination.',
        narrationText: 'High in the mountains, he stands alone, gazing at the endless sky, dreaming of flight and freedom.',
        endFramePrompt: 'The camera focuses on the man\'s face, capturing his determined expression as the wind blows through his hair.',
        videoDurationSec: 6,
        status: 'prompt_ready',
      },
      {
        id: 'seg-2',
        index: 1,
        videoPrompt: 'Cut to a medium shot of the man spreading his arms wide, as if preparing to take flight. [Tilt down] to show his feet firmly planted on the rocky ground, emphasizing the contrast between his dreams and reality. The light is warm, casting long shadows.',
        narrationText: 'With arms outstretched, he imagines the sensation of soaring through the air, yet his feet remain grounded.',
        endFramePrompt: 'The camera settles on a close-up of his hands gripping the edge of a rock, signifying his connection to the earth.',
        videoDurationSec: 6,
        status: 'prompt_ready',
      },
      {
        id: 'seg-3',
        index: 2,
        videoPrompt: 'Transition to a close-up of the man\'s face as he lowers his arms and smiles softly. [Pull out] to reveal the surrounding landscape, capturing the peaceful and accepting atmosphere. The golden light of the setting sun bathes the scene, adding warmth and tranquility.',
        narrationText: 'Though he cannot fly, a smile spreads across his face as he embraces the beauty around him, finding joy in the moment.',
        endFramePrompt: 'The scene ends with a wide shot of the man silhouetted against the sunset, his smile evident as he gazes into the horizon.',
        videoDurationSec: 6,
        status: 'prompt_ready',
      },
    ],
    continuityNotes: 'Maintain consistent lighting and color grading throughout the segments to emphasize the transition from determination to acceptance. Ensure the wind is a constant presence, symbolizing the man\'s aspirations and connection to nature.',
  },

  /**
   * GET /api/v1/segments/project/{project_id}
   * Initial segments data - REAL DATA from OpenAI plan generation
   * Will be mutated by update/approve operations
   */
  projectSegments: [
    {
      id: 'seg-1',
      projectId: 'project-123',
      index: 0,
      videoPrompt: 'The scene opens with a wide shot of a solitary man standing on a rugged mountain peak, surrounded by vast, snow-capped ranges. The sky is a brilliant blue with a few wispy clouds. [Zoom in] slowly towards the man as the wind gently rustles his hair and clothes, creating a sense of solitude and determination.',
      narrationText: 'High in the mountains, he stands alone, gazing at the endless sky, dreaming of flight and freedom.',
      endFramePrompt: 'The camera focuses on the man\'s face, capturing his determined expression as the wind blows through his hair.',
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
      id: 'seg-2',
      projectId: 'project-123',
      index: 1,
      videoPrompt: 'Cut to a medium shot of the man spreading his arms wide, as if preparing to take flight. [Tilt down] to show his feet firmly planted on the rocky ground, emphasizing the contrast between his dreams and reality. The light is warm, casting long shadows.',
      narrationText: 'With arms outstretched, he imagines the sensation of soaring through the air, yet his feet remain grounded.',
      endFramePrompt: 'The camera settles on a close-up of his hands gripping the edge of a rock, signifying his connection to the earth.',
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
      videoPrompt: 'Transition to a close-up of the man\'s face as he lowers his arms and smiles softly. [Pull out] to reveal the surrounding landscape, capturing the peaceful and accepting atmosphere. The golden light of the setting sun bathes the scene, adding warmth and tranquility.',
      narrationText: 'Though he cannot fly, a smile spreads across his face as he embraces the beauty around him, finding joy in the moment.',
      endFramePrompt: 'The scene ends with a wide shot of the man silhouetted against the sunset, his smile evident as he gazes into the horizon.',
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
  ],

  /**
   * POST /api/v1/generation/segment/{segment_id}
   * REAL DATA - uses task_id from chained video generation
   */
  generateSegment: {
    segmentId: 'seg-1',
    status: 'generating',
    videoTaskId: MINIMAX_MOCK_RESPONSES.chainedVideoGeneration.segment1.task_id,
    message: 'Segment generation started',
  },

  /**
   * GET /api/v1/generation/status/{task_id}
   * REAL DATA - uses captured video URLs from chained MiniMax generation
   */
  generationStatus: {
    taskId: '362090061725888',
    status: 'complete',
    progress: 100,
    result: {
      videoUrl: 'https://video-product.cdn.minimax.io/inference_output/video/2026-02-01/bbc3affb-5dab-42da-b50e-66052f2914d6/output.mp4',
      audioUrl: 'https://storage.example.com/audio/segment-1.mp3',
    },
    error: undefined as string | undefined,
  },

  /**
   * Generation status for each segment (REAL DATA)
   */
  generationStatusBySegment: {
    'seg-1': {
      taskId: '362090061725888',
      status: 'complete',
      progress: 100,
      result: {
        videoUrl: 'https://video-product.cdn.minimax.io/inference_output/video/2026-02-01/bbc3affb-5dab-42da-b50e-66052f2914d6/output.mp4',
        audioUrl: 'https://storage.example.com/audio/segment-1.mp3',
      },
    },
    'seg-2': {
      taskId: '362088904257821',
      status: 'complete',
      progress: 100,
      result: {
        videoUrl: 'https://video-product.cdn.minimax.io/inference_output/video/2026-02-01/c8de26fe-6951-472b-9c7d-81068aa0172e/output.mp4',
        audioUrl: 'https://storage.example.com/audio/segment-2.mp3',
      },
    },
    'seg-3': {
      taskId: '362086435836151',
      status: 'complete',
      progress: 100,
      result: {
        videoUrl: 'https://video-product.cdn.minimax.io/inference_output/video/2026-02-01/56578a0a-8a6d-45f4-82e7-de6b07af0692/output.mp4',
        audioUrl: 'https://storage.example.com/audio/segment-3.mp3',
      },
    },
  },

  /**
   * PUT /api/v1/segments/{segment_id}
   */
  updateSegment: {
    id: 'seg-1',
    projectId: 'project-123',
    index: 0,
    videoPrompt: 'Edited prompt: A climber reaches the summit',
    narrationText: 'Edited narration for the segment.',
    endFramePrompt: 'Golden sunlight illuminating mountain peaks',
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

  /**
   * POST /api/v1/segments/{segment_id}/approve
   */
  approveSegment: {
    id: 'seg-1',
    projectId: 'project-123',
    index: 0,
    videoPrompt: 'Edited prompt: A climber reaches the summit',
    narrationText: 'Edited narration for the segment.',
    endFramePrompt: 'Golden sunlight illuminating mountain peaks',
    durationSec: 6,
    status: 'approved',
    approved: true,
    firstFrameUrl: null,
    lastFrameUrl: null,
    videoUrl: null,
    audioUrl: null,
    videoTaskId: null,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },

  /**
   * POST /api/v1/projects/{project_id}/finalize
   */
  finalizeProject: {
    projectId: 'project-123',
    status: 'completed',
    finalVideoUrl: 'https://storage.example.com/videos/final-video.mp4',
    durationSec: 30,
  },
};

/**
 * Helper function to setup route mocking in Playwright tests
 * 
 * IMPORTANT: This uses stateful mocking to track segment changes
 * so that edits and approvals are properly reflected in subsequent reads.
 */
export function setupMinimaxMocks(page: any) {
  // Stateful segments storage - deep copy to avoid mutation issues
  let segmentsState: typeof BACKEND_MOCK_RESPONSES.projectSegments = JSON.parse(
    JSON.stringify(BACKEND_MOCK_RESPONSES.projectSegments)
  );

  return {
    /**
     * Reset segments state to initial values
     */
    resetSegments() {
      segmentsState = JSON.parse(JSON.stringify(BACKEND_MOCK_RESPONSES.projectSegments.map(s => ({
        ...s,
        videoPrompt: s.index === 0 ? 'A peaceful sunrise over misty mountains' : s.videoPrompt,
        narrationText: s.index === 0 ? 'As dawn breaks, the mountains awaken to a new day.' : s.narrationText,
        status: 'prompt_ready',
        approved: false,
      }))));
    },

    /**
     * Mock voice cloning endpoint
     */
    async mockVoiceClone() {
      await page.route('**/api/v1/generation/voice-clone*', async (route: any) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(BACKEND_MOCK_RESPONSES.voiceClone),
        });
      });
    },

    /**
     * Mock plan generation endpoint
     */
    async mockGeneratePlan() {
      await page.route('**/api/v1/generation/plan', async (route: any) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(BACKEND_MOCK_RESPONSES.generatePlan),
        });
      });
    },

    /**
     * Mock get project segments endpoint - returns current stateful data
     */
    async mockProjectSegments() {
      await page.route('**/api/v1/segments/project/*', async (route: any) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(segmentsState),
        });
      });
    },

    /**
     * Mock segment generation endpoint
     */
    async mockGenerateSegment() {
      await page.route('**/api/v1/generation/segment/*', async (route: any) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(BACKEND_MOCK_RESPONSES.generateSegment),
        });
      });
    },

    /**
     * Mock generation status polling
     */
    async mockGenerationStatus(status: 'processing' | 'complete' | 'failed' = 'complete') {
      await page.route('**/api/v1/generation/status/*', async (route: any) => {
        let response = BACKEND_MOCK_RESPONSES.generationStatus;
        
        if (status === 'processing') {
          response = {
            ...response,
            status: 'processing',
            progress: 50,
          };
        } else if (status === 'failed') {
          response = {
            ...response,
            status: 'failed',
            progress: 0,
            error: 'Generation failed',
          };
        }

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(response),
        });
      });
    },

    /**
     * Mock project finalization
     */
    async mockFinalizeProject() {
      await page.route('**/api/v1/projects/*/finalize', async (route: any) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(BACKEND_MOCK_RESPONSES.finalizeProject),
        });
      });
    },

    /**
     * Mock segment approval endpoint - updates stateful data
     */
    async mockApproveSegment() {
      await page.route('**/api/v1/segments/*/approve', async (route: any) => {
        const url = route.request().url();
        const segmentIdMatch = url.match(/\/segments\/([^/]+)\/approve/);
        const segmentId = segmentIdMatch ? segmentIdMatch[1] : 'seg-1';

        // Find and update the segment in state
        const segmentIndex = segmentsState.findIndex(s => s.id === segmentId);
        if (segmentIndex !== -1) {
          segmentsState[segmentIndex] = {
            ...segmentsState[segmentIndex],
            status: 'approved',
            approved: true,
            updatedAt: new Date().toISOString(),
          };
        }

        // Return the updated segment
        const updatedSegment = segmentIndex !== -1 
          ? segmentsState[segmentIndex] 
          : { ...BACKEND_MOCK_RESPONSES.approveSegment, id: segmentId };

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(updatedSegment),
        });
      });
    },

    /**
     * Mock segment update endpoint - updates stateful data
     */
    async mockUpdateSegment() {
      await page.route('**/api/v1/segments/*', async (route: any) => {
        if (route.request().method() === 'PUT') {
          const url = route.request().url();
          // Extract segment ID from URL (e.g., /api/v1/segments/seg-1)
          const segmentIdMatch = url.match(/\/segments\/([^/]+)$/);
          const segmentId = segmentIdMatch ? segmentIdMatch[1] : 'seg-1';

          // Parse the request body to get the updated values
          const requestBody = route.request().postDataJSON();

          // Find and update the segment in state
          const segmentIndex = segmentsState.findIndex(s => s.id === segmentId);
          if (segmentIndex !== -1) {
            segmentsState[segmentIndex] = {
              ...segmentsState[segmentIndex],
              videoPrompt: requestBody.videoPrompt ?? segmentsState[segmentIndex].videoPrompt,
              narrationText: requestBody.narrationText ?? segmentsState[segmentIndex].narrationText,
              updatedAt: new Date().toISOString(),
            };
          }

          // Return the updated segment
          const updatedSegment = segmentIndex !== -1 
            ? segmentsState[segmentIndex] 
            : { ...BACKEND_MOCK_RESPONSES.updateSegment, id: segmentId };

          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(updatedSegment),
          });
        } else {
          await route.continue();
        }
      });
    },

    /**
     * Mock all endpoints at once
     */
    async mockAll() {
      // Reset state before setting up mocks
      this.resetSegments();
      
      await this.mockVoiceClone();
      await this.mockGeneratePlan();
      await this.mockProjectSegments();
      await this.mockUpdateSegment();
      await this.mockApproveSegment();
      await this.mockGenerateSegment();
      await this.mockGenerationStatus();
      await this.mockFinalizeProject();
    },
  };
}
