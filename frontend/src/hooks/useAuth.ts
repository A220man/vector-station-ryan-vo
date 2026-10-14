import { useState, useEffect, useCallback } from "react";
import { api } from "../api/client";
import type { User } from "../types/api";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUser = useCallback(async () => {
    if (!api.isAuthenticated()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const userData = await api.getMe();
      setUser(userData);
      setError(null);
    } catch (err) {
      setError("Failed to fetch user");
      setUser(null);
      api.clearTokens();
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = async (username: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      await api.login({ username, password });
      await fetchUser();
      return true;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Login failed";
      setError(message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    await api.logout();
    setUser(null);
  };

  const handleOAuthCallback = async (accessToken: string, refreshToken: string) => {
    api.setTokens(accessToken, refreshToken);
    await fetchUser();
  };

  return {
    user,
    loading,
    error,
    login,
    logout,
    handleOAuthCallback,
    isAuthenticated: !!user,
    refetch: fetchUser,
  };
}