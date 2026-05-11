import cv2
import mediapipe as mp

class HandDetector:
    def __init__(self, mode=False, max_hands=1, detection_con=0.7, track_con=0.7):
        try:
            self.mp_hands = mp.solutions.hands
            self.mp_draw = mp.solutions.drawing_utils
        except AttributeError:
            raise ImportError(
                "mediapipe.solutions not found. This project requires Python 3.10/3.12."
            )
            
        self.hands = self.mp_hands.Hands(static_image_mode=mode, 
                                        max_num_hands=max_hands, 
                                        min_detection_confidence=detection_con, 
                                        min_tracking_confidence=track_con)

    def find_hands(self, img, draw=True):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)
        if self.results.multi_hand_landmarks:
            for hand_lms in self.results.multi_hand_landmarks:
                if draw:
                    self.mp_draw.draw_landmarks(img, hand_lms, self.mp_hands.HAND_CONNECTIONS)
        return img

    def find_position(self, img, hand_no=0, draw=True):
        self.lm_list = [] # Store as instance variable for other methods
        if self.results.multi_hand_landmarks:
            my_hand = self.results.multi_hand_landmarks[hand_no]
            h, w, c = img.shape
            for id, lm in enumerate(my_hand.landmark):
                # We store both pixel coordinates and normalized ones [0.0, 1.0]
                cx, cy = int(lm.x * w), int(lm.y * h)
                self.lm_list.append([id, cx, cy, lm.x, lm.y])
                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
        return self.lm_list

    def fingers_up(self):
        """
        Returns a list of 5 integers (0 or 1) representing the state of each finger.
        Uses a more robust check based on joint orientation.
        """
        if not hasattr(self, 'lm_list') or not self.lm_list:
            return [0, 0, 0, 0, 0]

        fingers = []

        # 1. Thumb: Check if tip (4) is outside the thumb-index joint (2)
        # We need to know if it's a left or right hand for perfect accuracy,
        # but comparing x distance from wrist center works for most orientations.
        if self.lm_list[4][1] > self.lm_list[3][1]: # Simplified for right hand/mirrored
            fingers.append(1)
        else:
            fingers.append(0)

        # 2. Other 4 fingers: Check if tip is above the second joint
        tip_ids = [8, 12, 16, 20]
        for tip_id in tip_ids:
            if self.lm_list[tip_id][2] < self.lm_list[tip_id - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

    def get_gesture_name(self, fingers):
        if fingers == [0, 0, 0, 0, 0]: return "Fist"
        if fingers == [1, 1, 1, 1, 1]: return "Open Palm"
        if fingers == [0, 1, 0, 0, 0]: return "Pointing"
        if fingers == [0, 1, 1, 0, 0]: return "Victory"
        if fingers == [0, 0, 0, 0, 1]: return "Pinky Up"
        return "Custom"