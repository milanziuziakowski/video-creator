# Video Generation Status Polling - Beginner's Guide

## What's This All About? (Simple Explanation)

Imagine you order a pizza:

1. **You call the restaurant** → "I want a pizza with pepperoni"
2. **They give you a number** → "Your order number is 42"
3. **You can't wait at the counter** → You go home
4. **You check on your pizza** → "Is order 42 ready yet?"
5. **Restaurant says** → "Still cooking... 10 more minutes"
6. **You check again later** → "Your pizza is ready! Come pick it up"

**That's exactly what `query_video_generation()` does!**

- Step 1 = `generate_video()` (submits generation task)
- Step 2 = Returns task_id (your order number)
- Steps 4-6 = `query_video_generation()` (checking status repeatedly)

---

## How Video Generation Works in MiniMax

### The Problem

Generating a video takes **time** (2-10 minutes):
- Your code can't just wait (blocks everything)
- User experience would be terrible
- Server resources would be wasted

### The Solution: Async Operations

```
Time: 0 seconds
├─ generate_video() called
│  ├─ Submit to MiniMax
│  └─ Return task_id immediately (don't wait)
│  
Time: Continues...
├─ query_video_generation() called every 10 seconds
│  ├─ Check: "Is task_id done yet?"
│  └─ Return status
│  
Time: 120-600 seconds
└─ Finally: Status = "completed"
   ├─ Get file_id
   └─ Download video!
```

---

## The Status Values Explained

### 1. "submitted"
```
┌─────────────────────┐
│   Your video job    │
│   is in the queue   │
│   waiting to start  │
└─────────────────────┘
```
- **What it means:** Waiting in line
- **What to do:** Keep checking
- **When it changes:** When server is ready to process

### 2. "processing"
```
┌─────────────────────┐
│   Computer is       │
│   generating your   │
│   video right now   │
│   ████████░░░░░░░░  │ 50% done
└─────────────────────┘
```
- **What it means:** Currently being created
- **How long:** Usually 2-10 minutes
- **What to do:** Keep checking every 10 seconds

### 3. "completed"
```
┌─────────────────────┐
│   Your video is     │
│   READY!            │
│   ✅ file_id: 12345 │
│   Ready to download │
└─────────────────────┘
```
- **What it means:** Generation finished successfully
- **You get:** file_id to download the video
- **What to do:** Download the video file

### 4. "failed"
```
┌──────────────────────┐
│   ❌ ERROR!          │
│   Generation failed  │
│   Reason: Bad input  │
└──────────────────────┘
```
- **What it means:** Something went wrong
- **You get:** Error message explaining why
- **What to do:** Fix the input and try again

---

## How the Code Actually Works

### Step-by-Step Explanation

```python
# 1. User calls the function with task_id
result = await query_video_generation("abc123def456")

# Inside the function:
# ├─ Validate task_id (make sure it's not empty)
# ├─ Call MiniMax API to check status
# │  └─ HTTP GET /v1/query/video_generation?task_id=abc123def456
# ├─ Parse the response from MiniMax
# └─ Return a nice result dict

# 2. Result comes back with status
if result["status"] == "completed":
    file_id = result["file_id"]
    # ✅ Video is ready! Use file_id to download
    
elif result["status"] == "processing":
    # ⏳ Still working... check again in 10 seconds
    
elif result["status"] == "failed":
    error = result["error"]
    # ❌ Something went wrong
```

---

## What About Errors?

### Transient Errors (Temporary)
```
Error: "Connection reset" or "502 Bad Gateway"
├─ Reason: Temporary server problem
├─ Solution: Automatic retry with backoff
│          Wait 1 second → retry
│          Wait 2 seconds → retry
│          Wait 4 seconds → retry
└─ Result: Usually succeeds on retry
```

### Permanent Errors (Fatal)
```
Error: "404 Not Found" or "task_id invalid"
├─ Reason: Your task_id is wrong
├─ Solution: Check task_id, regenerate with new one
└─ Result: Need human intervention
```

---

## Real-World Example: Making a Video

### Complete Workflow

```
┌─────────────────────────────────────────────────────┐
│ Step 1: Submit Video Generation                     │
│ ─────────────────────────────────────────────────────│
│ generate_video(                                     │
│   prompt="Beautiful sunset over mountains",         │
│   first_frame="s3://bucket/frame1.jpg",             │
│   last_frame="s3://bucket/frame2.jpg"               │
│ )                                                   │
│ → Returns: task_id = "video_123456"                 │
│ → Takes: < 1 second                                 │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ Step 2: Poll Status (Every 10 seconds)              │
│ ─────────────────────────────────────────────────────│
│ Iteration 1 (10 sec):  status = "submitted"         │
│ Iteration 2 (20 sec):  status = "submitted"         │
│ Iteration 3 (30 sec):  status = "processing"        │
│ Iteration 4 (40 sec):  status = "processing"        │
│ ...                                                 │
│ Iteration 15 (150 sec): status = "completed"        │
│                         file_id = 54321             │
│ → Takes: 2.5 minutes                                │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ Step 3: Download Video (Future Implementation)      │
│ ─────────────────────────────────────────────────────│
│ retrieve_video_file(file_id="54321")                │
│ → Returns: video_url = "s3://bucket/video.mp4"      │
│ → Takes: 10-30 seconds                              │
└─────────────────────────────────────────────────────┘
                         ↓
                   ✅ Video Ready!
```

**Total Time:** 3-4 minutes from start to finish

---

## The Polling Loop Explained

### Why We Check Every 10 Seconds?

```
Too fast (every 1 second):
├─ Wastes API rate limit
├─ Floods the server
└─ No benefit (status won't change that fast)

Too slow (every 60 seconds):
├─ User has to wait longer
├─ No harm, but slower
└─ Could miss the completion

Just right (every 10 seconds):
├─ Respects API limits
├─ Detects completion quickly
└─ Balances efficiency and user experience
```

### How Long Does It Actually Take?

```
Typical Scenarios:

480p video, 6 seconds, turbo model:
   2-4 minutes of generating
   + polls every 10 seconds
   = status updates every 10 seconds
   = about 12-24 status checks

720p video, 6 seconds, standard model:
   4-8 minutes of generating
   = about 24-48 status checks

1080p video, 10 seconds, HD model:
   6-10 minutes of generating
   = about 36-60 status checks
```

---

## Key Concepts for Beginners

### Async/Await (Non-blocking)

```python
# ❌ WRONG - Blocks everything
result = query_video_generation(task_id)  # Waits here for 10 minutes!
print("This doesn't print for 10 minutes")

# ✅ CORRECT - Non-blocking
result = await query_video_generation(task_id)  # Returns immediately
print("This prints right away!")
```

**Why it matters:** Your server can handle other requests while waiting

### Retry Logic (Resilience)

```
First try:        Server says "503 Error, try again"
                  ├─ Wait 1 second
Second try:       Server says "503 Error, try again"
                  ├─ Wait 2 seconds
Third try:        Server says "Success! status=processing"
                  └─ We got the answer!
```

**Why it matters:** Temporary problems don't crash your code

---

## Common Questions

### Q: Why not just wait for the video to be done?

A: Because it takes 2-10 minutes! Your code would be stuck the whole time, unable to handle other users or requests. Polling lets you do other work while waiting.

### Q: What if I stop polling?

A: The video will still be generated! But you won't know when it's done. MiniMax keeps it for 7 days, so you can ask later. You just need the task_id.

### Q: Why every 10 seconds?

A: MiniMax API officially recommends 10 seconds. Faster wastes your API rate limit. Slower makes users wait longer for completion notification.

### Q: What if the server is down?

A: The code automatically retries 3 times with increasing delays (1s, 2s, 4s). If still failing, returns an error. You can try again later.

### Q: Why does it return file_id and not video_url?

A: file_id is just a reference number. To get the actual video file, we need a separate step (retrieve_video_file) that's implemented next.

---

## Debug Output (What You'll See)

```
INFO: query_video_generation called: task_id=abc123def456
INFO: Querying video generation status: task_id=abc123def456
INFO: Video generation still processing: task_id=abc123def456
```

**What this means:**
- Function was called with that task_id
- We asked MiniMax for status
- Status came back as "processing"

---

## Security Notes

### API Key Safety

```python
# ❌ WRONG - Never do this!
url = f"https://api.minimax.ai/video?key=sk-abc123"  # Exposed in URL!

# ✅ CORRECT - Use Authorization header
headers = {"Authorization": f"Bearer {MINIMAX_API_KEY}"}
response = await client.get(url, headers=headers)
```

**Why:** API keys in URLs can be logged, cached, or exposed. Headers are safer.

---

## Learning Path

### Level 1: Understand Concepts
- ✅ Read this beginner's guide
- ✅ Understand status values
- ✅ Know why polling is needed

### Level 2: Understand Code
- ✅ Read VIDEO_GENERATION_POLLING.md
- ✅ Understand retry logic
- ✅ See code structure

### Level 3: Implement & Test
- Get MINIMAX_API_KEY from MiniMax dashboard
- Add to .env file
- Run integration tests with real API

### Level 4: Integrate
- Wire into orchestrator.py
- Connect to full video generation workflow
- Test complete segment generation

---

## Quick Reference

| Term | Meaning |
|------|---------|
| task_id | Your order number for the video |
| file_id | Your receipt to download when ready |
| polling | Repeatedly asking "Is it done yet?" |
| async/await | Don't block, check back later |
| status | Current state (submitted, processing, completed, failed) |
| exponential backoff | Wait 1s, 2s, 4s between retries |
| rate limit | How many API calls allowed per minute |

---

## Summary

`query_video_generation()` does this:

1. **Takes task_id** → Your video order number
2. **Asks MiniMax** → "Is this video ready yet?"
3. **Gets status back** → submitted/processing/completed/failed
4. **Handles errors gracefully** → Retries if needed
5. **Returns result** → Simple dict you can understand

**Why you need it:** Videos take time, so you poll (check) repeatedly until done

**When to call it:** Every 10 seconds until status changes to "completed"

**Next:** Once completed, use file_id to download the video

---

**Ready to test with real API? Add MINIMAX_API_KEY to .env and run!**
