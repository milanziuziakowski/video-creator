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
test.describe('Project Creation', function () {
    test('should create a new project successfully', function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
        var page = _b.page;
        return __generator(this, function (_c) {
            switch (_c.label) {
                case 0: 
                // Navigate to dashboard
                return [4 /*yield*/, page.goto('/dashboard')];
                case 1:
                    // Navigate to dashboard
                    _c.sent();
                    // Click "Create New Project" button
                    return [4 /*yield*/, page.click('[data-testid="create-project-button"]')];
                case 2:
                    // Click "Create New Project" button
                    _c.sent();
                    // Verify we're on the new project page
                    return [4 /*yield*/, expect(page).toHaveURL('/projects/new')];
                case 3:
                    // Verify we're on the new project page
                    _c.sent();
                    return [4 /*yield*/, expect(page.locator('h1')).toContainText('Create New Project')];
                case 4:
                    _c.sent();
                    // Fill in project details
                    return [4 /*yield*/, page.fill('[data-testid="project-name"]', 'E2E Test Project')];
                case 5:
                    // Fill in project details
                    _c.sent();
                    return [4 /*yield*/, page.fill('[data-testid="story-prompt"]', 'A peaceful journey through the mountains at sunrise')];
                case 6:
                    _c.sent();
                    // Select target duration
                    return [4 /*yield*/, page.selectOption('[data-testid="target-duration"]', '30')];
                case 7:
                    // Select target duration
                    _c.sent();
                    // Submit form
                    return [4 /*yield*/, page.click('[data-testid="create-button"]')];
                case 8:
                    // Submit form
                    _c.sent();
                    // Wait for redirect to project detail page
                    return [4 /*yield*/, page.waitForURL(/\/projects\/[\w-]+$/, { timeout: 10000 })];
                case 9:
                    // Wait for redirect to project detail page
                    _c.sent();
                    // Verify project was created
                    return [4 /*yield*/, expect(page.locator('h1')).toContainText('E2E Test Project')];
                case 10:
                    // Verify project was created
                    _c.sent();
                    return [2 /*return*/];
            }
        });
    }); });
    test('should require project name', function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
        var page = _b.page;
        return __generator(this, function (_c) {
            switch (_c.label) {
                case 0: return [4 /*yield*/, page.goto('/projects/new')];
                case 1:
                    _c.sent();
                    // Submit should be disabled until name is provided
                    return [4 /*yield*/, expect(page.locator('[data-testid="create-button"]')).toBeDisabled()];
                case 2:
                    // Submit should be disabled until name is provided
                    _c.sent();
                    return [4 /*yield*/, page.fill('[data-testid="project-name"]', 'Required Name')];
                case 3:
                    _c.sent();
                    return [4 /*yield*/, expect(page.locator('[data-testid="create-button"]')).toBeEnabled()];
                case 4:
                    _c.sent();
                    return [2 /*return*/];
            }
        });
    }); });
    test('should upload first frame image', function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
        var fileInput;
        var page = _b.page;
        return __generator(this, function (_c) {
            switch (_c.label) {
                case 0: 
                // Create a project first
                return [4 /*yield*/, page.goto('/projects/new')];
                case 1:
                    // Create a project first
                    _c.sent();
                    return [4 /*yield*/, page.fill('[data-testid="project-name"]', 'Image Upload Test')];
                case 2:
                    _c.sent();
                    return [4 /*yield*/, page.click('[data-testid="create-button"]')];
                case 3:
                    _c.sent();
                    return [4 /*yield*/, page.waitForURL(/\/projects\/[\w-]+$/)];
                case 4:
                    _c.sent();
                    fileInput = page.locator('[data-testid="file-input-image"]');
                    // Upload test image
                    return [4 /*yield*/, fileInput.setInputFiles('./e2e/fixtures/test-image.jpg')];
                case 5:
                    // Upload test image
                    _c.sent();
                    // Verify image preview is shown
                    return [4 /*yield*/, expect(page.locator('img[alt="Preview"]')).toBeVisible({
                            timeout: 30000,
                        })];
                case 6:
                    // Verify image preview is shown
                    _c.sent();
                    return [2 /*return*/];
            }
        });
    }); });
    test('should upload audio sample', function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
        var audioInput;
        var page = _b.page;
        return __generator(this, function (_c) {
            switch (_c.label) {
                case 0: 
                // Create a project first
                return [4 /*yield*/, page.goto('/projects/new')];
                case 1:
                    // Create a project first
                    _c.sent();
                    return [4 /*yield*/, page.fill('[data-testid="project-name"]', 'Audio Upload Test')];
                case 2:
                    _c.sent();
                    return [4 /*yield*/, page.click('[data-testid="create-button"]')];
                case 3:
                    _c.sent();
                    return [4 /*yield*/, page.waitForURL(/\/projects\/[\w-]+$/)];
                case 4:
                    _c.sent();
                    audioInput = page.locator('[data-testid="file-input-audio"]');
                    return [4 /*yield*/, audioInput.setInputFiles('./e2e/fixtures/test-audio.mp3')];
                case 5:
                    _c.sent();
                    // Verify audio player is shown
                    return [4 /*yield*/, expect(page.locator('audio')).toBeVisible({ timeout: 30000 })];
                case 6:
                    // Verify audio player is shown
                    _c.sent();
                    return [2 /*return*/];
            }
        });
    }); });
    test('should generate story plan with AI', function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
        var mocks;
        var page = _b.page;
        return __generator(this, function (_c) {
            switch (_c.label) {
                case 0:
                    mocks = setupMinimaxMocks(page);
                    return [4 /*yield*/, mocks.mockVoiceClone()];
                case 1:
                    _c.sent();
                    return [4 /*yield*/, mocks.mockGeneratePlan()];
                case 2:
                    _c.sent();
                    // Create a project first
                    return [4 /*yield*/, page.goto('/projects/new')];
                case 3:
                    // Create a project first
                    _c.sent();
                    return [4 /*yield*/, page.fill('[data-testid="project-name"]', 'AI Story Test')];
                case 4:
                    _c.sent();
                    return [4 /*yield*/, page.fill('[data-testid="story-prompt"]', 'A futuristic city at night')];
                case 5:
                    _c.sent();
                    return [4 /*yield*/, page.click('[data-testid="create-button"]')];
                case 6:
                    _c.sent();
                    return [4 /*yield*/, page.waitForURL(/\/projects\/[\w-]+$/)];
                case 7:
                    _c.sent();
                    // Upload first frame and audio
                    return [4 /*yield*/, page.locator('[data-testid="file-input-image"]').setInputFiles('./e2e/fixtures/test-image.jpg')];
                case 8:
                    // Upload first frame and audio
                    _c.sent();
                    return [4 /*yield*/, expect(page.locator('img[alt="Preview"]')).toBeVisible({
                            timeout: 30000,
                        })];
                case 9:
                    _c.sent();
                    return [4 /*yield*/, page.locator('[data-testid="file-input-audio"]').setInputFiles('./e2e/fixtures/test-audio.mp3')];
                case 10:
                    _c.sent();
                    return [4 /*yield*/, expect(page.locator('audio')).toBeVisible({ timeout: 30000 })];
                case 11:
                    _c.sent();
                    // Clone voice (mocked - no real API call)
                    return [4 /*yield*/, page.click('[data-testid="clone-voice-button"]')];
                case 12:
                    // Clone voice (mocked - no real API call)
                    _c.sent();
                    return [4 /*yield*/, expect(page.locator('[data-testid="generate-plan-button"]')).toBeEnabled({
                            timeout: 60000,
                        })];
                case 13:
                    _c.sent();
                    // Generate plan (mocked - no real API call)
                    return [4 /*yield*/, page.click('[data-testid="generate-plan-button"]')];
                case 14:
                    // Generate plan (mocked - no real API call)
                    _c.sent();
                    // Verify segments were created (from mocked response)
                    return [4 /*yield*/, expect(page.locator('[data-testid="segment-card-0"]')).toBeVisible({
                            timeout: 60000,
                        })];
                case 15:
                    // Verify segments were created (from mocked response)
                    _c.sent();
                    return [2 /*return*/];
            }
        });
    }); });
});
