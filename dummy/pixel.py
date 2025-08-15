import cv2
from pyzbar.pyzbar import decode

# Real-world width of your QR code
KNOWN_QR_WIDTH_CM = 17.0
# Distance from camera for calibration (measure with ruler/tape)
KNOWN_DISTANCE_CM = 50.0  # example: 1 meter

cap = cv2.VideoCapture(0)

print("Show the QR code at exactly", KNOWN_DISTANCE_CM, "cm from the camera...")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    decoded_objs = decode(frame)
    for obj in decoded_objs:
        (x, y, w, h) = obj.rect
        focal_length = (w * KNOWN_DISTANCE_CM) / KNOWN_QR_WIDTH_CM
        print(f"QR pixel width: {w}, Focal length: {focal_length:.2f}")
        cap.release()
        cv2.destroyAllWindows()
        exit()

    cv2.imshow("Calibration", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
