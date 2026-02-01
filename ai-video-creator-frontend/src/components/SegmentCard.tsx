import { useState } from 'react';
import type { Segment, SegmentStatus } from '../types';
import { VideoThumbnail } from './VideoPlayer';

interface SegmentCardProps {
  segment: Segment;
  isActive?: boolean;
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
  generating_video: 'bg-purple-100 text-purple-800',
  generating_audio: 'bg-purple-100 text-purple-800',
  generated: 'bg-indigo-100 text-indigo-800',
  segment_approved: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
};

const statusLabels: Record<SegmentStatus, string> = {
  pending: 'Pending',
  prompt_ready: 'Prompt Ready',
  approved: 'Approved',
  generating_video: 'Generating Video',
  generating_audio: 'Generating Audio',
  generated: 'Generated',
  segment_approved: 'Approved',
  failed: 'Failed',
};

export function SegmentCard({
  segment,
  isActive,
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

        {/* Video Preview */}
        {segment.videoUrl && (
          <div className="mb-4">
            <h5 className="text-sm font-medium text-gray-700 mb-2">Video Preview</h5>
            <VideoThumbnail
              src={segment.videoUrl}
              title={`Segment ${segment.index + 1} Preview`}
              className="max-w-md"
            />
            <p className="text-xs text-gray-500 mt-1">Click to preview in fullscreen</p>
          </div>
        )}

        {/* Audio Preview */}
        {segment.audioUrl && (
          <div className="mb-4">
            <h5 className="text-sm font-medium text-gray-700 mb-2">Audio</h5>
            <audio
              src={segment.audioUrl}
              controls
              className="w-full"
              data-testid="segment-audio"
            />
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-wrap gap-2 mt-4">
          {segment.status === 'prompt_ready' && !isEditing && (
            <>
              <button
                onClick={() => setIsEditing(true)}
                className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-200"
                data-testid="edit-button"
              >
                Edit
              </button>
              <button
                onClick={onApprove}
                disabled={isLoading}
                className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50"
                data-testid="approve-button"
              >
                {isLoading ? 'Approving...' : 'Approve'}
              </button>
            </>
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

          {(segment.status === 'generating_video' || segment.status === 'generating_audio') && (
            <div className="flex items-center gap-2 text-purple-600">
              <div className="w-4 h-4 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
              <span className="text-sm font-medium">Generating...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
