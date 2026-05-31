"""
hand_tracking.py
================
Wraps MediaPipe Hands into a clean, game-friendly API.

Key responsibilities:
  • Capture webcam frames via OpenCV
  • Run MediaPipe hand detection
  • Expose the index-finger tip position (mapped to screen coords)
  • Detect gestures: FIST, TWO_FINGER, OPEN_PALM, POINTING
  • Compute swipe speed from frame-to-frame tip movement
"""

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
import numpy as np
from settings import (
    SCREEN_W, SCREEN_H,
    MAX_HANDS, DETECTION_CONFIDENCE, TRACKING_CONFIDENCE,
    FLIP_CAMERA, CAMERA_INDEX,
    FAST_SWIPE_THRESHOLD, SLOW_SWIPE_THRESHOLD,
    DEBUG_MODE,
)


# ── MediaPipe landmark indices ──────────────────────────────────────────────
# Reference: https://developers.google.com/mediapipe/solutions/vision/hand_landmarker
WRIST           = 0
THUMB_TIP       = 4
INDEX_MCP       = 5
INDEX_TIP       = 8
MIDDLE_MCP      = 9
MIDDLE_TIP      = 12
RING_MCP        = 13
RING_TIP        = 16
PINKY_MCP       = 17
PINKY_TIP       = 20


class HandTracker:
    """
    Singleton-style tracker.  One instance is created in main.py and
    passed around, so the webcam stays open for the whole game session.
    """

    def __init__(self, cam_index: int = CAMERA_INDEX):
        # ── MediaPipe setup (new tasks-based API) ──────────────────────
        base_options = mp_python.BaseOptions(model_asset_path='hand_landmarker.task')
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=MAX_HANDS,
            min_hand_detection_confidence=DETECTION_CONFIDENCE,
            min_hand_presence_confidence=TRACKING_CONFIDENCE,
            min_tracking_confidence=TRACKING_CONFIDENCE,
        )
        try:
            self.landmarker = vision.HandLandmarker.create_from_options(options)
        except Exception:
            # Fallback: model file not available, create with default
            self.landmarker = vision.HandLandmarker.create_from_options(
                vision.HandLandmarkerOptions(
                    base_options=mp_python.BaseOptions(),
                    num_hands=MAX_HANDS,
                )
            )

        # ── Webcam ──────────────────────────────────────────────────────
        self.cap = cv2.VideoCapture(cam_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        # ── State ───────────────────────────────────────────────────────
        self.tip_pos: tuple[int, int] | None = None   # screen-space (x, y)
        self.prev_tip: tuple[int, int] | None = None
        self.swipe_speed: float = 0.0                 # pixels/frame
        self.gesture: str = "NONE"                    # current gesture label
        self.raw_frame: np.ndarray | None = None      # last BGR frame
        self._frame_w = 640
        self._frame_h = 480
        self._hand_landmarks = None  # for debug rendering

    # ────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ────────────────────────────────────────────────────────────────────

    def update(self) -> bool:
        """
        Read one webcam frame, run hand detection, update all state.
        Returns True if a frame was successfully captured.
        """
        ok, frame = self.cap.read()
        if not ok:
            return False

        if FLIP_CAMERA:
            frame = cv2.flip(frame, 1)           # mirror horizontally

        self._frame_h, self._frame_w = frame.shape[:2]
        self.raw_frame = frame.copy()

        # Convert BGR → RGB for MediaPipe
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create an Image object for the landmarker
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        
        # Run hand detection
        detection_result = self.landmarker.detect(mp_image)

        # Reset
        self.prev_tip = self.tip_pos
        self.tip_pos  = None
        self.gesture  = "NONE"
        self.swipe_speed = 0.0
        self._hand_landmarks = None

        if detection_result.hand_landmarks:
            lm_list = detection_result.hand_landmarks[0]  # first hand only
            self._hand_landmarks = lm_list

            # ── Index finger tip in screen space ────────────────────────
            tip_norm = lm_list[INDEX_TIP]
            sx = int(tip_norm.x * SCREEN_W)
            sy = int(tip_norm.y * SCREEN_H)
            self.tip_pos = (sx, sy)

            # ── Swipe speed ─────────────────────────────────────────────
            if self.prev_tip:
                dx = sx - self.prev_tip[0]
                dy = sy - self.prev_tip[1]
                self.swipe_speed = (dx**2 + dy**2) ** 0.5

            # ── Gesture detection ────────────────────────────────────────
            self.gesture = self._classify_gesture(lm_list)

            # ── Debug overlay on raw_frame ───────────────────────────────
            if DEBUG_MODE and self._hand_landmarks:
                self._draw_landmarks_on_frame()

        return True

    def _draw_landmarks_on_frame(self):
        """Draw hand landmarks on the raw frame for debug visualization."""
        if not self._hand_landmarks:
            return
        
        # Draw circles for each landmark
        for lm in self._hand_landmarks:
            x = int(lm.x * self._frame_w)
            y = int(lm.y * self._frame_h)
            cv2.circle(self.raw_frame, (x, y), 3, (0, 255, 0), -1)
        
        # Draw connections between landmarks (simplified hand skeleton)
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),      # thumb
            (0, 5), (5, 6), (6, 7), (7, 8),      # index
            (0, 9), (9, 10), (10, 11), (11, 12), # middle
            (0, 13), (13, 14), (14, 15), (15, 16), # ring
            (0, 17), (17, 18), (18, 19), (19, 20), # pinky
        ]
        
        for start_idx, end_idx in connections:
            if start_idx < len(self._hand_landmarks) and end_idx < len(self._hand_landmarks):
                start = self._hand_landmarks[start_idx]
                end = self._hand_landmarks[end_idx]
                x1, y1 = int(start.x * self._frame_w), int(start.y * self._frame_h)
                x2, y2 = int(end.x * self._frame_w), int(end.y * self._frame_h)
                cv2.line(self.raw_frame, (x1, y1), (x2, y2), (0, 255, 0), 1)

    @property
    def is_slicing(self) -> bool:
        """True when the tip is moving fast enough to count as a slice."""
        return self.swipe_speed >= SLOW_SWIPE_THRESHOLD

    @property
    def is_fast_swipe(self) -> bool:
        """True when swipe is fast enough for a bonus."""
        return self.swipe_speed >= FAST_SWIPE_THRESHOLD

    def release(self):
        """Clean up webcam and MediaPipe resources."""
        self.cap.release()
        self.landmarker.close()

    # ────────────────────────────────────────────────────────────────────
    # INTERNAL HELPERS
    # ────────────────────────────────────────────────────────────────────

    def _classify_gesture(self, lm) -> str:
        """
        Rule-based gesture classifier.
        Compares fingertip Y positions against their MCP (knuckle) joints.
        A finger is 'raised' if its tip is above its MCP in image space
        (smaller Y value = higher on screen because Y increases downward).
        """
        # Is each finger extended? (tip above MCP = extended)
        index_up  = lm[INDEX_TIP].y  < lm[INDEX_MCP].y
        middle_up = lm[MIDDLE_TIP].y < lm[MIDDLE_MCP].y
        ring_up   = lm[RING_TIP].y   < lm[RING_MCP].y
        pinky_up  = lm[PINKY_TIP].y  < lm[PINKY_MCP].y

        fingers_up = sum([index_up, middle_up, ring_up, pinky_up])

        if fingers_up == 0:
            return "FIST"                  # → Shield power
        if index_up and not middle_up and not ring_up and not pinky_up:
            return "POINTING"              # → Normal blade mode
        if index_up and middle_up and not ring_up and not pinky_up:
            return "TWO_FINGER"            # → Combo mode
        if fingers_up >= 4:
            return "OPEN_PALM"             # → Slow-motion
        return "OTHER"
