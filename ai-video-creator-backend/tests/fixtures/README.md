# MiniMax API Mock Fixtures

This directory contains real API responses from MiniMax captured for use in E2E tests.

## Files

- **minimax_real_responses.json** - Real API responses from MiniMax (aligned with API endpoint names)
- **test-audio.mp3** - Sample audio file used for voice cloning tests (located in `ai-video-creator-frontend/e2e/fixtures/`)

## MiniMax API Endpoints Coverage

### 1. File Upload - `POST /v1/files/upload`
Upload audio file for voice cloning.

**Request:**
```json
{
  "purpose": "voice_clone",
  "file": "<binary data>"
}
```

**Response:**
```json
{
  "file_id": 362069085524212
}
```

### 2. Voice Clone - `POST /v1/voice_clone`
Clone voice from uploaded audio file.

**Request:**
```json
{
  "file_id": 362069085524212,
  "voice_id": "test-voice-20260201133125",
  "need_noise_reduction": true,
  "need_volume_normalization": true
}
```

**Response:**
```json
{
  "voice_id": "test-voice-20260201133125"
}
```

### 3. Text-to-Audio (TTS) - `POST /v1/t2a_v2`
Generate audio from text using cloned voice.

**Request:**
```json
{
  "model": "speech-02-hd",
  "text": "This is a test narration.",
  "voice_setting": {
    "voice_id": "test-voice-20260201133125",
    "speed": 1.0
  },
  "audio_setting": {
    "format": "mp3"
  }
}
```

**Response:**
```json
{
  "data": {
    "audio": "<base64_encoded_audio>"
  }
}
```
**Generated audio size:** 44,160 bytes

### 4. Video Generation - `POST /v1/video_generation`
Start video generation task (FL2V - First & Last Frame Video).

**Request:**
```json
{
  "model": "MiniMax-Hailuo-02",
  "prompt": "[Zoom in] A beautiful sunset over mountains",
  "first_frame_image": "https://example.com/frame1.jpg",
  "last_frame_image": "https://example.com/frame2.jpg",
  "duration": 6,
  "resolution": "768P",
  "prompt_optimizer": true
}
```

**Response:**
```json
{
  "task_id": "task-12345"
}
```

### 5. Query Video Status - `GET /v1/query/video_generation?task_id={task_id}`
Poll video generation status.

**Response (Success):**
```json
{
  "task_id": "task-12345",
  "status": "Success",
  "file_id": "362067136205243"
}
```

**Response (Processing):**
```json
{
  "task_id": "task-12345",
  "status": "Processing"
}
```

**Response (Failed):**
```json
{
  "task_id": "task-12345",
  "status": "Fail",
  "error_msg": "Error description"
}
```

### 6. Retrieve File - `GET /v1/files/retrieve?file_id={file_id}`
Get download URL for generated video.

**Response:**
```json
{
  "file": {
    "file_id": "362067136205243",
    "download_url": "https://cdn.minimax.io/videos/..."
  }
}
```

## Backend Method Mapping

| Backend Method | MiniMax Endpoint | Purpose |
|---------------|------------------|---------|
| `upload_file()` | `POST /v1/files/upload` | Upload audio for voice cloning |
| `voice_clone()` | `POST /v1/voice_clone` | Clone voice from uploaded file |
| `text_to_audio()` | `POST /v1/t2a_v2` | Generate speech with cloned voice |
| `generate_video_fl2v()` | `POST /v1/video_generation` | Start FL2V video generation |
| `generate_video()` | `POST /v1/video_generation` | Start standard video generation |
| `query_video_status()` | `GET /v1/query/video_generation` | Poll video task status |
| `retrieve_file()` | `GET /v1/files/retrieve` | Get video download URL |
| `poll_video_until_complete()` | Polling loop | Poll until Success/Fail |

## Using in E2E Tests

### Option 1: Mock at Backend Level

Set the backend to use mock mode by setting environment variable:

```bash
MINIMAX_MOCK_MODE=true
```

When `MINIMAX_MOCK_MODE=true`, the `MinimaxClient` will return mock responses without making real API calls.

### Option 2: Mock at HTTP Level (Recommended for E2E)

Use a tool like `nock` (Node.js) or `httpx.mock` (Python) to intercept HTTP requests:

**Python Example:**
```python
import respx
import httpx

@respx.mock
async def test_voice_cloning():
    # Mock the upload endpoint
    respx.post("https://api.minimax.io/v1/files/upload").mock(
        return_value=httpx.Response(
            200,
            json={"file_id": "362069085524212"}
        )
    )
    
    # Mock the voice clone endpoint
    respx.post("https://api.minimax.io/v1/voice_clone").mock(
        return_value=httpx.Response(
            200,
            json={"voice_id": "test-voice-20260201133125"}
        )
    )
    
    # Your test code here
    ...
```

**Frontend E2E (Playwright):**

Mock the backend API endpoints in your Playwright tests:

```typescript
test('should clone voice', async ({ page }) => {
  // Mock the backend endpoint that calls MiniMax
  await page.route('**/api/v1/generation/voice-clone*', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        voice_id: 'test-voice-20260201133125',
        status: 'complete'
      })
    });
  });
  
  // Run your test
  await page.goto('/projects/123');
  await page.click('[data-testid="clone-voice-button"]');
  // ... assertions
});
```

## Important Notes

1. **No Real API Calls in E2E Tests** - Always use mocked responses to avoid:
   - Consuming API credits
   - Rate limiting
   - Network dependency
   - Slower test execution

2. **Environment Variables** - Ensure you clear any PowerShell environment variables:
   ```powershell
   $env:OPENAI_API_KEY = $null
   $env:MINIMAX_API_KEY = $null
   ```
   The `.env` file should be the source of truth.

3. **Regenerating Responses** - To capture new responses, run:
   ```bash
   python test_minimax_real.py
   ```

## API Key Configuration

**Correct Configuration** (in `.env`):
```
MINIMAX_API_KEY=your_minimax_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

- MiniMax keys start with `sk-api-`
- OpenAI keys start with `sk-proj-`
- Store actual keys in `.env` file (not in version control)
