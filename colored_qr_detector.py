import cv2
import numpy as np

COLOR_RANGES = {
    "red": [
        (np.array([0, 70, 50]), np.array([10, 255, 255])),
        (np.array([170, 70, 50]), np.array([180, 255, 255]))
    ],
    "green": [
        (np.array([36, 50, 50]), np.array([89, 255, 255]))
    ],
    "blue": [
        (np.array([90, 50, 50]), np.array([130, 255, 255]))
    ]
}

def detect_color(image, color):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    color = color.lower()

    if color not in COLOR_RANGES and color != "all":
        raise ValueError(f"Unsupported color: {color}")

    mask = None
    if color == "all":
        for ranges in COLOR_RANGES.values():
            for lower, upper in ranges:
                current_mask = cv2.inRange(hsv, lower, upper)
                mask = current_mask if mask is None else cv2.bitwise_or(mask, current_mask)
    else:
        for lower, upper in COLOR_RANGES[color]:
            current_mask = cv2.inRange(hsv, lower, upper)
            mask = current_mask if mask is None else cv2.bitwise_or(mask, current_mask)

    result = cv2.bitwise_and(image, image, mask=mask)
    return result
