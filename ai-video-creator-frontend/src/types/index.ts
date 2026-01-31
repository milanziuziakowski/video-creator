export interface User {
  id: string;
  email: string;
  name: string;
  createdAt: string;
}

export interface Project {
  id: string;
  name: string;
  storyPrompt: string | null;
  targetDurationSec: number;
  segmentDurationSec: number;
  status: ProjectStatus;
  firstFrameUrl: string | null;
  audioSampleUrl: string | null;
  voiceId: string | null;
  finalVideoUrl: string | null;
  createdAt: string;
  updatedAt: string;
}

export type ProjectStatus =
  | 'created'
  | 'media_uploaded'
  | 'planning'
  | 'plan_ready'
  | 'generating'
  | 'completed'
  | 'failed';

export interface ProjectCreate {
  name: string;
  storyPrompt?: string;
  targetDurationSec?: number;
  segmentDurationSec?: number;
}

export interface ProjectUpdate {
  name?: string;
  storyPrompt?: string;
  targetDurationSec?: number;
  segmentDurationSec?: number;
}

export interface ProjectListResponse {
  projects: Project[];
  total: number;
}

export interface Segment {
  id: string;
  projectId: string;
  index: number;
  videoPrompt: string;
  narrationText: string;
  endFramePrompt: string | null;
  approved: boolean;
  status: SegmentStatus;
  firstFrameUrl: string | null;
  lastFrameUrl: string | null;
  videoUrl: string | null;
  audioUrl: string | null;
  durationSec: number | null;
  videoTaskId: string | null;
  createdAt: string;
  updatedAt: string;
}

export type SegmentStatus =
  | 'pending'
  | 'prompt_ready'
  | 'approved'
  | 'generating_video'
  | 'generating_audio'
  | 'generated'
  | 'segment_approved'
  | 'failed';

export interface SegmentUpdate {
  videoPrompt?: string;
  narrationText?: string;
  endFramePrompt?: string;
}

export interface VideoPlan {
  title: string;
  segments: SegmentPrompt[];
}

export interface SegmentPrompt {
  index: number;
  videoPrompt: string;
  narrationText: string;
  endFramePrompt: string | null;
  cameraMovement: string | null;
}

export interface GeneratePlanRequest {
  projectId: string;
  storyPrompt: string;
}

export interface GenerationStatus {
  taskId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number | null;
  fileId: string | null;
  errorMessage: string | null;
}
