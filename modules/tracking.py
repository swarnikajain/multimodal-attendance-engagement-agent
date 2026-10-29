"""
Centroid Tracking module for Multimodal Attendance & Engagement Agent.
Associates detected faces across video frames using Euclidean distance matching.
Maintains persistent track IDs and duration metrics without storing biometric images.
"""

from typing import Dict, List, Tuple, Any, Optional
from collections import OrderedDict
import numpy as np
from config import TRACKING_MAX_DISAPPEARED, TRACKING_DISTANCE_THRESHOLD


class TrackedSubject:
    """Represents a single continuous tracked face/person across frames."""

    def __init__(self, track_id: int, centroid: Tuple[int, int], box: Tuple[int, int, int, int], timestamp_sec: float):
        self.track_id = track_id
        self.centroid = centroid
        self.box = box
        self.first_seen_sec = timestamp_sec
        self.last_seen_sec = timestamp_sec
        self.total_frames_seen = 1
        self.disappeared_count = 0
        self.centroid_history: List[Tuple[float, Tuple[int, int]]] = [(timestamp_sec, centroid)]

    def update(self, centroid: Tuple[int, int], box: Tuple[int, int, int, int], timestamp_sec: float):
        self.centroid = centroid
        self.box = box
        self.last_seen_sec = timestamp_sec
        self.total_frames_seen += 1
        self.disappeared_count = 0
        self.centroid_history.append((timestamp_sec, centroid))
        # Keep recent history manageable
        if len(self.centroid_history) > 100:
            self.centroid_history.pop(0)

    @property
    def duration_observed(self) -> float:
        """Total elapsed observation time from first seen to last seen in seconds."""
        return max(0.0, self.last_seen_sec - self.first_seen_sec)


class CentroidTracker:
    """
    Centroid-based multi-object tracker for classroom face detections.
    """

    def __init__(self, max_disappeared: int = TRACKING_MAX_DISAPPEARED,
                 distance_threshold: float = TRACKING_DISTANCE_THRESHOLD):
        self.next_track_id = 1
        self.objects: OrderedDict[int, TrackedSubject] = OrderedDict()
        self.completed_tracks: List[TrackedSubject] = []
        self.max_disappeared = max_disappeared
        self.distance_threshold = distance_threshold

    def register(self, centroid: Tuple[int, int], box: Tuple[int, int, int, int], timestamp_sec: float):
        """Register a new tracked subject."""
        track = TrackedSubject(self.next_track_id, centroid, box, timestamp_sec)
        self.objects[self.next_track_id] = track
        self.next_track_id += 1

    def deregister(self, track_id: int):
        """Move track from active to completed tracks list."""
        if track_id in self.objects:
            self.completed_tracks.append(self.objects[track_id])
            del self.objects[track_id]

    def update(self, rects: List[Tuple[int, int, int, int]],
               centroids: List[Tuple[int, int]],
               timestamp_sec: float) -> Dict[int, TrackedSubject]:
        """
        Update tracker with current frame detections.
        """
        # If no detections in current frame
        if len(rects) == 0:
            for track_id in list(self.objects.keys()):
                self.objects[track_id].disappeared_count += 1
                if self.objects[track_id].disappeared_count > self.max_disappeared:
                    self.deregister(track_id)
            return self.objects

        # If currently tracking no objects, register all detections
        if len(self.objects) == 0:
            for box, centroid in zip(rects, centroids):
                self.register(centroid, box, timestamp_sec)
            return self.objects

        # Existing tracked objects and current detections
        track_ids = list(self.objects.keys())
        object_centroids = [self.objects[tid].centroid for tid in track_ids]

        # Compute distance matrix between existing objects and current detections
        D = np.zeros((len(object_centroids), len(centroids)), dtype=np.float32)
        for i, obj_pt in enumerate(object_centroids):
            for j, det_pt in enumerate(centroids):
                dist = np.linalg.norm(np.array(obj_pt) - np.array(det_pt))
                D[i, j] = dist

        # Find matching pairs with minimum distance
        rows = D.min(axis=1).argsort()
        cols = D.argmin(axis=1)[rows]

        used_rows = set()
        used_cols = set()

        for (row, col) in zip(rows, cols):
            if row in used_rows or col in used_cols:
                continue

            # If distance exceeds threshold, it is likely a different individual
            if D[row, col] > self.distance_threshold:
                continue

            tid = track_ids[row]
            self.objects[tid].update(centroids[col], rects[col], timestamp_sec)

            used_rows.add(row)
            used_cols.add(col)

        unused_rows = set(range(len(object_centroids))) - used_rows
        unused_cols = set(range(len(centroids))) - used_cols

        # Increment disappeared for unmatched existing tracks
        for row in unused_rows:
            tid = track_ids[row]
            self.objects[tid].disappeared_count += 1
            if self.objects[tid].disappeared_count > self.max_disappeared:
                self.deregister(tid)

        # Register new objects for unmatched new detections
        for col in unused_cols:
            self.register(centroids[col], rects[col], timestamp_sec)

        return self.objects

    def finalize(self) -> List[TrackedSubject]:
        """Combine all remaining active tracks into the completed tracks list."""
        for tid in list(self.objects.keys()):
            self.deregister(tid)
        return self.completed_tracks
