import React, { useState, useEffect } from "react";
import { useSynthesis, useVoices } from "../hooks/useSynthesis";
import { VoiceSelector } from "../components/VoiceSelector";
import { AudioPlayer } from "../components/AudioPlayer";

export const Dashboard: React.FC = () => {
  const { voices, loading: voicesLoading, fetchVoices } = useVoices();
  const {
    createSynthesis,
    fetchJobs,
    pollJob,
    downloadAudio,
    jobs,
    error,
    currentJob,
    setCurrentJob,
  } = useSynthesis();

  const [text, setText] = useState("");
  const [selectedVoiceId, setSelectedVoiceId] = useState<number | null>(null);
  const [speed, setSpeed] = useState(100);
  const [pitch, setPitch] = useState(0);
  const [synthesizing, setSynthesizing] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" | "info" } | null>(null);

  useEffect(() => {
    fetchVoices({ is_active: true });
    fetchJobs({ page_size: 10 });
  }, [fetchVoices, fetchJobs]);

  const showToast = (message: string, type: "success" | "error" | "info" = "info") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() || !selectedVoiceId) {
      showToast("Please enter text and select a voice", "error");
      return;
    }

    setSynthesizing(true);
    setAudioUrl(null);
    try {
      const job = await createSynthesis({
        text,
        voice_id: selectedVoiceId,
        speed,
        pitch,
      });
      showToast("Synthesis started...", "info");
      const completedJob = await pollJob(job.id);
      if (completedJob.status === "completed") {
        const blob = await downloadAudio(completedJob.id);
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        setCurrentJob(completedJob);
        showToast("Synthesis completed!", "success");
      } else {
        showToast(`Synthesis failed: ${completedJob.error_message || "Unknown error"}`, "error");
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Synthesis failed";
      showToast(message, "error");
    } finally {
      setSynthesizing(false);
    }
  };

  const handleJobClick = async (job: typeof jobs[0]) => {
    setCurrentJob(job);
    if (job.status === "completed" && job.output_path) {
      try {
        const blob = await downloadAudio(job.id);
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
      } catch {
        showToast("Failed to load audio", "error");
      }
    }
  };

  const selectedVoice = voices.find((v) => v.id === selectedVoiceId);

  return (
    <div>
      <div style={{ marginBottom: "var(--spacing-xl)" }}>
        <h1 style={{ fontSize: "1.875rem", fontWeight: 700, marginBottom: "var(--spacing-xs)" }}>
          Text to Speech
        </h1>
        <p style={{ color: "var(--color-text-secondary)" }}>
          Enter text and select a voice to generate speech audio.
        </p>
      </div>

      <div style={{ display: "grid", gap: "var(--spacing-lg)", gridTemplateColumns: "1fr" }}>
        <section className="card" style={{ padding: "var(--spacing-lg)" }}>
          <h2 style={{ fontSize: "1.125rem", fontWeight: 600, marginBottom: "var(--spacing-lg)" }}>
            Generate Speech
          </h2>
          <form onSubmit={handleSubmit}>
            <div className="form-group" style={{ marginBottom: "var(--spacing-md)" }}>
              <label className="form-label" htmlFor="text-input">
                Text to Synthesize
              </label>
              <textarea
                id="text-input"
                className="form-textarea"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Enter text to convert to speech (max 5000 characters)..."
                rows={6}
                maxLength={5000}
                disabled={synthesizing}
              />
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--color-text-muted)" }}>
                <span>{text.length} / 5000 characters</span>
                <span>{text.trim().split(/\s+/).filter(Boolean).length} words</span>
              </div>
            </div>

            <div style={{ display: "grid", gap: "var(--spacing-md)", gridTemplateColumns: "1fr" }}>
              <div className="form-group">
                <label className="form-label" htmlFor="voice-select">
                  Voice
                </label>
                <VoiceSelector
                  voices={voices}
                  selectedVoiceId={selectedVoiceId}
                  onSelect={setSelectedVoiceId}
                  loading={voicesLoading}
                  disabled={synthesizing}
                />
                {selectedVoice && (
                  <div style={{ marginTop: "var(--spacing-xs)", display: "flex", gap: "var(--spacing-sm)", flexWrap: "wrap" }}>
                    <span className="badge badge-neutral">{selectedVoice.language.toUpperCase()}</span>
                    <span className="badge badge-neutral">{selectedVoice.sample_rate} Hz</span>
                  </div>
                )}
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="speed">
                  Speed: {speed}%
                </label>
                <input
                  id="speed"
                  type="range"
                  min="50"
                  max="200"
                  value={speed}
                  onChange={(e) => setSpeed(Number(e.target.value))}
                  disabled={synthesizing}
                  style={{ width: "100%" }}
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="pitch">
                  Pitch: {pitch >= 0 ? "+" : ""}{pitch} semitones
                </label>
                <input
                  id="pitch"
                  type="range"
                  min="-12"
                  max="12"
                  value={pitch}
                  onChange={(e) => setPitch(Number(e.target.value))}
                  disabled={synthesizing}
                  style={{ width: "100%" }}
                />
              </div>
            </div>

            <div style={{ marginTop: "var(--spacing-lg)", display: "flex", gap: "var(--spacing-md)" }}>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={synthesizing || !text.trim() || !selectedVoiceId}
                style={{ flex: 1 }}
              >
                {synthesizing ? (
                  <>
                    <span className="loading-spinner" style={{ width: "16px", height: "16px" }} />
                    Generating...
                  </>
                ) : (
                  "Generate Speech"
                )}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setText("")}
                disabled={synthesizing}
              >
                Clear
              </button>
            </div>
          </form>
        </section>

        {audioUrl && currentJob && (
          <section className="card" style={{ padding: "var(--spacing-lg)" }}>
            <h2 style={{ fontSize: "1.125rem", fontWeight: 600, marginBottom: "var(--spacing-lg)" }}>
              Generated Audio
            </h2>
            <div style={{ marginBottom: "var(--spacing-md)" }}>
              <AudioPlayer src={audioUrl} />
            </div>
            <div style={{ display: "flex", gap: "var(--spacing-md)", flexWrap: "wrap" }}>
              <a
                href={audioUrl}
                download={`speech-${currentJob.id}.wav`}
                className="btn btn-secondary"
              >
                Download WAV
              </a>
              <span style={{ alignSelf: "center", fontSize: "0.875rem", color: "var(--color-text-secondary)" }}>
                Duration: ~{currentJob.duration_seconds}s
              </span>
            </div>
          </section>
        )}

        <section className="card" style={{ padding: "var(--spacing-lg)" }}>
          <h2 style={{ fontSize: "1.125rem", fontWeight: 600, marginBottom: "var(--spacing-lg)" }}>
            Recent Synthesis Jobs
          </h2>
          {error && (
            <div className="toast toast-error" style={{ position: "static", marginBottom: "var(--spacing-md)" }}>
              {error}
            </div>
          )}
          {jobs.length === 0 ? (
            <p style={{ color: "var(--color-text-muted)", textAlign: "center", padding: "var(--spacing-xl)" }}>
              No synthesis jobs yet. Generate your first speech above!
            </p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--color-border)" }}>
                    <th style={{ textAlign: "left", padding: "var(--spacing-sm)", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)" }}>Text</th>
                    <th style={{ textAlign: "left", padding: "var(--spacing-sm)", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)" }}>Voice</th>
                    <th style={{ textAlign: "left", padding: "var(--spacing-sm)", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)" }}>Status</th>
                    <th style={{ textAlign: "left", padding: "var(--spacing-sm)", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)" }}>Created</th>
                    <th style={{ textAlign: "left", padding: "var(--spacing-sm)", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)" }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.slice(0, 10).map((job) => (
                    <tr
                      key={job.id}
                      style={{
                        borderBottom: "1px solid var(--color-border)",
                        cursor: "pointer",
                        background: currentJob?.id === job.id ? "var(--color-primary-light)" : "transparent",
                      }}
                      onClick={() => handleJobClick(job)}
                    >
                      <td style={{ padding: "var(--spacing-sm)", fontSize: "0.875rem", maxWidth: "300px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {job.text.length > 80 ? job.text.slice(0, 80) + "..." : job.text}
                      </td>
                      <td style={{ padding: "var(--spacing-sm)", fontSize: "0.875rem" }}>
                        {job.voice?.name || `Voice #${job.voice_id}`}
                      </td>
                      <td style={{ padding: "var(--spacing-sm)" }}>
                        <span
                          className={`badge ${
                            job.status === "completed" ? "badge-success" :
                            job.status === "processing" ? "badge-warning" :
                            job.status === "failed" ? "badge-error" :
                            "badge-neutral"
                          }`}
                        >
                          {job.status}
                        </span>
                      </td>
                      <td style={{ padding: "var(--spacing-sm)", fontSize: "0.875rem", color: "var(--color-text-secondary)" }}>
                        {new Date(job.created_at).toLocaleString()}
                      </td>
                      <td style={{ padding: "var(--spacing-sm)" }}>
                        {job.status === "completed" && (
                          <button
                            className="btn btn-ghost"
                            onClick={(e) => { e.stopPropagation(); handleJobClick(job); }}
                            style={{ fontSize: "0.75rem", padding: "2px 8px" }}
                          >
                            Play
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>

      {toast && (
        <div className={`toast toast-${toast.type}`} role="alert">
          {toast.message}
        </div>
      )}
    </div>
  );
};