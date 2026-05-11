from flask import Flask, render_template, Response, jsonify, request
import cv2
import json
import os
import time
from modules.hand_tracking import HandDetector
from modules.controller import SystemController

app = Flask(__name__)

# Initialize detector and controller
detector = HandDetector(detection_con=0.8, track_con=0.8)
controller = None # Will be initialized per camera feed

def gen_frames(cam_id=1):
    global controller
    print(f"Attempting to open camera {cam_id}...")
    cap = cv2.VideoCapture(cam_id)
    
    if not cap.isOpened():
        print(f"Error: Could not open camera {cam_id}")
        return

    w_cam = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h_cam = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Camera opened: {w_cam}x{h_cam}")
    
    if controller is None:
        controller = SystemController(frame_width=w_cam, frame_height=h_cam)

    try:
        while True:
            success, frame = cap.read()
            if not success:
                print("Failed to read frame from camera")
                break
            
            # Process frame
            controller.load_config() 
            frame = detector.find_hands(frame)
            lm_list = detector.find_position(frame, draw=False)
            fingers = detector.fingers_up()
            
            if lm_list:
                controller.move_mouse(lm_list[8][1], lm_list[8][2])
                controller.process_gestures(lm_list, fingers)

            # Encode for streaming
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        cap.release()
        print("Camera released.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_config')
def get_config():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            return jsonify(json.load(f))
    return jsonify({"mappings": {}})

@app.route('/update_config', methods=['POST'])
def update_config():
    new_config = request.json
    with open("config.json", "w") as f:
        json.dump(new_config, f, indent=2)
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
