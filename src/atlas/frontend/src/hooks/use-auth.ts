import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getAuthToken, setAuthToken } from "@/lib/queryClient";

// Combined auth user type with identity and domain user fields
export interface AuthUser {
  id: string;
  email: string | null;
  firstName: string | null;
  lastName: string | null;
  profileImageUrl: string | null;
  userId?: string;
  tenantId?: string;
  role: string;
  platformRole?: string;
}

async function fetchUser(): Promise<AuthUser | null> {
  const token = getAuthToken();
  const headers: HeadersInit = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch("/api/auth/user", {
    credentials: "include",
    headers,
  });

  if (response.status === 401) {
    setAuthToken(null);
    return null;
  }

  if (!response.ok) {
    throw new Error(`${response.status}: ${response.statusText}`);
  }

  const data = await response.json();
  return data.user ?? data;
}

async function logout(): Promise<void> {
  const token = getAuthToken();
  const headers: HeadersInit = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  await fetch("/api/auth/logout", {
    method: "POST",
    credentials: "include",
    headers,
  }).catch(() => {});
  setAuthToken(null);
  window.location.href = "/login";
}

export function useAuth() {
  const queryClient = useQueryClient();
  const { data: user, isLoading } = useQuery<AuthUser | null>({
    queryKey: ["/api/auth/user"],
    queryFn: fetchUser,
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.setQueryData(["/api/auth/user"], null);
    },
  });

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    logout: logoutMutation.mutate,
    isLoggingOut: logoutMutation.isPending,
  };
}
