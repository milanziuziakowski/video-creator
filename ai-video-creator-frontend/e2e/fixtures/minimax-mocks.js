/**
 * MiniMax API Mock Responses for E2E Tests
 *
 * These are REAL responses captured from MiniMax API on 2026-02-01.
 * Use these to mock backend endpoints in Playwright tests.
 */
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
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
export var MINIMAX_MOCK_RESPONSES = {
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
export var BACKEND_MOCK_RESPONSES = {
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
        error: undefined,
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
export function setupMinimaxMocks(page) {
    // Stateful segments storage - deep copy to avoid mutation issues
    var segmentsState = JSON.parse(JSON.stringify(BACKEND_MOCK_RESPONSES.projectSegments));
    return {
        /**
         * Reset segments state to initial values
         */
        resetSegments: function () {
            segmentsState = JSON.parse(JSON.stringify(BACKEND_MOCK_RESPONSES.projectSegments.map(function (s) { return (__assign(__assign({}, s), { videoPrompt: s.index === 0 ? 'A peaceful sunrise over misty mountains' : s.videoPrompt, narrationText: s.index === 0 ? 'As dawn breaks, the mountains awaken to a new day.' : s.narrationText, status: 'prompt_ready', approved: false })); })));
        },
        /**
         * Mock voice cloning endpoint
         */
        mockVoiceClone: function () {
            return __awaiter(this, void 0, void 0, function () {
                var _this = this;
                return __generator(this, function (_a) {
                    switch (_a.label) {
                        case 0: return [4 /*yield*/, page.route('**/api/v1/generation/voice-clone*', function (route) { return __awaiter(_this, void 0, void 0, function () {
                                return __generator(this, function (_a) {
                                    switch (_a.label) {
                                        case 0: return [4 /*yield*/, route.fulfill({
                                                status: 200,
                                                contentType: 'application/json',
                                                body: JSON.stringify(BACKEND_MOCK_RESPONSES.voiceClone),
                                            })];
                                        case 1:
                                            _a.sent();
                                            return [2 /*return*/];
                                    }
                                });
                            }); })];
                        case 1:
                            _a.sent();
                            return [2 /*return*/];
                    }
                });
            });
        },
        /**
         * Mock plan generation endpoint
         */
        mockGeneratePlan: function () {
            return __awaiter(this, void 0, void 0, function () {
                var _this = this;
                return __generator(this, function (_a) {
                    switch (_a.label) {
                        case 0: return [4 /*yield*/, page.route('**/api/v1/generation/plan', function (route) { return __awaiter(_this, void 0, void 0, function () {
                                return __generator(this, function (_a) {
                                    switch (_a.label) {
                                        case 0: return [4 /*yield*/, route.fulfill({
                                                status: 200,
                                                contentType: 'application/json',
                                                body: JSON.stringify(BACKEND_MOCK_RESPONSES.generatePlan),
                                            })];
                                        case 1:
                                            _a.sent();
                                            return [2 /*return*/];
                                    }
                                });
                            }); })];
                        case 1:
                            _a.sent();
                            return [2 /*return*/];
                    }
                });
            });
        },
        /**
         * Mock get project segments endpoint - returns current stateful data
         */
        mockProjectSegments: function () {
            return __awaiter(this, void 0, void 0, function () {
                var _this = this;
                return __generator(this, function (_a) {
                    switch (_a.label) {
                        case 0: return [4 /*yield*/, page.route('**/api/v1/segments/project/*', function (route) { return __awaiter(_this, void 0, void 0, function () {
                                return __generator(this, function (_a) {
                                    switch (_a.label) {
                                        case 0: return [4 /*yield*/, route.fulfill({
                                                status: 200,
                                                contentType: 'application/json',
                                                body: JSON.stringify(segmentsState),
                                            })];
                                        case 1:
                                            _a.sent();
                                            return [2 /*return*/];
                                    }
                                });
                            }); })];
                        case 1:
                            _a.sent();
                            return [2 /*return*/];
                    }
                });
            });
        },
        /**
         * Mock segment generation endpoint
         */
        mockGenerateSegment: function () {
            return __awaiter(this, void 0, void 0, function () {
                var _this = this;
                return __generator(this, function (_a) {
                    switch (_a.label) {
                        case 0: return [4 /*yield*/, page.route('**/api/v1/generation/segment/*', function (route) { return __awaiter(_this, void 0, void 0, function () {
                                return __generator(this, function (_a) {
                                    switch (_a.label) {
                                        case 0: return [4 /*yield*/, route.fulfill({
                                                status: 200,
                                                contentType: 'application/json',
                                                body: JSON.stringify(BACKEND_MOCK_RESPONSES.generateSegment),
                                            })];
                                        case 1:
                                            _a.sent();
                                            return [2 /*return*/];
                                    }
                                });
                            }); })];
                        case 1:
                            _a.sent();
                            return [2 /*return*/];
                    }
                });
            });
        },
        /**
         * Mock generation status polling
         */
        mockGenerationStatus: function () {
            return __awaiter(this, arguments, void 0, function (status) {
                var _this = this;
                if (status === void 0) { status = 'complete'; }
                return __generator(this, function (_a) {
                    switch (_a.label) {
                        case 0: return [4 /*yield*/, page.route('**/api/v1/generation/status/*', function (route) { return __awaiter(_this, void 0, void 0, function () {
                                var response;
                                return __generator(this, function (_a) {
                                    switch (_a.label) {
                                        case 0:
                                            response = BACKEND_MOCK_RESPONSES.generationStatus;
                                            if (status === 'processing') {
                                                response = __assign(__assign({}, response), { status: 'processing', progress: 50 });
                                            }
                                            else if (status === 'failed') {
                                                response = __assign(__assign({}, response), { status: 'failed', progress: 0, error: 'Generation failed' });
                                            }
                                            return [4 /*yield*/, route.fulfill({
                                                    status: 200,
                                                    contentType: 'application/json',
                                                    body: JSON.stringify(response),
                                                })];
                                        case 1:
                                            _a.sent();
                                            return [2 /*return*/];
                                    }
                                });
                            }); })];
                        case 1:
                            _a.sent();
                            return [2 /*return*/];
                    }
                });
            });
        },
        /**
         * Mock project finalization
         */
        mockFinalizeProject: function () {
            return __awaiter(this, void 0, void 0, function () {
                var _this = this;
                return __generator(this, function (_a) {
                    switch (_a.label) {
                        case 0: return [4 /*yield*/, page.route('**/api/v1/projects/*/finalize', function (route) { return __awaiter(_this, void 0, void 0, function () {
                                return __generator(this, function (_a) {
                                    switch (_a.label) {
                                        case 0: return [4 /*yield*/, route.fulfill({
                                                status: 200,
                                                contentType: 'application/json',
                                                body: JSON.stringify(BACKEND_MOCK_RESPONSES.finalizeProject),
                                            })];
                                        case 1:
                                            _a.sent();
                                            return [2 /*return*/];
                                    }
                                });
                            }); })];
                        case 1:
                            _a.sent();
                            return [2 /*return*/];
                    }
                });
            });
        },
        /**
         * Mock segment approval endpoint - updates stateful data
         */
        mockApproveSegment: function () {
            return __awaiter(this, void 0, void 0, function () {
                var _this = this;
                return __generator(this, function (_a) {
                    switch (_a.label) {
                        case 0: return [4 /*yield*/, page.route('**/api/v1/segments/*/approve', function (route) { return __awaiter(_this, void 0, void 0, function () {
                                var url, segmentIdMatch, segmentId, segmentIndex, updatedSegment;
                                return __generator(this, function (_a) {
                                    switch (_a.label) {
                                        case 0:
                                            url = route.request().url();
                                            segmentIdMatch = url.match(/\/segments\/([^/]+)\/approve/);
                                            segmentId = segmentIdMatch ? segmentIdMatch[1] : 'seg-1';
                                            segmentIndex = segmentsState.findIndex(function (s) { return s.id === segmentId; });
                                            if (segmentIndex !== -1) {
                                                segmentsState[segmentIndex] = __assign(__assign({}, segmentsState[segmentIndex]), { status: 'approved', approved: true, updatedAt: new Date().toISOString() });
                                            }
                                            updatedSegment = segmentIndex !== -1
                                                ? segmentsState[segmentIndex]
                                                : __assign(__assign({}, BACKEND_MOCK_RESPONSES.approveSegment), { id: segmentId });
                                            return [4 /*yield*/, route.fulfill({
                                                    status: 200,
                                                    contentType: 'application/json',
                                                    body: JSON.stringify(updatedSegment),
                                                })];
                                        case 1:
                                            _a.sent();
                                            return [2 /*return*/];
                                    }
                                });
                            }); })];
                        case 1:
                            _a.sent();
                            return [2 /*return*/];
                    }
                });
            });
        },
        /**
         * Mock segment update endpoint - updates stateful data
         */
        mockUpdateSegment: function () {
            return __awaiter(this, void 0, void 0, function () {
                var _this = this;
                return __generator(this, function (_a) {
                    switch (_a.label) {
                        case 0: return [4 /*yield*/, page.route('**/api/v1/segments/*', function (route) { return __awaiter(_this, void 0, void 0, function () {
                                var url, segmentIdMatch, segmentId_1, requestBody, segmentIndex, updatedSegment;
                                var _a, _b;
                                return __generator(this, function (_c) {
                                    switch (_c.label) {
                                        case 0:
                                            if (!(route.request().method() === 'PUT')) return [3 /*break*/, 2];
                                            url = route.request().url();
                                            segmentIdMatch = url.match(/\/segments\/([^/]+)$/);
                                            segmentId_1 = segmentIdMatch ? segmentIdMatch[1] : 'seg-1';
                                            requestBody = route.request().postDataJSON();
                                            segmentIndex = segmentsState.findIndex(function (s) { return s.id === segmentId_1; });
                                            if (segmentIndex !== -1) {
                                                segmentsState[segmentIndex] = __assign(__assign({}, segmentsState[segmentIndex]), { videoPrompt: (_a = requestBody.videoPrompt) !== null && _a !== void 0 ? _a : segmentsState[segmentIndex].videoPrompt, narrationText: (_b = requestBody.narrationText) !== null && _b !== void 0 ? _b : segmentsState[segmentIndex].narrationText, updatedAt: new Date().toISOString() });
                                            }
                                            updatedSegment = segmentIndex !== -1
                                                ? segmentsState[segmentIndex]
                                                : __assign(__assign({}, BACKEND_MOCK_RESPONSES.updateSegment), { id: segmentId_1 });
                                            return [4 /*yield*/, route.fulfill({
                                                    status: 200,
                                                    contentType: 'application/json',
                                                    body: JSON.stringify(updatedSegment),
                                                })];
                                        case 1:
                                            _c.sent();
                                            return [3 /*break*/, 4];
                                        case 2: return [4 /*yield*/, route.continue()];
                                        case 3:
                                            _c.sent();
                                            _c.label = 4;
                                        case 4: return [2 /*return*/];
                                    }
                                });
                            }); })];
                        case 1:
                            _a.sent();
                            return [2 /*return*/];
                    }
                });
            });
        },
        /**
         * Mock all endpoints at once
         */
        mockAll: function () {
            return __awaiter(this, void 0, void 0, function () {
                return __generator(this, function (_a) {
                    switch (_a.label) {
                        case 0:
                            // Reset state before setting up mocks
                            this.resetSegments();
                            return [4 /*yield*/, this.mockVoiceClone()];
                        case 1:
                            _a.sent();
                            return [4 /*yield*/, this.mockGeneratePlan()];
                        case 2:
                            _a.sent();
                            return [4 /*yield*/, this.mockProjectSegments()];
                        case 3:
                            _a.sent();
                            return [4 /*yield*/, this.mockUpdateSegment()];
                        case 4:
                            _a.sent();
                            return [4 /*yield*/, this.mockApproveSegment()];
                        case 5:
                            _a.sent();
                            return [4 /*yield*/, this.mockGenerateSegment()];
                        case 6:
                            _a.sent();
                            return [4 /*yield*/, this.mockGenerationStatus()];
                        case 7:
                            _a.sent();
                            return [4 /*yield*/, this.mockFinalizeProject()];
                        case 8:
                            _a.sent();
                            return [2 /*return*/];
                    }
                });
            });
        },
    };
}
