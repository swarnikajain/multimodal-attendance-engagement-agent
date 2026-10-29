"""
Audio processing and speech activity estimation module.
Performs lightweight, local audio analysis using SciPy / SoundFile / NumPy.
Measures RMS energy, silence intervals, speech activity intervals, and audio signal quality.
"""

import os
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

# Optional SoundFile import
try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    sf = None
    SOUNDFILE_AVAILABLE = False

# Fallback wave / scipy
import wave
from scipy.io import wavfile


def load_audio_file(audio_path: str, target_sr: int = 16000) -> Tuple[Optional[np.ndarray], int, Optional[str]]:
    """
    Loads an audio file into a 1D float32 numpy array normalized to [-1.0, 1.0].
    Tries soundfile first, then scipy.io.wavfile, then standard wave module.
    """
    if not os.path.exists(audio_path):
        return None, 0, f"Audio file not found: {audio_path}"

    # Try soundfile
    if SOUNDFILE_AVAILABLE and sf is not None:
        try:
            data, sr = sf.read(audio_path, dtype="float32")
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)  # Convert stereo/multichannel to mono
            return data, sr, None
        except Exception as e:
            pass  # Fallback to scipy

    # Try scipy.io.wavfile
    try:
        sr, data = wavfile.read(audio_path)
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)
        # Normalize int16 or int32 to float32 [-1, 1]
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32768.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483648.0
        elif data.dtype == np.uint8:
            data = (data.astype(np.float32) - 128.0) / 128.0
        return data, sr, None
    except Exception as e:
        return None, 0, f"Could not decode audio: {str(e)}"


def compute_audio_timeline(
    audio_data: np.ndarray,
    sr: int,
    window_sec: float = 1.0,
    energy_threshold_multiplier: float = 1.5
) -> Dict[str, Any]:
    """
    Analyzes audio signal in discrete time windows.
    Detects active speech candidates, silence periods, and audio quality diagnostics.
    """
    if audio_data is None or len(audio_data) == 0 or sr <= 0:
        return {
            "valid": False,
            "error": "Empty or invalid audio stream."
        }

    total_samples = len(audio_data)
    duration_sec = total_samples / float(sr)
    samples_per_window = int(window_sec * sr)

    if samples_per_window <= 0:
        samples_per_window = sr

    num_windows = int(np.ceil(total_samples / float(samples_per_window)))

    # Compute baseline noise floor (median absolute deviation)
    abs_signal = np.abs(audio_data)
    noise_floor = float(np.percentile(abs_signal, 20))
    speech_threshold = max(0.015, noise_floor * energy_threshold_multiplier)

    # Detect clipping (values very close to +/- 1.0)
    clipping_count = int(np.sum(abs_signal >= 0.99))
    clipping_ratio = float(clipping_count / total_samples)

    timeline: List[Dict[str, Any]] = []
    active_windows = 0
    silence_windows = 0

    current_silence_start: Optional[float] = None
    silence_intervals: List[Dict[str, float]] = []

    for w in range(num_windows):
        start_idx = w * samples_per_window
        end_idx = min(start_idx + samples_per_window, total_samples)
        chunk = audio_data[start_idx:end_idx]

        if len(chunk) == 0:
            continue

        # Root Mean Square (RMS) energy
        rms = float(np.sqrt(np.mean(chunk**2)))
        normalized_energy = min(1.0, rms * 5.0)  # Scale to 0-1 range

        # Zero-Crossing Rate
        zcr = float(np.mean(np.abs(np.diff(np.sign(chunk)))) / 2.0)

        t_sec = round(w * window_sec, 2)
        is_speech = (rms >= speech_threshold) and (0.01 <= zcr <= 0.45)

        if is_speech:
            active_windows += 1
            if current_silence_start is not None:
                # Silence ended
                silence_dur = t_sec - current_silence_start
                if silence_dur >= 8.0:  # Register prolonged silence
                    silence_intervals.append({
                        "start_sec": current_silence_start,
                        "end_sec": t_sec,
                        "duration_sec": round(silence_dur, 2)
                    })
                current_silence_start = None
        else:
            silence_windows += 1
            if current_silence_start is None:
                current_silence_start = t_sec

        timeline.append({
            "timestamp_sec": t_sec,
            "rms_energy": round(normalized_energy, 3),
            "zero_crossing_rate": round(zcr, 3),
            "speech_active": 1 if is_speech else 0
        })

    # Catch trailing silence
    if current_silence_start is not None:
        final_silence_dur = duration_sec - current_silence_start
        if final_silence_dur >= 8.0:
            silence_intervals.append({
                "start_sec": current_silence_start,
                "end_sec": round(duration_sec, 2),
                "duration_sec": round(final_silence_dur, 2)
            })

    total_valid_windows = max(1, active_windows + silence_windows)
    speech_ratio = round(active_windows / float(total_valid_windows), 3)
    silence_ratio = round(silence_windows / float(total_valid_windows), 3)

    # Audio quality diagnostics
    quality_score = 100.0
    quality_notes = []
    if clipping_ratio > 0.05:
        quality_score -= 25.0
        quality_notes.append(f"Audio clipping observed in {round(clipping_ratio*100, 1)}% of samples (microphone gain too high).")
    if rms < 0.005:
        quality_score -= 30.0
        quality_notes.append("Very low recording level; audio volume might be insufficient.")

    quality_score = max(20.0, min(100.0, quality_score))

    return {
        "valid": True,
        "duration_sec": round(duration_sec, 2),
        "sample_rate": sr,
        "timeline": timeline,
        "total_active_sec": round(active_windows * window_sec, 2),
        "total_silence_sec": round(silence_windows * window_sec, 2),
        "speech_ratio": speech_ratio,
        "silence_ratio": silence_ratio,
        "silence_intervals": silence_intervals,
        "audio_quality_score": round(quality_score, 1),
        "clipping_ratio": round(clipping_ratio, 4),
        "quality_notes": quality_notes
    }


def process_audio_pipeline(audio_path: str, window_sec: float = 1.0) -> Dict[str, Any]:
    """
    Main audio processing entry point.
    """
    data, sr, err = load_audio_file(audio_path)
    if err or data is None:
        return {
            "success": False,
            "error": err or "Failed to load audio file.",
            "timeline": [],
            "quality": {}
        }

    analysis = compute_audio_timeline(data, sr, window_sec=window_sec)
    if not analysis.get("valid"):
        return {
            "success": False,
            "error": analysis.get("error", "Audio analysis failed."),
            "timeline": [],
            "quality": {}
        }

    return {
        "success": True,
        "duration_sec": analysis["duration_sec"],
        "speech_ratio": analysis["speech_ratio"],
        "silence_ratio": analysis["silence_ratio"],
        "silence_intervals": analysis["silence_intervals"],
        "timeline": analysis["timeline"],
        "quality": {
            "audio_quality_score": analysis["audio_quality_score"],
            "clipping_ratio": analysis["clipping_ratio"],
            "notes": analysis["quality_notes"]
        }
    }
