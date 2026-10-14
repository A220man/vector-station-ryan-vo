import React, { useState, useEffect } from "react";
import { useVoices } from "../hooks/useSynthesis";
import { api } from "../api/client";
import type { Voice, VoiceCreate } from "../types/api";

export const Voices: React.FC = () => {
  const { voices, loading, fetchVoices } = useVoices();
  const [showModal, setShowModal] = useState(false);
  const [editingVoice, setEditingVoice] = useState<Voice | null>(null);
  const [formData, setFormData] = useState<VoiceCreate>({
    name: "",
    description: "",
    language: "en",
    sample_rate: 22050,
    voice_type: "cloned",
    reference_audio_path: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  useEffect(() => {
    fetchVoices({ is_active: true });
  }, [fetchVoices]);

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      language: "en",
      sample_rate: 22050,
      voice_type: "cloned",
      reference_audio_path: "",
    });
    setEditingVoice(null);
  };

  const openCreateModal = () => {
    resetForm();
    setShowModal(true);
  };

  const openEditModal = (voice: Voice) => {
    setEditingVoice(voice);
    setFormData({
      name: voice.name,
      description: voice.description || "",
      language: voice.language,
      sample_rate: voice.sample_rate,
      voice_type: voice.voice_type,
      reference_audio_path: voice.reference_audio_path || "",
      design_params: voice.design_params || "",
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      showToast("Name is required", "error");
      return;
    }
    if (formData.voice_type === "cloned" && !formData.reference_audio_path) {
      showToast("Reference audio path is required for cloned voices", "error");
      return;
    }
    if (formData.voice_type === "designed" && !formData.design_params) {
      showToast("Design parameters are required for designed voices", "error");
      return;
    }

    setSubmitting(true);
    try {
      if (editingVoice) {
        await api.updateVoice(editingVoice.id, formData);
        showToast("Voice updated successfully");
      } else {
        await api.createVoice(formData);
        showToast("Voice created successfully");
      }
      setShowModal(false);
      resetForm();
      fetchVoices({ is_active: true });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Operation failed";
      showToast(message, "error");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (voice: Voice) => {
    if (!window.confirm(`Delete voice "${voice.name}"? This cannot be undone.`)) return;
    try {
      await api.deleteVoice(voice.id);
      showToast("Voice deleted");
      fetchVoices({ is_active: true });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Delete failed";
      showToast(message, "error");
    }
  };

  const getTypeBadge = (type: string) => {
    const badges: Record<string, string> = {
      builtin: "badge-info",
      cloned: "badge-success",
      designed: "badge-warning",
    };
    return badges[type] || "badge-neutral";
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--spacing-lg)", flexWrap: "wrap", gap: "var(--spacing-md)" }}>
        <div>
          <h1 style={{ fontSize: "1.875rem", fontWeight: 700, marginBottom: "var(--spacing-xs)" }}>
            Voices
          </h1>
          <p style={{ color: "var(--color-text-secondary)" }}>
            Manage available voices for synthesis
          </p>
        </div>
        <button className="btn btn-primary" onClick={openCreateModal}>
          Add Voice
        </button>
      </div>

      {loading ? (
        <div className="card" style={{ padding: "var(--spacing-xl)", textAlign: "center" }}>
          <div className="loading-spinner" style={{ margin: "0 auto var(--spacing-md)" }} />
          <p>Loading voices...</p>
        </div>
      ) : voices.length === 0 ? (
        <div className="card" style={{ padding: "var(--spacing-xl)", textAlign: "center" }}>
          <p style={{ color: "var(--color-text-muted)", marginBottom: "var(--spacing-md)" }}>
            No voices available yet.
          </p>
          <button className="btn btn-primary" onClick={openCreateModal}>
            Create Your First Voice
          </button>
        </div>
      ) : (
        <div className="card" style={{ overflow: "hidden" }}>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--color-border)" }}>
                  <th style={{ textAlign: "left", padding: "var(--spacing-md)", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)" }}>Name</th>
                  <th style={{ textAlign: "left", padding: "var(--spacing-md)", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)" }}>Type</th>
                  <th style={{ textAlign: "left", padding: "var(--spacing-md)", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)" }}>Language</th>
                  <th style={{ textAlign: "left", padding: "var(--spacing-md)", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)" }}>Sample Rate</th>
                  <th style={{ textAlign: "left", padding: "var(--spacing-md)", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)" }}>Status</th>
                  <th style={{ textAlign: "left", padding: "var(--spacing-md)", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {voices.map((voice) => (
                  <tr key={voice.id} style={{ borderBottom: "1px solid var(--color-border)" }}>
                    <td style={{ padding: "var(--spacing-md)" }}>
                      <div style={{ fontWeight: 500 }}>{voice.name}</div>
                      {voice.description && (
                        <div style={{ fontSize: "0.875rem", color: "var(--color-text-secondary)", marginTop: "2px" }}>
                          {voice.description}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: "var(--spacing-md)" }}>
                      <span className={`badge ${getTypeBadge(voice.voice_type)}`}>
                        {voice.voice_type}
                      </span>
                    </td>
                    <td style={{ padding: "var(--spacing-md)", fontSize: "0.875rem" }}>
                      {voice.language.toUpperCase()}
                    </td>
                    <td style={{ padding: "var(--spacing-md)", fontSize: "0.875rem" }}>
                      {voice.sample_rate} Hz
                    </td>
                    <td style={{ padding: "var(--spacing-md)" }}>
                      <span className={voice.is_active ? "badge badge-success" : "badge badge-neutral"}>
                        {voice.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td style={{ padding: "var(--spacing-md)", display: "flex", gap: "var(--spacing-sm)" }}>
                      {voice.voice_type !== "builtin" && (
                        <>
                          <button
                            className="btn btn-ghost"
                            onClick={() => openEditModal(voice)}
                            style={{ fontSize: "0.75rem", padding: "4px 8px" }}
                          >
                            Edit
                          </button>
                          <button
                            className="btn btn-ghost"
                            onClick={() => handleDelete(voice)}
                            style={{ fontSize: "0.75rem", padding: "4px 8px", color: "var(--color-error)" }}
                          >
                            Delete
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showModal && (
        <div
          className="card"
          style={{
            position: "fixed",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: "90%",
            maxWidth: "500px",
            maxHeight: "90vh",
            overflow: "auto",
            zIndex: 1000,
            boxShadow: "var(--shadow-lg)",
          }}
        >
          <div style={{ padding: "var(--spacing-lg)", borderBottom: "1px solid var(--color-border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 style={{ fontSize: "1.125rem", fontWeight: 600 }}>
              {editingVoice ? "Edit Voice" : "Create Voice"}
            </h2>
            <button className="btn btn-ghost" onClick={() => setShowModal(false)}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
          <form onSubmit={handleSubmit} style={{ padding: "var(--spacing-lg)" }}>
            <div className="form-group" style={{ marginBottom: "var(--spacing-md)" }}>
              <label className="form-label" htmlFor="voice-name">Name *</label>
              <input
                id="voice-name"
                type="text"
                className="form-input"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>

            <div className="form-group" style={{ marginBottom: "var(--spacing-md)" }}>
              <label className="form-label" htmlFor="voice-description">Description</label>
              <textarea
                id="voice-description"
                className="form-textarea"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
              />
            </div>

            <div style={{ display: "grid", gap: "var(--spacing-md)", gridTemplateColumns: "1fr 1fr" }}>
              <div className="form-group">
                <label className="form-label" htmlFor="voice-type">Voice Type *</label>
                <select
                  id="voice-type"
                  className="form-select"
                  value={formData.voice_type}
                  onChange={(e) => setFormData({ ...formData, voice_type: e.target.value as VoiceCreate["voice_type"] })}
                >
                  <option value="builtin">Built-in</option>
                  <option value="cloned">Cloned</option>
                  <option value="designed">Designed</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="voice-language">Language</label>
                <input
                  id="voice-language"
                  type="text"
                  className="form-input"
                  value={formData.language}
                  onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                  maxLength={10}
                />
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: "var(--spacing-md)" }}>
              <label className="form-label" htmlFor="voice-sample-rate">Sample Rate</label>
              <input
                id="voice-sample-rate"
                type="number"
                className="form-input"
                value={formData.sample_rate}
                onChange={(e) => setFormData({ ...formData, sample_rate: Number(e.target.value) })}
                min={8000}
                max={48000}
              />
            </div>

            {formData.voice_type === "cloned" && (
              <div className="form-group" style={{ marginBottom: "var(--spacing-md)" }}>
                <label className="form-label" htmlFor="voice-reference">Reference Audio Path *</label>
                <input
                  id="voice-reference"
                  type="text"
                  className="form-input"
                  value={formData.reference_audio_path}
                  onChange={(e) => setFormData({ ...formData, reference_audio_path: e.target.value })}
                  placeholder="/path/to/reference.wav"
                />
              </div>
            )}

            {formData.voice_type === "designed" && (
              <div className="form-group" style={{ marginBottom: "var(--spacing-md)" }}>
                <label className="form-label" htmlFor="voice-design">Design Parameters (JSON) *</label>
                <textarea
                  id="voice-design"
                  className="form-textarea"
                  value={formData.design_params || ""}
                  onChange={(e) => setFormData({ ...formData, design_params: e.target.value })}
                  rows={4}
                  placeholder='{"pitch": 0, "timbre": "neutral", ...}'
                />
              </div>
            )}

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "var(--spacing-md)", marginTop: "var(--spacing-lg)" }}>
              <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? "Saving..." : editingVoice ? "Update" : "Create"}
              </button>
            </div>
          </form>
        </div>
      )}

      {showModal && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.5)",
            zIndex: 999,
          }}
          onClick={() => setShowModal(false)}
        />
      )}

      {toast && (
        <div className={`toast toast-${toast.type}`} role="alert">
          {toast.message}
        </div>
      )}
    </div>
  );
};