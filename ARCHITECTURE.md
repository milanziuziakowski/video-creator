# Iterative 1-Minute Video Studio (MiniMax + OpenAI Agents) — Architecture Guideline

## Goal
Build 1-minute videos by generating 6s/10s segments with:
- cloned narration voice from user-provided audio
- first-frame + last-frame controlled video generation
- human approval after every segment (HITL)
- ffmpeg-based stitching so audio/video stay aligned

## Key Constraints
- target_duration_sec <= 60
- segment_len_sec ∈ {6, 10}
- per-segment approval (approve / regenerate / edit prompts)
- deterministic media ops (concat/mux/frames) must be done outside the LLM

## System Components
1) **OpenAI Orchestrator (Agents SDK / Agent Builder prototype)**
   - Supervisor/Director Agent: creates a full VideoPlan (segments, prompts, narration, continuity rules)
   - Frame Designer Agent: produces end-frame prompts (and optionally generates end-frame images)
   - HITL Gate: blocks progress until user approves each segment

2) **Tooling Layer (MCP Servers)**
   - MiniMax MCP (official):
     - voice_clone, text_to_audio, generate_video, query_video_generation, text_to_image
   - MediaOps MCP (custom, Python + ffmpeg):
     - extract_last_frame(video) -> image
     - concat_videos(videos[]) -> video
     - concat_audios(audios[]) -> audio
     - mux_audio_video(video, audio) -> final_video
     - normalize_audio(), probe_duration()
   - FL2V MCP Wrapper (custom):
     - create_fl2v_task(prompt, first_frame_image, last_frame_image, model, duration, resolution) -> task_id/video_url

3) **Storage + UI**
   - Object storage for images/audio/video (S3/Azure Blob)
   - DB for project metadata + segment statuses
   - UI for upload + preview + approve/regenerate per segment
   - Job queue for long video tasks + polling async results

## Project State Schema (minimal)
- project_id
- target_duration_sec
- segment_len_sec
- segment_count
- voice_id
- segments[]:
  - segment_index
  - prompt
  - narration_text
  - first_frame_image_url
  - last_frame_image_url
  - video_task_id
  - segment_video_url
  - segment_audio_url
  - approved: bool
- assembled_video_url
- assembled_audio_url
- final_video_url

## Runtime Flow (happy path)
1) Inputs: start_frame_image, voice_sample_audio, story_prompt, duration<=60, segment_len
2) Supervisor builds VideoPlan JSON (segments + narration + continuity rules)
3) Clone voice -> voice_id
4) For each segment i:
   - first_frame = start_frame (i=0) else last_frame(prev_segment_video)
   - last_frame = generated end-frame image for segment i
   - generate segment video via FL2V (first+last frame)
   - generate segment audio via cloned voice TTS
   - HITL: user approves or edits prompt -> regenerate if needed
   - append segment_video + segment_audio to assembled tracks
5) Finalize: mux assembled_video + assembled_audio -> final_video (<= 60s)

## Implementation Notes
- Prefer running the segment loop in code (Agents SDK) or UI-triggered “one segment per run”
  to avoid workflow-loop edge cases with approvals.
- Treat ffmpeg ops as deterministic tools (MediaOps MCP), not “LLM code execution”.
- Store every intermediate artifact; never regenerate blindly (cost control).
