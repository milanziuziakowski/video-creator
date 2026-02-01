import { useState, useEffect, useRef, useCallback } from 'react';
import type { Segment, SegmentStatus } from '../types';
import { VideoThumbnail } from './VideoPlayer';
import { getMediaUrl, useCheckSegmentComplete, useUploadSegmentFrame, useRemoveSegmentLastFrame, useExtractLastFrame } from '../api';

interface SegmentCardProps {
  segment: Segment;
  isActive?: boolean;
  canGenerate?: boolean; // Whether this segment can start generating (previous completed)
  projectFirstFrameUrl?: string | null; // For first segment to inherit from project
  onApprove?: () => void;
  onApproveVideo?: () => void;
  onRegenerate?: () => void;
  onEdit?: (data: { videoPrompt?: string; narrationText?: string }) => void;
  onGenerate?: () => void;
  isLoading?: boolean;
}

const statusColors: Record<SegmentStatus, string> = {
  pending: 'bg-gray-100 text-gray-800',
  prompt_ready: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-blue-100 text-blue-800',
  generating: 'bg-purple-100 text-purple-800',
  generated: 'bg-indigo-100 text-indigo-800',
  segment_approved: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
};

const statusLabels: Record<SegmentStatus, string> = {
  pending: 'Pending',
  prompt_ready: 'Prompt Ready',
  approved: 'Approved',
  generating: 'Generating...',
  generated: 'Generated',
  segment_approved: 'Approved',
  failed: 'Failed',
};

export function SegmentCard({
  segment,
  isActive,
  canGenerate = true,
  projectFirstFrameUrl,
  onApprove,
  onApproveVideo,
  onRegenerate,
  onEdit,
  onGenerate,
  isLoading,
}: SegmentCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedPrompt, setEditedPrompt] = useState(segment.videoPrompt);
  const [editedNarration, setEditedNarration] = useState(segment.narrationText);
  
  const checkComplete = useCheckSegmentComplete();
  const uploadFrame = useUploadSegmentFrame();
  const removeLastFrame = useRemoveSegmentLastFrame();
  const extractLastFrame = useExtractLastFrame();
  const checkCompleteRef = useRef(checkComplete);
  checkCompleteRef.current = checkComplete;

  // For first segment, use project's first frame as fallback
  const effectiveFirstFrameUrl = segment.firstFrameUrl || (segment.index === 0 ? projectFirstFrameUrl : null);

  const handleRemoveLastFrame = useCallback(() => {
    if (confirm('Are you sure you want to remove the last frame?')) {
      removeLastFrame.mutate(segment.id);
    }
  }, [segment.id, removeLastFrame]);

  const handleExtractLastFrame = useCallback(() => {
    extractLastFrame.mutate(segment.id);
  }, [segment.id, extractLastFrame]);

  // Auto-check if generation is complete when segment is generating
  useEffect(() => {
    if (segment.status === 'generating') {
      const interval = setInterval(() => {
        checkCompleteRef.current.mutate(segment.id);
      }, 5000); // Check every 5 seconds

      return () => clearInterval(interval);
    }
  }, [segment.id, segment.status]);

  const handleSaveEdit = () => {
    onEdit?.({
      videoPrompt: editedPrompt,
      narrationText: editedNarration,
    });
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditedPrompt(segment.videoPrompt);
    setEditedNarration(segment.narrationText);
    setIsEditing(false);
  };

  const handleFrameUpload = useCallback((frameType: 'first' | 'last') => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        await uploadFrame.mutateAsync({
          segmentId: segment.id,
          frameType,
          file,
        });
      }
    };
    input.click();
  }, [segment.id, uploadFrame]);

  // Determine if generation is blocked
  const isGenerationBlocked = !canGenerate;
  
  // Show frame section when segment has prompts ready or later, but doesn't have video yet
  const showFrameSection = (
    ['prompt_ready', 'approved', 'generated'].includes(segment.status) || segment.audioUrl
  ) && !segment.videoUrl && segment.status !== 'generating';

  return (
    <div
      className={`bg-white rounded-lg shadow-sm border-2 transition-colors ${
        isActive ? 'border-blue-500' : 'border-gray-200'
      }`}
      data-testid={`segment-card-${segment.index}`}
    >
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center gap-3">
            <span className="flex items-center justify-center w-8 h-8 bg-blue-600 text-white text-sm font-bold rounded-full">
              {segment.index + 1}
            </span>
            <h4 className="font-medium text-gray-900">Segment {segment.index + 1}</h4>
          </div>
          <span
            className={`px-2 py-1 text-xs font-medium rounded-full ${
              statusColors[segment.status]
            }`}
          >
            {statusLabels[segment.status]}
          </span>
        </div>

        {/* Content */}
        {isEditing ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Video Prompt
              </label>
              <textarea
                value={editedPrompt}
                onChange={(e) => setEditedPrompt(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Narration Text
              </label>
              <textarea
                value={editedNarration}
                onChange={(e) => setEditedNarration(e.target.value)}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleSaveEdit}
                className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
              >
                Save
              </button>
              <button
                onClick={handleCancelEdit}
                className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-200"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="mb-4">
              <h5 className="text-sm font-medium text-gray-700 mb-1">Video Prompt</h5>
              <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md">
                {segment.videoPrompt}
              </p>
            </div>
            <div className="mb-4">
              <h5 className="text-sm font-medium text-gray-700 mb-1">Narration</h5>
              <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md">
                {segment.narrationText}
              </p>
            </div>
          </>
        )}

        {/* First & Last Frame Section - Show when ready for video generation */}
        {showFrameSection && (
          <div className="mb-4 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg border border-indigo-200">
            <h5 className="text-sm font-semibold text-indigo-900 mb-3 flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              Video Generation Frames
            </h5>
            
            <div className="grid grid-cols-2 gap-4">
              {/* First Frame */}
              <div>
                <p className="text-xs font-medium text-gray-600 mb-2">
                  First Frame (Start)
                  {!segment.firstFrameUrl && effectiveFirstFrameUrl && (
                    <span className="ml-1 text-blue-500">(from project)</span>
                  )}
                </p>
                {effectiveFirstFrameUrl ? (
                  <div className="relative group aspect-video bg-gray-100 rounded-lg overflow-hidden border border-gray-200">
                    <img
                      src={getMediaUrl(effectiveFirstFrameUrl)!}
                      alt="First frame"
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.style.display = 'none';
                        target.parentElement?.classList.add('flex', 'items-center', 'justify-center');
                        const fallback = document.createElement('span');
                        fallback.className = 'text-xs text-gray-400';
                        fallback.textContent = 'Image failed to load';
                        target.parentElement?.appendChild(fallback);
                      }}
                    />
                    <button
                      onClick={() => handleFrameUpload('first')}
                      className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center rounded-lg"
                    >
                      <span className="text-white text-xs font-medium">Replace</span>
                    </button>
                    <span className={`absolute bottom-1 left-1 text-white text-xs px-1.5 py-0.5 rounded ${segment.firstFrameUrl ? 'bg-green-500' : 'bg-blue-500'}`}>
                      {segment.firstFrameUrl ? '✓ Set' : '↑ Inherited'}
                    </span>
                  </div>
                ) : (
                  <button
                    onClick={() => handleFrameUpload('first')}
                    disabled={uploadFrame.isPending}
                    className="w-full aspect-video border-2 border-dashed border-gray-300 rounded-lg hover:border-indigo-400 hover:bg-indigo-50 transition-colors flex flex-col items-center justify-center gap-1"
                  >
                    {uploadFrame.isPending ? (
                      <div className="w-5 h-5 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <>
                        <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        <span className="text-xs text-gray-500">Upload First Frame</span>
                      </>
                    )}
                  </button>
                )}
              </div>

              {/* Last Frame */}
              <div>
                <p className="text-xs font-medium text-gray-600 mb-2">Last Frame (End) - Optional</p>
                {segment.lastFrameUrl ? (
                  <div className="relative group aspect-video bg-gray-100 rounded-lg overflow-hidden border border-gray-200">
                    <img
                      src={getMediaUrl(segment.lastFrameUrl)!}
                      alt="Last frame"
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.style.display = 'none';
                        target.parentElement?.classList.add('flex', 'items-center', 'justify-center');
                        const fallback = document.createElement('span');
                        fallback.className = 'text-xs text-gray-400';
                        fallback.textContent = 'Image failed to load';
                        target.parentElement?.appendChild(fallback);
                      }}
                    />
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 rounded-lg">
                      <button
                        onClick={() => handleFrameUpload('last')}
                        className="px-2 py-1 bg-white text-gray-800 text-xs font-medium rounded hover:bg-gray-100"
                      >
                        Replace
                      </button>
                      <button
                        onClick={handleRemoveLastFrame}
                        disabled={removeLastFrame.isPending}
                        className="px-2 py-1 bg-red-500 text-white text-xs font-medium rounded hover:bg-red-600 disabled:opacity-50"
                      >
                        {removeLastFrame.isPending ? '...' : 'Remove'}
                      </button>
                    </div>
                    <span className="absolute bottom-1 left-1 bg-green-500 text-white text-xs px-1.5 py-0.5 rounded">
                      ✓ Set
                    </span>
                  </div>
                ) : (
                  <button
                    onClick={() => handleFrameUpload('last')}
                    disabled={uploadFrame.isPending}
                    className="w-full aspect-video border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-400 hover:bg-purple-50 transition-colors flex flex-col items-center justify-center gap-1"
                  >
                    {uploadFrame.isPending ? (
                      <div className="w-5 h-5 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <>
                        <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        <span className="text-xs text-gray-500">Upload Last Frame</span>
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>

            {!effectiveFirstFrameUrl && (
              <p className="text-xs text-amber-600 mt-2 flex items-center gap-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                First frame is required for video generation
              </p>
            )}

            {effectiveFirstFrameUrl && !segment.lastFrameUrl && (
              <p className="text-xs text-gray-500 mt-2">
                💡 Last frame is optional. If not set, the video will end naturally.
              </p>
            )}
          </div>
        )}

        {/* Video Preview */}
        {segment.videoUrl && (
          <div className="mb-4">
            <h5 className="text-sm font-medium text-gray-700 mb-2">Video Preview</h5>
            <VideoThumbnail
              src={getMediaUrl(segment.videoUrl)!}
              title={`Segment ${segment.index + 1} Preview`}
              className="max-w-md"
            />
            <p className="text-xs text-gray-500 mt-1">Click to preview in fullscreen</p>
          </div>
        )}

        {/* Frame previews after generation (show extracted frames) */}
        {segment.videoUrl && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <h5 className="text-sm font-medium text-gray-700">Frame Extraction</h5>
              <button
                onClick={handleExtractLastFrame}
                disabled={extractLastFrame.isPending}
                className="px-3 py-1.5 bg-indigo-100 text-indigo-700 text-xs font-medium rounded-md hover:bg-indigo-200 disabled:opacity-50 flex items-center gap-1.5 transition-colors"
                data-testid="extract-last-frame-button"
                title="Extract last frame from video and set as next segment's first frame"
              >
                {extractLastFrame.isPending ? (
                  <>
                    <div className="w-3 h-3 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
                    Extracting...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    Extract Last Frame → Next Segment
                  </>
                )}
              </button>
            </div>
            {(segment.firstFrameUrl || segment.lastFrameUrl) && (
              <div className="grid grid-cols-2 gap-4">
                {segment.firstFrameUrl && (
                  <div>
                    <p className="text-xs font-medium text-gray-600 mb-1">First Frame</p>
                    <img
                      src={getMediaUrl(segment.firstFrameUrl)!}
                      alt="First frame"
                      className="w-full h-24 object-cover rounded border border-gray-200"
                    />
                  </div>
                )}
                {segment.lastFrameUrl && (
                  <div>
                    <p className="text-xs font-medium text-gray-600 mb-1">Last Frame (Auto-extracted)</p>
                    <img
                      src={getMediaUrl(segment.lastFrameUrl)!}
                      alt="Last frame"
                      className="w-full h-24 object-cover rounded border border-gray-200"
                    />
                  </div>
                )}
              </div>
            )}
            {!segment.lastFrameUrl && (
              <p className="text-xs text-gray-500 mt-1">
                Click "Extract Last Frame" to extract the last frame and auto-set it as the next segment's first frame.
              </p>
            )}
          </div>
        )}

        {/* Audio Preview */}
        {segment.audioUrl && (
          <div className="mb-4">
            <h5 className="text-sm font-medium text-gray-700 mb-2">Audio</h5>
            <audio
              key={segment.audioUrl}
              src={getMediaUrl(segment.audioUrl)!}
              controls
              className="w-full"
              data-testid="segment-audio"
              preload="metadata"
            />
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-wrap gap-2 mt-4">
          {/* Edit button - available for prompt_ready and approved statuses */}
          {['prompt_ready', 'approved'].includes(segment.status) && !isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-200"
              data-testid="edit-button"
            >
              Edit
            </button>
          )}

          {segment.status === 'prompt_ready' && !isEditing && (
            <button
              onClick={onApprove}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50"
              data-testid="approve-button"
            >
              {isLoading ? 'Approving...' : 'Approve'}
            </button>
          )}

          {segment.status === 'approved' && (
            <button
              onClick={onGenerate}
              disabled={isLoading}
              className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-md hover:bg-purple-700 disabled:opacity-50"
              data-testid="generate-button"
            >
              {isLoading ? 'Starting...' : 'Generate'}
            </button>
          )}

          {/* Show Generate Video button when audio exists but no video */}
          {showFrameSection && (
            <>
              {isGenerationBlocked ? (
                <div className="px-4 py-2 bg-gray-100 text-gray-500 text-sm font-medium rounded-md flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  Waiting for Segment {segment.index} to complete
                </div>
              ) : (
                <button
                  onClick={onGenerate}
                  disabled={isLoading || !segment.firstFrameUrl}
                  className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-md hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2"
                  data-testid="generate-video-button"
                  title={!segment.firstFrameUrl ? 'Upload first frame to enable generation' : ''}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {isLoading ? 'Starting...' : 'Generate Video'}
                </button>
              )}
            </>
          )}

          {segment.status === 'generated' && (
            <>
              <button
                onClick={onRegenerate}
                disabled={isLoading}
                className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-200 disabled:opacity-50"
                data-testid="regenerate-button"
              >
                Regenerate
              </button>
              <button
                onClick={onApproveVideo}
                disabled={isLoading}
                className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 disabled:opacity-50"
                data-testid="approve-video-button"
              >
                {isLoading ? 'Approving...' : 'Approve Video'}
              </button>
            </>
          )}

          {segment.status === 'generating' && (
            <div className="flex items-center gap-2 text-purple-600">
              <div className="w-4 h-4 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
              <span className="text-sm font-medium">
                {segment.audioUrl && !segment.videoUrl ? 'Generating Video...' : 'Generating...'}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}