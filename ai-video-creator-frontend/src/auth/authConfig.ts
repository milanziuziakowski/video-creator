/**
 * Simple JWT Authentication Configuration
 * 
 * This app uses simple username/password authentication with JWT tokens.
 * No Azure Entra ID or other OAuth providers - just straightforward JWT auth.
 * 
 * - User registers with username/email/password
 * - User logs in and receives JWT access token
 * - Token is stored in localStorage
 * - Token is attached to all API requests via Authorization header
 */

// Token storage key
export const TOKEN_STORAGE_KEY = 'access_token';

// API base URL
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

/**
 * Get stored access token from localStorage
 */
export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

/**
 * Store access token in localStorage
 */
export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

/**
 * Remove access token from localStorage
 */
export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

/**
 * Check if user is authenticated (has token)
 */
export function isAuthenticated(): boolean {
  return !!getStoredToken();
}
