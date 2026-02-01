import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Backend base URL for media files (without /api/v1)
export const BACKEND_URL = API_BASE_URL.replace('/api/v1', '');

let getAccessTokenFn: (() => Promise<string | null>) | null = null;

export function setAccessTokenGetter(fn: () => Promise<string | null>) {
  getAccessTokenFn = fn;
}

/**
 * Convert a media URL path to a full URL.
 * Backend returns paths like '/uploads/projects/xxx/file.jpg'
 * This converts them to 'http://localhost:8000/uploads/projects/xxx/file.jpg'
 */
export function getMediaUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  // If it's already a full URL, return as-is
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  // Prepend backend URL
  return `${BACKEND_URL}${path}`;
}

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    if (getAccessTokenFn) {
      const token = await getAccessTokenFn();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export { apiClient };
