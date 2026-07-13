# AI-Smart-Road-Assistant
Final year project: AI-based object detection and voice guidance for the visually impaired
![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.0+-green.svg)
![Flask](https://img.shields.io/badge/Flask-Web_Framework-lightgrey.svg)

The AI Smart Road Assistant uses your laptop's camera to read the road ahead, calculate distances using YOLOv3, and provide instant audio nudges to help visually impaired individuals navigate their surroundings safely.

## 🔗 Install

Make sure you have Python installed, then run the following in your terminal:

```bash
# Install required libraries
pip install flask opencv-python numpy pywin32
**Important Note:** The yolov3.weights file is too large to host on GitHub. Please download it from the official YOLO source and place it in the root directory next to app.py.

## 🔗 First run
1.Ensure your laptop webcam is uncovered and active.
2.Open your terminal and run the server:
python app.py
3.Open your web browser and navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000).
4.Click Start System on the secure login page.

## 🔗 Features
1.Real-time Object Detection: Identifies people, cars, traffic lights, and more using YOLOv3.
2.Audio Guidance: Nudges the user with directional audio (e.g., "Car 5 meters ahead, move right").
3.Traffic Light Recognition: Specifically tailored to read red/green signal colors for safe street crossing.
4.Fully Local: Everything runs 100% offline on your machine—no internet connection required after setup.

## 🔗 Dashboard Controls
**Button       Description**
System Info :Triggers an audio breakdown of the system's capabilities.
Pause System:Temporarily halts the camera feed and audio alerts.
Stop System :Safely shuts down the camera and returns you to the login screen.

## 🔗 How it works
The system captures frames via OpenCV and passes them through a pre-trained YOLOv3 neural network. By calculating the bounding box (bw, bh) of detected objects against the frame width, the AI estimates distance and trajectory, converting that data into speech via the Windows SAPI voice engine.

🔗 License
This project is licensed under the MIT License.
