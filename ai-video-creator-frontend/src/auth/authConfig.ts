/**
 * Authentication configuration for JWT-based auth.
 */

// Token storage key
export const TOKEN_STORAGE_KEY = 'access_token';

// API base URL
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

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
