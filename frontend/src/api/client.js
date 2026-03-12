const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8001";

export async function apiFetch(path, options = {}) {
  const token = localStorage.getItem("access_token")
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  }
  const res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  if (res.status === 401) {
    localStorage.removeItem("access_token")
    window.location.href = "/login"
    return
  }
  return res
}
