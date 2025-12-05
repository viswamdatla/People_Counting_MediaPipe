"""
Flask backend for People Counting Dashboard.
Mirrors the exact logic from People_Counting.py
"""

from flask import Flask, jsonify, send_file
from flask_cors import CORS
import cv2
import mediapipe as mp
import threading
import time
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# MediaPipe setup (same as People_Counting.py)
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Global counter state
class CounterState:
    def __init__(self):
        self.count_in = 0
        self.count_out = 0
        self.count_inside = 0
        self.lock = threading.Lock()
        
        # Tracking state (same as People_Counting.py)
        self.prev_region = None
        self.initialized = False
        
        # Door lines (same as People_Counting.py)
        self.LEFT_LINE_X = 200
        self.RIGHT_LINE_X = 380
        
        self.is_running = False

counter_state = CounterState()

def get_region(cx, state):
    """Return OUTSIDE or INSIDE based on vertical lines."""
    if state.LEFT_LINE_X <= cx <= state.RIGHT_LINE_X:
        return "INSIDE"
    return "OUTSIDE"

def process_frame(frame, state):
    """Process a single frame exactly like People_Counting.py"""
    try:
        H, W, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)
        
        if results.pose_landmarks:
            # Get nose coordinates
            nose = results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE]
            cx = int(nose.x * W)
            cy = int(nose.y * H)
            
            region = get_region(cx, state)
            
            with state.lock:
                # FIRST DETECTION INITIALIZATION
                if not state.initialized:
                    state.prev_region = region
                    state.initialized = True
                    print(f"[INIT] First detection - Region: {region}")
                else:
                    # INTERCHANGED LOGIC (same as People_Counting.py)
                    
                    # INSIDE -> OUTSIDE = IN
                    if state.prev_region == "INSIDE" and region == "OUTSIDE":
                        state.count_in += 1
                        print(f"[IN DETECTED] Total IN: {state.count_in}, OUT: {state.count_out}, PRESENT: {state.count_in - state.count_out}")
                    
                    # OUTSIDE -> INSIDE = OUT
                    if state.prev_region == "OUTSIDE" and region == "INSIDE":
                        state.count_out += 1
                        print(f"[OUT DETECTED] Total IN: {state.count_in}, OUT: {state.count_out}, PRESENT: {state.count_in - state.count_out}")
                
                state.prev_region = region
                # Update inside count (how many people are inside right now)
                state.count_inside = 1 if region == "INSIDE" else 0
    
    except Exception as e:
        print(f"Frame processing error: {e}")

def video_processor(state):
    """Background thread to process video frames continuously."""
    try:
        cap = cv2.VideoCapture("walking.mp4")
        
        if not cap.isOpened():
            print("[ERROR] Video 'walking.mp4' could not be opened")
            print("   Current directory:", os.getcwd())
            print("   Files in directory:", os.listdir())
            state.is_running = False
            return
        
        state.is_running = True
        print("[SUCCESS] Video stream started successfully")
        print(f"   Video: walking.mp4")
        print(f"   Resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
        print(f"   FPS: {cap.get(cv2.CAP_PROP_FPS)}")
        
        frame_count = 0
        
        while state.is_running:
            ret, frame = cap.read()
            if not ret:
                # Loop the video
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            process_frame(frame, state)
            frame_count += 1
            
            # Process at ~30 FPS
            time.sleep(0.033)
        
    except Exception as e:
        print(f"Video processor error: {e}")
    finally:
        cap.release()
        state.is_running = False
        print("[SUCCESS] Video stream stopped")

@app.route('/', methods=['GET'])
def serve_dashboard():
    """Serve the main dashboard HTML."""
    return send_file('INDEX.HTML', mimetype='text/html')

@app.route('/api/counts', methods=['GET'])
def get_counts():
    """API endpoint to get current IN, OUT, and INSIDE counts."""
    # Use non-blocking lock to minimize response time
    acquired = counter_state.lock.acquire(blocking=False)
    if acquired:
        try:
            in_count = counter_state.count_in
            out_count = counter_state.count_out
            inside_count = counter_state.count_inside
        finally:
            counter_state.lock.release()
    else:
        # If lock is busy, return current values (slightly stale but faster)
        in_count = counter_state.count_in
        out_count = counter_state.count_out
        inside_count = counter_state.count_inside
    
    # Calculate present as IN - OUT (people currently inside)
    present = max(0, in_count - out_count)
    
    response = jsonify({
        'in': in_count,
        'out': out_count,
        'present': present
    })
    # Prevent caching to always get fresh data
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/reset', methods=['POST'])
def reset_counts():
    """API endpoint to reset counters."""
    with counter_state.lock:
        counter_state.count_in = 0
        counter_state.count_out = 0
        counter_state.count_inside = 0
        counter_state.initialized = False
        counter_state.prev_region = None
    
    return jsonify({
        'status': 'reset',
        'in': 0,
        'out': 0,
        'present': 0
    })

@app.route('/api/status', methods=['GET'])
def get_status():
    """API endpoint to check server status."""
    return jsonify({
        'status': 'running',
        'video_active': counter_state.is_running
    })

if __name__ == '__main__':
    # Start video processor in background thread
    processor_thread = threading.Thread(target=video_processor, args=(counter_state,), daemon=True)
    processor_thread.start()
    
    print("=" * 70)
    print("People Counting Dashboard")
    print("=" * 70)
    print("✅ Dashboard: http://localhost:8000")
    print("✅ API: http://localhost:8000/api/counts")
    print("\nAvailable endpoints:")
    print("  GET  /            - Dashboard")
    print("  GET  /api/counts  - Get IN, OUT, PRESENT counts (JSON)")
    print("  POST /api/reset   - Reset all counters")
    print("  GET  /api/status  - Check server status")
    print("=" * 70)
    print()
    
    # Run Flask server on port 8000
    app.run(debug=False, host='127.0.0.1', port=8000, threaded=True)
