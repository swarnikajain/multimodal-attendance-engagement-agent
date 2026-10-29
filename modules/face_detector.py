"""
Face detection module for Multimodal Attendance & Engagement Agent.
Uses OpenCV's built-in Haar Cascade detector with quality diagnostics.
Runs 100% locally and does not transmit any media data.
"""

from typing import List, Tuple, Dict, Any, Optional
import numpy as np

# Safe import of cv2
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    cv2 = None
    OPENCV_AVAILABLE = False


class FaceDetector:
    """
    Lightweight, reliable local face detector using OpenCV Haar Cascades
    with image quality assessment (lighting, blur).
    """

    def __init__(self, scale_factor: float = 1.1, min_neighbors: int = 4, min_size: Tuple[int, int] = (30, 30)):
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors
        self.min_size = min_size
        self.cascade = None
        self._init_cascade()

    def _init_cascade(self):
        if not OPENCV_AVAILABLE:
            return
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.cascade = cv2.CascadeClassifier(cascade_path)
        if self.cascade.empty():
            # Alternative fallback attempt
            alt_path = cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml"
            self.cascade = cv2.CascadeClassifier(alt_path)

    def is_available(self) -> bool:
        return OPENCV_AVAILABLE and (self.cascade is not None) and (not self.cascade.empty())

    def assess_frame_quality(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Evaluate frame brightness, contrast, and sharpness.
        Helps generate transparent data quality metrics.
        """
        if frame is None or not OPENCV_AVAILABLE:
            return {
                "brightness": 0.0,
                "sharpness": 0.0,
                "lighting_condition": "Unknown",
                "blur_detected": False
            }

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        brightness = float(np.mean(gray))  # 0 to 255
        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())  # Higher = sharper

        if brightness < 45:
            lighting = "Low Light"
        elif brightness > 215:
            lighting = "Overexposed"
        else:
            lighting = "Acceptable"

        blur_detected = sharpness < 35.0

        return {
            "brightness": round(brightness, 2),
            "sharpness": round(sharpness, 2),
            "lighting_condition": lighting,
            "blur_detected": blur_detected
        }

    def detect_faces(self, frame: np.ndarray) -> Tuple[List[Tuple[int, int, int, int]], List[Tuple[int, int]], Dict[str, Any]]:
        """
        Detect faces in a given BGR frame.
        Returns:
            - bounding_boxes: List of (x, y, w, h)
            - centroids: List of (center_x, center_y)
            - quality_info: Dict with lighting and blur indicators
        """
        if frame is None or not self.is_available():
            return [], [], {"brightness": 0, "sharpness": 0, "lighting_condition": "Unavailable", "blur_detected": False}

        quality = self.assess_frame_quality(frame)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame

        # Histogram equalization to enhance contrast in dim or uneven light
        equalized = cv2.equalizeHist(gray)

        rects = self.cascade.detectMultiScale(
            equalized,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=self.min_size,
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        boxes: List[Tuple[int, int, int, int]] = []
        centroids: List[Tuple[int, int]] = []

        for (x, y, w, h) in rects:
            boxes.append((int(x), int(y), int(w), int(h)))
            cx = int(x + w / 2.0)
            cy = int(y + h / 2.0)
            centroids.append((cx, cy))

        return boxes, centroids, quality
