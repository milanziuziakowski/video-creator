# Using MiniMax API Mocks in Tests

This guide explains how to use the captured real MiniMax API responses in your tests.

## Overview

We've captured real responses from MiniMax API and created mock helpers to use them in tests **without making actual API calls or using API keys**.

## File Structure

```
tests/fixtures/
├── minimax_real_responses.json    # Real API responses (Python/JSON format)
├── minimax_mocks.py                # Python mock helpers (Backend tests)
└── README.md                       # Documentation

e2e/fixtures/
├── minimax-mocks.ts                # TypeScript mock helpers (Frontend E2E)
├── test-audio.mp3                  # Sample audio file
└── test-image.jpg                  # Sample image file
```

---

## Backend Tests (Python/pytest)

### Import the Mocks

```python
from tests.fixtures.minimax_mocks import MinimaxMockResponses
```

### Using with pytest Fixtures

The `conftest.py` already sets up a `mock_minimax_client` fixture that uses real responses:

```python
@pytest.mark.asyncio
async def test_voice_cloning(async_client, mock_minimax_client):
    """Test voice cloning with mocked MiniMax client."""
    response = await async_client.post(
        "/api/v1/generation/voice-clone",
        params={"project_id": "test-project"},
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Assert using real captured values
    assert data["voice_id"] == "test-voice-20260201133125"
    assert data["status"] == "complete"
```

### HTTP-Level Mocking with respx

For more control, use `respx` to mock HTTP requests:

```python
import respx
import httpx
from tests.fixtures.minimax_mocks import MinimaxMockResponses

@respx.mock
@pytest.mark.asyncio
async def test_minimax_upload():
    """Test file upload with HTTP mocking."""
    # Mock the MiniMax upload endpoint
    respx.post("https://api.minimax.io/v1/files/upload").mock(
        return_value=httpx.Response(
            200,
            json=MinimaxMockResponses.files_upload()
        )
    )
    
    # Your test code here
    result = await minimax_client.upload_file(b"audio data", "test.mp3")
    assert result == "362069085524212"
```

### Available Mock Methods

```python
# Success responses
MinimaxMockResponses.files_upload()           # File upload
MinimaxMockResponses.voice_clone()            # Voice cloning
MinimaxMockResponses.t2a_v2()                 # Text-to-audio
MinimaxMockResponses.video_generation()       # Video generation start
MinimaxMockResponses.query_video_generation("Success")  # Status check
MinimaxMockResponses.files_retrieve()         # Get download URL

# Error responses
MinimaxMockResponses.files_upload(success=False)           # Auth error
MinimaxMockResponses.voice_clone(duplicate=True)           # Duplicate voice_id
MinimaxMockResponses.query_video_generation("Fail")        # Failed generation
```

---

## Frontend E2E Tests (Playwright)

### Import the Mocks

```typescript
import { setupMinimaxMocks, BACKEND_MOCK_RESPONSES } from './fixtures/minimax-mocks';
```

### Setup in Your Test

```typescript
test('should complete workflow', async ({ page }) => {
  // Setup all mocks at once
  const mocks = setupMinimaxMocks(page);
  await mocks.mockAll();

  // Now all API calls will return mocked responses
  await page.goto('/projects/new');
  // ... rest of your test
});
```

### Selective Mocking

Mock only specific endpoints:

```typescript
test('should clone voice', async ({ page }) => {
  const mocks = setupMinimaxMocks(page);
  
  // Mock only voice cloning
  await mocks.mockVoiceClone();
  
  // Your test
  await page.click('[data-testid="clone-voice-button"]');
  await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
});
```

### Mock Different Scenarios

```typescript
test('should handle generation in progress', async ({ page }) => {
  const mocks = setupMinimaxMocks(page);
  
  // Mock processing status
  await mocks.mockGenerationStatus('processing');
  
  // Test will see "processing" status
  await page.click('[data-testid="generate-button"]');
  await expect(page.locator('[data-testid="progress-bar"]')).toBeVisible();
});

test('should handle generation failure', async ({ page }) => {
  const mocks = setupMinimaxMocks(page);
  
  // Mock failed status
  await mocks.mockGenerationStatus('failed');
  
  // Test error handling
  await page.click('[data-testid="generate-button"]');
  await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
});
```

### Available Mock Methods

```typescript
const mocks = setupMinimaxMocks(page);

await mocks.mockVoiceClone();                    // Mock voice cloning
await mocks.mockGeneratePlan();                  // Mock AI plan generation
await mocks.mockGenerateSegment();               // Mock segment generation
await mocks.mockGenerationStatus('complete');    // Mock status ('processing'|'complete'|'failed')
await mocks.mockFinalizeProject();               // Mock project finalization
await mocks.mockAll();                           // Mock all endpoints
```

### Access Raw Mock Data

```typescript
import { MINIMAX_MOCK_RESPONSES, BACKEND_MOCK_RESPONSES } from './fixtures/minimax-mocks';

// MiniMax API responses
console.log(MINIMAX_MOCK_RESPONSES.voiceClone.voice_id);  // 'test-voice-20260201133125'
console.log(MINIMAX_MOCK_RESPONSES.filesUpload.file_id);  // '362069085524212'

// Backend API responses
console.log(BACKEND_MOCK_RESPONSES.generatePlan.segments.length);  // 5
```

---

## Key Benefits

✅ **No API Keys Required** - Tests run without real authentication
✅ **No API Costs** - No charges for test runs
✅ **Fast Tests** - No network delays
✅ **Reliable** - No rate limiting or network issues
✅ **Real Data** - Using actual API response formats
✅ **Offline Testing** - Works without internet connection

---

## Example: Complete E2E Test

```typescript
import { test, expect } from '@playwright/test';
import { setupMinimaxMocks } from './fixtures/minimax-mocks';

test.describe('Video Generation', () => {
  test('should generate video from start to finish', async ({ page }) => {
    // Setup all mocks
    const mocks = setupMinimaxMocks(page);
    await mocks.mockAll();

    // 1. Create project
    await page.goto('/projects/new');
    await page.fill('[data-testid="project-name"]', 'Test Project');
    await page.fill('[data-testid="story-prompt"]', 'A beautiful sunset');
    await page.click('[data-testid="create-button"]');

    // 2. Upload media
    await page.locator('[data-testid="file-input-image"]').setInputFiles(
      './e2e/fixtures/test-image.jpg'
    );
    await page.locator('[data-testid="file-input-audio"]').setInputFiles(
      './e2e/fixtures/test-audio.mp3'
    );

    // 3. Clone voice (mocked)
    await page.click('[data-testid="clone-voice-button"]');
    await expect(page.locator('[data-testid="voice-cloned"]')).toBeVisible();

    // 4. Generate plan (mocked)
    await page.click('[data-testid="generate-plan-button"]');
    
    // 5. Verify segments created (from mocked response)
    await expect(page.locator('[data-testid="segment-card-0"]')).toBeVisible();
    
    const segments = page.locator('[data-testid^="segment-card-"]');
    await expect(segments).toHaveCount(5);  // 5 segments for 30-second video
  });
});
```

---

## Troubleshooting

### Mock not working?

1. **Check the route pattern** - Make sure it matches your API endpoint:
   ```typescript
   // ✓ Correct - catches all query params
   await page.route('**/api/v1/generation/voice-clone*', ...)
   
   // ✗ Wrong - won't catch query params
   await page.route('**/api/v1/generation/voice-clone', ...)
   ```

2. **Setup mocks before navigation**:
   ```typescript
   // ✓ Correct order
   const mocks = setupMinimaxMocks(page);
   await mocks.mockAll();
   await page.goto('/projects');
   
   // ✗ Wrong - mocks set up too late
   await page.goto('/projects');
   await mocks.mockAll();
   ```

3. **Check backend is using mock mode**:
   ```bash
   # Set environment variable
   MINIMAX_MOCK_MODE=true
   ```

### Need to update mocks?

1. Run the test script:
   ```bash
   cd ai-video-creator-backend
   python test_minimax_real.py
   ```

2. New responses saved to `tests/fixtures/minimax_real_responses.json`

3. Update `minimax_mocks.py` and `minimax-mocks.ts` if structure changed

---

## Resources

- **Backend Mock Helper**: [tests/fixtures/minimax_mocks.py](../../tests/fixtures/minimax_mocks.py)
- **Frontend Mock Helper**: [e2e/fixtures/minimax-mocks.ts](minimax-mocks.ts)
- **Real Responses**: [tests/fixtures/minimax_real_responses.json](../../tests/fixtures/minimax_real_responses.json)
- **MiniMax API Reference**: [tests/fixtures/MINIMAX_API_REFERENCE.md](../../tests/fixtures/MINIMAX_API_REFERENCE.md)
