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
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { chromium } from '@playwright/test';
var __filename = fileURLToPath(import.meta.url);
var __dirname = path.dirname(__filename);
var authFile = path.join(__dirname, '../.auth/user.json');
function globalSetup(config) {
    return __awaiter(this, void 0, void 0, function () {
        var baseURL, browser, context, page, useMockAuth, testEmail, testPassword;
        var _a, _b;
        return __generator(this, function (_c) {
            switch (_c.label) {
                case 0:
                    baseURL = ((_b = (_a = config.projects[0]) === null || _a === void 0 ? void 0 : _a.use) === null || _b === void 0 ? void 0 : _b.baseURL) ||
                        process.env.BASE_URL ||
                        'http://localhost:5173';
                    return [4 /*yield*/, fs.mkdir(path.dirname(authFile), { recursive: true })];
                case 1:
                    _c.sent();
                    return [4 /*yield*/, chromium.launch()];
                case 2:
                    browser = _c.sent();
                    return [4 /*yield*/, browser.newContext()];
                case 3:
                    context = _c.sent();
                    return [4 /*yield*/, context.newPage()];
                case 4:
                    page = _c.sent();
                    useMockAuth = process.env.E2E_MOCK_AUTH !== 'false';
                    if (!useMockAuth) return [3 /*break*/, 7];
                    return [4 /*yield*/, page.goto(baseURL, { waitUntil: 'domcontentloaded' })];
                case 5:
                    _c.sent();
                    return [4 /*yield*/, page.evaluate(function () {
                            // Use the backend's development token which bypasses JWT validation
                            var devToken = 'dev-token';
                            localStorage.setItem('access_token', devToken);
                        })];
                case 6:
                    _c.sent();
                    return [3 /*break*/, 13];
                case 7:
                    testEmail = process.env.E2E_TEST_EMAIL;
                    testPassword = process.env.E2E_TEST_PASSWORD;
                    if (!testEmail || !testPassword) {
                        throw new Error('E2E_TEST_EMAIL and E2E_TEST_PASSWORD must be set for real authentication');
                    }
                    return [4 /*yield*/, page.goto("".concat(baseURL, "/login"), { waitUntil: 'domcontentloaded' })];
                case 8:
                    _c.sent();
                    return [4 /*yield*/, page.fill('[data-testid="email-input"]', testEmail)];
                case 9:
                    _c.sent();
                    return [4 /*yield*/, page.fill('[data-testid="password-input"]', testPassword)];
                case 10:
                    _c.sent();
                    return [4 /*yield*/, page.click('[data-testid="login-button"]')];
                case 11:
                    _c.sent();
                    return [4 /*yield*/, page.waitForURL("".concat(baseURL, "/dashboard"), { timeout: 10000 })];
                case 12:
                    _c.sent();
                    _c.label = 13;
                case 13: return [4 /*yield*/, context.storageState({ path: authFile })];
                case 14:
                    _c.sent();
                    return [4 /*yield*/, browser.close()];
                case 15:
                    _c.sent();
                    return [2 /*return*/];
            }
        });
    });
}
export default globalSetup;
