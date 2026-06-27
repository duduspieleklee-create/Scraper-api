import { useEffect } from "react";
import { useLocation } from "wouter";
import { useAdminMe } from "@/hooks/useAdmin";

export function AdminProtectedRoute({ children }: { children: React.ReactNode }) {
  const [, setLocation] = useLocation();
  const token = localStorage.getItem("admin_token");
  const { isError, isLoading } = useAdminMe();

  useEffect(() => {
    if (!token || isError) {
      setLocation("/admin/login");
    }
  }, [token, isError, setLocation]);

  if (!token || isLoading) return null;

  return <>{children}</>;
}