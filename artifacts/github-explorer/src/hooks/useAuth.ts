import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch, getAuthToken } from "@/lib/apiClient";
import { useLocation } from "wouter";

export function useAuth() {
  const [, setLocation] = useLocation();
  const queryClient = useQueryClient();

  const userQuery = useQuery({
    queryKey: ["user"],
    queryFn: () => apiFetch("/auth/me"),
    enabled: !!getAuthToken(),
    retry: false,
  });

  const loginMutation = useMutation({
    mutationFn: (credentials: any) =>
      apiFetch("/auth/login", {
        method: "POST",
        body: JSON.stringify(credentials),
      }),
    onSuccess: (data) => {
      localStorage.setItem("auth_token", data.access_token);
      queryClient.invalidateQueries({ queryKey: ["user"] });
      setLocation("/dashboard");
    },
  });

  const logout = () => {
    localStorage.removeItem("auth_token");
    queryClient.clear();
    setLocation("/login");
  };

  return {
    user: userQuery.data,
    isLoading: userQuery.isLoading,
    isError: userQuery.isError,
    login: loginMutation.mutate,
    isLoggingIn: loginMutation.isPending,
    logout,
  };
}
