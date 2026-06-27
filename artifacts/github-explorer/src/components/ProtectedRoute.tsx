import { useEffect } from "react";
import { useLocation } from "wouter";
import { getAuthToken } from "@/lib/apiClient";
import { useAuth } from "@/hooks/useAuth";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const [, setLocation] = useLocation();
  const token = getAuthToken();
  const { isError } = useAuth();

  useEffect(() => {
    if (!token || isError) {
      setLocation("/login");
    }
  }, [token, isError, setLocation]);

  if (!token) return null;

  return <>{children}</>;
}
