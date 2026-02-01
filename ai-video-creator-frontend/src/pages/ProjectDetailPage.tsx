import { useParams, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import {
  useProject,
  useProjectSegments,
  useUploadFirstFrame,
  useUploadAudioSample,
  useGeneratePlan,
  useCloneVoice,
  useApproveSegment,
  useApproveSegmentVideo,
  useUpdateSegment,
  useRegenerateSegment,
  useGenerateSegment,
  useFinalizeProject,
  useDeleteProject,
  getMediaUrl,
} from '../api';
import { FileUpload, SegmentCard, PageLoading, VideoPlayer, VoiceSelector } from '../components';
import type { ProjectStatus } from '../types';

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [activeSegmentId, _setActiveSegmentId] = useState<string | null>(null);

  const { data: project, isLoading: projectLoading } = useProject(projectId!);
  const { data: segments, isLoading: segmentsLoading } = useProjectSegments(
    projectId!
  );

  const uploadFirstFrame = useUploadFirstFrame();
  const uploadAudio = useUploadAudioSample();
  const generatePlan = useGeneratePlan();
  const cloneVoice = useCloneVoice();
  const approveSegment = useApproveSegment();
  const approveVideo = useApproveSegmentVideo();
  const updateSegment = useUpdateSegment();
  const regenerateSegment = useRegenerateSegment();
  const generateSegment = useGenerateSegment();
  const finalizeProject = useFinalizeProject();
  const deleteProject = useDeleteProject();

  if (projectLoading || segmentsLoading) {
    return <PageLoading message="Loading project..." />;
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Project not found</p>
      </div>
    );
  }

  const handleFirstFrameUpload = async (file: File) => {
    await uploadFirstFrame.mutateAsync({ projectId: projectId!, file });
  };

  const handleAudioUpload = async (file: File) => {
    await uploadAudio.mutateAsync({ projectId: projectId!, file });
  };

  const handleGeneratePlan = async () => {
    if (!project.storyPrompt) return;
    await generatePlan.mutateAsync({
      projectId: projectId!,
      storyPrompt: project.storyPrompt,
    });
  };

  const handleCloneVoice = async () => {
    await cloneVoice.mutateAsync(projectId!);
  };

  const handleFinalize = async () => {
    await finalizeProject.mutateAsync(projectId!);
  };

  const handleDelete = async () => {
    if (confirm('Are you sure you want to delete this project?')) {
      await deleteProject.mutateAsync(projectId!);
      navigate('/projects');
    }
  };

  const canGeneratePlan =
    project.firstFrameUrl && project.storyPrompt && project.voiceId;

  const canShowVoiceSelection =
    project.firstFrameUrl && project.storyPrompt;

  const allSegmentsApproved =
    segments && segments.length > 0 && segments.every((s) => s.status === 'segment_approved');

  // Check if all segments have audio but some need video generation
  const allHaveAudio = segments && segments.length > 0 && segments.every((s) => s.audioUrl);
  const allVideosGenerated = segments && segments.length > 0 && segments.every((s) => s.videoUrl);
  const someGenerating = segments && segments.some((s) => s.status === 'generating');

  // Find the next segment that can be generated (sequential)
  const nextGeneratableSegment = segments?.find((segment, index) => {
    if (segment.videoUrl || segment.status === 'generating') return false;
    if (!segment.audioUrl || !segment.firstFrameUrl) return false;
    // Check if previous segment has video (or is first segment)
    if (index === 0) return true;
    const prevSegment = segments[index - 1];
    return prevSegment?.videoUrl != null;
  });

  const handleGenerateNextVideo = async () => {
    if (!nextGeneratableSegment) return;
    await generateSegment.mutateAsync(nextGeneratableSegment.id);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
          <p className="text-gray-600">{project.storyPrompt || 'No story prompt'}</p>
        </div>
        <div className="flex gap-3">
          {allSegmentsApproved && (
            <button
              onClick={handleFinalize}
              disabled={finalizeProject.isPending}
              className="px-4 py-2 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 disabled:opacity-50"
              data-testid="finalize-button"
            >
              {finalizeProject.isPending ? 'Finalizing...' : 'Finalize Video'}
            </button>
          )}
          <button
            onClick={handleDelete}
            disabled={deleteProject.isPending}
            className="px-4 py-2 bg-red-100 text-red-700 font-medium rounded-lg hover:bg-red-200 disabled:opacity-50"
          >
            Delete
          </button>
        </div>
      </div>

      {/* Status Bar */}
      <ProjectStatusBar status={project.status} />

      {/* Media Upload Section */}
      {(project.status === 'created' || project.status === 'media_uploaded') && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload Media</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <FileUpload
              accept="image/*"
              label="First Frame Image"
              onUpload={handleFirstFrameUpload}
              isLoading={uploadFirstFrame.isPending}
              previewUrl={getMediaUrl(project.firstFrameUrl)}
              type="image"
            />
            <FileUpload
              accept="audio/*"
              label="Voice Sample (for cloning)"
              onUpload={handleAudioUpload}
              isLoading={uploadAudio.isPending}
              previewUrl={getMediaUrl(project.audioSampleUrl)}
              type="audio"
            />
          </div>

          {canShowVoiceSelection && (
            <div className="mt-6 space-y-4">
              {/* Voice Selection Section */}
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Voice Selection</h3>
                <div className="flex flex-wrap items-center gap-3">
                  {!project.voiceId && (
                    <>
                      {/* Option 1: Use existing voice */}
                      <VoiceSelector
                        projectId={projectId!}
                        currentVoiceId={project.voiceId}
                      />
                      
                      <span className="text-gray-400">or</span>
                      
                      {/* Option 2: Clone new voice */}
                      <button
                        onClick={handleCloneVoice}
                        disabled={cloneVoice.isPending || !project.audioSampleUrl}
                        className="px-4 py-2 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2"
                        data-testid="clone-voice-button"
                        title={!project.audioSampleUrl ? 'Upload audio sample first' : ''}
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        {cloneVoice.isPending ? 'Cloning Voice...' : 'Clone New Voice'}
                      </button>
                      {!project.audioSampleUrl && (
                        <span className="text-xs text-gray-500">
                          (Upload audio sample to clone new voice)
                        </span>
                      )}
                    </>
                  )}
                  {project.voiceId && (
                    <VoiceSelector
                      projectId={projectId!}
                      currentVoiceId={project.voiceId}
                    />
                  )}
                </div>
              </div>

              {/* Generate Plan Button */}
              <div className="flex gap-4">
                <button
                  onClick={handleGeneratePlan}
                  disabled={generatePlan.isPending || !project.voiceId}
                  className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  data-testid="generate-plan-button"
                >
                  {generatePlan.isPending ? 'Generating Plan...' : 'Generate Video Plan'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Segments Section */}
      {segments && segments.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Video Segments ({segments.length})
          </h2>

          {/* Video Generation Progress Banner */}
          {allHaveAudio && !allVideosGenerated && (
            <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-purple-900 flex items-center gap-2">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    {someGenerating ? 'Video Generation In Progress' : 'Ready to Generate Videos'}
                  </h3>
                  <p className="text-sm text-purple-700 mt-1">
                    {someGenerating 
                      ? `${segments.filter(s => s.status === 'generating').length} video(s) are being generated...`
                      : nextGeneratableSegment 
                        ? `Ready to generate Segment ${nextGeneratableSegment.index + 1}. Videos must be generated sequentially.`
                        : `Upload first frame for the next segment to continue.`}
                  </p>
                </div>
                {nextGeneratableSegment && !someGenerating && (
                  <button
                    onClick={handleGenerateNextVideo}
                    disabled={generateSegment.isPending}
                    className="px-6 py-3 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2 shadow-md"
                    data-testid="generate-next-video-button"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {generateSegment.isPending ? 'Starting...' : `Generate Segment ${nextGeneratableSegment.index + 1}`}
                  </button>
                )}
                {someGenerating && (
                  <div className="flex items-center gap-2 text-purple-600">
                    <div className="w-6 h-6 border-3 border-purple-600 border-t-transparent rounded-full animate-spin" />
                    <span className="font-medium">Processing...</span>
                  </div>
                )}
              </div>
              
              {/* Progress indicator */}
              <div className="mt-4">
                <div className="flex justify-between text-sm text-purple-700 mb-1">
                  <span>Video Progress</span>
                  <span>{segments.filter(s => s.videoUrl).length} / {segments.length}</span>
                </div>
                <div className="w-full bg-purple-200 rounded-full h-2">
                  <div 
                    className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${(segments.filter(s => s.videoUrl).length / segments.length) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          )}

          {/* All Videos Generated Banner */}
          {allVideosGenerated && !allSegmentsApproved && (
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200 p-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-green-900">All Videos Generated!</h3>
                  <p className="text-sm text-green-700">
                    Review each video below and click "Approve Video" to proceed to finalization.
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="space-y-4">
            {segments.map((segment, index) => {
              // Sequential generation: can only generate if previous segment has video
              const previousSegment = index > 0 ? segments[index - 1] : null;
              const canGenerate = index === 0 || (previousSegment?.videoUrl != null);
              
              return (
                <SegmentCard
                  key={segment.id}
                  segment={segment}
                  isActive={activeSegmentId === segment.id}
                  canGenerate={canGenerate}
                  projectFirstFrameUrl={project.firstFrameUrl}
                  onApprove={() => approveSegment.mutate(segment.id)}
                  onApproveVideo={() => approveVideo.mutate(segment.id)}
                  onRegenerate={() => regenerateSegment.mutate(segment.id)}
                  onEdit={(data) =>
                    updateSegment.mutate({ segmentId: segment.id, data })
                  }
                  onGenerate={() => generateSegment.mutate(segment.id)}
                  isLoading={
                    approveSegment.isPending ||
                    approveVideo.isPending ||
                    updateSegment.isPending ||
                    regenerateSegment.isPending ||
                    generateSegment.isPending
                  }
                />
              );
            })}
          </div>
        </div>
      )}

      {/* Final Video Section */}
      {project.status === 'completed' && project.finalVideoUrl && (
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg shadow-sm border border-green-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">🎉 Video Complete!</h2>
              <p className="text-sm text-gray-600">Your AI-generated video is ready</p>
            </div>
          </div>
          
          <VideoPlayer
            src={getMediaUrl(project.finalVideoUrl)!}
            title={project.name}
            className="max-w-3xl mx-auto mb-6"
          />
          
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <a
              href={getMediaUrl(project.finalVideoUrl)!}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 shadow-md hover:shadow-lg transition-all"
              download={`${project.name}.mp4`}
              data-testid="download-button"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                />
              </svg>
              Download Video (MP4)
            </a>
            <button
              onClick={() => {
                navigator.clipboard.writeText(getMediaUrl(project.finalVideoUrl)!);
                alert('Video URL copied to clipboard!');
              }}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white text-gray-700 font-medium rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Copy Link
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function ProjectStatusBar({ status }: { status: ProjectStatus }) {
  const steps = [
    { key: 'created', label: 'Created' },
    { key: 'media_uploaded', label: 'Media Uploaded' },
    { key: 'planning', label: 'Planning' },
    { key: 'plan_ready', label: 'Plan Ready' },
    { key: 'generating', label: 'Generating' },
    { key: 'completed', label: 'Completed' },
  ];

  const currentIndex = steps.findIndex((s) => s.key === status);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => (
          <div key={step.key} className="flex items-center">
            <div
              className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
                index <= currentIndex
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-600'
              }`}
            >
              {index < currentIndex ? (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                index + 1
              )}
            </div>
            <span
              className={`ml-2 text-sm font-medium ${
                index <= currentIndex ? 'text-blue-600' : 'text-gray-500'
              }`}
            >
              {step.label}
            </span>
            {index < steps.length - 1 && (
              <div
                className={`w-12 h-0.5 mx-4 ${
                  index < currentIndex ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
