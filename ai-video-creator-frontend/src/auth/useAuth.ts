import { useMsal } from '@azure/msal-react';
import { useCallback, useState } from 'react';
import { apiRequest } from './msalConfig';

export function useAuth() {
  const { instance, accounts } = useMsal();
  const [isLoading, setIsLoading] = useState(false);

  const account = accounts[0] || null;

  const getAccessToken = useCallback(async (): Promise<string | null> => {
    if (!account) return null;

    try {
      const response = await instance.acquireTokenSilent({
        ...apiRequest,
        account,
      });
      return response.accessToken;
    } catch (error) {
      console.error('Failed to acquire token silently:', error);
      try {
        const response = await instance.acquireTokenPopup(apiRequest);
        return response.accessToken;
      } catch (popupError) {
        console.error('Failed to acquire token via popup:', popupError);
        return null;
      }
    }
  }, [instance, account]);

  const login = useCallback(async () => {
    setIsLoading(true);
    try {
      await instance.loginRedirect(apiRequest);
    } catch (error) {
      console.error('Login failed:', error);
      setIsLoading(false);
    }
  }, [instance]);

  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      await instance.logoutRedirect({
        postLogoutRedirectUri: window.location.origin,
      });
    } catch (error) {
      console.error('Logout failed:', error);
      setIsLoading(false);
    }
  }, [instance]);

  return {
    account,
    isAuthenticated: !!account,
    isLoading,
    getAccessToken,
    login,
    logout,
  };
}
