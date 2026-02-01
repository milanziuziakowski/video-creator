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
import { test as setup, expect } from '@playwright/test';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
var __filename = fileURLToPath(import.meta.url);
var __dirname = path.dirname(__filename);
var authFile = path.join(__dirname, '../.auth/user.json');
/**
 * Authentication setup for E2E tests.
 *
 * Since this app uses JWT token-based authentication,
 * we'll create a mock login flow for testing purposes.
 *
 * In a real scenario, you would:
 * 1. Call the /auth/login endpoint with test credentials
 * 2. Store the returned JWT token in localStorage
 * 3. Save the authenticated state for reuse in tests
 */
setup('authenticate', function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
    var useMockAuth, testEmail, testPassword;
    var page = _b.page, request = _b.request;
    return __generator(this, function (_c) {
        switch (_c.label) {
            case 0:
                useMockAuth = process.env.E2E_MOCK_AUTH !== 'false';
                if (!useMockAuth) return [3 /*break*/, 5];
                console.log('Using mock authentication for E2E tests');
                // Navigate to the app
                return [4 /*yield*/, page.goto('/')];
            case 1:
                // Navigate to the app
                _c.sent();
                // Set mock JWT token in localStorage
                return [4 /*yield*/, page.evaluate(function () {
                        var mockToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItaWQiLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIiwiZXhwIjo5OTk5OTk5OTk5fQ.mock_signature';
                        localStorage.setItem('access_token', mockToken);
                    })];
            case 2:
                // Set mock JWT token in localStorage
                _c.sent();
                // Verify we can access protected routes
                return [4 /*yield*/, page.goto('/dashboard')];
            case 3:
                // Verify we can access protected routes
                _c.sent();
                return [4 /*yield*/, expect(page).toHaveURL('/dashboard')];
            case 4:
                _c.sent();
                return [3 /*break*/, 12];
            case 5:
                console.log('Using real authentication for E2E tests');
                testEmail = process.env.E2E_TEST_EMAIL;
                testPassword = process.env.E2E_TEST_PASSWORD;
                if (!testEmail || !testPassword) {
                    throw new Error('E2E_TEST_EMAIL and E2E_TEST_PASSWORD must be set for real authentication');
                }
                // Navigate to login page
                return [4 /*yield*/, page.goto('/login')];
            case 6:
                // Navigate to login page
                _c.sent();
                // Fill in credentials
                return [4 /*yield*/, page.fill('[data-testid="email-input"]', testEmail)];
            case 7:
                // Fill in credentials
                _c.sent();
                return [4 /*yield*/, page.fill('[data-testid="password-input"]', testPassword)];
            case 8:
                _c.sent();
                // Submit login form
                return [4 /*yield*/, page.click('[data-testid="login-button"]')];
            case 9:
                // Submit login form
                _c.sent();
                // Wait for redirect to dashboard
                return [4 /*yield*/, page.waitForURL('/dashboard', { timeout: 10000 })];
            case 10:
                // Wait for redirect to dashboard
                _c.sent();
                // Verify we're logged in
                return [4 /*yield*/, expect(page.locator('[data-testid="user-menu"]')).toBeVisible()];
            case 11:
                // Verify we're logged in
                _c.sent();
                _c.label = 12;
            case 12: 
            // Save authentication state for reuse
            return [4 /*yield*/, fs.mkdir(path.dirname(authFile), { recursive: true })];
            case 13:
                // Save authentication state for reuse
                _c.sent();
                return [4 /*yield*/, page.context().storageState({ path: authFile })];
            case 14:
                _c.sent();
                console.log('Authentication setup complete');
                return [2 /*return*/];
        }
    });
}); });
