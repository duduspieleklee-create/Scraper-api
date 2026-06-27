export function getApiBaseUrl() {
  return localStorage.getItem("SCRAPER_API_URL") || "http://localhost:8000";
}

export function getAuthToken() {
  return localStorage.getItem("auth_token");
}

export async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const baseUrl = getApiBaseUrl();
  const token = getAuthToken();

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${baseUrl}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.message || errorBody.detail || "API request failed");
  }

  return response.json();
}
