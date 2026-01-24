/**
 * SECURITY: Backend-First API Client
 *
 * This module provides a secure API client that enforces the backend-first
 * architecture pattern. ALL data access MUST go through the API layer.
 *
 * CRITICAL: NEVER use client-side database SDKs directly in the frontend.
 * The frontend is a VIEW LAYER ONLY - it speaks to APIs, not databases.
 */

import { QueryClient, QueryFunction } from "@tanstack/react-query";

// API base URL - uses relative paths to work with Vite proxy
const API_BASE_URL = "";

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  public status: number;
  public data: unknown;

  constructor(status: number, message: string, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

/**
 * Secure API request function that handles authentication and error handling.
 *
 * SECURITY: All requests are routed through the backend API.
 * - Never exposes database credentials to the client
 * - Authentication tokens are handled via httpOnly cookies (when implemented)
 * - All sensitive operations happen server-side
 *
 * @param method HTTP method
 * @param endpoint API endpoint (relative to API_BASE_URL)
 * @param body Optional request body
 * @returns Response object
 */
export async function apiRequest(
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE",
  endpoint: string,
  body?: Record<string, unknown>
): Promise<Response> {
  const url = `${API_BASE_URL}${endpoint}`;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  const config: RequestInit = {
    method,
    headers,
    credentials: "include", // Include cookies for session-based auth
  };

  if (body && method !== "GET") {
    config.body = JSON.stringify(body);
  }

  const response = await fetch(url, config);

  // Handle authentication errors
  if (response.status === 401) {
    // Optionally redirect to login or dispatch an auth event
    window.dispatchEvent(new CustomEvent("auth:unauthorized"));
    throw new ApiError(401, "Unauthorized - Please log in");
  }

  // Handle forbidden errors
  if (response.status === 403) {
    throw new ApiError(403, "Forbidden - Insufficient permissions");
  }

  // Handle server errors
  if (response.status >= 500) {
    throw new ApiError(response.status, "Server error - Please try again later");
  }

  return response;
}

/**
 * Default query function for React Query.
 * Uses the secure apiRequest function for all data fetching.
 */
const defaultQueryFn: QueryFunction = async ({ queryKey }) => {
  const [endpoint] = queryKey as [string];
  const response = await apiRequest("GET", endpoint);

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      error.message || `Request failed: ${response.statusText}`,
      error
    );
  }

  return response.json();
};

/**
 * React Query client with secure defaults.
 *
 * SECURITY CONFIGURATION:
 * - All queries use the secure apiRequest function
 * - Retry is disabled for 4xx errors (client errors)
 * - Stale time prevents excessive API calls
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      queryFn: defaultQueryFn,
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: (failureCount, error) => {
        // Don't retry on authentication/authorization errors
        if (error instanceof ApiError) {
          if (error.status === 401 || error.status === 403 || error.status === 404) {
            return false;
          }
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

/**
 * Type-safe API request helper with automatic JSON parsing.
 *
 * @example
 * const user = await fetchApi<User>("/api/users/me");
 */
export async function fetchApi<T>(
  endpoint: string,
  options?: {
    method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
    body?: Record<string, unknown>;
  }
): Promise<T> {
  const { method = "GET", body } = options ?? {};
  const response = await apiRequest(method, endpoint, body);

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      error.detail || error.message || `Request failed: ${response.statusText}`,
      error
    );
  }

  return response.json();
}
