const BASE = "/api";

function getToken() { 
  return localStorage.getItem("admin_token"); 
}

export async function adminFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
      ...init?.headers,
    },
  });
  
  if (!res.ok) {
    if (res.status === 401) {
      localStorage.removeItem("admin_token");
      if (window.location.pathname !== "/admin/login") {
        window.location.href = "/admin/login";
      }
    }
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error ?? res.statusText);
  }
  
  if (res.status === 204) return undefined as T;
  return res.json();
}