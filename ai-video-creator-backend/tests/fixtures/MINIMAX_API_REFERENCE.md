# MiniMax API Complete Reference

**Base URL:** `https://api.minimax.io/v1`

**Authentication:** Bearer token in `Authorization` header

---

## API Endpoint Summary

| Endpoint | Method | Purpose | Backend Method |
|----------|--------|---------|---------------|
| `/files/upload` | POST | Upload audio file | `upload_file()` |
| `/voice_clone` | POST | Clone voice from file | `voice_clone()` |
| `/t2a_v2` | POST | Text-to-Speech (TTS) | `text_to_audio()` |
| `/video_generation` | POST | Start video generation | `generate_video_fl2v()` / `generate_video()` |
| `/query/video_generation` | GET | Poll video status | `query_video_status()` |
| `/files/retrieve` | GET | Get file download URL | `retrieve_file()` |

---

## Complete Workflow Examples

### Voice Cloning Workflow

```
1. Upload Audio File
   POST /v1/files/upload
   └─> file_id

2. Clone Voice
   POST /v1/voice_clone
   {file_id, voice_id}
   └─> voice_id

3. Generate Speech
   POST /v1/t2a_v2
   {text, voice_id}
   └─> audio bytes
```

### Video Generation Workflow (FL2V)

```
1. Generate Images
   (External: DALL-E, Stable Diffusion, etc.)
   └─> first_frame.jpg, last_frame.jpg

2. Start Video Generation
   POST /v1/video_generation
   {prompt, first_frame_image, last_frame_image}
   └─> task_id

3. Poll Status (10s intervals)
   GET /v1/query/video_generation?task_id={task_id}
   └─> status: Processing | Success | Fail

4. Get Download URL
   GET /v1/files/retrieve?file_id={file_id}
   └─> download_url
```

### Complete Segment Generation (Full Pipeline)

```
Story Prompt
    │
    ├─> OpenAI Agent (GPT-4o)
    │   └─> Video Plan (segments with prompts)
    │
    ├─> For each segment:
    │   │
    │   ├─> Generate First Frame Image
    │   │   POST OpenAI DALL-E
    │   │   └─> first_frame.jpg
    │   │
    │   ├─> Generate Last Frame Image
    │   │   POST OpenAI DALL-E
    │   │   └─> last_frame.jpg
    │   │
    │   ├─> Generate Video
    │   │   POST /v1/video_generation
    │   │   └─> task_id → poll → video file
    │   │
    │   └─> Generate Audio
    │       POST /v1/t2a_v2
    │       └─> audio bytes
    │
    └─> Combine All Segments
        FFmpeg concatenation + muxing
        └─> final_video.mp4
```

---

## Detailed Endpoint Specifications

### 1. POST /v1/files/upload

**Purpose:** Upload audio file for voice cloning

**Request:**
- **Content-Type:** `multipart/form-data`
- **Fields:**
  - `file`: Binary file data
  - `purpose`: String (e.g., "voice_clone")

**Response:**
```json
{
  "base_resp": {
    "status_code": 0,
    "status_msg": "success"
  },
  "file": {
    "file_id": "362069085524212"
  }
}
```

**Error Response:**
```json
{
  "base_resp": {
    "status_code": 1004,
    "status_msg": "login fail: Please carry the API secret key..."
  }
}
```

---

### 2. POST /v1/voice_clone

**Purpose:** Clone voice from uploaded audio file

**Request:**
```json
{
  "file_id": "362069085524212",
  "voice_id": "my-custom-voice-id",
  "need_noise_reduction": true,
  "need_volume_normalization": true
}
```

**Response:**
```json
{
  "base_resp": {
    "status_code": 0,
    "status_msg": "success"
  }
}
```
**Note:** Returns the same `voice_id` if successful

**Error Response:**
```json
{
  "base_resp": {
    "status_code": 1001,
    "status_msg": "voice clone voice id duplicate"
  }
}
```

---

### 3. POST /v1/t2a_v2

**Purpose:** Generate audio from text using cloned voice (TTS)

**Request:**
```json
{
  "model": "speech-02-hd",
  "text": "This is the narration text.",
  "voice_setting": {
    "voice_id": "my-custom-voice-id",
    "speed": 1.0
  },
  "audio_setting": {
    "format": "mp3"
  }
}
```

**Parameters:**
- `model`: "speech-01" | "speech-02" | "speech-02-hd"
- `speed`: 0.5 - 2.0
- `format`: "mp3" | "wav" | "flac"

**Response:**
```json
{
  "data": {
    "audio": "<base64_encoded_audio_data>"
  }
}
```
**OR** (if streaming)
```
Content-Type: audio/mpeg
<binary audio data>
```

---

### 4. POST /v1/video_generation

**Purpose:** Start video generation task (FL2V or standard)

**Request (FL2V - First & Last Frame):**
```json
{
  "model": "MiniMax-Hailuo-02",
  "prompt": "[Zoom in] A beautiful mountain landscape at sunset",
  "first_frame_image": "https://example.com/first.jpg",
  "last_frame_image": "https://example.com/last.jpg",
  "duration": 6,
  "resolution": "768P",
  "prompt_optimizer": true,
  "callback_url": "https://myserver.com/webhook"
}
```

**Parameters:**
- `model`: "MiniMax-Hailuo-02" (required for FL2V)
- `prompt`: Max 2000 chars, can include camera commands
- `first_frame_image`: URL or base64 data URL (optional for FL2V)
- `last_frame_image`: URL or base64 data URL (required for FL2V)
- `duration`: 6 or 10 seconds
- `resolution`: "768P" | "1080P" (512P NOT supported for FL2V)
- `prompt_optimizer`: true | false
- `callback_url`: Optional webhook for async notifications

**Camera Commands:**
```
[Zoom in]       - Camera zooms in
[Zoom out]      - Camera zooms out
[Pan left]      - Camera pans left
[Pan right]     - Camera pans right
[Tilt up]       - Camera tilts up
[Tilt down]     - Camera tilts down
[Dolly forward] - Camera moves forward
[Dolly back]    - Camera moves backward
[Orbit left]    - Camera orbits left
[Orbit right]   - Camera orbits right
[Crane up]      - Camera cranes up
[Crane down]    - Camera cranes down
[Static shot]   - No camera movement
```

**Response:**
```json
{
  "base_resp": {
    "status_code": 0,
    "status_msg": "success"
  },
  "task_id": "task-abc123def456"
}
```

---

### 5. GET /v1/query/video_generation

**Purpose:** Poll video generation task status

**Query Parameters:**
- `task_id`: Task ID from video_generation response

**Response (Processing):**
```json
{
  "base_resp": {
    "status_code": 0,
    "status_msg": "success"
  },
  "task_id": "task-abc123def456",
  "status": "Processing"
}
```

**Response (Success):**
```json
{
  "base_resp": {
    "status_code": 0,
    "status_msg": "success"
  },
  "task_id": "task-abc123def456",
  "status": "Success",
  "file_id": "362067136205243"
}
```

**Response (Failed):**
```json
{
  "base_resp": {
    "status_code": 0,
    "status_msg": "success"
  },
  "task_id": "task-abc123def456",
  "status": "Fail",
  "error_msg": "Content policy violation"
}
```

**Polling Recommendations:**
- Initial delay: 5 seconds
- Poll interval: 10 seconds
- Max attempts: 60 (10 minutes total)

---

### 6. GET /v1/files/retrieve

**Purpose:** Get download URL for a generated file

**Query Parameters:**
- `file_id`: File ID from video generation success response

**Response:**
```json
{
  "base_resp": {
    "status_code": 0,
    "status_msg": "success"
  },
  "file": {
    "file_id": "362067136205243",
    "download_url": "https://cdn.minimax.io/videos/xyz.mp4",
    "expires_at": "2026-02-01T14:00:00Z"
  }
}
```

---

## Error Handling

### Common Error Codes

| Status Code | Meaning |
|-------------|---------|
| 0 | Success |
| 1001 | Duplicate voice_id |
| 1004 | Authentication failed |
| 1005 | Insufficient credits |
| 2001 | Content policy violation |
| 3001 | Invalid parameters |
| 5001 | Server error |

### Best Practices

1. **Always check `base_resp.status_code`** - Even 200 HTTP responses can contain API errors
2. **Implement exponential backoff** - For rate limiting
3. **Use webhooks for long tasks** - Instead of continuous polling
4. **Cache download URLs** - They expire after a certain time
5. **Validate inputs** - Before sending to API (saves costs)

---

## Mock Mode in Tests

When `MINIMAX_API_KEY` is empty or `MINIMAX_MOCK_MODE=true`:
- All methods return mock responses
- No actual API calls are made
- Use captured real responses from `minimax_real_responses.json`

**Example:**
```python
# In conftest.py or test setup
os.environ["MINIMAX_MOCK_MODE"] = "true"

# Or use mocking library
import respx

@respx.mock
async def test_voice_clone():
    respx.post("https://api.minimax.io/v1/voice_clone").mock(
        return_value=httpx.Response(
            200,
            json={
                "base_resp": {"status_code": 0, "status_msg": "success"}
            }
        )
    )
```

---

## Resources

- **MiniMax Platform:** https://platform.minimax.io
- **API Key Management:** https://platform.minimax.io/user-center/basic-information/interface-key
- **Backend Implementation:** See [app/integrations/minimax_client.py](../../app/integrations/minimax_client.py)
- **Real Responses:** See [minimax_real_responses.json](./minimax_real_responses.json)
