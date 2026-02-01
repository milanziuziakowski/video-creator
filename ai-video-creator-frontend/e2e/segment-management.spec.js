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
test.describe('Segment Management', function () {
    test.beforeEach(function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
        var mocks;
        var page = _b.page;
        return __generator(this, function (_c) {
            switch (_c.label) {
                case 0:
                    mocks = setupMinimaxMocks(page);
                    return [4 /*yield*/, mocks.mockAll()];
                case 1:
                    _c.sent();
                    // Create a project
                    return [4 /*yield*/, page.goto('/projects/new')];
                case 2:
                    // Create a project
                    _c.sent();
                    return [4 /*yield*/, page.fill('[data-testid="project-name"]', 'Segment Test Project')];
                case 3:
                    _c.sent();
                    return [4 /*yield*/, page.fill('[data-testid="story-prompt"]', 'A mountain adventure')];
                case 4:
                    _c.sent();
                    return [4 /*yield*/, page.click('[data-testid="create-button"]')];
                case 5:
                    _c.sent();
                    return [4 /*yield*/, page.waitForURL(/\/projects\/[\w-]+$/)];
                case 6:
                    _c.sent();
                    // Upload first frame and audio
                    return [4 /*yield*/, page.locator('[data-testid="file-input-image"]').setInputFiles('./e2e/fixtures/test-image.jpg')];
                case 7:
                    // Upload first frame and audio
                    _c.sent();
                    return [4 /*yield*/, expect(page.locator('img[alt="Preview"]')).toBeVisible({
                            timeout: 30000,
                        })];
                case 8:
                    _c.sent();
                    return [4 /*yield*/, page.locator('[data-testid="file-input-audio"]').setInputFiles('./e2e/fixtures/test-audio.mp3')];
                case 9:
                    _c.sent();
                    return [4 /*yield*/, expect(page.locator('audio')).toBeVisible({ timeout: 30000 })];
                case 10:
                    _c.sent();
                    // Clone voice and generate plan
                    return [4 /*yield*/, page.click('[data-testid="clone-voice-button"]')];
                case 11:
                    // Clone voice and generate plan
                    _c.sent();
                    return [4 /*yield*/, expect(page.locator('[data-testid="generate-plan-button"]')).toBeEnabled({
                            timeout: 60000,
                        })];
                case 12:
                    _c.sent();
                    return [4 /*yield*/, page.click('[data-testid="generate-plan-button"]')];
                case 13:
                    _c.sent();
                    // Wait for segments to appear
                    return [4 /*yield*/, expect(page.locator('[data-testid="segment-card-0"]')).toBeVisible({
                            timeout: 60000,
                        })];
                case 14:
                    // Wait for segments to appear
                    _c.sent();
                    return [2 /*return*/];
            }
        });
    }); });
    test('should display generated segments', function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
        var segments, count, firstSegment;
        var page = _b.page;
        return __generator(this, function (_c) {
            switch (_c.label) {
                case 0:
                    segments = page.locator('[data-testid^="segment-card-"]');
                    return [4 /*yield*/, segments.count()];
                case 1:
                    count = _c.sent();
                    expect(count).toBeGreaterThan(0);
                    expect(count).toBeLessThanOrEqual(10);
                    firstSegment = segments.first();
                    return [4 /*yield*/, expect(firstSegment.getByText('Video Prompt')).toBeVisible()];
                case 2:
                    _c.sent();
                    return [4 /*yield*/, expect(firstSegment.getByText('Narration')).toBeVisible()];
                case 3:
                    _c.sent();
                    return [2 /*return*/];
            }
        });
    }); });
    test('should edit segment prompt and narration', function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
        var firstSegment, promptInput, narrationInput;
        var page = _b.page;
        return __generator(this, function (_c) {
            switch (_c.label) {
                case 0:
                    firstSegment = page.locator('[data-testid="segment-card-0"]');
                    return [4 /*yield*/, firstSegment.locator('[data-testid="edit-button"]').click()];
                case 1:
                    _c.sent();
                    promptInput = firstSegment.locator('textarea').nth(0);
                    narrationInput = firstSegment.locator('textarea').nth(1);
                    return [4 /*yield*/, promptInput.fill('Edited prompt: A climber reaches the summit')];
                case 2:
                    _c.sent();
                    return [4 /*yield*/, narrationInput.fill('Edited narration for the segment.')];
                case 3:
                    _c.sent();
                    return [4 /*yield*/, firstSegment.getByRole('button', { name: 'Save' }).click()];
                case 4:
                    _c.sent();
                    return [4 /*yield*/, expect(firstSegment).toContainText('Edited prompt: A climber reaches the summit')];
                case 5:
                    _c.sent();
                    return [4 /*yield*/, expect(firstSegment).toContainText('Edited narration for the segment.')];
                case 6:
                    _c.sent();
                    return [2 /*return*/];
            }
        });
    }); });
    test('should approve a segment', function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
        var firstSegment;
        var page = _b.page;
        return __generator(this, function (_c) {
            switch (_c.label) {
                case 0:
                    firstSegment = page.locator('[data-testid="segment-card-0"]');
                    return [4 /*yield*/, firstSegment.locator('[data-testid="approve-button"]').click()];
                case 1:
                    _c.sent();
                    // After approval, the Generate button should appear
                    return [4 /*yield*/, expect(firstSegment.locator('[data-testid="generate-button"]')).toBeVisible({
                            timeout: 30000,
                        })];
                case 2:
                    // After approval, the Generate button should appear
                    _c.sent();
                    return [2 /*return*/];
            }
        });
    }); });
});
