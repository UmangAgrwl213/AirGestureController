import cv2
import json
import os
import time
import asyncio
import threading
from typing import Optional
from fastapi import FastAPI, Response, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from modules.engine import GestureEngine

app = FastAPI(title="AirGesture Professional Web")

# Setup for frontend
templates = Jinja2Templates(directory="templates")
if not os.path.exists("templates"):
    os.makedirs("templates")

# Global state
class GlobalState:
    engine: Optional[GestureEngine] = None
    event_queue = asyncio.Queue()
    last_heartbeat = time.time()
    shutdown_flag = False

state = GlobalState()

def monitor_heartbeat():
    """Background task to check if the browser is still alive."""
    while not state.shutdown_flag:
        if time.time() - state.last_heartbeat > 10: # 10 second grace period
            print("\n[!] NO_HEARTBEAT_DETECTED: Browser closed or disconnected.")
            print("[!] SHUTTING_DOWN_BIO_LINK...")
            if state.engine:
                state.engine.stop()
            state.shutdown_flag = True
            # Force exit after a small delay
            time.sleep(1)
            os._exit(0)
        time.sleep(2)

# Start heartbeat monitor
threading.Thread(target=monitor_heartbeat, daemon=True).start()

def engine_callback(message):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.call_soon_threadsafe(state.event_queue.put_nowait, message)
    except:
        pass

class ConfigModel(BaseModel):
    settings: dict
    mappings: dict

@app.get("/")
async def index(request: Request):
    state.last_heartbeat = time.time() # Reset on load
    return templates.TemplateResponse(request, "index.html")

@app.post("/heartbeat")
async def heartbeat():
    state.last_heartbeat = time.time()
    return {"status": "alive"}

@app.get("/config")
async def get_config():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            return json.load(f)
    return {"settings": {"smoothing": 7, "camera_id": 1}, "mappings": {}}

@app.post("/config")
async def save_config(config: ConfigModel):
    with open("config.json", "w") as f:
        json.dump(config.dict(), f, indent=2)
    if state.engine:
        state.engine.smoothing = config.settings.get("smoothing", 7)
    return {"status": "success"}

def gen_frames():
    while True:
        if state.engine and state.engine.running:
            frame = state.engine.get_frame()
            if frame is not None:
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            time.sleep(0.1)
        time.sleep(0.03)

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.post("/engine/toggle")
async def toggle_engine():
    if state.engine is None or not state.engine.running:
        with open("config.json", "r") as f:
            data = json.load(f)
            cam_id = data.get("settings", {}).get("camera_id", 1)
            smooth = data.get("settings", {}).get("smoothing", 7)
        state.engine = GestureEngine(camera_id=cam_id, smoothing=smooth, callback=engine_callback)
        state.engine.start()
        return {"status": "started"}
    else:
        state.engine.stop()
        state.engine = None
        return {"status": "stopped"}

@app.get("/events")
async def event_stream():
    async def event_generator():
        while True:
            message = await state.event_queue.get()
            yield f"data: {message}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
