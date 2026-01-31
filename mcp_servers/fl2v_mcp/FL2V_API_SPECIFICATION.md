# FL2V (First-Last Frame Video) API - Complete Technical Specification

**Research Date:** January 8, 2026  
**API Provider:** MiniMax (MiniMax-Hailuo-02 model)  
**API Region:** Global (`https://api.minimaxi.com`) or Mainland China (`https://api.minimaxi.com`)

---

## Executive Summary

FL2V is a **first-last frame to video** generation mode available through MiniMax's video generation API. It generates smooth videos that:
- **Start with** a specific first frame image you provide
- **End with** a specific last frame image you provide
- **Follow** a text prompt describing the scene/action

This is ideal for creating seamless video segments where you need precise control over beginning and end frames.

---

## 1. ENDPOINT URLS

### 1.1 Video Generation Submission
```
POST https://api.minimaxi.com/v1/video_generation
```

**Region Variants:**
- **Global:** `https://api.minimaxi.com/v1/video_generation`
- **Mainland China:** `https://api.minimaxi.com/v1/video_generation`

**Important:** Ensure your API key and host region match (global key → global host).

### 1.2 Status Polling
```
GET https://api.minimaxi.com/v1/query/video_generation
```

**Query Parameters:**
```
?task_id={task_id}
```

### 1.3 File Retrieval
```
GET https://api.minimaxi.com/v1/files/retrieve
```

**Query Parameters:**
```
?file_id={file_id}
```

---

## 2. REQUEST FORMAT - FL2V SUBMISSION

### 2.1 HTTP Headers

```http
POST /v1/video_generation HTTP/1.1
Authorization: Bearer {API_KEY}
Content-Type: application/json
```

**Headers Detail:**
| Header | Value | Required | Notes |
|--------|-------|----------|-------|
| `Authorization` | `Bearer {API_KEY}` | ✓ | MiniMax API key from dashboard |
| `Content-Type` | `application/json` | ✓ | Always JSON for video generation |

### 2.2 Request Body (FL2V Mode)

```json
{
  "model": "MiniMax-Hailuo-02",
  "prompt": "A person walks through a sunny meadow towards a tree",
  "duration": 6,
  "resolution": "720P",
  "first_frame_image": "data:image/jpeg;base64,...BASE64_ENCODED_IMAGE...",
  "last_frame_image": "data:image/jpeg;base64,...BASE64_ENCODED_IMAGE...",
  "prompt_optimizer": true,
  "fast_pretreatment": false
}
```

### 2.3 Required Parameters

| Parameter | Type | Required | Values | Description |
|-----------|------|----------|--------|-------------|
| `model` | string | ✓ | See Section 3.1 | Must support FL2V: `MiniMax-Hailuo-02` |
| `prompt` | string | ✓ | Max 2000 chars | Scene description for video generation |
| `first_frame_image` | string | ✓ (for FL2V) | Data URL or HTTP URL | First frame image (Base64 or URL) |
| `last_frame_image` | string | ✓ (for FL2V) | Data URL or HTTP URL | Last frame image (Base64 or URL) |

### 2.4 Optional Parameters

| Parameter | Type | Default | Values | Description |
|-----------|------|---------|--------|-------------|
| `duration` | integer | 6 | 6 or 10 | Video length in seconds |
| `resolution` | string | Varies | 512P, 768P, 1080P | Output video resolution |
| `prompt_optimizer` | boolean | true | true/false | Auto-optimize prompt for better results |
| `fast_pretreatment` | boolean | false | true/false | Shorten optimization time (trades quality) |
| `callback_url` | string | null | Valid HTTPS URL | Webhook for async notifications |
| `aigc_watermark` | boolean | false | true/false | Add MiniMax watermark to output |

### 2.5 Complete FL2V Request Example

```python
import base64
import requests
import json

def submit_fl2v_task(api_key: str, prompt: str, 
                     first_frame_path: str, last_frame_path: str):
    """Submit FL2V video generation task."""
    
    # Read and encode images to Base64
    with open(first_frame_path, "rb") as f:
        first_frame_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    with open(last_frame_path, "rb") as f:
        last_frame_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    # Determine image format (jpg or png)
    first_ext = first_frame_path.split(".")[-1].lower()
    last_ext = last_frame_path.split(".")[-1].lower()
    first_mime = f"image/{first_ext if first_ext in ['jpg', 'png'] else 'jpeg'}"
    last_mime = f"image/{last_ext if last_ext in ['jpg', 'png'] else 'jpeg'}"
    
    # Build request
    url = "https://api.minimaxi.com/v1/video_generation"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "MiniMax-Hailuo-02",
        "prompt": prompt,
        "duration": 6,
        "resolution": "720P",
        "first_frame_image": f"data:{first_mime};base64,{first_frame_b64}",
        "last_frame_image": f"data:{last_mime};base64,{last_frame_b64}",
        "prompt_optimizer": True,
        "fast_pretreatment": False
    }
    
    # Submit request
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    task_id = data["task_id"]
    
    print(f"✓ FL2V task submitted: {task_id}")
    return task_id
```

### 2.6 Image Format Requirements

**Supported Formats:**
- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- WebP (`.webp`)

**Image Constraints:**
| Constraint | Value | Notes |
|-----------|-------|-------|
| **Max Size** | 5 MB per image | Consider Base64 encoding overhead |
| **Min Resolution** | 512×512 px | Recommended minimum |
| **Recommended Resolution** | Match target resolution | 1280×720 for 720P, 1920×1080 for 1080P |
| **Aspect Ratio** | 16:9 (widescreen) | Standard video aspect ratio |
| **Color Space** | RGB/RGBA | Automatic conversion from CMYK |
| **Encoding** | JPEG baseline or PNG | Progressive JPEG not required |

**Image Upload Methods:**
1. **Base64 Data URL** (recommended):
   - Embed directly: `"data:image/jpeg;base64,{BASE64_DATA}"`
   - Simpler, single API call
   - Payload size limit: ~50 MB

2. **HTTP/HTTPS URLs**:
   - `"https://example.com/image.jpg"`
   - MiniMax downloads from your server
   - URL must be publicly accessible
   - Response time may be slower

---

## 3. RESPONSE FORMAT - VIDEO GENERATION SUBMISSION

### 3.1 Success Response (Status 200)

```json
{
  "task_id": "106916112212032",
  "base_resp": {
    "status_code": 0,
    "status_msg": "success"
  }
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Unique identifier for this generation task. Use this to poll status. |
| `base_resp.status_code` | integer | 0 = success, non-zero = error |
| `base_resp.status_msg` | string | Human-readable status message |

### 3.2 Error Response (Status 200 with error code)

```json
{
  "base_resp": {
    "status_code": 1001,
    "status_msg": "Invalid API key"
  }
}
```

**Common Error Codes:**
| Code | Message | Cause | Solution |
|------|---------|-------|----------|
| 0 | success | Task submitted | Proceed with polling |
| 1001 | Invalid API key | Wrong/expired key | Verify API key in dashboard |
| 1002 | Unauthorized region | Region mismatch | Ensure host region matches key region |
| 1003 | Invalid model | Model doesn't support FL2V | Use `MiniMax-Hailuo-02` |
| 1004 | Invalid prompt | Prompt too long or invalid | Keep under 2000 characters |
| 1005 | Invalid image format | Image encoding error | Use valid JPEG/PNG Base64 |
| 1010 | Rate limit exceeded | Too many requests | Wait and retry after 10+ seconds |
| 1020 | Insufficient quota | Out of API credits | Add billing or contact support |

### 3.3 task_id Structure

**Example task_id:** `106916112212032`

**Properties:**
- **Type:** String (numeric string)
- **Length:** 12-18 digits
- **Uniqueness:** Globally unique
- **Expiration:** Valid for 7 days after submission
- **Use:** Required for all status polling and file retrieval

---

## 4. STATUS POLLING - TASK_ID STRUCTURE & FLOW

### 4.1 Polling Endpoint

```http
GET /v1/query/video_generation?task_id=106916112212032
Authorization: Bearer {API_KEY}
```

### 4.2 Status Response Format

```json
{
  "task_id": "106916112212032",
  "status": "Success",
  "file_id": "205258526306433",
  "base_resp": {
    "status_code": 0,
    "status_msg": "success"
  }
}
```

**Response Fields:**
| Field | Type | When Present | Description |
|-------|------|--------------|-------------|
| `task_id` | string | Always | Echo of queried task_id |
| `status` | string | Always | Current task status (see Section 4.3) |
| `file_id` | string | On success | Video file ID for retrieval (only when `status == "Success"`) |
| `error_message` | string | On failure | Reason for failure (when `status == "Fail"`) |
| `base_resp.status_code` | integer | Always | 0 = API call successful |
| `base_resp.status_msg` | string | Always | Status message |

### 4.3 Status Values & Meanings

| Status | Meaning | Action | Typical Duration |
|--------|---------|--------|------------------|
| `submitted` | Task accepted and queued | Continue polling | 0-30 seconds |
| `processing` | Video generation in progress | Continue polling | 20-120 seconds |
| `Success` | Generation complete ✓ | Retrieve `file_id`, download video | N/A |
| `Fail` | Generation failed ✗ | Log `error_message`, may retry | N/A |

**Status Transition Flow:**
```
submitted → processing → Success
                      ↓
                      Fail
```

### 4.4 Response for Each Status

#### Status: `submitted`
```json
{
  "task_id": "106916112212032",
  "status": "submitted",
  "file_id": null,
  "base_resp": {
    "status_code": 0,
    "status_msg": "success"
  }
}
```
**Action:** Task is in queue. Wait and poll again in 10 seconds.

#### Status: `processing`
```json
{
  "task_id": "106916112212032",
  "status": "processing",
  "file_id": null,
  "base_resp": {
    "status_code": 0,
    "status_msg": "success"
  }
}
```
**Action:** Video is being generated. Continue polling every 10 seconds.

#### Status: `Success`
```json
{
  "task_id": "106916112212032",
  "status": "Success",
  "file_id": "205258526306433",
  "base_resp": {
    "status_code": 0,
    "status_msg": "success"
  }
}
```
**Action:** Generation complete! Use `file_id` to retrieve video.

#### Status: `Fail`
```json
{
  "task_id": "106916112212032",
  "status": "Fail",
  "error_message": "Model overloaded, please retry later",
  "base_resp": {
    "status_code": 0,
    "status_msg": "success"
  }
}
```
**Action:** Generation failed. Log error and optionally retry with adjusted parameters.

### 4.5 Polling Implementation Example

```python
import asyncio
import time
from typing import Optional

async def poll_fl2v_status(
    task_id: str, 
    api_key: str,
    poll_interval: int = 10,
    max_wait_sec: int = 600  # 10 minutes
) -> Optional[dict]:
    """Poll FL2V task status with proper retry logic."""
    
    import httpx
    
    url = "https://api.minimaxi.com/v1/query/video_generation"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"task_id": task_id}
    
    start_time = time.time()
    poll_count = 0
    
    while True:
        elapsed = time.time() - start_time
        poll_count += 1
        
        # Timeout check
        if elapsed > max_wait_sec:
            raise TimeoutError(f"Task {task_id} did not complete in {max_wait_sec}s")
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
            
            data = response.json()
            status = data.get("status")
            
            print(f"[Poll {poll_count}] Status: {status} (elapsed: {elapsed:.1f}s)")
            
            if status == "Success":
                file_id = data.get("file_id")
                print(f"✓ Video generation complete! file_id: {file_id}")
                return {"status": "Success", "file_id": file_id, "task_id": task_id}
            
            elif status == "Fail":
                error = data.get("error_message", "Unknown error")
                print(f"✗ Generation failed: {error}")
                return {"status": "Fail", "error": error, "task_id": task_id}
            
            elif status in ["submitted", "processing"]:
                print(f"  Waiting {poll_interval}s before next poll...")
                await asyncio.sleep(poll_interval)
            
            else:
                print(f"⚠ Unknown status: {status}, retrying...")
                await asyncio.sleep(poll_interval)
        
        except asyncio.TimeoutError:
            print(f"⚠ Request timeout, retrying in {poll_interval}s...")
            await asyncio.sleep(poll_interval)
        
        except Exception as e:
            print(f"⚠ Error during polling: {e}, retrying in {poll_interval}s...")
            await asyncio.sleep(poll_interval)
```

---

## 5. SUPPORTED MODELS FOR FL2V

### 5.1 FL2V-Compatible Models

**Currently Available:**
| Model | FL2V Support | Max Duration | Max Resolution | Status | Notes |
|-------|--------------|--------------|-----------------|--------|-------|
| `MiniMax-Hailuo-02` | ✓ | 6s, 10s | 512P, 768P, 1080P | **Active** | Only current FL2V option |
| `MiniMax-Hailuo-2.3` | ✗ | 6s, 10s | 768P, 1080P | Latest | Not yet supporting FL2V |
| `MiniMax-Hailuo-2.3-Fast` | ✗ | 6s, 10s | 768P, 1080P | Latest | Not yet supporting FL2V |

**Note:** Currently, **only `MiniMax-Hailuo-02` supports FL2V mode**. This is the previous-generation model but offers excellent first-last frame control.

### 5.2 Model Selection for FL2V

```python
# For FL2V, you MUST use:
model = "MiniMax-Hailuo-02"

# This model supports:
# - Durations: 6 or 10 seconds
# - Resolutions: 512P, 768P, 1080P
```

---

## 6. RESOLUTION & DURATION SPECIFICATIONS

### 6.1 Resolution Requirements

**Available Resolutions for MiniMax-Hailuo-02:**
| Resolution | Dimensions | Aspect Ratio | Use Case |
|-----------|-----------|--------------|----------|
| `512P` | 768×432 | 16:9 | Draft/preview, fast generation |
| `768P` | 1280×720 | 16:9 | **Recommended default** |
| `1080P` | 1920×1080 | 16:9 | High quality, slower generation |

**Recommended for FL2V:**
- Use `768P` for balance of quality and speed
- Use `1080P` for professional content
- Use `512P` for testing/quick iterations

### 6.2 Duration Requirements

**Available Durations:**
- `6` seconds (default, faster)
- `10` seconds (longer videos, slightly slower)

**Generation Time by Resolution:**
| Resolution | Typical Time |
|-----------|-------------|
| 512P | 20-40 seconds |
| 768P | 40-80 seconds |
| 1080P | 60-120 seconds |

---

## 7. IMAGE UPLOAD HANDLING

### 7.1 Image Format: Base64 Data URL (Recommended)

```json
{
  "first_frame_image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJ...",
  "last_frame_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
}
```

**Encoding Process:**
```python
import base64

def load_image_as_data_url(image_path: str) -> str:
    """Load image file and convert to Base64 data URL."""
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    # Detect format from file extension
    ext = image_path.lower().split(".")[-1]
    mime_type = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp"
    }.get(ext, "image/jpeg")
    
    # Encode to Base64
    b64_str = base64.b64encode(image_data).decode("utf-8")
    
    return f"data:{mime_type};base64,{b64_str}"

# Usage
first_frame_url = load_image_as_data_url("first_frame.jpg")
last_frame_url = load_image_as_data_url("last_frame.jpg")
```

### 7.2 Image Format: HTTP/HTTPS URLs

```json
{
  "first_frame_image": "https://example.com/images/frame1.jpg",
  "last_frame_image": "https://storage.example.com/frame2.png"
}
```

**Requirements:**
- URL must be publicly accessible (no authentication required)
- HTTPS preferred over HTTP
- Content-Type header must be image/* 
- Response time: MiniMax will wait up to 30 seconds
- Image must be served with proper CORS headers (if from different domain)

**When to use URLs:**
- Images are already hosted on a CDN or cloud storage
- File size is very large (>5 MB)
- Convenience: no local Base64 encoding needed

### 7.3 Choosing Upload Method

| Method | Pros | Cons | When to Use |
|--------|------|------|-----------|
| **Base64 Data URL** | Single API call, no external dependencies, simple | Larger payload, Base64 overhead (+33%) | ✓ Recommended for most cases |
| **HTTP URL** | Smaller API payload, MiniMax manages download | Requires external hosting, URL must be public | ✓ Large files, existing cloud storage |

---

## 8. RATE LIMITING & CONSTRAINTS

### 8.1 Rate Limits

| Tier | Requests Per Minute (RPM) | Concurrent Tasks | Status |
|------|--------------------------|-----------------|--------|
| **Free Users** | 5 RPM | Limited | Applies to demo accounts |
| **Paid Users** | 20 RPM | Higher | Standard paid tier |
| **Enterprise** | Custom | Unlimited | Contact sales |

**RPM Calculation:**
- Measured against `/v1/video_generation` submission requests
- Status polling (`/v1/query/video_generation`) typically doesn't count
- File retrieval typically doesn't count

**Example:** With 5 RPM limit, minimum 12 seconds between submissions:
- 60 seconds ÷ 5 requests = 12 seconds per request

### 8.2 Rate Limit Response

**HTTP Status:** 429 Too Many Requests

```json
{
  "base_resp": {
    "status_code": 1010,
    "status_msg": "Rate limit exceeded"
  }
}
```

**Response Headers:**
```
Retry-After: 60
```

**Handling Rate Limits:**
```python
import asyncio
import random

async def submit_with_rate_limit_handling(api_key: str, payload: dict, 
                                         max_retries: int = 5) -> Optional[str]:
    """Submit FL2V task with rate limit retry logic."""
    
    import httpx
    
    url = "https://api.minimaxi.com/v1/video_generation"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(url, headers=headers, json=payload)
            
            # Check for rate limit
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                wait_time = retry_after + random.uniform(0, 5)
                print(f"Rate limited. Waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                continue
            
            response.raise_for_status()
            
            data = response.json()
            if data.get("base_resp", {}).get("status_code") == 0:
                return data.get("task_id")
            else:
                raise Exception(f"API error: {data['base_resp']}")
        
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
            else:
                raise
    
    raise Exception(f"Failed after {max_retries} attempts")
```

### 8.3 Other Constraints

| Constraint | Value | Notes |
|-----------|-------|-------|
| **Max task_id validity** | 7 days | Can only poll completed tasks for 7 days |
| **Max download URL validity** | 7 days | Must download video within 7 days of completion |
| **Max concurrent tasks per API key** | ~10-50 | Depends on tier, contact support for higher |
| **Max prompt length** | 2000 characters | Longer prompts are truncated |
| **Image file size** | 5 MB max | Per image |
| **Request timeout** | 30 seconds | MiniMax server may take longer |

---

## 9. ERROR HANDLING PATTERNS

### 9.1 Common Error Scenarios & Solutions

| Scenario | HTTP Status | Response | Common Cause | Solution |
|----------|-------------|----------|--------------|----------|
| Invalid API key | 200 | `status_code: 1001` | Expired or wrong key | Verify key in dashboard, regenerate if needed |
| Region mismatch | 200 | `status_code: 1002` | Key is for different region | Check API host matches key region |
| FL2V not supported by model | 200 | `status_code: 1003` | Using wrong model | Use `MiniMax-Hailuo-02` |
| Invalid image format | 200 | `status_code: 1005` | Bad Base64 or image | Verify PNG/JPEG encoding, re-encode |
| Rate limited | 429 | Rate limit headers | Too many requests | Implement backoff, wait 10+ seconds |
| Quota exceeded | 200 | `status_code: 1020` | Out of credits | Add payment method or buy credits |
| Network timeout | 408/504 | Connection error | Slow network or server | Retry with exponential backoff |
| Task expired | 200 | `status: "Fail"` | Task ID over 7 days old | Keep task_id in database, don't reuse after 7 days |
| Server error | 500-503 | Server error response | MiniMax infrastructure issue | Retry with exponential backoff (10s → 30s → 60s) |
| Webhook URL unreachable | N/A | Callback not received | Callback endpoint down/invalid | Ensure endpoint is publicly accessible, returns 200 |

### 9.2 Retry Strategy with Exponential Backoff

```python
import asyncio
import random
from typing import Callable, Any, Optional

async def retry_with_backoff(
    func: Callable,
    max_retries: int = 5,
    base_wait: float = 1.0,
    max_wait: float = 60.0,
    jitter: bool = True
) -> Optional[Any]:
    """
    Generic retry function with exponential backoff.
    
    Waits: 1s, 2s, 4s, 8s, 16s (with optional jitter)
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            return await func()
        
        except Exception as e:
            last_error = e
            
            if attempt < max_retries - 1:
                # Exponential backoff: 2^attempt
                wait_time = min(base_wait * (2 ** attempt), max_wait)
                
                # Add jitter to prevent thundering herd
                if jitter:
                    wait_time += random.uniform(0, wait_time * 0.1)
                
                print(f"Attempt {attempt + 1} failed: {e}")
                print(f"Retrying in {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
            else:
                print(f"Failed after {max_retries} attempts")
    
    raise last_error

# Usage example for FL2V submission
async def submit_fl2v_with_retry(api_key: str, payload: dict) -> str:
    """Submit FL2V task with automatic retry on transient failures."""
    
    async def _submit():
        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.minimaxi.com/v1/video_generation",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("base_resp", {}).get("status_code") != 0:
                raise Exception(f"API error: {data['base_resp']['status_msg']}")
            
            return data["task_id"]
    
    return await retry_with_backoff(_submit)
```

### 9.3 Comprehensive Error Handling Example

```python
import logging
from enum import Enum

logger = logging.getLogger("FL2V")

class FL2VError(Enum):
    """FL2V-specific error classifications."""
    INVALID_API_KEY = "invalid_api_key"
    INVALID_IMAGE = "invalid_image"
    MODEL_NOT_SUPPORTED = "model_not_supported"
    RATE_LIMITED = "rate_limited"
    QUOTA_EXCEEDED = "quota_exceeded"
    TASK_EXPIRED = "task_expired"
    GENERATION_FAILED = "generation_failed"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"

async def submit_fl2v_with_comprehensive_error_handling(
    api_key: str, 
    payload: dict
) -> tuple[Optional[str], Optional[FL2VError]]:
    """
    Submit FL2V task with comprehensive error classification.
    
    Returns:
        (task_id, error_type) - One is None on success
    """
    
    import httpx
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.minimaxi.com/v1/video_generation",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload
            )
        
        # Handle rate limiting
        if response.status_code == 429:
            logger.warning("Rate limit exceeded")
            return None, FL2VError.RATE_LIMITED
        
        response.raise_for_status()
        
        data = response.json()
        
        # Handle API errors
        api_status = data.get("base_resp", {})
        if api_status.get("status_code") != 0:
            msg = api_status.get("status_msg", "Unknown error")
            
            # Classify error
            if "Invalid API key" in msg or "Unauthorized" in msg:
                logger.error(f"Invalid API key: {msg}")
                return None, FL2VError.INVALID_API_KEY
            
            elif "image" in msg.lower():
                logger.error(f"Invalid image: {msg}")
                return None, FL2VError.INVALID_IMAGE
            
            elif "model" in msg.lower() or "not support" in msg.lower():
                logger.error(f"Model not supported for FL2V: {msg}")
                return None, FL2VError.MODEL_NOT_SUPPORTED
            
            elif "quota" in msg.lower():
                logger.error(f"Quota exceeded: {msg}")
                return None, FL2VError.QUOTA_EXCEEDED
            
            else:
                logger.error(f"API error {api_status['status_code']}: {msg}")
                return None, FL2VError.UNKNOWN_ERROR
        
        # Success
        task_id = data.get("task_id")
        logger.info(f"FL2V task submitted: {task_id}")
        return task_id, None
    
    except asyncio.TimeoutError:
        logger.error("Network timeout submitting FL2V task")
        return None, FL2VError.NETWORK_ERROR
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return None, FL2VError.NETWORK_ERROR
```

---

## 10. COMPLETE WORKFLOW EXAMPLE

### 10.1 Full FL2V Generation Workflow

```python
import asyncio
import base64
from pathlib import Path
from typing import Optional

class FL2VGenerator:
    """Production-grade FL2V video generator."""
    
    API_BASE = "https://api.minimaxi.com"
    MODEL = "MiniMax-Hailuo-02"  # Only FL2V-supporting model
    DEFAULT_RESOLUTION = "768P"
    DEFAULT_DURATION = 6
    POLL_INTERVAL = 10  # seconds
    MAX_WAIT_TIME = 600  # 10 minutes
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def submit_fl2v_task(
        self,
        prompt: str,
        first_frame_path: str,
        last_frame_path: str,
        duration: int = 6,
        resolution: str = "768P"
    ) -> Optional[str]:
        """Step 1: Submit FL2V video generation task."""
        
        import httpx
        
        # Load and encode images
        first_frame_url = self._load_image_as_data_url(first_frame_path)
        last_frame_url = self._load_image_as_data_url(last_frame_path)
        
        payload = {
            "model": self.MODEL,
            "prompt": prompt[:2000],  # Max 2000 chars
            "duration": duration,
            "resolution": resolution,
            "first_frame_image": first_frame_url,
            "last_frame_image": last_frame_url,
            "prompt_optimizer": True,
            "fast_pretreatment": False
        }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.API_BASE}/v1/video_generation",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload
                )
            
            if response.status_code == 429:
                raise Exception("Rate limited - wait before retrying")
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("base_resp", {}).get("status_code") != 0:
                raise Exception(f"API error: {data['base_resp']['status_msg']}")
            
            task_id = data["task_id"]
            print(f"✓ FL2V task submitted: {task_id}")
            return task_id
        
        except Exception as e:
            print(f"✗ Failed to submit FL2V task: {e}")
            return None
    
    async def poll_status(self, task_id: str) -> Optional[str]:
        """Step 2: Poll status until completion."""
        
        import httpx
        
        start_time = asyncio.get_event_loop().time()
        poll_count = 0
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            
            if elapsed > self.MAX_WAIT_TIME:
                raise TimeoutError(f"Task did not complete in {self.MAX_WAIT_TIME}s")
            
            poll_count += 1
            
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(
                        f"{self.API_BASE}/v1/query/video_generation",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        params={"task_id": task_id}
                    )
                
                response.raise_for_status()
                data = response.json()
                status = data.get("status")
                
                print(f"[Poll {poll_count}] Status: {status} (elapsed: {elapsed:.1f}s)")
                
                if status == "Success":
                    file_id = data.get("file_id")
                    print(f"✓ Generation complete: {file_id}")
                    return file_id
                
                elif status == "Fail":
                    raise Exception(f"Generation failed: {data.get('error_message')}")
                
                elif status in ["submitted", "processing"]:
                    await asyncio.sleep(self.POLL_INTERVAL)
                
                else:
                    print(f"⚠ Unknown status: {status}")
                    await asyncio.sleep(self.POLL_INTERVAL)
            
            except asyncio.TimeoutError:
                print("⚠ Polling timeout, retrying...")
                await asyncio.sleep(self.POLL_INTERVAL)
            
            except Exception as e:
                print(f"⚠ Polling error: {e}")
                await asyncio.sleep(self.POLL_INTERVAL)
    
    async def download_video(self, file_id: str, output_path: str):
        """Step 3: Download generated video."""
        
        import httpx
        
        # Get download URL
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.API_BASE}/v1/files/retrieve",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={"file_id": file_id}
            )
        
        response.raise_for_status()
        download_url = response.json()["file"]["download_url"]
        
        # Download video
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(download_url)
            response.raise_for_status()
            
            with open(output_path, "wb") as f:
                f.write(response.content)
        
        print(f"✓ Video downloaded: {output_path}")
    
    async def generate_full(
        self,
        prompt: str,
        first_frame_path: str,
        last_frame_path: str,
        output_path: str,
        **kwargs
    ) -> bool:
        """Complete workflow: submit → poll → download."""
        
        try:
            # Step 1: Submit
            task_id = await self.submit_fl2v_task(
                prompt, 
                first_frame_path, 
                last_frame_path,
                **kwargs
            )
            if not task_id:
                return False
            
            # Step 2: Poll
            file_id = await self.poll_status(task_id)
            if not file_id:
                return False
            
            # Step 3: Download
            await self.download_video(file_id, output_path)
            
            return True
        
        except Exception as e:
            print(f"✗ Workflow failed: {e}")
            return False
    
    @staticmethod
    def _load_image_as_data_url(image_path: str) -> str:
        """Convert image file to Base64 data URL."""
        path = Path(image_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        with open(path, "rb") as f:
            image_data = f.read()
        
        # Detect MIME type from extension
        ext = path.suffix.lower()
        mime_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp"
        }.get(ext, "image/jpeg")
        
        b64_str = base64.b64encode(image_data).decode("utf-8")
        return f"data:{mime_type};base64,{b64_str}"

# Usage example
async def main():
    gen = FL2VGenerator(api_key="your-api-key")
    
    success = await gen.generate_full(
        prompt="A person walks through a beautiful forest towards a waterfall",
        first_frame_path="path/to/first_frame.jpg",
        last_frame_path="path/to/last_frame.jpg",
        output_path="output_video.mp4",
        duration=6,
        resolution="1080P"
    )
    
    if success:
        print("✓ FL2V video generation workflow complete!")
    else:
        print("✗ Workflow failed")

# Run
asyncio.run(main())
```

---

## 11. KEY TECHNICAL POINTS SUMMARY

| Aspect | Details |
|--------|---------|
| **Endpoint** | `POST https://api.minimaxi.com/v1/video_generation` |
| **Authentication** | `Authorization: Bearer {API_KEY}` |
| **Model** | Must use `MiniMax-Hailuo-02` (only FL2V support) |
| **Images** | Base64 data URLs or HTTP URLs (PNG/JPEG/WebP) |
| **Prompt** | Max 2000 characters, descriptive scene details |
| **Duration** | 6 or 10 seconds |
| **Resolution** | 512P, 768P (recommended), or 1080P |
| **Response** | `task_id` for polling |
| **Status Polling** | `GET /v1/query/video_generation?task_id={task_id}` every 10 seconds |
| **Status Values** | submitted → processing → Success/Fail |
| **File Retrieval** | `GET /v1/files/retrieve?file_id={file_id}` |
| **Rate Limit** | 5 RPM free / 20 RPM paid |
| **Timeout** | ~30-120 seconds typical generation time |
| **Error Handling** | Check `status_code` in response, implement backoff |

---

## 12. QUICK REFERENCE - API CALLS

### Submit FL2V Task
```bash
curl -X POST https://api.minimaxi.com/v1/video_generation \
  -H "Authorization: Bearer API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MiniMax-Hailuo-02",
    "prompt": "A person walks towards a tree",
    "duration": 6,
    "resolution": "768P",
    "first_frame_image": "data:image/jpeg;base64,...",
    "last_frame_image": "data:image/jpeg;base64,..."
  }'
```

### Poll Status
```bash
curl -X GET "https://api.minimaxi.com/v1/query/video_generation?task_id=106916112212032" \
  -H "Authorization: Bearer API_KEY"
```

### Download Video
```bash
curl -X GET "https://api.minimaxi.com/v1/files/retrieve?file_id=205258526306433" \
  -H "Authorization: Bearer API_KEY"
```

---

**Last Updated:** January 8, 2026  
**Research Source:** MiniMax official API documentation, workspace reference implementations
