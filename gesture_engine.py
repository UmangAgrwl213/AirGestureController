import cv2
import mediapipe as mp
import sys

if __name__ == "__main__":
    try:
        # Check for camera ID argument
        cam_id = 1
        if len(sys.argv) > 1:
            try:
                cam_id = int(sys.argv[1])
            except ValueError:
                print(f"Invalid camera index: {sys.argv[1]}. Using default (1).")

        # 1. Initialize the Hand tracking 'brain'
        try:
            mp_hands = mp.solutions.hands
            mp_draw = mp.solutions.drawing_utils
        except AttributeError:
            print("Error: mediapipe.solutions not found. This project requires legacy MediaPipe solutions.")
            print("Please use Python 3.10/3.12 or check your MediaPipe installation.")
            input("\nPress Enter to exit...")
            exit(1)

        hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.5)

        # 2. Open the webcam
        cap = cv2.VideoCapture(cam_id)

        while True:
            success, img = cap.read()
            if not success:
                print(f"Failed to capture image from camera {cam_id}")
                break

            # AI models usually work better with RGB images, but OpenCV reads in BGR
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) 
            
            # 3. Process the frame and find hands
            results = hands.process(img_rgb)
            
            # 4. If a hand is found, draw the connections
            if results.multi_hand_landmarks:
                for hand_lms in results.multi_hand_landmarks:
                    mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)
                    
            # Display the result
            cv2.imshow("AI Hand Tracker", img)
            
            # Press 'q' to stop the program
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        input("\nPress Enter to exit...")