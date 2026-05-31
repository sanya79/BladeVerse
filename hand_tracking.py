"""
hand_tracking.py
================
Wraps MediaPipe Hands into a clean, game-friendly API.

This file supports two modes:
  1. MediaPipe hand tracking when a compatible `mp.solutions` package is installed
  2. Mouse fallback mode for systems where MediaPipe is unavailable or incompatible
"""

import math
import cv2
import numpy as np
import pygame

try:
    import mediapipe as mp
    MEDIA_PIPE_AVAILABLE = hasattr(mp, 'solutions')
except Exception:
    mp = None
    MEDIA_PIPE_AVAILABLE = False

from settings import (
    SCREEN_W, SCREEN_H,
    MAX_HANDS, DETECTION_CONFIDENCE, TRACKING_CONFIDENCE,
    FLIP_CAMERA, CAMERA_INDEX,
    FAST_SWIPE_THRESHOLD, SLOW_SWIPE_THRESHOLD,
    DEBUG_MODE,
)


# MediaPipe landmark IDs
WRIST           = 0
THUMB_CMC       = 1
THUMB_MCP       = 2
THUMB_IP        = 3
THUMB_TIP       = 4
INDEX_MCP       = 5
INDEX_PIP       = 6
INDEX_DIP       = 7
INDEX_TIP       = 8
MIDDLE_MCP      = 9
MIDDLE_PIP      = 10
MIDDLE_DIP      = 11
MIDDLE_TIP      = 12
RING_MCP        = 13
RING_PIP        = 14
RING_DIP        = 15
RING_TIP        = 16
PINKY_MCP       = 17
PINKY_PIP       = 18
PINKY_DIP       = 19
PINKY_TIP       = 20


class HandTracker:
    def __init__(self, cam_index: int = CAMERA_INDEX):
        self.use_mouse = not MEDIA_PIPE_AVAILABLE
        self.tip_pos = None
        self.prev_tip = None
        self.swipe_speed = 0.0
        self.gesture = "NONE"
        self.raw_frame = None
        self._frame_w = SCREEN_W
        self._frame_h = SCREEN_H
        self._smooth_x = None
        self._smooth_y = None
        self._ALPHA = 0.45
        self._vel_history = [(0.0, 0.0)] * 4
        self._vel_idx = 0

        if self.use_mouse:
            self.cap = None
            return

        self._mp_hands = mp.solutions.hands
        self._mp_draw = mp.solutions.drawing_utils
        self._draw_spec_dot = mp.solutions.drawing_utils.DrawingSpec(
            color=(0, 255, 200), thickness=2, circle_radius=3)
        self._draw_spec_conn = mp.solutions.drawing_utils.DrawingSpec(
            color=(0, 200, 255), thickness=2)

        self.hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=MAX_HANDS,
            model_complexity=1,
            min_detection_confidence=DETECTION_CONFIDENCE,
            min_tracking_confidence=TRACKING_CONFIDENCE,
        )

        self.cap = cv2.VideoCapture(cam_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def update(self) -> bool:
        if self.use_mouse:
            self.prev_tip = self.tip_pos
            self.tip_pos = pygame.mouse.get_pos()
            self.swipe_speed = 0.0
            if self.prev_tip is not None:
                dx = self.tip_pos[0] - self.prev_tip[0]
                dy = self.tip_pos[1] - self.prev_tip[1]
                self.swipe_speed = math.hypot(dx, dy)

            buttons = pygame.mouse.get_pressed()
            if buttons[0]:
                self.gesture = "FIST"
            elif buttons[2]:
                self.gesture = "OPEN_PALM"
            elif buttons[1]:
                self.gesture = "TWO_FINGER"
            else:
                self.gesture = "POINTING"

            return True

        ok, frame = self.cap.read()
        if not ok:
            return False

        if FLIP_CAMERA:
            frame = cv2.flip(frame, 1)

        self._frame_h, self._frame_w = frame.shape[:2]
        self.raw_frame = frame.copy()

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self.hands.process(rgb)
        rgb.flags.writeable = True

        self.prev_tip = self.tip_pos
        self.tip_pos = None
        self.gesture = "NONE"
        self.swipe_speed = 0.0

        if results.multi_hand_landmarks:
            lm = results.multi_hand_landmarks[0].landmark
            raw_x = lm[INDEX_TIP].x * SCREEN_W
            raw_y = lm[INDEX_TIP].y * SCREEN_H

            if self._smooth_x is None:
                self._smooth_x = raw_x
                self._smooth_y = raw_y
            else:
                self._smooth_x = self._ALPHA * raw_x + (1 - self._ALPHA) * self._smooth_x
                self._smooth_y = self._ALPHA * raw_y + (1 - self._ALPHA) * self._smooth_y

            self.tip_pos = (int(self._smooth_x), int(self._smooth_y))

            if self.prev_tip:
                dx = self._smooth_x - self.prev_tip[0]
                dy = self._smooth_y - self.prev_tip[1]
                self.swipe_speed = math.hypot(dx, dy)

            self.gesture = self._classify_gesture(lm)

            if DEBUG_MODE:
                self._mp_draw.draw_landmarks(
                    self.raw_frame,
                    results.multi_hand_landmarks[0],
                    self._mp_hands.HAND_CONNECTIONS,
                    self._draw_spec_dot,
                    self._draw_spec_conn,
                )
                cv2.putText(self.raw_frame, f"Gesture: {self.gesture}",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            (0, 255, 200), 2)

        else:
            self._smooth_x = None
            self._smooth_y = None

        return True

    @property
    def is_slicing(self):
        return self.swipe_speed >= SLOW_SWIPE_THRESHOLD

    @property
    def is_fast_swipe(self):
        return self.swipe_speed >= FAST_SWIPE_THRESHOLD

    def release(self):
        if not self.use_mouse and self.cap is not None:
            self.cap.release()
            self.hands.close()

    def _classify_gesture(self, lm) -> str:
        def finger_up(tip, pip, mcp):
            tip_above = lm[tip].y < lm[mcp].y
            tip_straight = lm[tip].y < lm[pip].y
            return tip_above and tip_straight

        index_up = finger_up(INDEX_TIP, INDEX_PIP, INDEX_MCP)
        middle_up = finger_up(MIDDLE_TIP, MIDDLE_PIP, MIDDLE_MCP)
        ring_up = finger_up(RING_TIP, RING_PIP, RING_MCP)
        pinky_up = finger_up(PINKY_TIP, PINKY_PIP, PINKY_MCP)

        if index_up and not middle_up and not ring_up and not pinky_up:
            return "POINTING"
        if index_up and middle_up and not ring_up and not pinky_up:
            return "TWO_FINGER"
        if index_up and middle_up and ring_up and pinky_up:
            return "OPEN_PALM"
        if not index_up and not middle_up and not ring_up and not pinky_up:
            return "FIST"
        return "OTHER"
