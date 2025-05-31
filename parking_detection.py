import cv2
import torch
import matplotlib.pyplot as plt

print(cv2.__version__)
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

PARKING_SLOTS = [
    (100, 200, 80, 150),
    (200, 200, 80, 150),
    (300, 200, 80, 150),
    (400, 200, 80, 150),
    (500, 200, 80, 150)
]

def detect_parking_slots():
    cap = cv2.VideoCapture('carPark.mp4')  # Load video

    plt.figure()  # Initialize Matplotlib window

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        occupied_slots = []
        for *box, conf, cls in results.xyxy[0]:
            if conf > 0.5 and int(cls) == 2:
                x1, y1, x2, y2 = map(int, box)
                occupied_slots.append((x1, y1, x2, y2))

        parking_status = {}
        for i, (x, y, w, h) in enumerate(PARKING_SLOTS):
            slot_status = "Available"
            for car in occupied_slots:
                car_x1, car_y1, car_x2, car_y2 = car
                if (x < car_x2 and x + w > car_x1) and (y < car_y2 and y + h > car_y1):
                    slot_status = "Occupied"
                    break

            parking_status[f"Slot {i+1}"] = slot_status
            color = (0, 255, 0) if slot_status == "Available" else (0, 0, 255)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, f"Slot {i+1} - {slot_status}", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        cv2.imshow("Parking Slot Detection", frame)
        cv2.waitKey(1)  # Process events properly

        # Display using Matplotlib in a continuous loop
        #plt.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        #plt.axis("off")
        #plt.draw()
        #plt.pause(0.01)  # Allow Matplotlib to update dynamically
        #plt.clf()  # Clear figure for the next frame

    cap.release()
    plt.close()  # Close Matplotlib window when done

detect_parking_slots()
