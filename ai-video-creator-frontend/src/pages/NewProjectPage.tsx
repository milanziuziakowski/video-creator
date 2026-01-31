import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateProject } from '../api';

export function NewProjectPage() {
  const navigate = useNavigate();
  const createProject = useCreateProject();

  const [formData, setFormData] = useState({
    name: '',
    storyPrompt: '',
    targetDurationSec: 60,
    segmentDurationSec: 6,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const project = await createProject.mutateAsync({
        name: formData.name,
        storyPrompt: formData.storyPrompt || undefined,
        targetDurationSec: formData.targetDurationSec,
        segmentDurationSec: formData.segmentDurationSec,
      });
      navigate(`/projects/${project.id}`);
    } catch (error) {
      console.error('Failed to create project:', error);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Create New Project</h1>
        <p className="text-gray-600">Set up your AI video project</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-6">
          {/* Project Name */}
          <div>
            <label
              htmlFor="name"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Project Name *
            </label>
            <input
              id="name"
              type="text"
              required
              value={formData.name}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, name: e.target.value }))
              }
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="My AI Video Project"
              data-testid="project-name"
            />
          </div>

          {/* Story Prompt */}
          <div>
            <label
              htmlFor="storyPrompt"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Story Prompt
            </label>
            <textarea
              id="storyPrompt"
              value={formData.storyPrompt}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, storyPrompt: e.target.value }))
              }
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Describe the story or narrative for your video..."
              data-testid="story-prompt"
            />
            <p className="mt-1 text-xs text-gray-500">
              This will be used by AI to generate video segment prompts
            </p>
          </div>

          {/* Duration Settings */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="targetDuration"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Target Duration (seconds)
              </label>
              <select
                id="targetDuration"
                value={formData.targetDurationSec}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    targetDurationSec: parseInt(e.target.value),
                  }))
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                data-testid="target-duration"
              >
                <option value={30}>30 seconds</option>
                <option value={42}>42 seconds</option>
                <option value={48}>48 seconds</option>
                <option value={54}>54 seconds</option>
                <option value={60}>60 seconds</option>
              </select>
            </div>

            <div>
              <label
                htmlFor="segmentDuration"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Segment Duration
              </label>
              <select
                id="segmentDuration"
                value={formData.segmentDurationSec}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    segmentDurationSec: parseInt(e.target.value),
                  }))
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                data-testid="segment-duration"
              >
                <option value={6}>6 seconds</option>
                <option value={10}>10 seconds</option>
              </select>
            </div>
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex gap-3">
              <svg
                className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <div>
                <p className="text-sm text-blue-800 font-medium">Next Steps</p>
                <p className="text-sm text-blue-700 mt-1">
                  After creating the project, you'll need to upload a first frame image
                  and an audio sample for voice cloning before generating video segments.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-4">
          <button
            type="button"
            onClick={() => navigate('/projects')}
            className="px-6 py-2 text-gray-700 font-medium bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={createProject.isPending || !formData.name}
            className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            data-testid="create-button"
          >
            {createProject.isPending ? 'Creating...' : 'Create Project'}
          </button>
        </div>
      </form>
    </div>
  );
}
