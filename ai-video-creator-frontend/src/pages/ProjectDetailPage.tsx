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
} from '../api';
import { FileUpload, SegmentCard, PageLoading, VideoPlayer } from '../components';
import type { ProjectStatus } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

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
    project.firstFrameUrl && project.audioSampleUrl && project.storyPrompt;

  const allSegmentsApproved =
    segments && segments.length > 0 && segments.every((s) => s.status === 'segment_approved');

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
              previewUrl={project.firstFrameUrl}
              type="image"
            />
            <FileUpload
              accept="audio/*"
              label="Voice Sample (for cloning)"
              onUpload={handleAudioUpload}
              isLoading={uploadAudio.isPending}
              previewUrl={project.audioSampleUrl}
              type="audio"
            />
          </div>

          {canGeneratePlan && (
            <div className="mt-6 flex gap-4">
              {!project.voiceId && (
                <button
                  onClick={handleCloneVoice}
                  disabled={cloneVoice.isPending}
                  className="px-4 py-2 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 disabled:opacity-50"
                  data-testid="clone-voice-button"
                >
                  {cloneVoice.isPending ? 'Cloning Voice...' : 'Clone Voice'}
                </button>
              )}
              {project.voiceId && (
                <span className="px-4 py-2 bg-green-100 text-green-700 rounded-lg">
                  ✓ Voice Cloned
                </span>
              )}
              <button
                onClick={handleGeneratePlan}
                disabled={generatePlan.isPending || !project.voiceId}
                className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
                data-testid="generate-plan-button"
              >
                {generatePlan.isPending ? 'Generating Plan...' : 'Generate Video Plan'}
              </button>
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
          <div className="space-y-4">
            {segments.map((segment) => (
              <SegmentCard
                key={segment.id}
                segment={segment}
                isActive={activeSegmentId === segment.id}
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
            ))}
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
            src={project.finalVideoUrl}
            title={project.name}
            className="max-w-3xl mx-auto mb-6"
          />
          
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <a
              href={`${API_BASE_URL}/media/download/${projectId}/final`}
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
                navigator.clipboard.writeText(project.finalVideoUrl!);
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
