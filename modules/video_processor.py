"""
Video processing and computer vision analysis pipeline.
Performs frame sampling, face detection, centroid tracking, observable motion measurement,
and video signal diagnostics.
"""

import os
from typing import Dict, List, Any, Optional, Callable, Tuple
import numpy as np

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    cv2 = None
    OPENCV_AVAILABLE = False

from modules.face_detector import FaceDetector
from modules.tracking import CentroidTracker, TrackedSubject
from config import DEFAULT_SAMPLING_INTERVAL_SEC


def get_video_metadata(video_path: str) -> Dict[str, Any]:
    """
    Extracts metadata from video file without reading all frames.
    """
    if not OPENCV_AVAILABLE or not os.path.exists(video_path):
        return {
            "valid": False,
            "error": "OpenCV is not available or video file not found."
        }

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {
            "valid": False,
            "error": "Failed to open video file. Format may be unsupported or file corrupted."
        }

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_sec = total_frames / fps if fps > 0 else 0.0

    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])

    cap.release()

    return {
        "valid": True,
        "fps": round(fps, 2),
        "total_frames": total_frames,
        "width": width,
        "height": height,
        "duration_sec": round(duration_sec, 2),
        "codec": codec
    }


def compute_frame_motion(prev_gray: Optional[np.ndarray], curr_gray: np.ndarray) -> float:
    """
    Computes observable pixel motion between consecutive sampled frames.
    Returns normalized motion intensity [0.0, 1.0].
    """
    if prev_gray is None or curr_gray is None or not OPENCV_AVAILABLE:
        return 0.0

    # Ensure identical dimensions
    if prev_gray.shape != curr_gray.shape:
        return 0.0

    diff = cv2.absdiff(curr_gray, prev_gray)
    # Threshold slight noise
    _, thresh = cv2.threshold(diff, 20, 255, cv2.THRESH_BINARY)
    motion_ratio = float(np.mean(thresh) / 255.0)

    # Scale to realistic 0-1 observational range
    return float(np.clip(motion_ratio * 4.0, 0.0, 1.0))


def estimate_frontal_pose_proxy(boxes: List[Tuple[int, int, int, int]]) -> Optional[float]:
    """
    Lightweight heuristic proxy for frontal face orientation.
    Based on face bounding box aspect ratios (frontal faces typically exhibit 1:1 to 1:1.3 ratio).
    Note: Explicitly a geometric proxy, NOT a neurological attention measurement.
    """
    if not boxes:
        return None

    ratios = []
    for (x, y, w, h) in boxes:
        if h > 0:
            aspect = w / float(h)
            # Frontal faces typically cluster around 0.75 - 1.05 aspect ratio in Haar Cascades
            frontal_closeness = 1.0 - min(abs(aspect - 0.88) / 0.5, 1.0)
            ratios.append(frontal_closeness)

    return float(np.mean(ratios)) if ratios else None


def process_video_pipeline(
    video_path: str,
    sampling_interval_sec: float = DEFAULT_SAMPLING_INTERVAL_SEC,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Dict[str, Any]:
    """
    Complete video analysis execution:
    1. Reads frames at specified sampling intervals.
    2. Detects faces locally using FaceDetector.
    3. Tracks faces across time using CentroidTracker.
    4. Computes frame motion and geometric pose proxies.
    5. Compiles video data quality diagnostics.
    """
    meta = get_video_metadata(video_path)
    if not meta.get("valid"):
        return {
            "success": False,
            "error": meta.get("error", "Invalid video file"),
            "tracks": [],
            "timeline": [],
            "metadata": meta,
            "quality": {}
        }

    duration_sec = meta["duration_sec"]
    fps = meta["fps"]

    cap = cv2.VideoCapture(video_path)
    detector = FaceDetector()
    tracker = CentroidTracker()

    timeline: List[Dict[str, Any]] = []
    prev_gray: Optional[np.ndarray] = None

    blur_count = 0
    low_light_count = 0
    overexposed_count = 0
    sampled_frame_count = 0

    current_sec = 0.0

    while current_sec < duration_sec:
        # Seek frame by timestamp in milliseconds
        target_msec = current_sec * 1000.0
        cap.set(cv2.CAP_PROP_POS_MSEC, target_msec)
        ret, frame = cap.read()

        if not ret or frame is None:
            # Handle end of stream or frame decode skip
            break

        sampled_frame_count += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        boxes, centroids, quality = detector.detect_faces(frame)

        # Quality diagnostics tracking
        if quality.get("blur_detected"):
            blur_count += 1
        if quality.get("lighting_condition") == "Low Light":
            low_light_count += 1
        elif quality.get("lighting_condition") == "Overexposed":
            overexposed_count += 1

        # Tracker update
        active_objects = tracker.update(boxes, centroids, current_sec)

        # Observable motion
        motion = compute_frame_motion(prev_gray, gray)
        prev_gray = gray

        # Frontal pose proxy
        gaze_proxy = estimate_frontal_pose_proxy(boxes)

        timeline.append({
            "timestamp_sec": round(current_sec, 2),
            "people_count": len(boxes),
            "motion_score": round(motion, 3),
            "gaze_score": round(gaze_proxy, 3) if gaze_proxy is not None else None,
            "quality": quality
        })

        if progress_callback and duration_sec > 0:
            pct = min(1.0, current_sec / duration_sec)
            progress_callback(pct, f"Processing video: {int(current_sec)}s / {int(duration_sec)}s ({int(pct*100)}%)")

        current_sec += sampling_interval_sec

    cap.release()

    # Finalize tracks
    completed_tracks = tracker.finalize()

    # Calculate overall video quality metric
    quality_score = 100.0
    quality_issues = []
    if sampled_frame_count > 0:
        blur_ratio = blur_count / sampled_frame_count
        lighting_issue_ratio = (low_light_count + overexposed_count) / sampled_frame_count

        if blur_ratio > 0.3:
            quality_score -= 20.0
            quality_issues.append(f"High motion blur or low focus detected in {int(blur_ratio*100)}% of frames.")
        if lighting_issue_ratio > 0.3:
            quality_score -= 20.0
            quality_issues.append(f"Suboptimal lighting conditions detected in {int(lighting_issue_ratio*100)}% of frames.")

    quality_score = max(20.0, min(100.0, quality_score))

    quality_report = {
        "video_quality_score": round(quality_score, 1),
        "sampled_frames": sampled_frame_count,
        "blur_frames": blur_count,
        "low_light_frames": low_light_count,
        "overexposed_frames": overexposed_count,
        "quality_issues": quality_issues
    }

    if progress_callback:
        progress_callback(1.0, "Video analysis complete.")

    return {
        "success": True,
        "metadata": meta,
        "tracks": completed_tracks,
        "timeline": timeline,
        "quality": quality_report
    }
