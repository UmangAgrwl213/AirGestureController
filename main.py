import cv2
import math
import sys
import numpy as np
from modules.hand_tracking import HandDetector
from modules.controller import SystemController

def main(cam_id=1):
    # 1. Initialize Webcam and Modules
    cap = cv2.VideoCapture(cam_id)
    
    # Set webcam resolution to 720p if possible
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    w_cam = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h_cam = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    detector = HandDetector(detection_con=0.8, track_con=0.8)
    controller = SystemController(frame_width=w_cam, frame_height=h_cam)

    print(f"Macro Controller initialized using camera {cam_id}.")
    print("Default mappings: Pinch Index -> Left Click, Pinch Middle -> Right Click, Fist -> Show Desktop")

    try:
        while True:
            # Check for config updates (Hot-Reload)
            controller.load_config()

            success, img = cap.read()
            if not success:
                print(f"Failed to capture image from camera {cam_id}")
                break
                
            # 2. Find Hand Landmarks
            img = detector.find_hands(img)
            lm_list, handedness = detector.find_position(img, draw=False) 
            fingers = detector.fingers_up(lm_list)
            
            # 3. Draw Active Area
            fr = controller.frame_reduction
            cv2.rectangle(img, (fr, fr), (w_cam - fr, h_cam - fr), (255, 0, 0), 2)

            if len(lm_list) != 0:
                # 4. Mouse Movement (Index finger)
                controller.move_mouse(lm_list[8][1], lm_list[8][2])
                
                # 5. Gesture Processing (Macros)
                # Determine if pinching for shape signature
                x0, y0 = lm_list[0][3], lm_list[0][4]
                x9, y9 = lm_list[9][3], lm_list[9][4]
                hand_scale = np.hypot(x9 - x0, y9 - y0)
                is_pinching = np.hypot(lm_list[8][3] - lm_list[4][3], lm_list[8][4] - lm_list[4][4]) < (hand_scale * 0.15)
                
                current_shape = detector.get_signature_shape(fingers, is_pinching)
                gesture = controller.process_gestures(lm_list, fingers, handedness, current_shape)
                
                # 6. Visual Feedback
                # Draw all finger states
                cv2.putText(img, f"Fingers: {fingers}", (w_cam - 300, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                if gesture:
                    cv2.putText(img, f"ACTION: {gesture}", (50, 100), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)

                # Color markers based on state
                idx_color = (0, 255, 0) if controller.states["pinch_index"]["active"] else (0, 0, 255)
                mid_color = (0, 255, 0) if controller.states["pinch_middle"]["active"] else (0, 0, 255)
                fist_color = (0, 255, 0) if controller.states["fist"]["active"] else (255, 255, 255)

                # Draw Index and Middle markers
                cv2.circle(img, (lm_list[8][1], lm_list[8][2]), 10, idx_color, cv2.FILLED)
                cv2.circle(img, (lm_list[12][1], lm_list[12][2]), 10, mid_color, cv2.FILLED)
                
                if controller.states["fist"]["active"]:
                     cv2.putText(img, "FIST DETECTED", (w_cam // 2 - 100, h_cam // 2), 
                                 cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)

            # 7. Display the feed
            cv2.imshow("Air Gesture Macro Controller", img)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        if cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()
        print("Resources released.")

if __name__ == "__main__":
    try:
        cam_index = 1
        if len(sys.argv) > 1:
            try:
                cam_index = int(sys.argv[1])
            except ValueError:
                print(f"Invalid camera index: {sys.argv[1]}. Using default (1).")
        
        main(cam_index)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
