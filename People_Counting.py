import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


cap = cv2.VideoCapture("walking.mp4")


LEFT_LINE_X = 200
RIGHT_LINE_X = 380


prev_region = None
initialized = False   

count_in = 0
count_out = 0

def get_region(cx):
    if LEFT_LINE_X <= cx <= RIGHT_LINE_X:
        return "INSIDE"
    return "OUTSIDE"

while True:
    ret, frame = cap.read()
    if not ret:
        break


    H, W, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb)

    if results.pose_landmarks:
        
        nose = results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE]
        cx = int(nose.x * W)
        cy = int(nose.y * H)

        
        cv2.circle(frame, (cx, cy), 7, (0,255,0), -1)

        region = get_region(cx)

        
        if not initialized:
            prev_region = region
            initialized = True
        else:
            
            if prev_region == "INSIDE" and region == "OUTSIDE":
                count_in += 1
                print("IN detected →", count_in)

            if prev_region == "OUTSIDE" and region == "INSIDE":
                count_out += 1
                print("OUT detected →", count_out)

        prev_region = region

    
    cv2.line(frame, (LEFT_LINE_X, 0), (LEFT_LINE_X, H), (0,0,255), 3)
    cv2.line(frame, (RIGHT_LINE_X, 0), (RIGHT_LINE_X, H), (0,0,255), 3)

    
    cv2.putText(frame, f"IN: {count_in}", (30, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 3)
    cv2.putText(frame, f"OUT: {count_out}", (30, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255), 3)

    cv2.imshow("Nose Tracking IN/OUT Counter", frame)


    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC pressed
        break


    if cv2.getWindowProperty("Nose Tracking IN/OUT Counter", cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
cv2.destroyAllWindows()


