import cv2
from time import time
import numpy as np
from ultralytics.solutions.solutions import BaseSolution
from ultralytics.utils.plotting import Annotator, colors
from datetime import datetime
import mysql.connector
from paddleocr import PaddleOCR
import os
import torch


class SpeedEstimator(BaseSolution):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initialize_region()  # Initialize speed region
        self.spd = {}  # Dictionary to store speed data
        self.trkd_ids = []  # List for already tracked and speed-estimated IDs
        self.trk_pt = {}  # Dictionary for previous timestamps
        self.trk_pp = {}  # Dictionary for previous positions
        self.logged_ids = set()  # Set to keep track of already logged IDs

        # Initialize the OCR system
        self.ocr = PaddleOCR(use_angle_cls=True, lang='en')

        # MySQL database connection
        self.db_connection = self.connect_to_db()

    def connect_to_db(self):
        """Establish connection to MySQL database and create database/table if not exists."""
        try:
            # Connect to MySQL server
            connection = mysql.connector.connect(
                host="localhost",
                user="root",  # Replace with your MySQL username
                password="mysql@123",   # Replace with your MySQL password
                port=3306
            )
            cursor = connection.cursor()

            # Create database if it doesn't exist
            cursor.execute("CREATE DATABASE IF NOT EXISTS smart_parking")
            print("Database 'smart_parking' checked/created.")

            # Connect to the newly created or existing database
            connection.database = "smart_parking"

            # Create table if it doesn't exist
            create_table_query = """
            CREATE TABLE IF NOT EXISTS my_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATE,
                time TIME,
                track_id INT,
                class_name VARCHAR(255),
                speed FLOAT,
                numberplate TEXT
            )
            """
            cursor.execute(create_table_query)
            print("Table 'my_data' checked/created.")
            connection.commit()
            return connection
        except mysql.connector.Error as err:
            print(f"Error connecting to database: {err}")
            return None

    def perform_ocr(self, image_array):
        """Performs OCR on the given image and returns the extracted text."""
        if image_array is None:
            raise ValueError("Image is None")
        if isinstance(image_array, np.ndarray):
            results = self.ocr.ocr(image_array, rec=True)
        else:
            raise TypeError("Input image is not a valid numpy array")
        return ' '.join([result[1][0] for result in results[0]] if results[0] else "")

    def save_to_database(self, date, time, track_id, class_name, speed, numberplate):
        """Save data to the MySQL database."""
        if self.db_connection is None:
            print("Database connection not available.")
            return
        try:
            cursor = self.db_connection.cursor()
            query = """
                INSERT INTO my_data (date, time, track_id, class_name, speed, numberplate)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (date, time, track_id, class_name, speed, numberplate))
            self.db_connection.commit()
            print(f"Data saved to database: {date}, {time}, {track_id}, {class_name}, {speed}, {numberplate}")
        except mysql.connector.Error as err:
            print(f"Error saving to database: {err}")

    def estimate_speed(self, im0):
        """Estimate speed of objects and track them."""
        self.annotator = Annotator(im0, line_width=self.line_width)  # Initialize annotator
        self.extract_tracks(im0)  # Extract tracks

        # Get current date and time
        current_time = datetime.now()

        for box, track_id, cls in zip(self.boxes, self.track_ids, self.clss):
            x1, y1, x2, y2 = map(int, box)
            cropped_image = np.array(im0)[y1:y2, x1:x2]
            ocr_text = self.perform_ocr(cropped_image)

            class_name = self.names[int(cls)]
            speed = self.spd.get(track_id, 0)

            if track_id not in self.logged_ids and ocr_text.strip() and speed is not None:
                self.save_to_database(
                    current_time.strftime("%Y-%m-%d"),
                    current_time.strftime("%H:%M:%S.%f")[:-3],
                    track_id,
                    class_name,
                    speed,
                    ocr_text
                )
                self.logged_ids.add(track_id)

        self.display_output(im0)
        return im0


# Open the video file
cap = cv2.VideoCapture('tc.mp4')

region_points = [(0, 145), (1018, 145)]
# Define the correct model path
# Define the absolute path to best.pt
MODEL_PATH = r"C:\\Users\\conta\Desktop\\Raj-Learning-all\\smart-parking-system\\backend\\best.pt"


# Load YOLOv5 model correctly
model = torch.hub.load('ultralytics/yolov5', 'custom', path=MODEL_PATH, force_reload=True)


# Correct SpeedEstimator initialization
speed_obj = SpeedEstimator(
    region=region_points,
    model=model,  # Pass the loaded model
    line_width=2
)

count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    count += 1
    if count % 3 != 0:
        continue

    frame = cv2.resize(frame, (1020, 500))

    result = speed_obj.estimate_speed(frame)

    cv2.imshow("Speed Estimator", result)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
