import React from "react";

interface AudioPlayerProps {
  src: string;
  onEnded?: () => void;
  onError?: (error: React.SyntheticEvent<HTMLAudioElement>) => void;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({ src, onEnded, onError }) => {
  const [playing, setPlaying] = React.useState(false);
  const [progress, setProgress] = React.useState(0);
  const [duration, setDuration] = React.useState(0);
  const audioRef = React.useRef<HTMLAudioElement>(null);

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setProgress(audioRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };

  const handlePlayPause = () => {
    if (audioRef.current) {
      if (playing) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setPlaying(!playing);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      setProgress(time);
    }
  };

  const handleEnded = () => {
    setPlaying(false);
    setProgress(0);
    onEnded?.();
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="audio-player" style={{ width: "100%", maxWidth: "500px" }}>
      <audio
        ref={audioRef}
        src={src}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={handleEnded}
        onError={onError}
        preload="metadata"
      />
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <button
          className="btn btn-primary"
          onClick={handlePlayPause}
          aria-label={playing ? "Pause" : "Play"}
          style={{ width: "40px", height: "40px", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center" }}
        >
          {playing ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style={{ marginLeft: "2px" }}>
              <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style={{ marginLeft: "4px" }}>
              <path d="M8 5v14l11-7z" />
            </svg>
          )}
        </button>
        <div style={{ flex: 1, display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--color-text-secondary)", minWidth: "45px" }}>
            {formatTime(progress)}
          </span>
          <input
            type="range"
            min={0}
            max={duration || 100}
            value={progress}
            onChange={handleSeek}
            style={{ flex: 1, height: "4px", accentColor: "var(--color-primary)" }}
            aria-label="Playback progress"
          />
          <span style={{ fontSize: "0.75rem", color: "var(--color-text-secondary)", minWidth: "45px", textAlign: "right" }}>
            {formatTime(duration)}
          </span>
        </div>
      </div>
    </div>
  );
};