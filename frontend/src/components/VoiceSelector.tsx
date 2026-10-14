import React from "react";
import type { Voice } from "../types/api";

interface VoiceSelectorProps {
  voices: Voice[];
  selectedVoiceId: number | null;
  onSelect: (voiceId: number) => void;
  loading?: boolean;
  disabled?: boolean;
}

export const VoiceSelector: React.FC<VoiceSelectorProps> = ({
  voices,
  selectedVoiceId,
  onSelect,
  loading = false,
  disabled = false,
}) => {
  const activeVoices = voices.filter((v) => v.is_active);

  if (loading) {
    return (
      <select className="form-select" disabled id="voice-select">
        <option value="">Loading voices...</option>
      </select>
    );
  }

  if (activeVoices.length === 0) {
    return (
      <select className="form-select" disabled id="voice-select">
        <option value="">No voices available</option>
      </select>
    );
  }

  return (
    <select
      className="form-select"
      id="voice-select"
      value={selectedVoiceId || ""}
      onChange={(e) => onSelect(Number(e.target.value))}
      disabled={disabled || activeVoices.length === 0}
    >
      <option value="">Select a voice...</option>
      {activeVoices.map((voice) => (
        <option key={voice.id} value={voice.id}>
          {voice.name} {voice.voice_type !== "builtin" && `(${voice.voice_type})`}
        </option>
      ))}
    </select>
  );
};

interface VoiceBadgeProps {
  voice: Voice;
}

export const VoiceBadge: React.FC<VoiceBadgeProps> = ({ voice }) => {
  const getBadgeClass = (type: string) => {
    switch (type) {
      case "builtin":
        return "badge-info";
      case "cloned":
        return "badge-success";
      case "designed":
        return "badge-warning";
      default:
        return "badge-neutral";
    }
  };

  return (
    <span className={`badge ${getBadgeClass(voice.voice_type)}`}>
      {voice.voice_type}
    </span>
  );
};