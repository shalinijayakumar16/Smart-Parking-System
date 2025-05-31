import cv2
import easyocr
import numpy as np  # Fix for NameError: name 'np' is not defined

def recognize_plate(image):
    reader = easyocr.Reader(['en'])
    image = cv2.imdecode(np.frombuffer(image.read(), np.uint8), cv2.IMREAD_COLOR)
    results = reader.readtext(image)

    for (bbox, text, prob) in results:
        return text  # Return first detected plate

    return "Unknown"
