# MiniMax Video Generation API - Status Polling & Querying Guide

**Source:** Official MiniMax Platform Documentation  
**Last Updated:** January 8, 2026  
**API Hosts:**
- Global: `https://api.minimax.io`
- Mainland China: `https://api.minimaxi.com`

---

## 1. VIDEO GENERATION WORKFLOW OVERVIEW

MiniMax video generation uses a **3-step asynchronous workflow**:

1. **Submit Task** → Receive `task_id`
2. **Poll Status** → Get `file_id` when complete
3. **Download Video** → Use `file_id` to retrieve video

---

## 2. TASK SUBMISSION (Step 1)

### 2.1 Submit Video Generation Task

**Endpoint:** `POST /v1/video_generation`

**Supported Video Generation Modes:**
- **T2V (Text-to-Video):** Generate from text prompt only
- **I2V (Image-to-Video):** First frame image + text prompt
- **FL2V (First-Last Frame to Video):** First frame + last frame + text prompt
- **S2V (Subject-to-Video):** Person reference image + text prompt

### 2.2 Request Format

**Headers:**
```http
Authorization: Bearer {API_KEY}
Content-Type: application/json
```

**Request Body (T2V Example):**
```json
{
  "model": "MiniMax-Hailuo-2.3",
  "prompt": "A man picks up a book, then reads.",
  "duration": 6,
  "resolution": "1080P",
  "callback_url": "https://your-domain.com/callback" 
}
```

### 2.3 Required vs Optional Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | ✓ | Model name (see Section 4.1) |
| `prompt` | string | ✓ | Video description (max 2000 chars) |
| `duration` | integer | ✗ | Video length in seconds (default: 6) |
| `resolution` | string | ✗ | 512P, 720P, 768P, 1080P (default: varies by model) |
| `prompt_optimizer` | boolean | ✗ | Auto-optimize prompt (default: true) |
| `fast_pretreatment` | boolean | ✗ | Shorten optimization time (default: false) |
| `first_frame_image` | string | ✗ | First frame URL or Base64 Data URL (I2V/FL2V) |
| `last_frame_image` | string | ✗ | Last frame URL or Base64 Data URL (FL2V only) |
| `subject_reference` | object | ✗ | Person reference for S2V mode |
| `callback_url` | string | ✗ | Webhook for async notifications |
| `aigc_watermark` | boolean | ✗ | Add watermark to video (default: false) |

### 2.4 Response Format

**Status Code:** 200 OK

```json
{
  "task_id": "106916112212032",
  "base_resp": {
    "status_code": 0,
    "status_msg": "success"
  }
}
```

**Key Fields:**
- `task_id` (string): Unique identifier for polling status and retrieving results
- `base_resp.status_code` (integer): 0 = success, non-zero = error
- `base_resp.status_msg` (string): Human-readable status message

---

## 3. STATUS POLLING (Step 2) - CORE IMPLEMENTATION

### 3.1 Query Task Status Endpoint

**Endpoint:** `GET /v1/query/video_generation`

**Request Format:**
```http
GET https://api.minimaxi.com/v1/query/video_generation?task_id=106916112212032
Authorization: Bearer {API_KEY}
```

**Query Parameters:**
```json
{
  "task_id": "string (required)"
}
```

### 3.2 Response Format

**Status Code:** 200 OK

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
| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Echo of the queried task ID |
| `status` | string | Current task status (see Section 3.3) |
| `file_id` | string | Video file ID (only on success) |
| `error_message` | string | Error details (on failure) |
| `base_resp.status_code` | integer | 0 = success, non-zero = error |
| `base_resp.status_msg` | string | Response message |

### 3.3 Status Values

| Status | Code | Meaning | Action |
|--------|------|---------|--------|
| `submitted` | - | Task accepted, in queue | Continue polling |
| `processing` | - | Video generation in progress | Continue polling |
| `Success` | - | Video generation complete | Retrieve `file_id`, proceed to download |
| `Fail` | - | Generation failed | Handle error with `error_message` |

**Status Flow:** submitted → processing → Success/Fail

### 3.4 Polling Behavior & Best Practices

#### Polling Interval
- **Recommended:** 10 seconds between polls
- **Rationale:** Balances responsiveness with server load
- **Typical Time to Completion:** 30-120 seconds (varies by resolution/duration)

#### Polling Loop Example (Python)
```python
import requests
import time

def query_task_status(task_id: str, api_key: str, max_wait_seconds: int = 600):
    """
    Poll task status until completion or timeout.
    
    Args:
        task_id: Task ID from submission
        api_key: MiniMax API key
        max_wait_seconds: Maximum time to wait (default: 10 minutes)
    
    Returns:
        file_id on success
        
    Raises:
        Exception on failure or timeout
    """
    url = "https://api.minimaxi.com/v1/query/video_generation"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"task_id": task_id}
    
    start_time = time.time()
    poll_count = 0
    
    while True:
        elapsed = time.time() - start_time
        
        # Timeout check
        if elapsed > max_wait_seconds:
            raise TimeoutError(
                f"Task {task_id} did not complete within {max_wait_seconds}s"
            )
        
        # Poll status
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            status = data.get("status")
            
            poll_count += 1
            print(f"Poll #{poll_count} - Status: {status} (elapsed: {elapsed:.1f}s)")
            
            if status == "Success":
                file_id = data.get("file_id")
                print(f"✓ Task completed successfully, file_id: {file_id}")
                return file_id
                
            elif status == "Fail":
                error_msg = data.get("error_message", "Unknown error")
                raise Exception(f"Video generation failed: {error_msg}")
                
            elif status in ["submitted", "processing"]:
                # Still processing, wait before next poll
                time.sleep(10)
            else:
                print(f"⚠ Unknown status: {status}, retrying...")
                time.sleep(10)
                
        except requests.exceptions.RequestException as e:
            print(f"⚠ Request error: {e}, retrying in 10s...")
            time.sleep(10)
```

### 3.5 Error Handling & Retry Logic

#### Common Error Scenarios

| Scenario | HTTP Status | Response | Action |
|----------|-------------|----------|--------|
| Invalid task_id | 200 | `{"status": "Fail"}` | Check task_id, may be expired |
| Network timeout | 408/504 | Exception | Retry after 10-30s |
| Rate limit exceeded | 429 | Response headers include retry-after | Back off exponentially |
| Unauthorized | 401 | `status_code: 401` | Verify API key and region alignment |
| Server error | 500-503 | Server error | Exponential backoff (10s → 30s → 60s) |

#### Retry Strategy
```python
import random
from typing import Optional

def query_with_retry(
    task_id: str, 
    api_key: str, 
    max_retries: int = 5,
    base_wait: int = 10
) -> str:
    """
    Query status with exponential backoff retry.
    """
    url = "https://api.minimaxi.com/v1/query/video_generation"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"task_id": task_id}
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url, 
                headers=headers, 
                params=params,
                timeout=30
            )
            
            if response.status_code == 429:
                # Rate limited - exponential backoff
                wait_time = base_wait * (2 ** attempt) + random.uniform(0, 1)
                print(f"Rate limited, waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            data = response.json()
            status = data.get("status")
            
            if status == "Success":
                return data.get("file_id")
            elif status == "Fail":
                raise Exception(f"Task failed: {data.get('error_message')}")
            elif status in ["submitted", "processing"]:
                return None  # Still processing
                
        except requests.exceptions.Timeout:
            wait_time = base_wait * (2 ** attempt)
            print(f"Timeout, retrying in {wait_time}s...")
            time.sleep(wait_time)
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = base_wait * (2 ** attempt)
                print(f"Error {e}, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
    
    raise Exception(f"Failed after {max_retries} retries")
```

---

## 4. MODEL & PARAMETER SPECIFICATIONS

### 4.1 Supported Models

| Model | T2V | I2V | FL2V | S2V | Max Duration | Max Resolution | Status |
|-------|-----|-----|------|-----|--------------|-----------------|--------|
| `MiniMax-Hailuo-2.3` | ✓ | ✓ | ✗ | ✗ | 6/10s | 768P/1080P | Latest |
| `MiniMax-Hailuo-2.3-Fast` | ✓ | ✓ | ✗ | ✗ | 6/10s | 768P/1080P | Optimized for speed |
| `MiniMax-Hailuo-02` | ✓ | ✓ | ✓ | ✗ | 6/10s | 512P/768P/1080P | Previous gen |
| `T2V-01-Director` | ✓ | ✗ | ✗ | ✗ | 6s | 720P | Legacy |
| `T2V-01` | ✓ | ✗ | ✗ | ✗ | 6s | 720P | Legacy |
| `I2V-01-Director` | ✗ | ✓ | ✗ | ✗ | 6s | 720P | Legacy |
| `I2V-01-live` | ✗ | ✓ | ✗ | ✗ | 6s | 720P | Legacy |
| `I2V-01` | ✗ | ✓ | ✗ | ✗ | 6s | 720P | Legacy |
| `S2V-01` | ✗ | ✗ | ✗ | ✓ | 6s | 1080P | Subject reference |

### 4.2 Resolution Availability by Model

| Resolution | MiniMax-Hailuo-2.3/2.3-Fast | MiniMax-Hailuo-02 | Other Models |
|------------|----------------------------|-------------------|--------------|
| 512P | ✗ | ✓ | ✗ |
| 720P | ✗ | ✗ | ✓ (default) |
| 768P | ✓ (default) | ✓ (default) | ✗ |
| 1080P | ✓ | ✓ | ✗ |

### 4.3 Duration Support

**MiniMax-Hailuo-2.3/2.3-Fast/Hailuo-02:**
- Options: 6 seconds or 10 seconds
- Default: 6 seconds
- Higher resolution → longer duration may affect quality

**Other Models:**
- Fixed at 6 seconds only

---

## 5. CALLBACK/WEBHOOK NOTIFICATIONS

### 5.1 Asynchronous Status Updates

Instead of polling, you can configure a callback URL to receive push notifications:

**Request Parameter:**
```json
{
  "callback_url": "https://your-domain.com/webhook/video-status"
}
```

### 5.2 Callback Flow

1. **Verification Request** (within 3 seconds of task submission):
   ```
   POST https://your-domain.com/webhook/video-status
   Content-Type: application/json
   
   {
     "challenge": "abc123xyz..."
   }
   ```
   
   **Required Response:**
   ```json
   {
     "challenge": "abc123xyz..."
   }
   ```
   Must return exact challenge value within 3 seconds.

2. **Status Update Notifications** (on status change):
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

### 5.3 Callback Implementation Example

```python
from fastapi import FastAPI, HTTPException, Request
import json

app = FastAPI()

@app.post("/video-callback")
async def receive_callback(request: Request):
    """Handle MiniMax video generation callbacks."""
    try:
        body = await request.json()
        challenge = body.get("challenge")
        
        # Verification request - echo challenge
        if challenge is not None:
            print(f"Received verification challenge: {challenge}")
            return {"challenge": challenge}
        
        # Status update - handle result
        task_id = body.get("task_id")
        status = body.get("status")
        file_id = body.get("file_id")
        error_msg = body.get("error_message")
        
        print(f"Task {task_id} status: {status}")
        
        if status == "Success":
            print(f"Video ready for download, file_id: {file_id}")
            # Save file_id to database, trigger download
        elif status == "Fail":
            print(f"Generation failed: {error_msg}")
            # Handle failure
        
        return {"status": "received"}
        
    except Exception as e:
        print(f"Error processing callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 6. FILE RETRIEVAL (Step 3)

### 6.1 Get Download URL

**Endpoint:** `GET /v1/files/retrieve`

**Request:**
```http
GET https://api.minimaxi.com/v1/files/retrieve?file_id=205258526306433
Authorization: Bearer {API_KEY}
```

**Response:**
```json
{
  "file": {
    "file_id": "205258526306433",
    "file_name": "video.mp4",
    "file_size": 1024000,
    "download_url": "https://filecdn.minimax.chat/...",
    "created_at": "2024-01-15T10:30:00Z",
    "expires_at": "2024-01-22T10:30:00Z"
  }
}
```

### 6.2 Download and Save Video

```python
import requests

def download_video(file_id: str, api_key: str, output_path: str = "video.mp4"):
    """Download generated video using file_id."""
    # Get download URL
    url = "https://api.minimaxi.com/v1/files/retrieve"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"file_id": file_id}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    download_url = response.json()["file"]["download_url"]
    file_name = response.json()["file"]["file_name"]
    
    # Download video
    video_response = requests.get(download_url, stream=True)
    video_response.raise_for_status()
    
    # Save to disk
    with open(output_path, "wb") as f:
        for chunk in video_response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    
    print(f"✓ Video saved to {output_path} ({file_name})")
```

---

## 7. RATE LIMITING & QUOTAS

### 7.1 Rate Limits for Video Generation

| Metric | Free Users | Paid Users |
|--------|-----------|-----------|
| **RPM** (Requests Per Minute) | 5 | 20 |
| **Concurrent Tasks** | Limited | Higher |
| **Burst Capacity** | None | Limited |

**RPM Definition:** Number of `/v1/video_generation` submission requests per minute

**Note:** Status polling (`/v1/query/video_generation`) requests typically don't count against video RPM limits.

### 7.2 Error Response for Rate Limiting

**HTTP Status:** 429 Too Many Requests

**Response Headers:**
```
Retry-After: 60
```

### 7.3 Respecting Rate Limits

```python
import time
from functools import wraps

def respect_rate_limit(min_interval: float = 12.0):
    """Decorator to enforce minimum interval between API calls."""
    last_call = [0.0]  # Use list for closure mutability
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_call[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            
            result = func(*args, **kwargs)
            last_call[0] = time.time()
            return result
        return wrapper
    return decorator

@respect_rate_limit(min_interval=12.0)  # 5 RPM = 1 req per 12 sec
def submit_video_generation(prompt: str, api_key: str):
    # Submit video generation
    pass
```

### 7.4 Requesting Higher Limits

**Current limits too low?**
- Contact: api@minimaxi.com
- Or: Use official support channels
- **Timeline:** 3-5 business days for approval
- **Requirement:** Data showing business need

---

## 8. BEST PRACTICES FOR PRODUCTION

### 8.1 Complete Workflow Implementation

```python
import requests
import time
from datetime import datetime, timedelta

class MiniMaxVideoGenerator:
    """Production-grade MiniMax video generation client."""
    
    BASE_URL = "https://api.minimaxi.com"
    POLL_INTERVAL = 10  # seconds
    MAX_WAIT_TIME = 600  # 10 minutes
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def submit_video(self, prompt: str, model: str = "MiniMax-Hailuo-2.3",
                    duration: int = 6, resolution: str = "1080P") -> str:
        """Submit video generation task."""
        url = f"{self.BASE_URL}/v1/video_generation"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution
        }
        
        response = requests.post(url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()
        
        task_id = response.json()["task_id"]
        print(f"✓ Task submitted: {task_id}")
        return task_id
    
    def poll_status(self, task_id: str, timeout: int = None) -> str:
        """Poll task status until completion."""
        if timeout is None:
            timeout = self.MAX_WAIT_TIME
        
        url = f"{self.BASE_URL}/v1/query/video_generation"
        params = {"task_id": task_id}
        start_time = time.time()
        poll_count = 0
        
        while time.time() - start_time < timeout:
            poll_count += 1
            elapsed = time.time() - start_time
            
            try:
                response = requests.get(
                    url, 
                    headers=self.headers, 
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                status = data.get("status")
                
                print(f"[Poll {poll_count}] Status: {status} (+{elapsed:.1f}s)")
                
                if status == "Success":
                    file_id = data.get("file_id")
                    print(f"✓ Generation complete, file_id: {file_id}")
                    return file_id
                
                elif status == "Fail":
                    error = data.get("error_message", "Unknown error")
                    raise Exception(f"Generation failed: {error}")
                
                else:  # submitted or processing
                    time.sleep(self.POLL_INTERVAL)
            
            except requests.exceptions.Timeout:
                print("⚠ Timeout on status poll, retrying...")
                time.sleep(self.POLL_INTERVAL)
            except requests.exceptions.RequestException as e:
                print(f"⚠ Request error: {e}, retrying...")
                time.sleep(self.POLL_INTERVAL)
        
        raise TimeoutError(f"Task {task_id} did not complete in {timeout}s")
    
    def download_video(self, file_id: str, output_path: str = "output.mp4"):
        """Download video file."""
        url = f"{self.BASE_URL}/v1/files/retrieve"
        params = {"file_id": file_id}
        
        response = requests.get(url, headers=self.headers, params=params, timeout=30)
        response.raise_for_status()
        
        download_url = response.json()["file"]["download_url"]
        
        video_response = requests.get(download_url, stream=True, timeout=60)
        video_response.raise_for_status()
        
        with open(output_path, "wb") as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"✓ Video downloaded: {output_path}")
    
    def generate_full_workflow(self, prompt: str, output_path: str = "video.mp4") -> bool:
        """Complete workflow: submit → poll → download."""
        try:
            # Step 1: Submit
            task_id = self.submit_video(prompt)
            
            # Step 2: Poll
            file_id = self.poll_status(task_id)
            
            # Step 3: Download
            self.download_video(file_id, output_path)
            
            return True
        
        except Exception as e:
            print(f"✗ Workflow failed: {e}")
            return False

# Usage Example
if __name__ == "__main__":
    gen = MiniMaxVideoGenerator(api_key="your-api-key")
    
    prompt = "A serene landscape with mountains and a flowing river at sunset"
    success = gen.generate_full_workflow(prompt, "output.mp4")
    
    if success:
        print("✓ Video generation workflow complete!")
    else:
        print("✗ Video generation workflow failed!")
```

### 8.2 Monitoring & Logging

```python
import logging
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MiniMaxVideoGen")

def log_task_submission(task_id: str, prompt: str, model: str):
    """Log video generation submission."""
    logger.info(f"Task submitted | task_id={task_id} | model={model} | prompt_len={len(prompt)}")

def log_polling_status(task_id: str, status: str, poll_num: int, elapsed: float):
    """Log polling status."""
    logger.info(f"Task status | task_id={task_id} | status={status} | poll={poll_num} | elapsed={elapsed:.1f}s")

def log_task_complete(task_id: str, file_id: str, total_time: float):
    """Log task completion."""
    logger.info(f"Task completed | task_id={task_id} | file_id={file_id} | total_time={total_time:.1f}s")
```

### 8.3 Error Recovery & Resilience

- **Implement exponential backoff** for transient errors (timeouts, 5xx)
- **Store task_ids** in database for recovery after outages
- **Handle rate limiting gracefully** with back-off strategy
- **Validate API key/host pairing** (global vs. mainland)
- **Set reasonable timeouts** (30s for requests, 10min total)
- **Monitor callback delivery** if using webhook notifications

---

## 9. TROUBLESHOOTING COMMON ISSUES

| Issue | Cause | Solution |
|-------|-------|----------|
| "Invalid API key" | Region mismatch | Verify API host matches key region (global vs. mainland) |
| 429 Rate limited | Too many requests | Implement exponential backoff, respect 10s interval |
| Timeout on poll | Network issues | Retry with increasing delays, check timeout value |
| Task "Fail" status | Model overloaded or bad prompt | Check prompt length/format, try with simpler description |
| file_id expired | Download URL expired | Download within 7 days of completion |
| Callback not received | Endpoint unreachable | Ensure endpoint is public, returns 200, echo challenge correctly |

---

## 10. SUMMARY - KEY IMPLEMENTATION POINTS

✅ **3-Step Workflow:** Submit → Poll (every 10s) → Download  
✅ **Query Endpoint:** `GET /v1/query/video_generation?task_id=XXX`  
✅ **Status Values:** submitted → processing → Success/Fail  
✅ **Polling Interval:** 10 seconds recommended  
✅ **Max Wait Time:** 10 minutes typical (vary by resolution/model)  
✅ **Rate Limits:** 5 RPM (free) / 20 RPM (paid)  
✅ **Error Handling:** Exponential backoff, timeout checks, validation  
✅ **Callbacks:** Optional webhook for push notifications  
✅ **FL2V & I2V:** Similar polling as general video generation  
✅ **Production Ready:** Use class-based client with logging/monitoring  

---

**Official Documentation:** https://platform.minimaxi.com/docs/guides/video-generation  
**GitHub Reference:** https://github.com/MiniMax-AI/MiniMax-MCP
