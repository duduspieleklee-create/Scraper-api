import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { adminFetch } from "@/lib/adminApiClient";
import { AdminCredentials, AdminToken, AdminUser } from "@workspace/api-client-react";
import { useLocation } from "wouter";
import { useToast } from "@/hooks/use-toast";

export function useAdminLogin() {
  const { toast } = useToast();
  const [, setLocation] = useLocation();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (credentials: AdminCredentials) => 
      adminFetch<AdminToken>("/admin/login", {
        method: "POST",
        body: JSON.stringify(credentials),
      }),
    onSuccess: (data) => {
      localStorage.setItem("admin_token", data.token);
      queryClient.setQueryData(["adminMe"], { username: data.username });
      setLocation("/admin");
    },
    onError: (error: Error) => {
      toast({
        title: "Login Failed",
        description: error.message,
        variant: "destructive",
      });
    }
  });
}

export function useAdminMe() {
  return useQuery({
    queryKey: ["adminMe"],
    queryFn: () => adminFetch<AdminUser>("/admin/me"),
    retry: false,
  });
}
