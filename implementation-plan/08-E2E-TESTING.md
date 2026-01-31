# E2E Testing Guide

**Phase:** 8  
**Technology:** Playwright, Pytest, Mock Services

---

## 1. Overview

End-to-end testing validates the complete user workflow from frontend through backend to external APIs. This guide covers:

- Playwright setup for frontend E2E tests
- API integration tests with mocked external services
- Test data management
- CI integration

```
┌─────────────────────────────────────────────────────────────────────┐
│                         E2E Test Architecture                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐                                                    │
│  │  Playwright  │──────────────────────────────────────┐            │
│  │   Browser    │                                       │            │
│  └──────────────┘                                       │            │
│         │                                               │            │
│         ▼                                               ▼            │
│  ┌──────────────┐    HTTP    ┌──────────────┐    ┌──────────────┐  │
│  │   Frontend   │───────────▶│   Backend    │───▶│ Mock Server  │  │
│  │  (Vite Dev)  │            │  (FastAPI)   │    │  (MiniMax,   │  │
│  └──────────────┘            └──────────────┘    │   OpenAI)    │  │
│                                     │            └──────────────┘  │
│                                     ▼                               │
│                              ┌──────────────┐                       │
│                              │   Test DB    │                       │
│                              │ (PostgreSQL) │                       │
│                              └──────────────┘                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Playwright Setup

### 2.1 Installation

```bash
cd frontend

# Install Playwright
npm install -D @playwright/test

# Install browsers
npx playwright install chromium firefox webkit
```

### 2.2 Configuration (playwright.config.ts)

```typescript
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ["html", { open: "never" }],
    ["json", { outputFile: "test-results/results.json" }],
    process.env.CI ? ["github"] : ["list"],
  ],
  
  use: {
    baseURL: process.env.BASE_URL || "http://localhost:5173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },

  projects: [
    // Auth setup (runs once before all tests)
    {
      name: "setup",
      testMatch: /.*\.setup\.ts/,
    },
    
    // Desktop browsers
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
      dependencies: ["setup"],
    },
    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
      dependencies: ["setup"],
    },
    {
      name: "webkit",
      use: { ...devices["Desktop Safari"] },
      dependencies: ["setup"],
    },
    
    // Mobile viewports
    {
      name: "mobile-chrome",
      use: { ...devices["Pixel 5"] },
      dependencies: ["setup"],
    },
  ],

  // Dev server configuration
  webServer: [
    {
      command: "npm run dev",
      url: "http://localhost:5173",
      reuseExistingServer: !process.env.CI,
    },
  ],
});
```

### 2.3 Authentication Setup (e2e/auth.setup.ts)

```typescript
import { test as setup, expect } from "@playwright/test";
import path from "path";

const authFile = path.join(__dirname, "../.auth/user.json");

/**
 * Since we use Azure Entra ID, we need to handle authentication
 * differently in E2E tests. Options:
 * 
 * 1. Mock authentication (recommended for CI)
 * 2. Use test tenant with test user
 * 3. Store authenticated state from manual login
 */

setup("authenticate", async ({ page }) => {
  // Option 1: Mock authentication for testing
  // The frontend should check for a test mode and skip MSAL
  
  if (process.env.E2E_MOCK_AUTH === "true") {
    // Set mock auth cookie/storage
    await page.goto("/");
    await page.evaluate(() => {
      // Set mock user in session storage
      sessionStorage.setItem(
        "msal.account.keys",
        JSON.stringify(["test-account-key"])
      );
      sessionStorage.setItem(
        "test-account-key",
        JSON.stringify({
          homeAccountId: "test-home-account-id",
          environment: "login.microsoftonline.com",
          tenantId: "test-tenant-id",
          username: "test@example.com",
          localAccountId: "test-local-account-id",
          name: "Test User",
        })
      );
    });
    
    await page.context().storageState({ path: authFile });
    return;
  }
  
  // Option 2: Real Azure login (for local development)
  // This requires manual intervention or a test user
  
  await page.goto("/login");
  
  // Wait for Azure login redirect
  await page.waitForURL(/login\.microsoftonline\.com/);
  
  // Fill in test credentials
  await page.fill('input[name="loginfmt"]', process.env.E2E_TEST_USER!);
  await page.click('input[type="submit"]');
  
  await page.waitForSelector('input[name="passwd"]');
  await page.fill('input[name="passwd"]', process.env.E2E_TEST_PASSWORD!);
  await page.click('input[type="submit"]');
  
  // Handle "Stay signed in?" prompt
  await page.click('input[value="No"]');
  
  // Wait for redirect back to app
  await page.waitForURL(/localhost/);
  
  // Verify we're logged in
  await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  
  // Save auth state
  await page.context().storageState({ path: authFile });
});
```

---

## 3. E2E Test Cases

### 3.1 Project Creation Flow (e2e/project-creation.spec.ts)

```typescript
import { test, expect } from "@playwright/test";

test.describe("Project Creation Flow", () => {
  test.use({ storageState: ".auth/user.json" });

  test("should create a new project", async ({ page }) => {
    // Go to dashboard
    await page.goto("/dashboard");
    
    // Click "New Project" button
    await page.click('[data-testid="new-project-button"]');
    
    // Verify we're on the new project page
    await expect(page).toHaveURL("/projects/new");
    
    // Fill in project details
    await page.fill('[data-testid="project-name-input"]', "E2E Test Project");
    await page.fill(
      '[data-testid="story-prompt-input"]',
      "A serene sunrise over mountain peaks"
    );
    
    // Select duration
    await page.selectOption('[data-testid="duration-select"]', "30");
    
    // Submit form
    await page.click('[data-testid="create-project-button"]');
    
    // Wait for redirect to project page
    await page.waitForURL(/\/projects\/[a-z0-9-]+$/);
    
    // Verify project was created
    await expect(page.locator('[data-testid="project-title"]')).toContainText(
      "E2E Test Project"
    );
    await expect(page.locator('[data-testid="project-status"]')).toContainText(
      "Created"
    );
  });

  test("should upload first frame image", async ({ page }) => {
    // Navigate to existing project
    await page.goto("/projects/test-project-id");
    
    // Click upload area
    const fileInput = page.locator('[data-testid="first-frame-upload"] input[type="file"]');
    
    // Upload test image
    await fileInput.setInputFiles("./e2e/fixtures/test-image.jpg");
    
    // Wait for upload to complete
    await expect(page.locator('[data-testid="upload-progress"]')).toBeHidden({
      timeout: 30000,
    });
    
    // Verify image preview is shown
    await expect(
      page.locator('[data-testid="first-frame-preview"] img')
    ).toBeVisible();
    
    // Verify status updated
    await expect(page.locator('[data-testid="project-status"]')).toContainText(
      "Media Uploaded"
    );
  });

  test("should upload audio sample and clone voice", async ({ page }) => {
    await page.goto("/projects/test-project-id");
    
    // Upload audio file
    const audioInput = page.locator(
      '[data-testid="audio-sample-upload"] input[type="file"]'
    );
    await audioInput.setInputFiles("./e2e/fixtures/test-audio.mp3");
    
    // Wait for upload
    await expect(page.locator('[data-testid="audio-upload-progress"]')).toBeHidden({
      timeout: 30000,
    });
    
    // Click "Clone Voice" button
    await page.click('[data-testid="clone-voice-button"]');
    
    // Wait for voice cloning to complete
    await expect(page.locator('[data-testid="voice-cloning-spinner"]')).toBeHidden({
      timeout: 60000,
    });
    
    // Verify voice ID is shown
    await expect(page.locator('[data-testid="voice-id"]')).toBeVisible();
  });
});
```

### 3.2 Video Plan Generation (e2e/video-plan.spec.ts)

```typescript
import { test, expect } from "@playwright/test";

test.describe("Video Plan Generation", () => {
  test.use({ storageState: ".auth/user.json" });

  test("should generate AI video plan", async ({ page }) => {
    // Navigate to project with uploaded media
    await page.goto("/projects/ready-project-id");
    
    // Click "Generate Plan" button
    await page.click('[data-testid="generate-plan-button"]');
    
    // Wait for plan generation (can take 10-30 seconds)
    await expect(page.locator('[data-testid="plan-generating-spinner"]')).toBeHidden({
      timeout: 60000,
    });
    
    // Verify segments are displayed
    const segments = page.locator('[data-testid="segment-card"]');
    await expect(segments).toHaveCount(5); // 30s / 6s = 5 segments
    
    // Verify first segment has content
    const firstSegment = segments.first();
    await expect(firstSegment.locator('[data-testid="video-prompt"]')).not.toBeEmpty();
    await expect(firstSegment.locator('[data-testid="narration-text"]')).not.toBeEmpty();
  });

  test("should edit segment prompt", async ({ page }) => {
    await page.goto("/projects/plan-ready-project-id");
    
    // Click edit on first segment
    await page.click('[data-testid="segment-card"]:first-child [data-testid="edit-button"]');
    
    // Modify the prompt
    const promptInput = page.locator('[data-testid="video-prompt-input"]');
    await promptInput.clear();
    await promptInput.fill("A dramatic close-up of a golden sunrise");
    
    // Save changes
    await page.click('[data-testid="save-segment-button"]');
    
    // Verify changes were saved
    await expect(
      page.locator('[data-testid="segment-card"]:first-child [data-testid="video-prompt"]')
    ).toContainText("dramatic close-up");
  });

  test("should approve segment for generation", async ({ page }) => {
    await page.goto("/projects/plan-ready-project-id");
    
    // Approve first segment
    await page.click(
      '[data-testid="segment-card"]:first-child [data-testid="approve-button"]'
    );
    
    // Verify approval badge
    await expect(
      page.locator('[data-testid="segment-card"]:first-child [data-testid="status-badge"]')
    ).toContainText("Approved");
    
    // Verify "Generate" button becomes available
    await expect(
      page.locator('[data-testid="segment-card"]:first-child [data-testid="generate-button"]')
    ).toBeEnabled();
  });
});
```

### 3.3 Video Generation Flow (e2e/video-generation.spec.ts)

```typescript
import { test, expect } from "@playwright/test";

test.describe("Video Generation", () => {
  test.use({ storageState: ".auth/user.json" });

  // This test should use mocked MiniMax API responses
  test("should generate video for approved segment", async ({ page }) => {
    await page.goto("/projects/approved-segment-project-id");
    
    // Click generate on first approved segment
    await page.click(
      '[data-testid="segment-card"]:first-child [data-testid="generate-button"]'
    );
    
    // Verify loading state
    await expect(
      page.locator('[data-testid="segment-card"]:first-child [data-testid="generating-indicator"]')
    ).toBeVisible();
    
    // Wait for generation to complete (mocked - should be fast)
    await expect(
      page.locator('[data-testid="segment-card"]:first-child [data-testid="generating-indicator"]')
    ).toBeHidden({ timeout: 120000 }); // 2 minutes max
    
    // Verify video preview is shown
    await expect(
      page.locator('[data-testid="segment-card"]:first-child video')
    ).toBeVisible();
    
    // Verify status updated
    await expect(
      page.locator('[data-testid="segment-card"]:first-child [data-testid="status-badge"]')
    ).toContainText("Generated");
  });

  test("should show generation progress", async ({ page }) => {
    await page.goto("/projects/generating-project-id");
    
    // Verify progress indicator is visible during generation
    const progressBar = page.locator('[data-testid="generation-progress"]');
    await expect(progressBar).toBeVisible();
    
    // Progress should update
    const initialProgress = await progressBar.getAttribute("aria-valuenow");
    await page.waitForTimeout(5000);
    const updatedProgress = await progressBar.getAttribute("aria-valuenow");
    
    // Note: With mocked API, progress might not actually change
    // This test is more relevant with real API
    expect(Number(updatedProgress)).toBeGreaterThanOrEqual(Number(initialProgress));
  });
});
```

### 3.4 Complete Workflow Test (e2e/complete-workflow.spec.ts)

```typescript
import { test, expect } from "@playwright/test";

test.describe("Complete Video Creation Workflow", () => {
  test.use({ storageState: ".auth/user.json" });
  
  // Long-running test - only run in CI with proper timeouts
  test.setTimeout(300000); // 5 minutes

  test("should complete full workflow from creation to final video", async ({
    page,
  }) => {
    // 1. Create project
    await page.goto("/dashboard");
    await page.click('[data-testid="new-project-button"]');
    
    await page.fill('[data-testid="project-name-input"]', "Full Workflow Test");
    await page.fill('[data-testid="story-prompt-input"]', "Ocean waves at sunset");
    await page.selectOption('[data-testid="duration-select"]', "12"); // 2 segments
    await page.click('[data-testid="create-project-button"]');
    
    await page.waitForURL(/\/projects\/[a-z0-9-]+$/);
    const projectUrl = page.url();
    
    // 2. Upload media
    const imageInput = page.locator('[data-testid="first-frame-upload"] input');
    await imageInput.setInputFiles("./e2e/fixtures/test-image.jpg");
    await expect(page.locator('[data-testid="first-frame-preview"]')).toBeVisible({
      timeout: 30000,
    });
    
    const audioInput = page.locator('[data-testid="audio-sample-upload"] input');
    await audioInput.setInputFiles("./e2e/fixtures/test-audio.mp3");
    await expect(page.locator('[data-testid="audio-preview"]')).toBeVisible({
      timeout: 30000,
    });
    
    // 3. Clone voice
    await page.click('[data-testid="clone-voice-button"]');
    await expect(page.locator('[data-testid="voice-id"]')).toBeVisible({
      timeout: 60000,
    });
    
    // 4. Generate plan
    await page.click('[data-testid="generate-plan-button"]');
    await expect(page.locator('[data-testid="segment-card"]')).toHaveCount(2, {
      timeout: 60000,
    });
    
    // 5. Approve all segments
    const approveButtons = page.locator('[data-testid="approve-button"]');
    await approveButtons.first().click();
    await approveButtons.last().click();
    
    // 6. Generate all segments
    const generateButtons = page.locator('[data-testid="generate-button"]');
    await generateButtons.first().click();
    await expect(
      page.locator('[data-testid="segment-card"]:first-child video')
    ).toBeVisible({ timeout: 120000 });
    
    await generateButtons.last().click();
    await expect(
      page.locator('[data-testid="segment-card"]:last-child video')
    ).toBeVisible({ timeout: 120000 });
    
    // 7. Approve generated segments
    const segmentApproveButtons = page.locator('[data-testid="approve-segment-button"]');
    await segmentApproveButtons.first().click();
    await segmentApproveButtons.last().click();
    
    // 8. Finalize project
    await page.click('[data-testid="finalize-button"]');
    await expect(page.locator('[data-testid="final-video-player"]')).toBeVisible({
      timeout: 60000,
    });
    
    // 9. Verify completion
    await expect(page.locator('[data-testid="project-status"]')).toContainText(
      "Completed"
    );
    await expect(page.locator('[data-testid="download-button"]')).toBeEnabled();
  });
});
```

---

## 4. Backend API Tests

### 4.1 Mock External Services (tests/mocks/minimax_mock.py)

```python
"""Mock MiniMax API responses for testing."""

from typing import Dict, Any
import httpx
from respx import MockRouter

# Sample responses
MOCK_TASK_ID = "mock-task-id-12345"
MOCK_FILE_ID = "mock-file-id-67890"
MOCK_VOICE_ID = "mock-voice-id"


def mock_minimax_api(respx_mock: MockRouter):
    """Set up mock MiniMax API responses."""
    
    # File upload
    respx_mock.post("https://api.minimax.io/v1/files/upload").mock(
        return_value=httpx.Response(
            200,
            json={
                "file": {"file_id": MOCK_FILE_ID},
                "base_resp": {"status_code": 0, "status_msg": "success"},
            },
        )
    )
    
    # Voice clone
    respx_mock.post("https://api.minimax.io/v1/voice_clone").mock(
        return_value=httpx.Response(
            200,
            json={
                "voice_id": MOCK_VOICE_ID,
                "base_resp": {"status_code": 0, "status_msg": "success"},
            },
        )
    )
    
    # Video generation
    respx_mock.post("https://api.minimax.io/v1/video_generation").mock(
        return_value=httpx.Response(
            200,
            json={
                "task_id": MOCK_TASK_ID,
                "base_resp": {"status_code": 0, "status_msg": "success"},
            },
        )
    )
    
    # Video status query - complete
    respx_mock.get(
        "https://api.minimax.io/v1/query/video_generation",
        params={"task_id": MOCK_TASK_ID}
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "Success",
                "file_id": MOCK_FILE_ID,
                "base_resp": {"status_code": 0, "status_msg": "success"},
            },
        )
    )
    
    # File retrieve (download URL)
    respx_mock.get(
        "https://api.minimax.io/v1/files/retrieve",
        params={"file_id": MOCK_FILE_ID}
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "file": {
                    "file_id": MOCK_FILE_ID,
                    "download_url": "https://example.com/mock-video.mp4",
                },
                "base_resp": {"status_code": 0, "status_msg": "success"},
            },
        )
    )
    
    # TTS
    respx_mock.post("https://api.minimax.io/v1/t2a_v2").mock(
        return_value=httpx.Response(
            200,
            content=b"mock audio content",
            headers={"content-type": "audio/mpeg"},
        )
    )
```

### 4.2 Integration Test (tests/integration/test_generation_flow.py)

```python
"""Integration tests for video generation flow."""

import pytest
from httpx import AsyncClient
import respx

from tests.mocks.minimax_mock import mock_minimax_api, MOCK_TASK_ID, MOCK_VOICE_ID


@pytest.mark.asyncio
class TestGenerationFlow:
    """Test the complete generation flow with mocked external APIs."""

    @respx.mock
    async def test_voice_clone_flow(
        self,
        client: AsyncClient,
        sample_project_with_audio: str,
    ):
        """Test voice cloning workflow."""
        mock_minimax_api(respx.mock)
        
        # Clone voice
        response = await client.post(
            f"/api/v1/generation/voice-clone",
            params={"project_id": sample_project_with_audio},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["voice_id"] == MOCK_VOICE_ID
        
        # Verify project was updated
        project_response = await client.get(
            f"/api/v1/projects/{sample_project_with_audio}"
        )
        assert project_response.json()["voiceId"] == MOCK_VOICE_ID

    @respx.mock
    async def test_video_generation_flow(
        self,
        client: AsyncClient,
        sample_project_with_plan: str,
    ):
        """Test video generation workflow."""
        mock_minimax_api(respx.mock)
        
        # Get project segments
        project_response = await client.get(
            f"/api/v1/projects/{sample_project_with_plan}"
        )
        segment_id = project_response.json()["segments"][0]["id"]
        
        # Start generation
        response = await client.post(f"/api/v1/generation/segment/{segment_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == MOCK_TASK_ID
        assert data["status"] == "submitted"
        
        # Poll status
        status_response = await client.get(
            f"/api/v1/generation/status/{MOCK_TASK_ID}"
        )
        
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == "Success"
        assert "downloadUrl" in status_data

    @respx.mock
    async def test_plan_generation(
        self,
        client: AsyncClient,
        sample_project: str,
    ):
        """Test AI plan generation."""
        # This test uses real OpenAI API or a mock
        response = await client.post(
            "/api/v1/generation/plan",
            json={
                "project_id": sample_project,
                "story_prompt": "A sunset over the ocean",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "title" in data
        assert "segments" in data
        assert len(data["segments"]) > 0
        
        # Verify segment structure
        segment = data["segments"][0]
        assert "videoPrompt" in segment
        assert "narrationText" in segment
        assert "endFramePrompt" in segment
```

---

## 5. Test Fixtures

### 5.1 E2E Test Fixtures (e2e/fixtures/)

```
e2e/
├── fixtures/
│   ├── test-image.jpg       # Sample first frame image
│   ├── test-audio.mp3       # Sample voice audio (10 seconds)
│   └── test-video.mp4       # Sample video for validation
└── helpers/
    └── test-utils.ts        # Shared test utilities
```

### 5.2 Test Utils (e2e/helpers/test-utils.ts)

```typescript
import { Page, expect } from "@playwright/test";

export async function createTestProject(
  page: Page,
  name: string = "Test Project",
  duration: number = 12
): Promise<string> {
  await page.goto("/projects/new");
  await page.fill('[data-testid="project-name-input"]', name);
  await page.fill('[data-testid="story-prompt-input"]', "Test story");
  await page.selectOption('[data-testid="duration-select"]', String(duration));
  await page.click('[data-testid="create-project-button"]');
  
  await page.waitForURL(/\/projects\/([a-z0-9-]+)$/);
  const match = page.url().match(/\/projects\/([a-z0-9-]+)$/);
  return match![1];
}

export async function uploadTestMedia(page: Page, projectId: string) {
  await page.goto(`/projects/${projectId}`);
  
  // Upload image
  const imageInput = page.locator('[data-testid="first-frame-upload"] input');
  await imageInput.setInputFiles("./e2e/fixtures/test-image.jpg");
  await expect(page.locator('[data-testid="first-frame-preview"]')).toBeVisible({
    timeout: 30000,
  });
  
  // Upload audio
  const audioInput = page.locator('[data-testid="audio-sample-upload"] input');
  await audioInput.setInputFiles("./e2e/fixtures/test-audio.mp3");
  await expect(page.locator('[data-testid="audio-preview"]')).toBeVisible({
    timeout: 30000,
  });
}

export async function waitForGenerationComplete(
  page: Page,
  segmentSelector: string,
  timeout: number = 120000
) {
  await expect(
    page.locator(`${segmentSelector} [data-testid="generating-indicator"]`)
  ).toBeHidden({ timeout });
  
  await expect(page.locator(`${segmentSelector} video`)).toBeVisible();
}
```

---

## 6. Running Tests

### 6.1 Local Development

```bash
# Run all E2E tests
npx playwright test

# Run specific test file
npx playwright test e2e/project-creation.spec.ts

# Run in headed mode (see browser)
npx playwright test --headed

# Run in UI mode (interactive)
npx playwright test --ui

# Debug a test
npx playwright test --debug

# Generate test report
npx playwright show-report
```

### 6.2 CI Configuration

```yaml
# In .github/workflows/e2e-tests.yml
- name: Run Playwright tests
  run: npx playwright test
  env:
    BASE_URL: http://localhost:5173
    E2E_MOCK_AUTH: "true"

- name: Upload test results
  uses: actions/upload-artifact@v4
  if: always()
  with:
    name: playwright-report
    path: playwright-report/
```

---

## 7. Test Data Management

### 7.1 Database Seeding (tests/seed.py)

```python
"""Seed test data for E2E tests."""

import asyncio
from app.db.session import AsyncSessionLocal
from app.db.models import User, Project, Segment
from app.db.models.project import ProjectStatus
from app.db.models.segment import SegmentStatus


async def seed_test_data():
    """Create test data for E2E tests."""
    async with AsyncSessionLocal() as session:
        # Create test user
        user = User(
            id="test-user-id",
            entra_id="test-entra-id",
            email="test@example.com",
            name="Test User",
        )
        session.add(user)
        
        # Create projects in various states
        projects = [
            Project(
                id="test-project-id",
                user_id=user.id,
                name="Test Project",
                status=ProjectStatus.CREATED,
                target_duration_sec=30,
                segment_len_sec=6,
            ),
            Project(
                id="ready-project-id",
                user_id=user.id,
                name="Ready Project",
                status=ProjectStatus.MEDIA_UPLOADED,
                target_duration_sec=30,
                segment_len_sec=6,
                first_frame_url="https://example.com/image.jpg",
                audio_sample_url="https://example.com/audio.mp3",
            ),
            # ... more test projects
        ]
        
        for project in projects:
            session.add(project)
        
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed_test_data())
```

---

## 8. Next Steps

After implementing E2E tests:

1. **Run test suite:**
   ```bash
   npx playwright test
   ```

2. **Review coverage:**
   - Identify untested workflows
   - Add tests for edge cases

3. **Proceed to Agents.md:**
   - See [Agents.md](../Agents.md) for GitHub Copilot instructions
