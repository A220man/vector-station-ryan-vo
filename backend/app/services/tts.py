import io
import os
import uuid
import wave
import struct
import math
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.exceptions import SynthesisError, NotFoundError

# Audio processing
import numpy as np
from pydub import AudioSegment


settings = get_settings()


class TTSService:
    def __init__(self):
        self.output_dir = Path(settings.upload_dir) / "synthesis"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sample_rate = settings.audio_sample_rate

    @property
    def output_format(self) -> str:
        """Get current output format from settings."""
        return get_settings().audio_output_format.lower()

    @property
    def _audio_extension(self) -> str:
        """Get file extension for current output format."""
        return "mp3" if self.output_format == "mp3" else "wav"

    def generate_tone_waveform(
        self,
        duration_seconds: float,
        frequency: float = 440.0,
        sample_rate: int = 22050,
        amplitude: float = 0.3,
    ) -> np.ndarray:
        """Generate a simple sine wave as placeholder audio. Returns numpy array of samples."""
        num_samples = int(duration_seconds * sample_rate)
        t = np.linspace(0, duration_seconds, num_samples, endpoint=False)
        # Simple ADSR envelope to avoid clicks
        attack = np.minimum(1.0, t / 0.01)
        release = np.where(
            t > duration_seconds - 0.05,
            np.maximum(0.0, 1.0 - (t - (duration_seconds - 0.05)) / 0.05),
            1.0
        )
        envelope = attack * release
        samples = amplitude * envelope * np.sin(2 * np.pi * frequency * t)
        # Clamp and convert to 16-bit PCM
        samples = np.clip(samples, -1.0, 1.0)
        return (samples * 32767).astype(np.int16)

    def _samples_to_wav_bytes(self, samples: np.ndarray, sample_rate: int) -> bytes:
        """Convert numpy samples to WAV bytes."""
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(samples.tobytes())
        return wav_buffer.getvalue()

    def _samples_to_mp3_bytes(self, samples: np.ndarray, sample_rate: int) -> bytes:
        """Convert numpy samples to MP3 bytes using pydub."""
        # Create AudioSegment from samples
        audio_segment = AudioSegment(
            samples.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,  # 16-bit
            channels=1,
        )
        # Export to MP3
        mp3_buffer = io.BytesIO()
        audio_segment.export(mp3_buffer, format="mp3", bitrate="128k")
        return mp3_buffer.getvalue()

    def _samples_to_audio_bytes(self, samples: np.ndarray, sample_rate: int) -> bytes:
        """Convert samples to audio bytes in configured output format."""
        if self.output_format == "mp3":
            return self._samples_to_mp3_bytes(samples, sample_rate)
        return self._samples_to_wav_bytes(samples, sample_rate)

    def _get_audio_extension(self) -> str:
        """Get file extension for current output format."""
        return self._audio_extension

    def text_to_speech_duration(self, text: str, speed: float = 1.0) -> float:
        """Estimate speech duration based on text length and speed."""
        # Rough estimate: ~150 words per minute at normal speed
        words = len(text.split())
        base_duration = (words / 150.0) * 60.0
        return base_duration / speed

    async def synthesize(
        self,
        text: str,
        voice_id: int,
        speed: int = 100,
        pitch: int = 0,
    ) -> tuple[bytes, float]:
        """
        Synthesize speech from text.
        Returns (audio_data, duration_seconds).
        """
        if not text.strip():
            raise SynthesisError("Text cannot be empty")
        if len(text) > settings.max_text_length:
            raise SynthesisError(f"Text exceeds maximum length of {settings.max_text_length} characters")

        # For now, generate a tone based on voice_id and pitch
        # In production, this would call a real TTS model
        duration = self.text_to_speech_duration(text, speed / 100.0)
        
        # Base frequency modified by pitch (semitones)
        base_freq = 220.0 + (voice_id % 5) * 55.0  # Different base per voice
        frequency = base_freq * (2 ** (pitch / 12.0))
        
        samples = self.generate_tone_waveform(
            duration_seconds=duration,
            frequency=frequency,
            sample_rate=self.sample_rate,
        )
        
        audio_data = self._samples_to_audio_bytes(samples, self.sample_rate)
        
        return audio_data, duration

    def save_audio(self, audio_data: bytes, job_id: int) -> str:
        """Save audio data to file and return path."""
        ext = self._get_audio_extension()
        filename = f"synthesis_{job_id}_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = self.output_dir / filename
        with open(filepath, "wb") as f:
            f.write(audio_data)
        return str(filepath)

    def get_audio_path(self, job_id: int) -> Optional[Path]:
        """Find audio file for a job."""
        ext = self._get_audio_extension()
        for f in self.output_dir.glob(f"synthesis_{job_id}_*.{ext}"):
            return f  # type: ignore[no-any-return]
        return None


tts_service = TTSService()
