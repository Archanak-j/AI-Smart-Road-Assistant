import cv2
import numpy as np
import time
import win32com.client
from flask import Flask, render_template, Response, jsonify, request, redirect, url_for, session

app = Flask(__name__)
# Secret key is required to use Flask sessions securely
app.secret_key = "smart_road_assistant_super_secret" 

# Global variables to handle the buttons from the web page
paused = False
show_about = False
speaker = win32com.client.Dispatch("SAPI.SpVoice")

def speak(text):
    speaker.Speak(text, 1) # 1 means async, prevents freezing

def stop_speak():
    speaker.Speak("", 3)

# Load your exact YOLO setup
net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
with open("coco.names", "r") as f:
    classes = [line.strip().lower() for line in f.readlines()]
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

TARGET_MAP = {"person":"Person","bicycle":"Bicycle","car":"Car","motorbike":"Motorbike","aeroplane":"Aeroplane","bus":"Bus","train":"Train",
              "truck":"Truck","boat":"Boat","traffic light":"Signal","fire hydrant":"Fire Hydrant","stop sign":"Stop Sign",
              "parking meter":"Parking Meter","bench":"Bench","bird":"Bird","cat":"Cat","dog":"Dog","horse":"Horse","sheep":"Sheep",
              "cow":"Cow","elephant":"Elephant","bear":"Bear","zebra":"Zebra","giraffe":"Giraffe","chair":"Chair",
              "pottedplant":"PottedPlant","toilet":"Toilet"}

def generate_frames():
    global paused, show_about
    cap = cv2.VideoCapture(0)
    last_voice_time = 0
    last_alert_text = ""

    speak("Smart road assistant start. System starting.")

    try:
        while True:
            success, frame = cap.read()
            if not success:
                break
            
            h, w = frame.shape[:2]

            if paused:
                # Draw Pause Screen
                (text_w, text_h), _ = cv2.getTextSize("PAUSED", cv2.FONT_HERSHEY_DUPLEX, 1.2, 2)
                cv2.putText(frame, "PAUSED", (w//2 - text_w//2, h//2), cv2.FONT_HERSHEY_DUPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                continue

            # ==========================================
            # EXACT ORIGINAL FAST DETECTION BLOCK 
            # ==========================================
            blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416))
            net.setInput(blob)
            outs = net.forward(output_layers)

            boxes, confidences, class_ids = [], [], []

            for out in outs:
                for det in out:
                    scores = det[5:]
                    cid = np.argmax(scores)
                    conf = scores[cid]

                    if conf > 0.20 and classes[cid] in TARGET_MAP:
                        cx, cy = int(det[0]*w), int(det[1]*h)
                        bw, bh = int(det[2]*w), int(det[3]*h)

                        boxes.append([int(cx-bw/2), int(cy-bh/2), bw, bh])
                        confidences.append(float(conf))
                        class_ids.append(cid)

            indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.4, 0.3)
            current_alerts = []

            if len(indices) > 0:
                for i in indices.flatten():
                    x,y,bw,bh = boxes[i]
                    label = classes[class_ids[i]]

                    cv2.rectangle(frame,(x,y),(x+bw,y+bh),(0,255,0),2)
                    cv2.putText(frame,label,(x,y-10),0,0.5,(0,255,0),2)

                    # SIGNAL COLOR
                    if label == "traffic light":
                        roi = frame[max(0,y):y+bh, max(0,x):x+bw]
                        if roi.size > 0:
                            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                            red = cv2.inRange(hsv,(0,120,120),(10,255,255)) + cv2.inRange(hsv,(170,120,120),(180,255,255))
                            green = cv2.inRange(hsv,(40,100,100),(90,255,255))
                            yellow = cv2.inRange(hsv,(15,120,120),(35,255,255))

                            if np.sum(red) > 400:
                                current_alerts.append("Signal Red Move")
                            elif np.sum(green) > 400:
                                current_alerts.append("Signal Green Stop")
                    
                    cx_center = x + (bw/2)

                    if cx_center < w/3:
                        direction = "left,move right"
                    elif cx_center > 2*w/3:
                        direction = "right,move left"
                    else:
                        direction = "ahead ,watchout"

                    distance = int(1000/(bh+1))
                    current_alerts.append(f"{label}  {distance} meter {direction}")

            # WALL DETECTION
            gray_wall = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges_wall = cv2.Canny(gray_wall, 80, 200)
            density_wall = np.sum(edges_wall) / (h * w)

            if density_wall > 0.12:
                current_alerts.append("Wall ahead")
                
            alert_text=". ".join(current_alerts[:2])

            if current_alerts and alert_text != last_alert_text and (time.time() - last_voice_time > 2):
                speak(alert_text)
                last_voice_time = time.time()
                last_alert_text = alert_text

            # Draw About Info panel directly on frame if requested
            if show_about:
                box_w, box_h = int(w * 0.90), int(h * 0.65)
                x1, y1 = (w - box_w) // 2, (h - box_h) // 2 - 30 
                x2, y2 = x1 + box_w, y1 + box_h
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), (30, 25, 25), -1)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (60, 60, 60), 2)
                cv2.putText(frame, "SYSTEM INFORMATION", (x1 + 25, y1 + 40), cv2.FONT_HERSHEY_DUPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
                
                lines = ["1. This system Uses YOLO Object Detection", "2. It Detects person, vehicles, traffic light, animals",
                         "3. It Calculates distance using object size", "4. It Gives voice guidance",
                         "5. It Helps visually impaired navigation", "6. It Uses computer vision and AI"]
                y_ptr = y1 + 90
                for line in lines:
                    cv2.putText(frame, line, (x1 + 25, y_ptr), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)
                    y_ptr += 35

            # Send frame to the website
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
    finally:
        # This guarantees the webcam light turns off immediately when you click Stop System
        cap.release()

# ==========================================
# FLASK WEB ROUTES
# ==========================================

# LOGIN/START SYSTEM
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Instantly grant access when the START button is clicked
        session['logged_in'] = True
        return redirect(url_for('index'))
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Remove the user from the session and send them back to the start page
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# MAIN PAGE (Protected)
@app.route('/')
def index():
    # If the user hasn't clicked START, send them to the start page
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/toggle_pause', methods=['POST'])
def toggle_pause():
    global paused
    paused = not paused
    speak("System paused." if paused else "System resumed.")
    return jsonify({"status": "success", "paused": paused})

@app.route('/toggle_about', methods=['POST'])
def toggle_about():
    global show_about
    show_about = not show_about
    if show_about:
        speak("Showing system information. This system Uses YOLO Object Detection. It Detects person, vehicles, traffic light, animals. It Calculates distance using object size. It Gives voice guidance. It Helps visually impaired navigation. It Uses computer vision and AI.")
    else:
        stop_speak()
    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)