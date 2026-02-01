# Frontend Implementation Guide

**Phase:** 5  
**Technology:** React 18+, TypeScript, Tailwind CSS, MSAL React, React Query

---

## 1. Project Setup

### 1.1 Manual Steps (wymagane przed rozpoczęciem)

```bash
# 1. Create React project with Vite (recommended)
npm create vite@latest ai-video-creator-frontend -- --template react-ts
cd ai-video-creator-frontend

# 2. Install core dependencies
npm install @azure/msal-browser @azure/msal-react
npm install @tanstack/react-query
npm install axios
npm install react-router-dom
npm install @headlessui/react @heroicons/react  # UI components
npm install react-dropzone  # File upload

# 3. Install Tailwind CSS
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# 4. Install dev dependencies
npm install -D @types/node prettier eslint-config-prettier

# 5. Start development server
npm run dev
```

### 1.2 Tailwind Configuration (tailwind.config.js)

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Custom brand colors
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        },
        dark: {
          100: '#1e293b',
          200: '#0f172a',
          300: '#020617',
        }
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}
```

### 1.3 Environment Configuration (.env)

```bash
# API
VITE_API_URL=http://localhost:8000/api/v1
```

---

## 2. JWT Authentication Setup

### 2.1 Auth Configuration (src/auth/authConfig.ts)

```typescript
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export const AUTH_STORAGE_KEY = 'ai-video-creator-auth';
```

### 2.2 Auth Provider (src/auth/AuthProvider.tsx)

```tsx
import { ReactNode, createContext, useContext, useEffect, useState } from "react";

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  return (
    <MsalProvider instance={msalInstance}>
      <AuthInitializer>{children}</AuthInitializer>
    </MsalProvider>
  );
}

function AuthInitializer({ children }: { children: ReactNode }) {
  const { instance, inProgress } = useMsal();
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Load auth state from localStorage on startup
    const authData = localStorage.getItem(AUTH_STORAGE_KEY);
    if (authData) {
      try {
        const parsed = JSON.parse(authData);
        setToken(parsed.access_token);
        setUser(parsed.user);
      } catch (error) {
        console.error('Failed to parse auth data:', error);
        localStorage.removeItem(AUTH_STORAGE_KEY);
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (credentials: LoginCredentials) => {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const authData: AuthResponse = await response.json();
    
    setToken(authData.access_token);
    setUser(authData.user);
    
    // Store in localStorage
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authData));
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem(AUTH_STORAGE_KEY);
  };

  const contextValue: AuthContextType = {
    user,
    token,
    login,
    logout,
    isAuthenticated: !!user && !!token,
    isLoading,
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-dark-200">
        <div className="animate-pulse text-white">Loading...</div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}
```

### 2.3 Auth Hook (src/auth/useAuth.ts)

```typescript
import { useContext } from "react";

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
      });
    } catch (error) {
      console.error("Logout error:", error);
      throw error;
    }
  }, [instance]);

  const getAccessToken = useCallback(async (): Promise<string> => {
    if (!account) {
      throw new Error("No account available");
    }

    try {
      const response = await instance.acquireTokenSilent({
        ...apiScopes,
        account,
      });
      return response.accessToken;
    } catch (error) {
      // Fall back to interactive
      const response = await instance.acquireTokenRedirect(apiScopes);
      // This will redirect, so we won't reach here
      throw error;
    }
  }, [instance, account]);

  const user: User | null = account
    ? {
        id: account.localAccountId,
        email: account.username,
        name: account.name || account.username,
      }
    : null;

  return {
    user,
    isAuthenticated,
    isLoading: inProgress !== InteractionStatus.None,
    login,
    logout,
    getAccessToken,
  };
}
```

---

## 3. API Client Setup

### 3.1 Axios Configuration (src/api/client.ts)

```typescript
import axios, { AxiosInstance, AxiosRequestConfig } from "axios";
import { msalInstance, apiScopes } from "../auth/msalConfig";

const API_URL = import.meta.env.VITE_API_URL;

async function getAccessToken(): Promise<string> {
  const accounts = msalInstance.getAllAccounts();
  if (accounts.length === 0) {
    throw new Error("No accounts available");
  }

  try {
    const response = await msalInstance.acquireTokenSilent({
      ...apiScopes,
      account: accounts[0],
    });
    return response.accessToken;
  } catch (error) {
    // Redirect to login
    await msalInstance.acquireTokenRedirect(apiScopes);
    throw error;
  }
}

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor - add auth token
apiClient.interceptors.request.use(
  async (config) => {
    try {
      const token = await getAccessToken();
      config.headers.Authorization = `Bearer ${token}`;
    } catch (error) {
      // Let request proceed, will fail with 401
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, try to refresh
      try {
        await msalInstance.acquireTokenRedirect(apiScopes);
      } catch {
        // Redirect to login
      }
    }
    return Promise.reject(error);
  }
);
```

### 3.2 React Query Setup (src/api/queryClient.ts)

```typescript
import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: (failureCount, error: any) => {
        // Don't retry on 401/403
        if (error?.response?.status === 401 || error?.response?.status === 403) {
          return false;
        }
        return failureCount < 3;
      },
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: false,
    },
  },
});
```

---

## 4. Type Definitions

### 4.1 Project Types (src/types/project.ts)

```typescript
export type ProjectStatus =
  | "created"
  | "media_uploaded"
  | "voice_cloning"
  | "plan_generating"
  | "plan_ready"
  | "generating"
  | "finalizing"
  | "completed"
  | "failed";

export type SegmentStatus =
  | "pending"
  | "prompt_ready"
  | "approved"
  | "generating"
  | "generated"
  | "segment_approved"
  | "failed";

export interface Segment {
  id: string;
  index: number;
  videoPrompt: string;
  narrationText: string;
  endFramePrompt: string;
  firstFrameUrl?: string;
  lastFrameUrl?: string;
  videoUrl?: string;
  audioUrl?: string;
  status: SegmentStatus;
  approved: boolean;
}

export interface Project {
  id: string;
  userId: string;
  name: string;
  storyPrompt?: string;
  targetDurationSec: number;
  segmentLenSec: number;
  segmentCount: number;
  voiceId?: string;
  firstFrameUrl?: string;
  audioSampleUrl?: string;
  finalVideoUrl?: string;
  status: ProjectStatus;
  segments: Segment[];
  createdAt: string;
  updatedAt: string;
}

export interface CreateProjectDto {
  name: string;
  storyPrompt?: string;
  targetDurationSec: number;
  segmentLenSec: number;
}

export interface UpdateProjectDto {
  name?: string;
  storyPrompt?: string;
}
```

### 4.2 Generation Types (src/types/generation.ts)

```typescript
export interface VideoPlanSegment {
  segmentIndex: number;
  videoPrompt: string;
  narrationText: string;
  endFramePrompt: string;
}

export interface VideoPlan {
  title: string;
  segments: VideoPlanSegment[];
  continuityNotes: string;
}

export interface GenerationStatus {
  taskId: string;
  status: "submitted" | "processing" | "Success" | "Fail";
  fileId?: string;
  downloadUrl?: string;
  error?: string;
  progress?: number;
}

// First & Last Frame Video Generation (FL2V) Types
export type FL2VResolution = "768P" | "1080P";

export type CameraCommand =
  | "[Truck left]"
  | "[Truck right]"
  | "[Pan left]"
  | "[Pan right]"
  | "[Push in]"
  | "[Pull out]"
  | "[Pedestal up]"
  | "[Pedestal down]"
  | "[Tilt up]"
  | "[Tilt down]"
  | "[Zoom in]"
  | "[Zoom out]"
  | "[Shake]"
  | "[Tracking shot]"
  | "[Static shot]";

export interface FL2VGenerateRequest {
  segmentId: string;
  prompt: string;
  firstFrameImage?: string;  // URL or base64 data URL
  lastFrameImage: string;    // Required - URL or base64 data URL
  duration: 6 | 10;
  resolution: FL2VResolution;
  promptOptimizer: boolean;
  cameraCommands?: CameraCommand[];
}

export interface FL2VGenerateResponse {
  taskId: string;
  segmentId: string;
  status: string;
  model: string;
}

// Camera command helpers
export const CAMERA_COMMANDS: { value: CameraCommand; label: string; category: string }[] = [
  { value: "[Truck left]", label: "Truck Left", category: "Movement" },
  { value: "[Truck right]", label: "Truck Right", category: "Movement" },
  { value: "[Pan left]", label: "Pan Left", category: "Pan" },
  { value: "[Pan right]", label: "Pan Right", category: "Pan" },
  { value: "[Push in]", label: "Push In", category: "Push" },
  { value: "[Pull out]", label: "Pull Out", category: "Push" },
  { value: "[Pedestal up]", label: "Pedestal Up", category: "Pedestal" },
  { value: "[Pedestal down]", label: "Pedestal Down", category: "Pedestal" },
  { value: "[Tilt up]", label: "Tilt Up", category: "Tilt" },
  { value: "[Tilt down]", label: "Tilt Down", category: "Tilt" },
  { value: "[Zoom in]", label: "Zoom In", category: "Zoom" },
  { value: "[Zoom out]", label: "Zoom Out", category: "Zoom" },
  { value: "[Shake]", label: "Shake", category: "Effect" },
  { value: "[Tracking shot]", label: "Tracking Shot", category: "Follow" },
  { value: "[Static shot]", label: "Static Shot", category: "Static" },
];

export function buildPromptWithCameraCommands(
  prompt: string,
  commands: CameraCommand[]
): string {
  if (!commands || commands.length === 0) return prompt;
  // Max 3 simultaneous commands
  const validCommands = commands.slice(0, 3);
  const commandStr = validCommands.map(c => c.replace(/[\[\]]/g, "")).join(",");
  return `${prompt} [${commandStr}]`;
}
```

---

## 5. API Hooks

### 5.1 Project Hooks (src/api/hooks/useProjects.ts)

```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../client";
import { Project, CreateProjectDto, UpdateProjectDto } from "../../types/project";

const PROJECTS_KEY = ["projects"];

export function useProjects() {
  return useQuery({
    queryKey: PROJECTS_KEY,
    queryFn: async () => {
      const { data } = await apiClient.get<{ projects: Project[]; total: number }>(
        "/projects"
      );
      return data;
    },
  });
}

export function useProject(projectId: string) {
  return useQuery({
    queryKey: [...PROJECTS_KEY, projectId],
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
    mutationFn: async (dto: CreateProjectDto) => {
      const { data } = await apiClient.post<Project>("/projects", dto);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PROJECTS_KEY });
    },
  });
}

export function useUpdateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, dto }: { id: string; dto: UpdateProjectDto }) => {
      const { data } = await apiClient.put<Project>(`/projects/${id}`, dto);
      return data;
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: [...PROJECTS_KEY, id] });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/projects/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PROJECTS_KEY });
    },
  });
}

export function useFinalizeProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<Project>(`/projects/${id}/finalize`);
      return data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: [...PROJECTS_KEY, id] });
    },
  });
}
```

### 5.2 Generation Hooks (src/api/hooks/useGeneration.ts)

```typescript
import { useState, useCallback, useRef, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../client";
import { VideoPlan, GenerationStatus } from "../../types/generation";

export function useGeneratePlan() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ projectId, storyPrompt }: { projectId: string; storyPrompt: string }) => {
      const { data } = await apiClient.post<VideoPlan>("/generation/plan", {
        project_id: projectId,
        story_prompt: storyPrompt,
      });
      return data;
    },
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
    },
  });
}

export function useCloneVoice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (projectId: string) => {
      const { data } = await apiClient.post<{ voice_id: string }>(
        `/generation/voice-clone?project_id=${projectId}`
      );
      return data.voice_id;
    },
    onSuccess: (_, projectId) => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
    },
  });
}

export function useGenerateSegment() {
  return useMutation({
    mutationFn: async (segmentId: string) => {
      const { data } = await apiClient.post<{ task_id: string; status: string }>(
        `/generation/segment/${segmentId}`
      );
      return data;
    },
  });
}

// Custom hook for polling generation status
export function useGenerationPolling() {
  const [status, setStatus] = useState<GenerationStatus | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const intervalRef = useRef<number | null>(null);
  const queryClient = useQueryClient();

  const pollStatus = useCallback(async (taskId: string) => {
    try {
      const { data } = await apiClient.get<GenerationStatus>(
        `/generation/status/${taskId}`
      );
      setStatus(data);

      if (data.status === "Success" || data.status === "Fail") {
        setIsPolling(false);
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        // Refresh project data
        queryClient.invalidateQueries({ queryKey: ["projects"] });
      }

      return data;
    } catch (error) {
      console.error("Polling error:", error);
      throw error;
    }
  }, [queryClient]);

  const startPolling = useCallback((taskId: string, interval = 5000) => {
    setIsPolling(true);
    setStatus({ taskId, status: "processing" });

    // Initial poll
    pollStatus(taskId);

    // Set up interval
    intervalRef.current = window.setInterval(() => {
      pollStatus(taskId);
    }, interval);
  }, [pollStatus]);

  const stopPolling = useCallback(() => {
    setIsPolling(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    status,
    isPolling,
    startPolling,
    stopPolling,
  };
}
```

---

## 6. Components

### 6.1 App Entry Point (src/App.tsx)

```tsx
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import { AuthProvider } from "./auth/AuthProvider";
import { queryClient } from "./api/queryClient";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";

import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ProjectPage } from "./pages/ProjectPage";
import { NewProjectPage } from "./pages/NewProjectPage";

import "./index.css";

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/projects/new"
              element={
                <ProtectedRoute>
                  <NewProjectPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/projects/:projectId"
              element={
                <ProtectedRoute>
                  <ProjectPage />
                </ProtectedRoute>
              }
            />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
```

### 6.2 Protected Route (src/components/auth/ProtectedRoute.tsx)

```tsx
import { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../auth/useAuth";

interface ProtectedRouteProps {
  children: ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-dark-200">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
          <span className="text-gray-300">Authenticating...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
```

### 6.3 Layout Component (src/components/layout/Layout.tsx)

```tsx
import { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../../auth/useAuth";
import {
  HomeIcon,
  FolderIcon,
  ArrowRightOnRectangleIcon,
} from "@heroicons/react/24/outline";

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuth();
  const location = useLocation();

  const navItems = [
    { path: "/dashboard", label: "Dashboard", icon: HomeIcon },
    { path: "/projects", label: "Projects", icon: FolderIcon },
  ];

  return (
    <div className="flex h-screen bg-dark-200">
      {/* Sidebar */}
      <aside className="flex w-64 flex-col bg-dark-300 border-r border-gray-700">
        <div className="flex h-16 items-center justify-center border-b border-gray-700">
          <h1 className="text-xl font-bold text-white">AI Video Creator</h1>
        </div>

        <nav className="flex-1 space-y-1 p-4">
          {navItems.map(({ path, label, icon: Icon }) => {
            const isActive = location.pathname.startsWith(path);
            return (
              <Link
                key={path}
                to={path}
                className={`flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary-600 text-white"
                    : "text-gray-300 hover:bg-dark-100 hover:text-white"
                }`}
              >
                <Icon className="h-5 w-5" />
                {label}
              </Link>
            );
          })}
        </nav>

        {/* User section */}
        <div className="border-t border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-primary-600 flex items-center justify-center">
              <span className="text-white font-medium">
                {user?.name?.[0] || "U"}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {user?.name}
              </p>
              <p className="text-xs text-gray-400 truncate">{user?.email}</p>
            </div>
            <button
              onClick={logout}
              className="p-2 text-gray-400 hover:text-white"
              title="Logout"
            >
              <ArrowRightOnRectangleIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="p-6">{children}</div>
      </main>
    </div>
  );
}
```

### 6.4 Project Card (src/components/projects/ProjectCard.tsx)

```tsx
import { Link } from "react-router-dom";
import { Project, ProjectStatus } from "../../types/project";
import { PlayIcon, ClockIcon, CheckCircleIcon } from "@heroicons/react/24/solid";

interface ProjectCardProps {
  project: Project;
}

const statusConfig: Record<ProjectStatus, { label: string; color: string }> = {
  created: { label: "Created", color: "bg-gray-500" },
  media_uploaded: { label: "Media Uploaded", color: "bg-blue-500" },
  voice_cloning: { label: "Cloning Voice", color: "bg-yellow-500" },
  plan_generating: { label: "Generating Plan", color: "bg-yellow-500" },
  plan_ready: { label: "Plan Ready", color: "bg-blue-500" },
  generating: { label: "Generating", color: "bg-yellow-500" },
  finalizing: { label: "Finalizing", color: "bg-yellow-500" },
  completed: { label: "Completed", color: "bg-green-500" },
  failed: { label: "Failed", color: "bg-red-500" },
};

export function ProjectCard({ project }: ProjectCardProps) {
  const status = statusConfig[project.status];
  const progress = calculateProgress(project);

  return (
    <Link
      to={`/projects/${project.id}`}
      className="block rounded-xl bg-dark-100 border border-gray-700 p-6 
                 transition-all hover:border-primary-500 hover:shadow-lg hover:shadow-primary-500/10"
    >
      {/* Thumbnail */}
      <div className="relative aspect-video rounded-lg bg-dark-300 mb-4 overflow-hidden">
        {project.firstFrameUrl ? (
          <img
            src={project.firstFrameUrl}
            alt={project.name}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <PlayIcon className="h-12 w-12 text-gray-600" />
          </div>
        )}

        {/* Status badge */}
        <span
          className={`absolute top-2 right-2 px-2 py-1 text-xs font-medium text-white rounded-full ${status.color}`}
        >
          {status.label}
        </span>
      </div>

      {/* Project info */}
      <h3 className="text-lg font-semibold text-white mb-2 truncate">
        {project.name}
      </h3>

      <div className="flex items-center gap-4 text-sm text-gray-400">
        <span className="flex items-center gap-1">
          <ClockIcon className="h-4 w-4" />
          {project.targetDurationSec}s
        </span>
        <span className="flex items-center gap-1">
          <CheckCircleIcon className="h-4 w-4" />
          {project.segments.filter((s) => s.approved).length}/{project.segmentCount} segments
        </span>
      </div>

      {/* Progress bar */}
      {progress > 0 && progress < 100 && (
        <div className="mt-4">
          <div className="h-1.5 w-full bg-dark-300 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-500 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}
    </Link>
  );
}

function calculateProgress(project: Project): number {
  if (project.status === "completed") return 100;
  if (project.status === "created") return 0;

  const totalSteps = project.segmentCount * 2 + 3; // segments * 2 (plan + generate) + upload + voice + finalize
  let completedSteps = 0;

  if (project.firstFrameUrl) completedSteps++;
  if (project.voiceId) completedSteps++;

  project.segments.forEach((segment) => {
    if (segment.status !== "pending") completedSteps++;
    if (segment.videoUrl) completedSteps++;
  });

  if (project.finalVideoUrl) completedSteps++;

  return Math.round((completedSteps / totalSteps) * 100);
}
```

### 6.5 Segment Editor (src/components/segments/SegmentEditor.tsx)

```tsx
import { useState, useCallback } from "react";
import { Segment } from "../../types/project";
import {
  CheckIcon,
  PencilIcon,
  PlayIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";

interface SegmentEditorProps {
  segment: Segment;
  isGenerating: boolean;
  onApprove: (segment: Segment) => void;
  onUpdate: (segment: Segment, updates: Partial<Segment>) => void;
  onGenerate: (segment: Segment) => void;
}

export function SegmentEditor({
  segment,
  isGenerating,
  onApprove,
  onUpdate,
  onGenerate,
}: SegmentEditorProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedPrompt, setEditedPrompt] = useState(segment.videoPrompt);
  const [editedNarration, setEditedNarration] = useState(segment.narrationText);

  const handleSave = useCallback(() => {
    onUpdate(segment, {
      videoPrompt: editedPrompt,
      narrationText: editedNarration,
    });
    setIsEditing(false);
  }, [segment, editedPrompt, editedNarration, onUpdate]);

  const handleCancel = useCallback(() => {
    setEditedPrompt(segment.videoPrompt);
    setEditedNarration(segment.narrationText);
    setIsEditing(false);
  }, [segment]);

  return (
    <div className="rounded-xl bg-dark-100 border border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between bg-dark-300 px-4 py-3">
        <span className="font-medium text-white">
          Segment {segment.index + 1}
        </span>
        <StatusBadge status={segment.status} />
      </div>

      <div className="p-4 space-y-4">
        {/* Video Preview / First Frame */}
        <div className="relative aspect-video rounded-lg bg-dark-300 overflow-hidden">
          {segment.videoUrl ? (
            <video
              src={segment.videoUrl}
              controls
              className="h-full w-full object-cover"
            />
          ) : segment.firstFrameUrl ? (
            <img
              src={segment.firstFrameUrl}
              alt={`Segment ${segment.index + 1}`}
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-gray-500">
              No preview
            </div>
          )}

          {isGenerating && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/50">
              <ArrowPathIcon className="h-10 w-10 text-white animate-spin" />
            </div>
          )}
        </div>

        {/* Editable Fields */}
        {isEditing ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Video Prompt
              </label>
              <textarea
                value={editedPrompt}
                onChange={(e) => setEditedPrompt(e.target.value)}
                rows={3}
                className="w-full rounded-lg bg-dark-300 border border-gray-600 px-4 py-2 
                           text-white placeholder-gray-500 focus:border-primary-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Narration
              </label>
              <textarea
                value={editedNarration}
                onChange={(e) => setEditedNarration(e.target.value)}
                rows={2}
                className="w-full rounded-lg bg-dark-300 border border-gray-600 px-4 py-2 
                           text-white placeholder-gray-500 focus:border-primary-500 focus:outline-none"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleSave}
                className="flex-1 rounded-lg bg-primary-600 px-4 py-2 text-white 
                           font-medium hover:bg-primary-700 transition-colors"
              >
                Save
              </button>
              <button
                onClick={handleCancel}
                className="flex-1 rounded-lg bg-gray-600 px-4 py-2 text-white 
                           font-medium hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-medium text-gray-400 mb-1">
                Video Prompt
              </h4>
              <p className="text-white">{segment.videoPrompt}</p>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-400 mb-1">
                Narration
              </h4>
              <p className="text-white">{segment.narrationText}</p>
            </div>
          </div>
        )}

        {/* Actions */}
        {!isEditing && (
          <div className="flex gap-2 pt-2">
            <button
              onClick={() => setIsEditing(true)}
              disabled={segment.approved || isGenerating}
              className="flex-1 flex items-center justify-center gap-2 rounded-lg 
                         bg-dark-300 px-4 py-2 text-white font-medium 
                         hover:bg-dark-100 transition-colors disabled:opacity-50"
            >
              <PencilIcon className="h-4 w-4" />
              Edit
            </button>

            {!segment.approved && segment.status === "prompt_ready" && (
              <button
                onClick={() => onApprove(segment)}
                disabled={isGenerating}
                className="flex-1 flex items-center justify-center gap-2 rounded-lg 
                           bg-green-600 px-4 py-2 text-white font-medium 
                           hover:bg-green-700 transition-colors disabled:opacity-50"
              >
                <CheckIcon className="h-4 w-4" />
                Approve
              </button>
            )}

            {segment.approved && !segment.videoUrl && (
              <button
                onClick={() => onGenerate(segment)}
                disabled={isGenerating}
                className="flex-1 flex items-center justify-center gap-2 rounded-lg 
                           bg-primary-600 px-4 py-2 text-white font-medium 
                           hover:bg-primary-700 transition-colors disabled:opacity-50"
              >
                <PlayIcon className="h-4 w-4" />
                Generate
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; color: string }> = {
    pending: { label: "Pending", color: "bg-gray-500" },
    prompt_ready: { label: "Ready", color: "bg-blue-500" },
    approved: { label: "Approved", color: "bg-green-500" },
    generating: { label: "Generating", color: "bg-yellow-500" },
    generated: { label: "Generated", color: "bg-green-500" },
    segment_approved: { label: "Complete", color: "bg-green-600" },
    failed: { label: "Failed", color: "bg-red-500" },
  };

  const { label, color } = config[status] || config.pending;

  return (
    <span className={`px-2 py-1 text-xs font-medium text-white rounded-full ${color}`}>
      {label}
    </span>
  );
}
```

### 6.6 File Upload Component (src/components/upload/FileUploader.tsx)

```tsx
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { CloudArrowUpIcon, XMarkIcon } from "@heroicons/react/24/outline";

interface FileUploaderProps {
  accept: Record<string, string[]>;
  maxSize?: number; // bytes
  label: string;
  hint?: string;
  onFileSelect: (file: File) => void;
  isUploading?: boolean;
  currentFile?: string;
}

export function FileUploader({
  accept,
  maxSize = 20 * 1024 * 1024, // 20MB default
  label,
  hint,
  onFileSelect,
  isUploading = false,
  currentFile,
}: FileUploaderProps) {
  const [preview, setPreview] = useState<string | null>(currentFile || null);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: any[]) => {
      setError(null);

      if (rejectedFiles.length > 0) {
        const rejection = rejectedFiles[0];
        if (rejection.errors[0]?.code === "file-too-large") {
          setError(`File is too large. Max size: ${maxSize / 1024 / 1024}MB`);
        } else {
          setError("Invalid file type");
        }
        return;
      }

      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];

        // Generate preview for images
        if (file.type.startsWith("image/")) {
          const reader = new FileReader();
          reader.onload = () => setPreview(reader.result as string);
          reader.readAsDataURL(file);
        }

        onFileSelect(file);
      }
    },
    [maxSize, onFileSelect]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxSize,
    multiple: false,
    disabled: isUploading,
  });

  const clearPreview = useCallback(() => {
    setPreview(null);
    setError(null);
  }, []);

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-300">{label}</label>

      {preview ? (
        <div className="relative rounded-lg overflow-hidden">
          <img src={preview} alt="Preview" className="w-full h-48 object-cover" />
          <button
            onClick={clearPreview}
            className="absolute top-2 right-2 p-1 rounded-full bg-black/50 
                       text-white hover:bg-black/70 transition-colors"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
      ) : (
        <div
          {...getRootProps()}
          className={`relative flex flex-col items-center justify-center h-48 
                      rounded-lg border-2 border-dashed transition-colors cursor-pointer
                      ${isDragActive ? "border-primary-500 bg-primary-500/10" : "border-gray-600 hover:border-gray-500"}
                      ${error ? "border-red-500" : ""}
                      ${isUploading ? "opacity-50 cursor-not-allowed" : ""}`}
        >
          <input {...getInputProps()} />

          {isUploading ? (
            <div className="flex flex-col items-center gap-2">
              <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
              <span className="text-gray-400">Uploading...</span>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <CloudArrowUpIcon className="h-10 w-10 text-gray-400" />
              <span className="text-gray-400">
                {isDragActive ? "Drop file here" : "Drag & drop or click to upload"}
              </span>
              {hint && <span className="text-xs text-gray-500">{hint}</span>}
            </div>
          )}
        </div>
      )}

      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  );
}
```

### 6.7 Dual Frame Uploader Component (src/components/upload/DualFrameUploader.tsx)

```tsx
/**
 * DualFrameUploader - Upload both first and last frame images for FL2V
 * 
 * This component supports the MiniMax First & Last Frame Video Generation API.
 * 
 * Image Requirements (per MiniMax API):
 * - Formats: JPG, JPEG, PNG, WebP
 * - Size: < 20MB each
 * - Dimensions: Short side > 300px, Aspect ratio 2:5 to 5:2
 * - Video resolution follows first_frame_image
 * - last_frame_image will be cropped to match first_frame dimensions
 */
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { 
  CloudArrowUpIcon, 
  XMarkIcon,
  ArrowRightIcon,
  ExclamationTriangleIcon 
} from "@heroicons/react/24/outline";

interface FrameImage {
  file: File;
  preview: string;
  dataUrl: string; // base64 data URL for API submission
}

interface DualFrameUploaderProps {
  onFramesChange: (frames: { firstFrame?: FrameImage; lastFrame: FrameImage }) => void;
  isUploading?: boolean;
  existingFirstFrame?: string;
  existingLastFrame?: string;
  showFirstFrame?: boolean; // If false, only show last frame upload
}

// Image validation constants (MiniMax API requirements)
const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20MB
const ACCEPTED_FORMATS = {
  "image/jpeg": [".jpg", ".jpeg"],
  "image/png": [".png"],
  "image/webp": [".webp"],
};
const MIN_SHORT_SIDE = 300;
const MIN_ASPECT_RATIO = 2 / 5; // 2:5
const MAX_ASPECT_RATIO = 5 / 2; // 5:2

interface ValidationResult {
  valid: boolean;
  error?: string;
}

async function validateImage(file: File): Promise<ValidationResult> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const { width, height } = img;
      const shortSide = Math.min(width, height);
      const aspectRatio = width / height;
      
      if (shortSide < MIN_SHORT_SIDE) {
        resolve({ 
          valid: false, 
          error: `Short side must be > ${MIN_SHORT_SIDE}px (got ${shortSide}px)` 
        });
        return;
      }
      
      if (aspectRatio < MIN_ASPECT_RATIO || aspectRatio > MAX_ASPECT_RATIO) {
        resolve({ 
          valid: false, 
          error: `Aspect ratio must be between 2:5 and 5:2 (got ${aspectRatio.toFixed(2)})` 
        });
        return;
      }
      
      resolve({ valid: true });
    };
    img.onerror = () => resolve({ valid: false, error: "Failed to load image" });
    img.src = URL.createObjectURL(file);
  });
}

function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export function DualFrameUploader({
  onFramesChange,
  isUploading = false,
  existingFirstFrame,
  existingLastFrame,
  showFirstFrame = true,
}: DualFrameUploaderProps) {
  const [firstFrame, setFirstFrame] = useState<FrameImage | null>(null);
  const [lastFrame, setLastFrame] = useState<FrameImage | null>(null);
  const [errors, setErrors] = useState<{ first?: string; last?: string }>({});

  const processFile = useCallback(async (
    file: File, 
    type: "first" | "last"
  ): Promise<FrameImage | null> => {
    // Validate image dimensions
    const validation = await validateImage(file);
    if (!validation.valid) {
      setErrors(prev => ({ ...prev, [type]: validation.error }));
      return null;
    }
    
    // Convert to data URL for API submission
    const dataUrl = await fileToDataUrl(file);
    const preview = URL.createObjectURL(file);
    
    return { file, preview, dataUrl };
  }, []);

  const handleFirstFrameDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    
    setErrors(prev => ({ ...prev, first: undefined }));
    const frame = await processFile(acceptedFiles[0], "first");
    
    if (frame) {
      setFirstFrame(frame);
      if (lastFrame) {
        onFramesChange({ firstFrame: frame, lastFrame });
      }
    }
  }, [processFile, lastFrame, onFramesChange]);

  const handleLastFrameDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    
    setErrors(prev => ({ ...prev, last: undefined }));
    const frame = await processFile(acceptedFiles[0], "last");
    
    if (frame) {
      setLastFrame(frame);
      onFramesChange({ 
        firstFrame: firstFrame || undefined, 
        lastFrame: frame 
      });
    }
  }, [processFile, firstFrame, onFramesChange]);

  const clearFirstFrame = useCallback(() => {
    if (firstFrame?.preview) URL.revokeObjectURL(firstFrame.preview);
    setFirstFrame(null);
    setErrors(prev => ({ ...prev, first: undefined }));
  }, [firstFrame]);

  const clearLastFrame = useCallback(() => {
    if (lastFrame?.preview) URL.revokeObjectURL(lastFrame.preview);
    setLastFrame(null);
    setErrors(prev => ({ ...prev, last: undefined }));
  }, [lastFrame]);

  const firstFrameDropzone = useDropzone({
    onDrop: handleFirstFrameDrop,
    accept: ACCEPTED_FORMATS,
    maxSize: MAX_FILE_SIZE,
    multiple: false,
    disabled: isUploading,
  });

  const lastFrameDropzone = useDropzone({
    onDrop: handleLastFrameDrop,
    accept: ACCEPTED_FORMATS,
    maxSize: MAX_FILE_SIZE,
    multiple: false,
    disabled: isUploading,
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm text-gray-400">
        <span>First & Last Frame Video Generation (FL2V)</span>
        <span className="text-xs bg-primary-600/20 text-primary-400 px-2 py-0.5 rounded">
          MiniMax-Hailuo-02
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
        {/* First Frame Upload (Optional) */}
        {showFirstFrame && (
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-300">
              First Frame <span className="text-gray-500">(Optional)</span>
            </label>
            
            {firstFrame ? (
              <div className="relative rounded-lg overflow-hidden aspect-video bg-dark-300">
                <img 
                  src={firstFrame.preview} 
                  alt="First frame" 
                  className="w-full h-full object-cover" 
                />
                <button
                  onClick={clearFirstFrame}
                  className="absolute top-2 right-2 p-1 rounded-full bg-black/50 
                             text-white hover:bg-black/70 transition-colors"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
                <div className="absolute bottom-2 left-2 text-xs bg-black/50 px-2 py-1 rounded text-white">
                  Video resolution follows this frame
                </div>
              </div>
            ) : (
              <div
                {...firstFrameDropzone.getRootProps()}
                className={`relative flex flex-col items-center justify-center aspect-video
                            rounded-lg border-2 border-dashed transition-colors cursor-pointer
                            ${firstFrameDropzone.isDragActive ? "border-primary-500 bg-primary-500/10" : "border-gray-600 hover:border-gray-500"}
                            ${errors.first ? "border-red-500" : ""}`}
              >
                <input {...firstFrameDropzone.getInputProps()} />
                <CloudArrowUpIcon className="h-8 w-8 text-gray-400 mb-2" />
                <span className="text-sm text-gray-400">First Frame</span>
                <span className="text-xs text-gray-500">Sets video resolution</span>
              </div>
            )}
            
            {errors.first && (
              <p className="text-sm text-red-500 flex items-center gap-1">
                <ExclamationTriangleIcon className="h-4 w-4" />
                {errors.first}
              </p>
            )}
          </div>
        )}

        {/* Arrow between frames */}
        {showFirstFrame && (
          <div className="hidden md:flex items-center justify-center">
            <ArrowRightIcon className="h-8 w-8 text-gray-500" />
          </div>
        )}

        {/* Last Frame Upload (Required) */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-300">
            Last Frame <span className="text-red-400">*</span>
          </label>
          
          {lastFrame ? (
            <div className="relative rounded-lg overflow-hidden aspect-video bg-dark-300">
              <img 
                src={lastFrame.preview} 
                alt="Last frame" 
                className="w-full h-full object-cover" 
              />
              <button
                onClick={clearLastFrame}
                className="absolute top-2 right-2 p-1 rounded-full bg-black/50 
                           text-white hover:bg-black/70 transition-colors"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
              <div className="absolute bottom-2 left-2 text-xs bg-black/50 px-2 py-1 rounded text-white">
                Will be cropped to match first frame
              </div>
            </div>
          ) : (
            <div
              {...lastFrameDropzone.getRootProps()}
              className={`relative flex flex-col items-center justify-center aspect-video
                          rounded-lg border-2 border-dashed transition-colors cursor-pointer
                          ${lastFrameDropzone.isDragActive ? "border-primary-500 bg-primary-500/10" : "border-gray-600 hover:border-gray-500"}
                          ${errors.last ? "border-red-500" : ""}`}
            >
              <input {...lastFrameDropzone.getInputProps()} />
              <CloudArrowUpIcon className="h-8 w-8 text-gray-400 mb-2" />
              <span className="text-sm text-gray-400">Last Frame (Required)</span>
              <span className="text-xs text-gray-500">Target end of video</span>
            </div>
          )}
          
          {errors.last && (
            <p className="text-sm text-red-500 flex items-center gap-1">
              <ExclamationTriangleIcon className="h-4 w-4" />
              {errors.last}
            </p>
          )}
        </div>
      </div>

      {/* Requirements hint */}
      <div className="text-xs text-gray-500 space-y-1">
        <p>• Formats: JPG, PNG, WebP • Max size: 20MB</p>
        <p>• Dimensions: Short side &gt; 300px, Aspect ratio 2:5 to 5:2</p>
        <p>• Supported resolutions: 768P, 1080P (512P not supported for FL2V)</p>
      </div>
    </div>
  );
}
```

### 6.8 Camera Command Selector (src/components/generation/CameraCommandSelector.tsx)

```tsx
/**
 * CameraCommandSelector - Select camera movement commands for FL2V prompts
 * 
 * MiniMax supports 15 camera commands that can be embedded in prompts.
 * Max 3 simultaneous commands allowed.
 */
import { useState, useCallback } from "react";
import { CameraCommand, CAMERA_COMMANDS } from "../../types/generation";
import { CheckIcon, XMarkIcon } from "@heroicons/react/24/outline";

interface CameraCommandSelectorProps {
  selected: CameraCommand[];
  onChange: (commands: CameraCommand[]) => void;
  maxCommands?: number;
}

export function CameraCommandSelector({
  selected,
  onChange,
  maxCommands = 3,
}: CameraCommandSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);

  const toggleCommand = useCallback((command: CameraCommand) => {
    if (selected.includes(command)) {
      onChange(selected.filter(c => c !== command));
    } else if (selected.length < maxCommands) {
      onChange([...selected, command]);
    }
  }, [selected, onChange, maxCommands]);

  const removeCommand = useCallback((command: CameraCommand) => {
    onChange(selected.filter(c => c !== command));
  }, [selected, onChange]);

  // Group commands by category
  const groupedCommands = CAMERA_COMMANDS.reduce((acc, cmd) => {
    if (!acc[cmd.category]) acc[cmd.category] = [];
    acc[cmd.category].push(cmd);
    return acc;
  }, {} as Record<string, typeof CAMERA_COMMANDS>);

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-300">
        Camera Commands <span className="text-gray-500">(max {maxCommands})</span>
      </label>

      {/* Selected commands */}
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {selected.map(cmd => (
            <span
              key={cmd}
              className="inline-flex items-center gap-1 px-2 py-1 text-sm 
                         bg-primary-600/20 text-primary-400 rounded"
            >
              {cmd.replace(/[\[\]]/g, "")}
              <button
                onClick={() => removeCommand(cmd)}
                className="hover:text-primary-200"
              >
                <XMarkIcon className="h-4 w-4" />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Command selector */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="text-sm text-primary-400 hover:text-primary-300"
      >
        {isOpen ? "Hide commands" : "Add camera command..."}
      </button>

      {isOpen && (
        <div className="rounded-lg bg-dark-300 border border-gray-600 p-3 space-y-3">
          {Object.entries(groupedCommands).map(([category, commands]) => (
            <div key={category}>
              <h4 className="text-xs font-medium text-gray-400 mb-1">{category}</h4>
              <div className="flex flex-wrap gap-1">
                {commands.map(({ value, label }) => {
                  const isSelected = selected.includes(value);
                  const isDisabled = !isSelected && selected.length >= maxCommands;
                  
                  return (
                    <button
                      key={value}
                      type="button"
                      onClick={() => toggleCommand(value)}
                      disabled={isDisabled}
                      className={`px-2 py-1 text-xs rounded transition-colors
                        ${isSelected 
                          ? "bg-primary-600 text-white" 
                          : isDisabled
                            ? "bg-gray-700 text-gray-500 cursor-not-allowed"
                            : "bg-dark-100 text-gray-300 hover:bg-dark-200"
                        }`}
                    >
                      {isSelected && <CheckIcon className="inline h-3 w-3 mr-1" />}
                      {label}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
          
          <p className="text-xs text-gray-500">
            Tip: Multiple commands like [Pan left,Zoom in] execute simultaneously
          </p>
        </div>
      )}
    </div>
  );
}
```

---

## 7. Pages

### 7.1 Dashboard Page (src/pages/DashboardPage.tsx)

```tsx
import { Link } from "react-router-dom";
import { Layout } from "../components/layout/Layout";
import { ProjectCard } from "../components/projects/ProjectCard";
import { useProjects } from "../api/hooks/useProjects";
import { PlusIcon } from "@heroicons/react/24/outline";

export function DashboardPage() {
  const { data, isLoading, error } = useProjects();

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Projects</h1>
            <p className="text-gray-400">
              Create and manage your AI video projects
            </p>
          </div>
          <Link
            to="/projects/new"
            className="flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 
                       text-white font-medium hover:bg-primary-700 transition-colors"
          >
            <PlusIcon className="h-5 w-5" />
            New Project
          </Link>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
          </div>
        ) : error ? (
          <div className="rounded-lg bg-red-500/10 border border-red-500 p-4 text-red-400">
            Failed to load projects. Please try again.
          </div>
        ) : data?.projects.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="rounded-full bg-dark-100 p-4 mb-4">
              <PlusIcon className="h-8 w-8 text-gray-500" />
            </div>
            <h3 className="text-lg font-medium text-white mb-2">
              No projects yet
            </h3>
            <p className="text-gray-400 mb-4">
              Create your first AI video project to get started
            </p>
            <Link
              to="/projects/new"
              className="rounded-lg bg-primary-600 px-4 py-2 text-white 
                         font-medium hover:bg-primary-700 transition-colors"
            >
              Create Project
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data?.projects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
```

---

## 8. Testing

### 8.1 Component Test Example (src/components/__tests__/ProjectCard.test.tsx)

```tsx
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { ProjectCard } from "../projects/ProjectCard";
import { Project } from "../../types/project";

const mockProject: Project = {
  id: "1",
  userId: "user-1",
  name: "Test Project",
  storyPrompt: "A test story",
  targetDurationSec: 30,
  segmentLenSec: 6,
  segmentCount: 5,
  status: "plan_ready",
  segments: [
    { id: "s1", index: 0, videoPrompt: "", narrationText: "", endFramePrompt: "", status: "approved", approved: true },
    { id: "s2", index: 1, videoPrompt: "", narrationText: "", endFramePrompt: "", status: "pending", approved: false },
  ],
  createdAt: "2024-01-01T00:00:00Z",
  updatedAt: "2024-01-01T00:00:00Z",
};

describe("ProjectCard", () => {
  it("renders project name", () => {
    render(
      <BrowserRouter>
        <ProjectCard project={mockProject} />
      </BrowserRouter>
    );

    expect(screen.getByText("Test Project")).toBeInTheDocument();
  });

  it("shows correct segment count", () => {
    render(
      <BrowserRouter>
        <ProjectCard project={mockProject} />
      </BrowserRouter>
    );

    expect(screen.getByText(/1\/5 segments/)).toBeInTheDocument();
  });

  it("displays status badge", () => {
    render(
      <BrowserRouter>
        <ProjectCard project={mockProject} />
      </BrowserRouter>
    );

    expect(screen.getByText("Plan Ready")).toBeInTheDocument();
  });
});
```

---

## 9. Next Steps

After implementing the frontend:

1. **Run locally:**
   ```bash
   npm run dev
   ```

2. **Run tests:**
   ```bash
   npm test
   ```

3. **Build for production:**
   ```bash
   npm run build
   ```

4. **Proceed to JWT Authentication:**
   - Your JWT authentication is now configured and ready to use
