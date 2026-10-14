import React from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export const Layout: React.FC = () => {
  const { user, logout, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const navItems = [
    { path: "/", label: "Dashboard" },
    { path: "/voices", label: "Voices" },
  ];

  if (authLoading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
        <div className="loading-spinner" />
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <header
        style={{
          background: "var(--color-surface)",
          borderBottom: "1px solid var(--color-border)",
          padding: "0 var(--spacing-md)",
          position: "sticky",
          top: 0,
          zIndex: 100,
        }}
      >
        <div className="container" style={{ height: "64px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <NavLink to="/" style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--color-primary)" }}>
            VoiceStudio
          </NavLink>
          <nav style={{ display: "flex", alignItems: "center", gap: "var(--spacing-md)" }}>
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                style={({ isActive }) => ({
                  padding: "var(--spacing-xs) var(--spacing-sm)",
                  borderRadius: "var(--radius-md)",
                  fontWeight: 500,
                  color: isActive ? "var(--color-primary)" : "var(--color-text-secondary)",
                  background: isActive ? "var(--color-primary-light)" : "transparent",
                })}
              >
                {item.label}
              </NavLink>
            ))}
            {user && (
              <div style={{ display: "flex", alignItems: "center", gap: "var(--spacing-md)" }}>
                <span style={{ fontSize: "0.875rem", color: "var(--color-text-secondary)" }}>
                  {user.full_name || user.username || user.email}
                </span>
                <span className={`badge ${user.role === "admin" ? "badge-info" : user.role === "operator" ? "badge-success" : "badge-neutral"}`}>
                  {user.role}
                </span>
                <button className="btn btn-ghost" onClick={handleLogout}>
                  Logout
                </button>
              </div>
            )}
          </nav>
        </div>
      </header>
      <main style={{ flex: 1, padding: "var(--spacing-lg) 0" }}>
        <div className="container">
          <Outlet />
        </div>
      </main>
      <footer
        style={{
          background: "var(--color-surface)",
          borderTop: "1px solid var(--color-border)",
          padding: "var(--spacing-md) 0",
          marginTop: "auto",
        }}
      >
        <div className="container" style={{ textAlign: "center", color: "var(--color-text-muted)", fontSize: "0.875rem" }}>
          VoiceStudio - Open-source AI Voice Synthesis
        </div>
      </footer>
    </div>
  );
};