import { useState, useCallback, useEffect } from "react";

const BASE = process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1";
const TOKEN_KEY = "fx_token";

export interface User {
  id: number;
  email: string;
  display_name: string;
  alert_pairs: string[];
  alert_min_score: number;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = localStorage.getItem(TOKEN_KEY);
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) { setLoading(false); return; }
    apiFetch<User>("/auth/me")
      .then(setUser)
      .catch(() => localStorage.removeItem(TOKEN_KEY))
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await apiFetch<{ access_token: string; user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    localStorage.setItem(TOKEN_KEY, res.access_token);
    setUser(res.user);
    return res.user;
  }, []);

  const register = useCallback(async (email: string, password: string, displayName: string) => {
    const res = await apiFetch<{ access_token: string; user: User }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, display_name: displayName }),
    });
    localStorage.setItem(TOKEN_KEY, res.access_token);
    setUser(res.user);
    return res.user;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  }, []);

  const updateAlerts = useCallback(async (pairs: string[], minScore: number) => {
    const updated = await apiFetch<User>("/auth/alerts", {
      method: "PUT",
      body: JSON.stringify({ pairs, min_score: minScore }),
    });
    setUser(updated);
  }, []);

  return { user, loading, login, register, logout, updateAlerts };
}
