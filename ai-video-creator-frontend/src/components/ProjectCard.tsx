import { Link } from 'react-router-dom';
import type { Project, ProjectStatus } from '../types';
import { getMediaUrl } from '../api';

interface ProjectCardProps {
  project: Project;
}

const statusColors: Record<ProjectStatus, string> = {
  created: 'bg-gray-100 text-gray-800',
  media_uploaded: 'bg-yellow-100 text-yellow-800',
  planning: 'bg-blue-100 text-blue-800',
  plan_ready: 'bg-indigo-100 text-indigo-800',
  generating: 'bg-purple-100 text-purple-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
};

const statusLabels: Record<ProjectStatus, string> = {
  created: 'Created',
  media_uploaded: 'Media Uploaded',
  planning: 'Planning',
  plan_ready: 'Plan Ready',
  generating: 'Generating',
  completed: 'Completed',
  failed: 'Failed',
};

export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Link
      to={`/projects/${project.id}`}
      className="block bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
      data-testid="project-card"
    >
      <div className="p-6">
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-lg font-semibold text-gray-900 truncate">
            {project.name}
          </h3>
          <span
            className={`px-2 py-1 text-xs font-medium rounded-full ${
              statusColors[project.status]
            }`}
          >
            {statusLabels[project.status]}
          </span>
        </div>

        {project.storyPrompt && (
          <p className="text-sm text-gray-600 mb-4 line-clamp-2">
            {project.storyPrompt}
          </p>
        )}

        <div className="flex justify-between items-center text-sm text-gray-500">
          <span>Duration: {project.targetDurationSec}s</span>
          <span>
            {new Date(project.createdAt).toLocaleDateString()}
          </span>
        </div>

        {project.firstFrameUrl && (
          <div className="mt-4">
            <img
              src={getMediaUrl(project.firstFrameUrl)!}
              alt="First frame"
              className="w-full h-32 object-cover rounded-md"
            />
          </div>
        )}
      </div>
    </Link>
  );
}
