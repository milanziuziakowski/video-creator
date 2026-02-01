/**
 * MiniMax API Mock Responses for E2E Tests
 *
 * These are REAL responses captured from MiniMax API on 2026-02-01.
 * Use these to mock backend endpoints in Playwright tests.
 */
export declare const MINIMAX_MOCK_RESPONSES: {
    /**
     * File Upload Response
     * Endpoint: POST /v1/files/upload
     * REAL DATA captured 2026-02-01
     */
    filesUpload: {
        file_id: string;
        status: string;
    };
    /**
     * Voice Clone Response
     * Endpoint: POST /v1/voice_clone
     * REAL DATA captured 2026-02-01
     */
    voiceClone: {
        voice_id: string;
        status: string;
    };
    /**
     * Text-to-Audio Response
     * Endpoint: POST /v1/t2a_v2
     * REAL DATA captured 2026-02-01
     */
    textToAudio: {
        audio_size_bytes: number;
        status: string;
        voice_id: string;
    };
    /**
     * Video Generation - Chained Segments (REAL DATA)
     * Captures real workflow: Segment 1 with FL2V, Segments 2-3 with extracted frames
     */
    chainedVideoGeneration: {
        segment1: {
            task_id: string;
            file_id: string;
            download_url: string;
            video_width: number;
            video_height: number;
            frame_source: string;
        };
        segment2: {
            task_id: string;
            file_id: string;
            download_url: string;
            video_width: number;
            video_height: number;
            frame_source: string;
        };
        segment3: {
            task_id: string;
            file_id: string;
            download_url: string;
            video_width: number;
            video_height: number;
            frame_source: string;
        };
    };
    /**
     * Video Generation Start Response (default - uses segment 1)
     * Endpoint: POST /v1/video_generation
     * REAL DATA captured 2026-02-01
     */
    videoGeneration: {
        task_id: string;
        status: string;
    };
    /**
     * Video Generation Status - Preparing
     * Endpoint: GET /v1/query/video_generation
     * REAL DATA captured 2026-02-01
     */
    videoStatusPreparing: {
        task_id: string;
        status: string;
        file_id: string;
        video_width: number;
        video_height: number;
    };
    /**
     * Video Generation Status - Processing
     * Endpoint: GET /v1/query/video_generation
     * REAL DATA captured 2026-02-01
     */
    videoStatusProcessing: {
        task_id: string;
        status: string;
        file_id: string;
        video_width: number;
        video_height: number;
    };
    /**
     * Video Generation Status - Success
     * Endpoint: GET /v1/query/video_generation
     * REAL DATA captured 2026-02-01
     */
    videoStatusSuccess: {
        task_id: string;
        status: string;
        file_id: string;
        video_width: number;
        video_height: number;
    };
    /**
     * File Retrieve Response
     * Endpoint: GET /v1/files/retrieve
     * REAL DATA captured 2026-02-01
     */
    fileRetrieve: {
        file_id: string;
        download_url: string;
    };
};
/**
 * Backend API Mock Responses
 * These are the responses from YOUR backend that wrap MiniMax API calls
 */
export declare const BACKEND_MOCK_RESPONSES: {
    /**
     * POST /api/v1/generation/voice-clone
     */
    voiceClone: {
        voice_id: string;
        status: string;
        message: string;
    };
    /**
     * POST /api/v1/generation/plan
     * REAL DATA from OpenAI GPT-4o structured output - captured 2026-02-01
     */
    generatePlan: {
        title: string;
        segments: {
            id: string;
            index: number;
            videoPrompt: string;
            narrationText: string;
            endFramePrompt: string;
            videoDurationSec: number;
            status: string;
        }[];
        continuityNotes: string;
    };
    /**
     * GET /api/v1/segments/project/{project_id}
     * Initial segments data - REAL DATA from OpenAI plan generation
     * Will be mutated by update/approve operations
     */
    projectSegments: {
        id: string;
        projectId: string;
        index: number;
        videoPrompt: string;
        narrationText: string;
        endFramePrompt: string;
        durationSec: number;
        status: string;
        approved: boolean;
        firstFrameUrl: null;
        lastFrameUrl: null;
        videoUrl: null;
        audioUrl: null;
        videoTaskId: null;
        createdAt: string;
        updatedAt: string;
    }[];
    /**
     * POST /api/v1/generation/segment/{segment_id}
     * REAL DATA - uses task_id from chained video generation
     */
    generateSegment: {
        segmentId: string;
        status: string;
        videoTaskId: string;
        message: string;
    };
    /**
     * GET /api/v1/generation/status/{task_id}
     * REAL DATA - uses captured video URLs from chained MiniMax generation
     */
    generationStatus: {
        taskId: string;
        status: string;
        progress: number;
        result: {
            videoUrl: string;
            audioUrl: string;
        };
        error: string | undefined;
    };
    /**
     * Generation status for each segment (REAL DATA)
     */
    generationStatusBySegment: {
        'seg-1': {
            taskId: string;
            status: string;
            progress: number;
            result: {
                videoUrl: string;
                audioUrl: string;
            };
        };
        'seg-2': {
            taskId: string;
            status: string;
            progress: number;
            result: {
                videoUrl: string;
                audioUrl: string;
            };
        };
        'seg-3': {
            taskId: string;
            status: string;
            progress: number;
            result: {
                videoUrl: string;
                audioUrl: string;
            };
        };
    };
    /**
     * PUT /api/v1/segments/{segment_id}
     */
    updateSegment: {
        id: string;
        projectId: string;
        index: number;
        videoPrompt: string;
        narrationText: string;
        endFramePrompt: string;
        durationSec: number;
        status: string;
        approved: boolean;
        firstFrameUrl: null;
        lastFrameUrl: null;
        videoUrl: null;
        audioUrl: null;
        videoTaskId: null;
        createdAt: string;
        updatedAt: string;
    };
    /**
     * POST /api/v1/segments/{segment_id}/approve
     */
    approveSegment: {
        id: string;
        projectId: string;
        index: number;
        videoPrompt: string;
        narrationText: string;
        endFramePrompt: string;
        durationSec: number;
        status: string;
        approved: boolean;
        firstFrameUrl: null;
        lastFrameUrl: null;
        videoUrl: null;
        audioUrl: null;
        videoTaskId: null;
        createdAt: string;
        updatedAt: string;
    };
    /**
     * POST /api/v1/projects/{project_id}/finalize
     */
    finalizeProject: {
        projectId: string;
        status: string;
        finalVideoUrl: string;
        durationSec: number;
    };
};
/**
 * Helper function to setup route mocking in Playwright tests
 *
 * IMPORTANT: This uses stateful mocking to track segment changes
 * so that edits and approvals are properly reflected in subsequent reads.
 */
export declare function setupMinimaxMocks(page: any): {
    /**
     * Reset segments state to initial values
     */
    resetSegments(): void;
    /**
     * Mock voice cloning endpoint
     */
    mockVoiceClone(): Promise<void>;
    /**
     * Mock plan generation endpoint
     */
    mockGeneratePlan(): Promise<void>;
    /**
     * Mock get project segments endpoint - returns current stateful data
     */
    mockProjectSegments(): Promise<void>;
    /**
     * Mock segment generation endpoint
     */
    mockGenerateSegment(): Promise<void>;
    /**
     * Mock generation status polling
     */
    mockGenerationStatus(status?: "processing" | "complete" | "failed"): Promise<void>;
    /**
     * Mock project finalization
     */
    mockFinalizeProject(): Promise<void>;
    /**
     * Mock segment approval endpoint - updates stateful data
     */
    mockApproveSegment(): Promise<void>;
    /**
     * Mock segment update endpoint - updates stateful data
     */
    mockUpdateSegment(): Promise<void>;
    /**
     * Mock all endpoints at once
     */
    mockAll(): Promise<void>;
};
