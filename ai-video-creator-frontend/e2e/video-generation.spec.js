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
import { test, expect } from '@playwright/test';
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
test.describe('Video Generation and Playback', function () {
    var mocks;
    test.beforeEach(function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
        var page = _b.page;
        return __generator(this, function (_c) {
            mocks = setupMinimaxMocks(page);
            return [2 /*return*/];
        });
    }); });
    test('should display uploaded first frame image', function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
        var imagePreview, imgSrc;
        var page = _b.page;
        return __generator(this, function (_c) {
            switch (_c.label) {
                case 0: return [4 /*yield*/, mocks.mockAll()];
                case 1:
                    _c.sent();
                    // Create project and upload image
                    return [4 /*yield*/, page.goto('/projects/new')];
                case 2:
                    // Create project and upload image
                    _c.sent();
                    return [4 /*yield*/, page.fill('[data-testid="project-name"]', 'Image Preview Test')];
                case 3:
                    _c.sent();
                    return [4 /*yield*/, page.fill('[data-testid="story-prompt"]', 'Test story')];
                case 4:
                    _c.sent();
                    return [4 /*yield*/, page.click('[data-testid="create-button"]')];
                case 5:
                    _c.sent();
                    return [4 /*yield*/, page.waitForURL(/\/projects\/[\w-]+$/)];
                case 6:
                    _c.sent();
                    // Upload first frame image
                    return [4 /*yield*/, page.locator('[data-testid="file-input-image"]').setInputFiles('./e2e/fixtures/first-frame.jpg')];
                case 7:
                    // Upload first frame image
                    _c.sent();
                    imagePreview = page.locator('img[alt="Preview"]');
                    return [4 /*yield*/, expect(imagePreview).toBeVisible({ timeout: 30000 })];
                case 8:
                    _c.sent();
                    return [4 /*yield*/, imagePreview.getAttribute('src')];
                case 9:
                    imgSrc = _c.sent();
                    expect(imgSrc).toBeTruthy();
                    expect(imgSrc.length).toBeGreaterThan(0);
                    return [2 /*return*/];
            }
        });
    }); });
    test('should show generation status during video creation', function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
        var segmentStatus, segmentApproved, firstSegment;
        var page = _b.page;
        return __generator(this, function (_c) {
            switch (_c.label) {
                case 0: 
                // Setup mocks with delayed status transitions
                return [4 /*yield*/, mocks.mockVoiceClone()];
                case 1:
                    // Setup mocks with delayed status transitions
                    _c.sent();
                    return [4 /*yield*/, mocks.mockGeneratePlan()];
                case 2:
                    _c.sent();
                    return [4 /*yield*/, mocks.mockUpdateSegment()];
                case 3:
                    _c.sent();
                    return [4 /*yield*/, mocks.mockApproveSegment()];
                case 4:
                    _c.sent();
                    segmentStatus = 'prompt_ready';
                    segmentApproved = false;
                    // Mock segments endpoint - returns current status
                    return [4 /*yield*/, page.route('**/api/v1/segments/project/*', function (route) { return __awaiter(void 0, void 0, void 0, function () {
                            var segments;
                            return __generator(this, function (_a) {
                                switch (_a.label) {
                                    case 0:
                                        segments = BACKEND_MOCK_RESPONSES.generatePlan.segments.map(function (seg, idx) { return ({
                                            id: "seg-".concat(idx + 1),
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
                                        }); });
                                        return [4 /*yield*/, route.fulfill({
                                                status: 200,
                                                contentType: 'application/json',
                                                body: JSON.stringify(segments),
                                            })];
                                    case 1:
                                        _a.sent();
                                        return [2 /*return*/];
                                }
                            });
                        }); })];
                case 5:
                    // Mock segments endpoint - returns current status
                    _c.sent();
                    // Mock approve segment - updates status
                    return [4 /*yield*/, page.route('**/api/v1/segments/*/approve', function (route) { return __awaiter(void 0, void 0, void 0, function () {
                            return __generator(this, function (_a) {
                                switch (_a.label) {
                                    case 0:
                                        segmentStatus = 'approved';
                                        segmentApproved = true;
                                        return [4 /*yield*/, route.fulfill({
                                                status: 200,
                                                contentType: 'application/json',
                                                body: JSON.stringify({
                                                    id: 'seg-1',
                                                    status: 'approved',
                                                    approved: true,
                                                }),
                                            })];
                                    case 1:
                                        _a.sent();
                                        return [2 /*return*/];
                                }
                            });
                        }); })];
                case 6:
                    // Mock approve segment - updates status
                    _c.sent();
                    // Mock generate segment - changes status to generating_video
                    return [4 /*yield*/, page.route('**/api/v1/generation/segment/*', function (route) { return __awaiter(void 0, void 0, void 0, function () {
                            return __generator(this, function (_a) {
                                switch (_a.label) {
                                    case 0:
                                        segmentStatus = 'generating_video';
                                        return [4 /*yield*/, route.fulfill({
                                                status: 200,
                                                contentType: 'application/json',
                                                body: JSON.stringify({
                                                    segmentId: 'seg-1',
                                                    status: 'generating',
                                                    videoTaskId: MINIMAX_MOCK_RESPONSES.chainedVideoGeneration.segment1.task_id,
                                                    message: 'Segment generation started',
                                                }),
                                            })];
                                    case 1:
                                        _a.sent();
                                        return [2 /*return*/];
                                }
                            });
                        }); })];
                case 7:
                    // Mock generate segment - changes status to generating_video
                    _c.sent();
                    // Create project and setup
                    return [4 /*yield*/, page.goto('/projects/new')];
                case 8:
                    // Create project and setup
                    _c.sent();
                    return [4 /*yield*/, page.fill('[data-testid="project-name"]', 'Status Test Project')];
                case 9:
                    _c.sent();
                    return [4 /*yield*/, page.fill('[data-testid="story-prompt"]', 'A mountain adventure')];
                case 10:
                    _c.sent();
                    return [4 /*yield*/, page.click('[data-testid="create-button"]')];
                case 11:
                    _c.sent();
                    return [4 /*yield*/, page.waitForURL(/\/projects\/[\w-]+$/)];
                case 12:
                    _c.sent();
                    // Upload media
                    return [4 /*yield*/, page.locator('[data-testid="file-input-image"]').setInputFiles('./e2e/fixtures/first-frame.jpg')];
                case 13:
                    // Upload media
                    _c.sent();
                    return [4 /*yield*/, expect(page.locator('img[alt="Preview"]')).toBeVisible({ timeout: 30000 })];
                case 14:
                    _c.sent();
                    return [4 /*yield*/, page.locator('[data-testid="file-input-audio"]').setInputFiles('./e2e/fixtures/test-audio.mp3')];
                case 15:
                    _c.sent();
                    return [4 /*yield*/, expect(page.locator('audio')).toBeVisible({ timeout: 30000 })];
                case 16:
                    _c.sent();
                    // Clone voice and generate plan
                    return [4 /*yield*/, page.click('[data-testid="clone-voice-button"]')];
                case 17:
                    // Clone voice and generate plan
                    _c.sent();
                    return [4 /*yield*/, expect(page.locator('[data-testid="generate-plan-button"]')).toBeEnabled({
                            timeout: 60000,
                        })];
                case 18:
                    _c.sent();
                    return [4 /*yield*/, page.click('[data-testid="generate-plan-button"]')];
                case 19:
                    _c.sent();
                    // Wait for segments
                    return [4 /*yield*/, expect(page.locator('[data-testid="segment-card-0"]')).toBeVisible({
                            timeout: 60000,
                        })];
                case 20:
                    // Wait for segments
                    _c.sent();
                    firstSegment = page.locator('[data-testid="segment-card-0"]');
                    return [4 /*yield*/, firstSegment.locator('[data-testid="approve-button"]').click()];
                case 21:
                    _c.sent();
                    // Wait for generate button to appear after approval
                    return [4 /*yield*/, expect(firstSegment.locator('[data-testid="generate-button"]')).toBeVisible({
                            timeout: 30000,
                        })];
                case 22:
                    // Wait for generate button to appear after approval
                    _c.sent();
                    // Start generation
                    return [4 /*yield*/, firstSegment.locator('[data-testid="generate-button"]').click()];
                case 23:
                    // Start generation
                    _c.sent();
                    // Verify "Generating..." spinner text is shown (specific to generating state)
                    return [4 /*yield*/, expect(firstSegment.getByText('Generating...')).toBeVisible({
                            timeout: 10000,
                        })];
                case 24:
                    // Verify "Generating..." spinner text is shown (specific to generating state)
                    _c.sent();
                    // Also verify the status badge shows "Generating Video"
                    return [4 /*yield*/, expect(firstSegment.getByText('Generating Video')).toBeVisible()];
                case 25:
                    // Also verify the status badge shows "Generating Video"
                    _c.sent();
                    return [2 /*return*/];
            }
        });
    }); });
    test('should display video player when segment is generated', function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
        var firstSegment, videoPlayer, videoSrc;
        var page = _b.page;
        return __generator(this, function (_c) {
            switch (_c.label) {
                case 0: 
                // Setup mocks with completed segment
                return [4 /*yield*/, mocks.mockVoiceClone()];
                case 1:
                    // Setup mocks with completed segment
                    _c.sent();
                    return [4 /*yield*/, mocks.mockGeneratePlan()];
                case 2:
                    _c.sent();
                    return [4 /*yield*/, mocks.mockUpdateSegment()];
                case 3:
                    _c.sent();
                    return [4 /*yield*/, mocks.mockApproveSegment()];
                case 4:
                    _c.sent();
                    // Mock segments with one already generated (has videoUrl)
                    return [4 /*yield*/, page.route('**/api/v1/segments/project/*', function (route) { return __awaiter(void 0, void 0, void 0, function () {
                            var segmentsWithVideo;
                            return __generator(this, function (_a) {
                                switch (_a.label) {
                                    case 0:
                                        segmentsWithVideo = [
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
                                        return [4 /*yield*/, route.fulfill({
                                                status: 200,
                                                contentType: 'application/json',
                                                body: JSON.stringify(segmentsWithVideo),
                                            })];
                                    case 1:
                                        _a.sent();
                                        return [2 /*return*/];
                                }
                            });
                        }); })];
                case 5:
                    // Mock segments with one already generated (has videoUrl)
                    _c.sent();
                    // Create project and generate plan
                    return [4 /*yield*/, page.goto('/projects/new')];
                case 6:
                    // Create project and generate plan
                    _c.sent();
                    return [4 /*yield*/, page.fill('[data-testid="project-name"]', 'Video Playback Test')];
                case 7:
                    _c.sent();
                    return [4 /*yield*/, page.fill('[data-testid="story-prompt"]', 'A mountain adventure')];
                case 8:
                    _c.sent();
                    return [4 /*yield*/, page.click('[data-testid="create-button"]')];
                case 9:
                    _c.sent();
                    return [4 /*yield*/, page.waitForURL(/\/projects\/[\w-]+$/)];
                case 10:
                    _c.sent();
                    // Upload media
                    return [4 /*yield*/, page.locator('[data-testid="file-input-image"]').setInputFiles('./e2e/fixtures/first-frame.jpg')];
                case 11:
                    // Upload media
                    _c.sent();
                    return [4 /*yield*/, expect(page.locator('img[alt="Preview"]')).toBeVisible({ timeout: 30000 })];
                case 12:
                    _c.sent();
                    return [4 /*yield*/, page.locator('[data-testid="file-input-audio"]').setInputFiles('./e2e/fixtures/test-audio.mp3')];
                case 13:
                    _c.sent();
                    // Clone voice and generate plan
                    return [4 /*yield*/, page.click('[data-testid="clone-voice-button"]')];
                case 14:
                    // Clone voice and generate plan
                    _c.sent();
                    return [4 /*yield*/, expect(page.locator('[data-testid="generate-plan-button"]')).toBeEnabled({
                            timeout: 60000,
                        })];
                case 15:
                    _c.sent();
                    return [4 /*yield*/, page.click('[data-testid="generate-plan-button"]')];
                case 16:
                    _c.sent();
                    // Wait for segments
                    return [4 /*yield*/, expect(page.locator('[data-testid="segment-card-0"]')).toBeVisible({
                            timeout: 60000,
                        })];
                case 17:
                    // Wait for segments
                    _c.sent();
                    firstSegment = page.locator('[data-testid="segment-card-0"]');
                    videoPlayer = firstSegment.locator('[data-testid="segment-video"]');
                    return [4 /*yield*/, expect(videoPlayer).toBeVisible({ timeout: 10000 })];
                case 18:
                    _c.sent();
                    return [4 /*yield*/, videoPlayer.getAttribute('src')];
                case 19:
                    videoSrc = _c.sent();
                    expect(videoSrc).toBe(MINIMAX_MOCK_RESPONSES.chainedVideoGeneration.segment1.download_url);
                    // Verify video has controls
                    return [4 /*yield*/, expect(videoPlayer).toHaveAttribute('controls', '')];
                case 20:
                    // Verify video has controls
                    _c.sent();
                    // Verify "Approve Video" button is visible for generated segment
                    return [4 /*yield*/, expect(firstSegment.locator('[data-testid="approve-video-button"]')).toBeVisible()];
                case 21:
                    // Verify "Approve Video" button is visible for generated segment
                    _c.sent();
                    return [2 /*return*/];
            }
        });
    }); });
    test('should display final video after project finalization', function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
        var finalVideo, videoSrc;
        var page = _b.page;
        return __generator(this, function (_c) {
            switch (_c.label) {
                case 0: 
                // Setup mocks
                return [4 /*yield*/, mocks.mockVoiceClone()];
                case 1:
                    // Setup mocks
                    _c.sent();
                    return [4 /*yield*/, mocks.mockGeneratePlan()];
                case 2:
                    _c.sent();
                    return [4 /*yield*/, mocks.mockUpdateSegment()];
                case 3:
                    _c.sent();
                    return [4 /*yield*/, mocks.mockApproveSegment()];
                case 4:
                    _c.sent();
                    // Mock segments - all approved
                    return [4 /*yield*/, page.route('**/api/v1/segments/project/*', function (route) { return __awaiter(void 0, void 0, void 0, function () {
                            var allApprovedSegments;
                            return __generator(this, function (_a) {
                                switch (_a.label) {
                                    case 0:
                                        allApprovedSegments = BACKEND_MOCK_RESPONSES.generatePlan.segments.map(function (seg, idx) {
                                            var _a, _b;
                                            return ({
                                                id: "seg-".concat(idx + 1),
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
                                                videoUrl: ((_a = MINIMAX_MOCK_RESPONSES.chainedVideoGeneration["segment".concat(idx + 1)]) === null || _a === void 0 ? void 0 : _a.download_url) || null,
                                                audioUrl: "https://storage.example.com/audio/segment-".concat(idx + 1, ".mp3"),
                                                videoTaskId: ((_b = MINIMAX_MOCK_RESPONSES.chainedVideoGeneration["segment".concat(idx + 1)]) === null || _b === void 0 ? void 0 : _b.task_id) || null,
                                                createdAt: new Date().toISOString(),
                                                updatedAt: new Date().toISOString(),
                                            });
                                        });
                                        return [4 /*yield*/, route.fulfill({
                                                status: 200,
                                                contentType: 'application/json',
                                                body: JSON.stringify(allApprovedSegments),
                                            })];
                                    case 1:
                                        _a.sent();
                                        return [2 /*return*/];
                                }
                            });
                        }); })];
                case 5:
                    // Mock segments - all approved
                    _c.sent();
                    // Mock project with final video URL
                    return [4 /*yield*/, page.route('**/api/v1/projects/*', function (route) { return __awaiter(void 0, void 0, void 0, function () {
                            return __generator(this, function (_a) {
                                switch (_a.label) {
                                    case 0:
                                        if (!(route.request().method() === 'GET')) return [3 /*break*/, 2];
                                        return [4 /*yield*/, route.fulfill({
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
                                            })];
                                    case 1:
                                        _a.sent();
                                        return [3 /*break*/, 4];
                                    case 2: return [4 /*yield*/, route.continue()];
                                    case 3:
                                        _a.sent();
                                        _a.label = 4;
                                    case 4: return [2 /*return*/];
                                }
                            });
                        }); })];
                case 6:
                    // Mock project with final video URL
                    _c.sent();
                    // Navigate directly to project detail
                    return [4 /*yield*/, page.goto('/projects/project-123')];
                case 7:
                    // Navigate directly to project detail
                    _c.sent();
                    finalVideo = page.locator('[data-testid="final-video"]');
                    return [4 /*yield*/, expect(finalVideo).toBeVisible({ timeout: 30000 })];
                case 8:
                    _c.sent();
                    return [4 /*yield*/, finalVideo.getAttribute('src')];
                case 9:
                    videoSrc = _c.sent();
                    expect(videoSrc).toBe('https://video-product.cdn.minimax.io/final/project-123.mp4');
                    // Verify video has controls
                    return [4 /*yield*/, expect(finalVideo).toHaveAttribute('controls', '')];
                case 10:
                    // Verify video has controls
                    _c.sent();
                    // Verify download button is visible
                    return [4 /*yield*/, expect(page.locator('[data-testid="download-button"]')).toBeVisible()];
                case 11:
                    // Verify download button is visible
                    _c.sent();
                    return [2 /*return*/];
            }
        });
    }); });
    test('should show all 3 segment videos with real MiniMax URLs', function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
        var videoUrls, i, segment, video, src;
        var page = _b.page;
        return __generator(this, function (_c) {
            switch (_c.label) {
                case 0: return [4 /*yield*/, mocks.mockVoiceClone()];
                case 1:
                    _c.sent();
                    return [4 /*yield*/, mocks.mockGeneratePlan()];
                case 2:
                    _c.sent();
                    return [4 /*yield*/, mocks.mockUpdateSegment()];
                case 3:
                    _c.sent();
                    return [4 /*yield*/, mocks.mockApproveSegment()];
                case 4:
                    _c.sent();
                    // Mock segments with all 3 videos generated (using real captured URLs)
                    return [4 /*yield*/, page.route('**/api/v1/segments/project/*', function (route) { return __awaiter(void 0, void 0, void 0, function () {
                            var segmentsWithAllVideos;
                            return __generator(this, function (_a) {
                                switch (_a.label) {
                                    case 0:
                                        segmentsWithAllVideos = [
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
                                        return [4 /*yield*/, route.fulfill({
                                                status: 200,
                                                contentType: 'application/json',
                                                body: JSON.stringify(segmentsWithAllVideos),
                                            })];
                                    case 1:
                                        _a.sent();
                                        return [2 /*return*/];
                                }
                            });
                        }); })];
                case 5:
                    // Mock segments with all 3 videos generated (using real captured URLs)
                    _c.sent();
                    // Create project
                    return [4 /*yield*/, page.goto('/projects/new')];
                case 6:
                    // Create project
                    _c.sent();
                    return [4 /*yield*/, page.fill('[data-testid="project-name"]', 'All Videos Test')];
                case 7:
                    _c.sent();
                    return [4 /*yield*/, page.fill('[data-testid="story-prompt"]', 'A mountain adventure')];
                case 8:
                    _c.sent();
                    return [4 /*yield*/, page.click('[data-testid="create-button"]')];
                case 9:
                    _c.sent();
                    return [4 /*yield*/, page.waitForURL(/\/projects\/[\w-]+$/)];
                case 10:
                    _c.sent();
                    // Upload media
                    return [4 /*yield*/, page.locator('[data-testid="file-input-image"]').setInputFiles('./e2e/fixtures/first-frame.jpg')];
                case 11:
                    // Upload media
                    _c.sent();
                    return [4 /*yield*/, expect(page.locator('img[alt="Preview"]')).toBeVisible({ timeout: 30000 })];
                case 12:
                    _c.sent();
                    return [4 /*yield*/, page.locator('[data-testid="file-input-audio"]').setInputFiles('./e2e/fixtures/test-audio.mp3')];
                case 13:
                    _c.sent();
                    // Clone voice and generate plan
                    return [4 /*yield*/, page.click('[data-testid="clone-voice-button"]')];
                case 14:
                    // Clone voice and generate plan
                    _c.sent();
                    return [4 /*yield*/, expect(page.locator('[data-testid="generate-plan-button"]')).toBeEnabled({
                            timeout: 60000,
                        })];
                case 15:
                    _c.sent();
                    return [4 /*yield*/, page.click('[data-testid="generate-plan-button"]')];
                case 16:
                    _c.sent();
                    // Wait for segments
                    return [4 /*yield*/, expect(page.locator('[data-testid="segment-card-0"]')).toBeVisible({
                            timeout: 60000,
                        })];
                case 17:
                    // Wait for segments
                    _c.sent();
                    videoUrls = [
                        MINIMAX_MOCK_RESPONSES.chainedVideoGeneration.segment1.download_url,
                        MINIMAX_MOCK_RESPONSES.chainedVideoGeneration.segment2.download_url,
                        MINIMAX_MOCK_RESPONSES.chainedVideoGeneration.segment3.download_url,
                    ];
                    i = 0;
                    _c.label = 18;
                case 18:
                    if (!(i < 3)) return [3 /*break*/, 22];
                    segment = page.locator("[data-testid=\"segment-card-".concat(i, "\"]"));
                    video = segment.locator('[data-testid="segment-video"]');
                    return [4 /*yield*/, expect(video).toBeVisible({ timeout: 10000 })];
                case 19:
                    _c.sent();
                    return [4 /*yield*/, video.getAttribute('src')];
                case 20:
                    src = _c.sent();
                    expect(src).toBe(videoUrls[i]);
                    _c.label = 21;
                case 21:
                    i++;
                    return [3 /*break*/, 18];
                case 22: return [2 /*return*/];
            }
        });
    }); });
    test('should display status badges correctly', function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
        var segment1, segment2, segment3;
        var page = _b.page;
        return __generator(this, function (_c) {
            switch (_c.label) {
                case 0: return [4 /*yield*/, mocks.mockVoiceClone()];
                case 1:
                    _c.sent();
                    return [4 /*yield*/, mocks.mockGeneratePlan()];
                case 2:
                    _c.sent();
                    return [4 /*yield*/, mocks.mockUpdateSegment()];
                case 3:
                    _c.sent();
                    return [4 /*yield*/, mocks.mockApproveSegment()];
                case 4:
                    _c.sent();
                    // Mock segments with different statuses
                    return [4 /*yield*/, page.route('**/api/v1/segments/project/*', function (route) { return __awaiter(void 0, void 0, void 0, function () {
                            var mixedStatusSegments;
                            return __generator(this, function (_a) {
                                switch (_a.label) {
                                    case 0:
                                        mixedStatusSegments = [
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
                                        return [4 /*yield*/, route.fulfill({
                                                status: 200,
                                                contentType: 'application/json',
                                                body: JSON.stringify(mixedStatusSegments),
                                            })];
                                    case 1:
                                        _a.sent();
                                        return [2 /*return*/];
                                }
                            });
                        }); })];
                case 5:
                    // Mock segments with different statuses
                    _c.sent();
                    // Create and setup project
                    return [4 /*yield*/, page.goto('/projects/new')];
                case 6:
                    // Create and setup project
                    _c.sent();
                    return [4 /*yield*/, page.fill('[data-testid="project-name"]', 'Status Badge Test')];
                case 7:
                    _c.sent();
                    return [4 /*yield*/, page.fill('[data-testid="story-prompt"]', 'Test story')];
                case 8:
                    _c.sent();
                    return [4 /*yield*/, page.click('[data-testid="create-button"]')];
                case 9:
                    _c.sent();
                    return [4 /*yield*/, page.waitForURL(/\/projects\/[\w-]+$/)];
                case 10:
                    _c.sent();
                    return [4 /*yield*/, page.locator('[data-testid="file-input-image"]').setInputFiles('./e2e/fixtures/first-frame.jpg')];
                case 11:
                    _c.sent();
                    return [4 /*yield*/, expect(page.locator('img[alt="Preview"]')).toBeVisible({ timeout: 30000 })];
                case 12:
                    _c.sent();
                    return [4 /*yield*/, page.locator('[data-testid="file-input-audio"]').setInputFiles('./e2e/fixtures/test-audio.mp3')];
                case 13:
                    _c.sent();
                    return [4 /*yield*/, page.click('[data-testid="clone-voice-button"]')];
                case 14:
                    _c.sent();
                    return [4 /*yield*/, expect(page.locator('[data-testid="generate-plan-button"]')).toBeEnabled({
                            timeout: 60000,
                        })];
                case 15:
                    _c.sent();
                    return [4 /*yield*/, page.click('[data-testid="generate-plan-button"]')];
                case 16:
                    _c.sent();
                    // Wait for segments
                    return [4 /*yield*/, expect(page.locator('[data-testid="segment-card-0"]')).toBeVisible({
                            timeout: 60000,
                        })];
                case 17:
                    // Wait for segments
                    _c.sent();
                    segment1 = page.locator('[data-testid="segment-card-0"]');
                    return [4 /*yield*/, expect(segment1.getByText('Approved')).toBeVisible()];
                case 18:
                    _c.sent();
                    segment2 = page.locator('[data-testid="segment-card-1"]');
                    return [4 /*yield*/, expect(segment2.getByText('Generating Video')).toBeVisible()];
                case 19:
                    _c.sent();
                    return [4 /*yield*/, expect(segment2.getByText('Generating...')).toBeVisible()];
                case 20:
                    _c.sent(); // Spinner text
                    segment3 = page.locator('[data-testid="segment-card-2"]');
                    return [4 /*yield*/, expect(segment3.getByText('Prompt Ready')).toBeVisible()];
                case 21:
                    _c.sent();
                    return [2 /*return*/];
            }
        });
    }); });
});
