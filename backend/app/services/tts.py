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


settings = get_settings()


class TTSService:
    def __init__(self):
        self.output_dir = Path(settings.upload_dir) / "synthesis"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sample_rate = settings.audio_sample_rate

    def generate_tone_waveform(
        self,
        duration_seconds: float,
        frequency: float = 440.0,
        sample_rate: int = 22050,
        amplitude: float = 0.3,
    ) -> bytes:
        """Generate a simple sine wave as placeholder audio."""
        num_samples = int(duration_seconds * sample_rate)
        samples = []
        for i in range(num_samples):
            t = i / sample_rate
            # Simple ADSR envelope to avoid clicks
            attack = min(1.0, t / 0.01)
            release = max(0.0, 1.0 - (t - (duration_seconds - 0.05)) / 0.05) if t > duration_seconds - 0.05 else 1.0
            envelope = attack * release
            value = amplitude * envelope * math.sin(2 * math.pi * frequency * t)
            # Clamp and convert to 16-bit PCM
            value = max(-1.0, min(1.0, value))
            samples.append(int(value * 32767))
        
        # Pack as 16-bit PCM WAV
        wav_buffer = bytearray()
        with wave.open(Path(self.output_dir / "temp.wav"), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(struct.pack(f"<{len(samples)}h", *samples))
        
        with open(self.output_dir / "temp.wav", "rb") as f:
            return f.read()

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
        
        audio_data = self.generate_tone_waveform(
            duration_seconds=duration,
            frequency=frequency,
            sample_rate=self.sample_rate,
        )
        
        return audio_data, duration

    def save_audio(self, audio_data: bytes, job_id: int) -> str:
        """Save audio data to file and return path."""
        filename = f"synthesis_{job_id}_{uuid.uuid4().hex[:8]}.wav"
        filepath = self.output_dir / filename
        with open(filepath, "wb") as f:
            f.write(audio_data)
        return str(filepath)

    def get_audio_path(self, job_id: int) -> Optional[Path]:
        """Find audio file for a job."""
        for f in self.output_dir.glob(f"synthesis_{job_id}_*.wav"):
            return f
        return None


tts_service = TTSService()