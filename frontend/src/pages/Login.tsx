import React, { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export const Login: React.FC = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, handleOAuthCallback } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const accessToken = searchParams.get("access_token");
  const refreshToken = searchParams.get("refresh_token");

  React.useEffect(() => {
    if (accessToken && refreshToken) {
      handleOAuthCallback(accessToken, refreshToken);
      navigate("/", { replace: true });
    }
  }, [accessToken, refreshToken, handleOAuthCallback, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const success = await login(username, password);
      if (success) {
        navigate("/");
      } else {
        setError("Invalid username or password");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleOidcLogin = () => {
    window.location.href = "/api/auth/oidc/login";
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "var(--spacing-lg)" }}>
      <div className="card" style={{ width: "100%", maxWidth: "400px", padding: "var(--spacing-xl)" }}>
        <div style={{ textAlign: "center", marginBottom: "var(--spacing-xl)" }}>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--color-primary)", marginBottom: "var(--spacing-xs)" }}>
            VoiceStudio
          </h1>
          <p style={{ color: "var(--color-text-secondary)" }}>Sign in to your account</p>
        </div>

        {error && (
          <div className="toast toast-error" style={{ position: "static", marginBottom: "var(--spacing-lg)" }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group" style={{ marginBottom: "var(--spacing-md)" }}>
            <label className="form-label" htmlFor="username">Username or Email</label>
            <input
              id="username"
              type="text"
              className="form-input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              required
              disabled={loading}
              autoComplete="username"
            />
          </div>

          <div className="form-group" style={{ marginBottom: "var(--spacing-md)" }}>
            <label className="form-label" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              disabled={loading}
              autoComplete="current-password"
            />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: "100%" }} disabled={loading}>
            {loading ? (
              <>
                <span className="loading-spinner" style={{ width: "16px", height: "16px" }} />
                Signing in...
              </>
            ) : (
              "Sign In"
            )}
          </button>
        </form>

        <div style={{ marginTop: "var(--spacing-lg)", paddingTop: "var(--spacing-lg)", borderTop: "1px solid var(--color-border)" }}>
          <button type="button" className="btn btn-secondary" style={{ width: "100%" }} onClick={handleOidcLogin}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style={{ marginRight: "8px" }}>
              <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.6 0 12 0zm5.5 17H6.5V15h11v2zm0-4H6.5v-2h11v2zm0-4H6.5V9h11v2z" />
            </svg>
            Sign in with Keycloak (OIDC)
          </button>
        </div>

        <div style={{ marginTop: "var(--spacing-md)", fontSize: "0.875rem", color: "var(--color-text-muted)", textAlign: "center" }}>
          <p>Demo credentials: <code>dev</code> / <code>dev</code></p>
        </div>
      </div>
    </div>
  );
};