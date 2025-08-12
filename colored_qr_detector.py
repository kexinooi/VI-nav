import cv2
import numpy as np
from pyzbar.pyzbar import decode

def detect_red(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 70, 50])
    upper_red2 = np.array([180, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)
    result = cv2.bitwise_and(image, image, mask=mask)
    return result

def detect_green(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_green = np.array([36, 50, 50])
    upper_green = np.array([89, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)
    result = cv2.bitwise_and(image, image, mask=mask)
    return result

def detect_blue(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([90, 50, 50])
    upper_blue = np.array([130, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    result = cv2.bitwise_and(image, image, mask=mask)
    return result

def detect_color(image, color):
    color = color.lower()
    if color == "red":
        return detect_red(image)
    elif color == "green":
        return detect_green(image)
    elif color == "blue":
        return detect_blue(image)
    elif color == "all":
        red = detect_red(image)
        green = detect_green(image)
        blue = detect_blue(image)
        combined = cv2.bitwise_or(cv2.bitwise_or(red, green), blue)
        return combined
    else:
        raise ValueError(f"Unsupported color: {color}")

