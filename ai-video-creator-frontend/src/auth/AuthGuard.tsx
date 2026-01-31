import { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import {
  useIsAuthenticated,
  useMsal,
  AuthenticatedTemplate,
  UnauthenticatedTemplate,
} from '@azure/msal-react';
import { InteractionStatus } from '@azure/msal-browser';

interface AuthGuardProps {
  children: ReactNode;
}

export function AuthGuard({ children }: AuthGuardProps) {
  const isAuthenticated = useIsAuthenticated();
  const { inProgress } = useMsal();
  const location = useLocation();

  if (inProgress !== InteractionStatus.None) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="mb-4 h-12 w-12 animate-spin rounded-full border-4 border-blue-600 border-t-transparent mx-auto" />
          <p className="text-gray-600">Authenticating...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <AuthenticatedTemplate>{children}</AuthenticatedTemplate>
      <UnauthenticatedTemplate>
        <Navigate to="/login" state={{ from: location }} replace />
      </UnauthenticatedTemplate>
    </>
  );
}
