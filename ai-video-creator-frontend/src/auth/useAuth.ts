import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getStoredToken,
  setStoredToken,
  clearStoredToken,
  API_BASE_URL,
} from './authConfig';

interface User {
  id: string;
  username: string;
  email: string;
  name: string | null;
  is_active: boolean;
}

interface LoginCredentials {
  username: string;
  password: string;
}

interface RegisterData {
  username: string;
  email: string;
  password: string;
  name?: string;
}

export function useAuth() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(() => !!getStoredToken());
  const navigate = useNavigate();

  // Fetch current user on mount if authenticated
  useEffect(() => {
    const token = getStoredToken();
    if (token && !user) {
      fetchCurrentUser();
    }
  }, []);

  const fetchCurrentUser = useCallback(async () => {
    const token = getStoredToken();
    if (!token) {
      setIsAuthenticated(false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setIsAuthenticated(true);
      } else {
        // Token is invalid
        clearStoredToken();
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch {
      console.error('Failed to fetch current user');
    }
  }, []);

  const getAccessToken = useCallback(async (): Promise<string | null> => {
    return getStoredToken();
  }, []);

  const login = useCallback(async (credentials: LoginCredentials) => {
    setIsLoading(true);
    setError(null);

    try {
      const formData = new URLSearchParams();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);

      const response = await fetch(`${API_BASE_URL}/auth/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
      }

      const data = await response.json();
      // API returns camelCase (accessToken) due to backend alias_generator
      setStoredToken(data.accessToken);
      setIsAuthenticated(true);

      // Fetch user info
      await fetchCurrentUser();

      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [navigate, fetchCurrentUser]);

  const register = useCallback(async (data: RegisterData) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Registration failed');
      }

      // Auto-login after registration
      await login({ username: data.username, password: data.password });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [login]);

  const logout = useCallback(() => {
    clearStoredToken();
    setUser(null);
    setIsAuthenticated(false);
    navigate('/login');
  }, [navigate]);

  return {
    user,
    account: user, // Alias for compatibility
    isAuthenticated,
    isLoading,
    error,
    getAccessToken,
    login,
    register,
    logout,
    fetchCurrentUser,
  };
}
