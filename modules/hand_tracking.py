import cv2
import mediapipe as mp
import numpy as np

class HandDetector:
    def __init__(self, mode=False, max_hands=2, detection_con=0.7, track_con=0.7):
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

    def update_config(self, detection_con=0.7, track_con=0.7):
        """Re-initializes MediaPipe Hands if confidence settings change."""
        self.hands = self.mp_hands.Hands(static_image_mode=False, 
                                        max_num_hands=2, 
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
        lm_list = []
        handedness = "Right"
        
        if self.results.multi_hand_landmarks and len(self.results.multi_hand_landmarks) > hand_no:
            if self.results.multi_handedness:
                # Since we flip the image in engine.py, MediaPipe's internal classification
                # of 'Left' or 'Right' is already correct relative to the user's hand.
                handedness = self.results.multi_handedness[hand_no].classification[0].label
                
            my_hand = self.results.multi_hand_landmarks[hand_no]
            h, w, c = img.shape
            for id, lm in enumerate(my_hand.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                lm_list.append([id, cx, cy, lm.x, lm.y, lm.z])
                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
        return lm_list, handedness

    def fingers_up(self, lm_list):
        """
        Returns a list of 5 integers (0 or 1) representing the state of each finger.
        Uses rotation-invariant vector math.
        """
        if not lm_list:
            return [0, 0, 0, 0, 0]

        fingers = []

        # 1. Thumb: Check distance from index MCP to thumb TIP
        dist = np.hypot(lm_list[4][3] - lm_list[5][3], 
                        lm_list[4][4] - lm_list[5][4])
        scale = np.hypot(lm_list[9][3] - lm_list[0][3], 
                         lm_list[9][4] - lm_list[0][4])
        
        if dist > scale * 0.6:
            fingers.append(1)
        else:
            fingers.append(0)

        # 2. Other 4 fingers: Vector check
        tip_ids = [8, 12, 16, 20]
        for tip_id in tip_ids:
            dist_tip = np.hypot(lm_list[tip_id][3] - lm_list[0][3], 
                                lm_list[tip_id][4] - lm_list[0][4])
            dist_pip = np.hypot(lm_list[tip_id-2][3] - lm_list[0][3], 
                                lm_list[tip_id-2][4] - lm_list[0][4])
            
            if dist_tip > dist_pip:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

    def get_signature_shape(self, fingers, is_pinching=False):
        """Matches finger array to a distinct named shape."""
        if is_pinching:
            if fingers[2:] == [0, 0, 0]: return "ok_sign" # Index-Thumb pinch
            if fingers[1] == 0 and fingers[2] == 1: return "pinch_middle" # Middle-Thumb pinch
        
        if fingers == [1, 0, 0, 0, 0]: return "thumb_up"
        if fingers == [1, 1, 0, 0, 0]: return "l_shape"
        if fingers == [0, 1, 1, 0, 0]: return "victory"
        if fingers == [0, 1, 1, 1, 0]: return "three_fingers"
        if fingers == [0, 1, 0, 0, 1]: return "rock_on"
        if fingers == [0, 0, 0, 0, 0]: return "fist"
        if fingers == [1, 1, 1, 1, 1]: return "open_palm"
        if fingers == [0, 1, 1, 1, 1]: return "clutch" # Index, Middle, Ring, Pinky up
        return None
