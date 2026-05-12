import cv2
import threading
import time
import numpy as np
from modules.hand_tracking import HandDetector
from modules.controller import SystemController

class GestureEngine(threading.Thread):
    def __init__(self, camera_id=0, smoothing=7, callback=None):
        super().__init__()
        self.camera_id = camera_id
        self.smoothing = smoothing
        self.callback = callback # Function to send status updates to UI
        self.running = False
        self.current_frame = None
        
        # Initialize modules
        self.detector = HandDetector(detection_con=0.8, track_con=0.8)
        self.controller = SystemController(smoothing=self.smoothing)
        
    def run(self):
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                if self.callback: self.callback(f"ERROR: Could not open camera {self.camera_id}")
                return

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            w_cam = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h_cam = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Re-initialize controller with correct resolution
            self.controller = SystemController(frame_width=w_cam, frame_height=h_cam, smoothing=self.smoothing)
            self.running = True
            
            if self.callback: self.callback("ENGINE_CONNECTED_TO_HARDWARE")

            while self.running:
                # Hot-reload config
                prev_con = (self.controller.detection_con, self.controller.track_con)
                self.controller.load_config()
                
                # If confidence settings changed, update detector
                if prev_con != (self.controller.detection_con, self.controller.track_con):
                    self.detector.update_config(self.controller.detection_con, self.controller.track_con)
                
                self.controller.smoothing = self.smoothing

                success, img = self.cap.read()
                if not success:
                    if self.callback: self.callback("ERROR: CAMERA_DISCONNECTED")
                    break
                
                # 1. Flip image for natural mirroring
                img = cv2.flip(img, 1)
                
                # 2. Find Hands
                img = self.detector.find_hands(img)
                
                # 3. Draw Biometric HUD (Custom Brackets & Crosshair)
                fr = self.controller.frame_reduction
                color_hud = (208, 142, 59) # Sage-Blue
                
                # Corner Brackets [ ]
                l = 30
                cv2.line(img, (fr, fr), (fr + l, fr), color_hud, 2)
                cv2.line(img, (fr, fr), (fr, fr + l), color_hud, 2)
                cv2.line(img, (w_cam - fr, fr), (w_cam - fr - l, fr), color_hud, 2)
                cv2.line(img, (w_cam - fr, fr), (w_cam - fr, fr + l), color_hud, 2)
                cv2.line(img, (fr, h_cam - fr), (fr + l, h_cam - fr), color_hud, 2)
                cv2.line(img, (fr, h_cam - fr), (fr, h_cam - fr - l), color_hud, 2)
                cv2.line(img, (w_cam - fr, h_cam - fr), (w_cam - fr - l, h_cam - fr), color_hud, 2)
                cv2.line(img, (w_cam - fr, h_cam - fr), (w_cam - fr, h_cam - fr - l), color_hud, 2)
                
                # Center Crosshair
                cx_mid, cy_mid = w_cam // 2, h_cam // 2
                gap = 5
                cv2.line(img, (cx_mid - 15, cy_mid), (cx_mid - gap, cy_mid), color_hud, 1)
                cv2.line(img, (cx_mid + gap, cy_mid), (cx_mid + 15, cy_mid), color_hud, 1)
                cv2.line(img, (cx_mid, cy_mid - 15), (cx_mid, cy_mid - gap), color_hud, 1)
                cv2.line(img, (cx_mid, cy_mid + gap), (cx_mid, cy_mid + 15), color_hud, 1)

                # 4. Process Multiple Hands
                if self.detector.results.multi_hand_landmarks:
                    num_hands = len(self.detector.results.multi_hand_landmarks)
                    
                    # We process each hand found
                    for i in range(num_hands):
                        lm_list, handedness = self.detector.find_position(img, hand_no=i, draw=False)
                        fingers = self.detector.fingers_up(lm_list)
                        
                        if lm_list:
                            # 4.1. Mouse Control (Strictly Right hand only)
                            if handedness == "Right":
                                try:
                                    self.controller.move_mouse(lm_list[8][1], lm_list[8][2])
                                except Exception as e:
                                    if self.callback: self.callback(f"MOUSE_ERROR: {str(e)[:30]}")

                            # 4.2. Process Gestures for this hand
                            try:
                                # Determine if pinching for shape signature
                                x0, y0 = lm_list[0][3], lm_list[0][4]
                                x9, y9 = lm_list[9][3], lm_list[9][4]
                                hand_scale = np.hypot(x9 - x0, y9 - y0)
                                is_pinching = np.hypot(lm_list[8][3] - lm_list[4][3], lm_list[8][4] - lm_list[4][4]) < (hand_scale * 0.15)
                                
                                current_shape = self.detector.get_signature_shape(fingers, is_pinching)
                                gesture = self.controller.process_gestures(lm_list, fingers, handedness, current_shape)
                                if gesture and self.callback:
                                    self.callback(f"TRIGGER: {gesture.upper()}")
                            except Exception as e:
                                if self.callback: self.callback(f"GESTURE_ERROR: {str(e)[:30]}")

                            # 5. Visual Overlays (Glowing Tracking Dots per hand)
                            x8, y8 = lm_list[8][1], lm_list[8][2]
                            # Use Sage for Right, Copper for Left
                            base_color = (176, 195, 168) if handedness == "Right" else (115, 163, 212)
                            
                            cv2.circle(img, (x8, y8), 18, base_color, 1)
                            cv2.circle(img, (x8, y8), 8, (255, 255, 255), -1)
                            cv2.putText(img, handedness[0], (x8 - 5, y8 + 5), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)

                self.current_frame = img
                time.sleep(0.01)

                self.current_frame = img
                time.sleep(0.01)

        except Exception as e:
            if self.callback: self.callback(f"CRITICAL_ENGINE_FAILURE: {str(e)}")
        finally:
            if hasattr(self, 'cap') and self.cap.isOpened():
                self.cap.release()
            self.running = False
            if self.callback: self.callback("ENGINE_RESOURCES_RELEASED")

    def stop(self):
        self.running = False
        if hasattr(self, 'cap'):
            self.cap.release()

    def get_frame(self):
        return self.current_frame
