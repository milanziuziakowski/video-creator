import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';
import type {
  Project,
  ProjectCreate,
  ProjectUpdate,
  ProjectListResponse,
  Segment,
  SegmentUpdate,
  VideoPlan,
  GeneratePlanRequest,
  GenerationStatus,
} from '../types';

// Projects
export function useProjects(skip = 0, limit = 20) {
  return useQuery({
    queryKey: ['projects', skip, limit],
    queryFn: async () => {
      const { data } = await apiClient.get<ProjectListResponse>('/projects/', {
        params: { skip, limit },
      });
      return data;
    },
  });
}

export function useProject(projectId: string) {
  return useQuery({
    queryKey: ['projects', projectId],
    queryFn: async () => {
      const { data } = await apiClient.get<Project>(`/projects/${projectId}`);
      return data;
    },
    enabled: !!projectId,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (project: ProjectCreate) => {
      const { data } = await apiClient.post<Project>('/projects/', project);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

export function useUpdateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      projectId,
      data: updateData,
    }: {
      projectId: string;
      data: ProjectUpdate;
    }) => {
      const { data } = await apiClient.put<Project>(
        `/projects/${projectId}`,
        updateData
      );
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.setQueryData(['projects', data.id], data);
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (projectId: string) => {
      await apiClient.delete(`/projects/${projectId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

export function useFinalizeProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (projectId: string) => {
      const { data } = await apiClient.post<Project>(
        `/projects/${projectId}/finalize`
      );
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.setQueryData(['projects', data.id], data);
    },
  });
}

// Segments
export function useProjectSegments(projectId: string) {
  return useQuery({
    queryKey: ['segments', projectId],
    queryFn: async () => {
      const { data } = await apiClient.get<Segment[]>(
        `/segments/project/${projectId}`
      );
      return data;
    },
    enabled: !!projectId,
  });
}

export function useSegment(segmentId: string) {
  return useQuery({
    queryKey: ['segments', 'detail', segmentId],
    queryFn: async () => {
      const { data } = await apiClient.get<Segment>(`/segments/${segmentId}`);
      return data;
    },
    enabled: !!segmentId,
  });
}

export function useUpdateSegment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      segmentId,
      data: updateData,
    }: {
      segmentId: string;
      data: SegmentUpdate;
    }) => {
      const { data } = await apiClient.put<Segment>(
        `/segments/${segmentId}`,
        updateData
      );
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['segments'] });
      queryClient.setQueryData(['segments', 'detail', data.id], data);
    },
  });
}

export function useApproveSegment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (segmentId: string) => {
      const { data } = await apiClient.post<Segment>(
        `/segments/${segmentId}/approve`
      );
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['segments'] });
      queryClient.setQueryData(['segments', 'detail', data.id], data);
    },
  });
}

export function useApproveSegmentVideo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (segmentId: string) => {
      const { data } = await apiClient.post<Segment>(
        `/segments/${segmentId}/approve-video`
      );
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['segments'] });
      queryClient.setQueryData(['segments', 'detail', data.id], data);
    },
  });
}

export function useRegenerateSegment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (segmentId: string) => {
      const { data } = await apiClient.post<Segment>(
        `/segments/${segmentId}/regenerate`
      );
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['segments'] });
      queryClient.setQueryData(['segments', 'detail', data.id], data);
    },
  });
}

// Generation
export function useGeneratePlan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (request: GeneratePlanRequest) => {
      const { data } = await apiClient.post<VideoPlan>(
        '/generation/plan',
        request
      );
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['segments', variables.projectId],
      });
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId],
      });
    },
  });
}

export function useCloneVoice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (projectId: string) => {
      const { data } = await apiClient.post<{ voice_id: string }>(
        '/generation/voice-clone',
        null,
        { params: { project_id: projectId } }
      );
      return { projectId, voiceId: data.voice_id };
    },
    onSuccess: async ({ projectId, voiceId }) => {
      // Update the cache with the voice_id
      queryClient.setQueryData(['projects', projectId], (oldData: any) => {
        if (!oldData) return oldData;
        return {
          ...oldData,
          voiceId: voiceId,
        };
      });
    },
  });
}

export function useGenerateSegment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (segmentId: string) => {
      const { data } = await apiClient.post<{ task_id: string; status: string }>(
        `/generation/segment/${segmentId}`
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['segments'] });
    },
  });
}

export function useGenerationStatus(taskId: string | null, enabled = true) {
  return useQuery({
    queryKey: ['generation', 'status', taskId],
    queryFn: async () => {
      const { data } = await apiClient.get<GenerationStatus>(
        `/generation/status/${taskId}`
      );
      return data;
    },
    enabled: !!taskId && enabled,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false;
      }
      return 5000; // Poll every 5 seconds
    },
  });
}

// Media uploads
export function useUploadFirstFrame() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      projectId,
      file,
    }: {
      projectId: string;
      file: File;
    }) => {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await apiClient.post<{ url: string; filename: string }>(
        '/media/upload/first-frame',
        formData,
        {
          params: { project_id: projectId },
          headers: { 'Content-Type': 'multipart/form-data' },
        }
      );
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId],
      });
    },
  });
}

export function useUploadAudioSample() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      projectId,
      file,
    }: {
      projectId: string;
      file: File;
    }) => {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await apiClient.post<{ url: string; filename: string }>(
        '/media/upload/audio',
        formData,
        {
          params: { project_id: projectId },
          headers: { 'Content-Type': 'multipart/form-data' },
        }
      );
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId],
      });
    },
  });
}
