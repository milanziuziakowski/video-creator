import { Routes, Route, Navigate } from 'react-router-dom';
import { useIsAuthenticated } from '@azure/msal-react';

import { AuthGuard } from './auth/AuthGuard';
import { Layout } from './components/Layout';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ProjectsPage } from './pages/ProjectsPage';
import { NewProjectPage } from './pages/NewProjectPage';
import { ProjectDetailPage } from './pages/ProjectDetailPage';

function App() {
  const isAuthenticated = useIsAuthenticated();

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />}
      />
      <Route
        path="/"
        element={
          <AuthGuard>
            <Layout />
          </AuthGuard>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="projects/new" element={<NewProjectPage />} />
        <Route path="projects/:projectId" element={<ProjectDetailPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
