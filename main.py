import cv2
import json
import difflib
import time
from vosk import Model, KaldiRecognizer
import pyaudio
from collections import deque
from pyzbar.pyzbar import decode
from indoor_navigation.indoorNav import dijkstra, find_edge_instruction
from audio_module.audio import speak, speak_instructions
from colored_qr_detector import detect_color
import speech_recognition as sr

# Example calibration: adjust for your camera
KNOWN_QR_WIDTH_CM = 15.0   # real-world QR code size
FOCAL_LENGTH = 508.82        # measured once using calibration

with open('hallway_graph.json') as f:
    graph = json.load(f)
    
adjacency = {}
for edge in graph['edges']:
    adjacency.setdefault(edge['from'], []).append((
        edge['to'],
        edge['weight'],
        edge.get('instruction', [])
    ))

room_to_node = {
    "1": "O",
    "2": "N",
    "3": "M",
    "Staircase 2": "L",
    "4": "K",
    "5": "J",
    "6": "I",
    "7": "H",
    "8": "G",
    "Washroom": "F",
    "9": "E",
    "10": "D",
    "11": "C",
    "12": "B",
    "Staircase 1": "A",
}

word_to_digit = {
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
    "eleven": "11",
    "twelve": "12",
}

def normalize_key(key):
    return key.strip().lower()

def detect_any_color(frame, target_color=None):
    """
    Detect QR codes in a specific color or in all preset colors.
    :param frame: Image frame from webcam
    :param target_color: 'red', 'green', 'blue', or None for all colors
    :return: List of tuples (decoded_object, bounding_box)
    """
    colors_to_check = [target_color] if target_color else ['red', 'green', 'blue']
    all_results = []

    # ✅ Color-based detection
    for color in colors_to_check:
        filtered = detect_color(frame, color)  # Filter by this color
        gray = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
        decoded_objs = decode(gray)

        for obj in decoded_objs:
            all_results.append((obj, obj.rect))  # store QR + bounding box

    # ✅ Fallback to normal grayscale detection (no color filter)
    if not target_color:
        gray_full = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        decoded_objs = decode(gray_full)
        for obj in decoded_objs:
            all_results.append((obj, obj.rect))

    return all_results

def recognize_speech_vosk(prompt=None):
    if prompt:
        speak(prompt)
        print(prompt)

    # Load Vosk model
    model = Model("model")  # folder with vosk model files
    recognizer = KaldiRecognizer(model, 16000)

    # Open microphone
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                    input=True, frames_per_buffer=8000)
    stream.start_stream()

    print("Listening...")
    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "").lower()
            print("Heard:", text)
            return text

def estimate_distance(bbox_width_px):
    # Simple pinhole camera model
    return (KNOWN_QR_WIDTH_CM * FOCAL_LENGTH) / bbox_width_px / 100  # meters

def scan_current_nearest_specific_color(cap, color=None):
    if color:
        speak(f"Rotate the camera slowly to search for the {color} QR code.")
    else:
        speak("Rotate the camera slowly to search for the nearest QR code.")

    last_seen_node = None
    last_speak_time = 0
    distance_history = deque(maxlen=5)

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        decoded_objs = detect_any_color(frame, color)
        if not decoded_objs:
            cv2.imshow("Scan Current Position", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                speak("Quitting.")
                exit()
            continue

        # Select nearest by width
        nearest_obj, rect = max(decoded_objs, key=lambda x: x[1][2])
        scanned_node = nearest_obj.data.decode('utf-8').strip().upper()
        x, y, w, h = rect
        center_x = x + w // 2
        frame_center = frame.shape[1] // 2

        # Draw bounding box for feedback
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
        cv2.putText(frame, scanned_node, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.9, (0, 255, 255), 2)

        distance = estimate_distance(w)
        distance_history.append(distance)
        avg_distance = sum(distance_history) / len(distance_history)

        if scanned_node != last_seen_node:
            speak(f"QR code detected: {scanned_node}")
            last_seen_node = scanned_node

        now = time.time()
        if now - last_speak_time > 1.0:
            if avg_distance <= 0.9:
                if scanned_node in graph['nodes']:
                    location = graph['nodes'][scanned_node]['name']
                    speak(f"Location confirmed: {location}")
                    print(f"Navigating to {location} ({scanned_node})")
                    return scanned_node
            elif avg_distance > 1.1:
                if center_x < frame_center - 50:
                    speak("Move camera to the left.")
                elif center_x > frame_center + 50:
                    speak("Move camera to the right.")
                else:
                    speak("QR code ahead.")
                speak(f"Approximately {avg_distance:.1f} meters away.")

            last_speak_time = now

        cv2.imshow("Scan Current Position", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            speak("Quitting.")
            exit()

def set_colored_qr_action():
    speak("Say 'red' to set QR code in red, 'green' to set QR code in green, or 'blue' to set QR code in blue.")

    while True:
        response = recognize_speech_vosk()
        if not response:
            continue

        response = response.lower().strip()

        if "red" in response or response == "1":
            return "red"
        elif "blue" in response or response == "2":
            return "blue"
        elif "green" in response or response == "3":
            return "green"
        else:
            speak("I didn't get that. Please say 'red', 'green', or 'blue'.")

def match_room_spoken(room_spoken, room_list):
    matches = difflib.get_close_matches(room_spoken, room_list, n=1, cutoff=0.6)
    return matches[0] if matches else None

def get_destination_node():
    speak("Where do you want to go? Please say a number from one to twelve or the location name.")
    while True:
        room_spoken = recognize_speech_vosk()
        if room_spoken:
            response = room_spoken.lower().strip()
            print("Heard:", response)

            # Convert word numbers to digits if possible
            if response in word_to_digit:
                response = word_to_digit[response]

            # Check direct match in room_to_node
            if response in room_to_node:
                node = room_to_node[response]
                if node in graph['nodes']:
                    destination_location = graph['nodes'][node]['name']
                    speak(f"Destination set to {destination_location}.")
                    return node
                else:
                    speak("That location is not in the map.")

            # Try partial match (for phrases like "go to room five")
            else:
                for word, digit in word_to_digit.items():
                    if word in response:
                        response = digit
                        break
                if response in room_to_node:
                    node = room_to_node[response]
                    destination_location = graph['nodes'][node]['name']
                    speak(f"Destination set to {destination_location}.")
                    return node
                else:
                    speak("Room not recognized. Please say again.")
        else:
            speak("I didn't catch that. Please say again.")


def get_user_action():
    speak("Say one to find a destination or two to scan a desired colroed QR code or three to locate current position")
    action = recognize_speech_vosk()

    if action == "one":
        return ("one") 
    elif action == "two":
        return ("two") 
    else:
        speak("No valid option selected. Please try again.")
        return get_user_action()

def simulate_navigation_with_audio(start, end, pause_seconds=3):
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # open webcam once

    # Compute the shortest path using Dijkstra's algorithm
    path = dijkstra(adjacency, start, end)
    print("Computed path:", path)

    if not path:
        speak("No path found!")
        cap.release()
        cv2.destroyAllWindows()
        return

    oriRoom = graph['nodes'][start]['name']
    destRoom = graph['nodes'][end]['name']
    speak(f"Starting navigation from {oriRoom} to {destRoom}")

    for i in range(len(path) - 1):
        current_node = path[i]
        next_node = path[i + 1]
        
        curRoom = graph['nodes'][current_node]['name']
        nextRoom = graph['nodes'][next_node]['name']
        
        instructions = find_edge_instruction(graph, current_node, next_node)
        print(f"Instructions from {curRoom} to {nextRoom}:", instructions)

        if instructions:
            speak_instructions(instructions, pause_seconds)
        else:
            speak(f"Walk from {curRoom} to {nextRoom}")

        speak(f"Please scan the QR code at node {nextRoom} to continue.")

        while True:
            scanned_node = scan_current_nearest_specific_color(cap)
            if scanned_node == next_node:
                speak(f"Node {nextRoom} confirmed. Proceeding...")
                break
            else:
                speak("Scanned node does not match. Please scan the correct QR code.")

    speak("You have arrived at your destination!")
    
def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        speak("Cannot open webcam.")
        return

    while True:
        speak("Please scan the QR code to locate your current position.")
        current_node = scan_current_nearest_specific_color(cap)
        action = get_user_action()

        if action == "one":
            destination_node = get_destination_node()
            simulate_navigation_with_audio(current_node, destination_node)
        elif action == "two":
            destination_node = scan_current_nearest_specific_color(cap, set_colored_qr_action())

        # After finishing navigation
        speak("Navigation completed. Do you want to start another navigation? Say 'yes' to continue or 'no' to exit.")
        while True:
            answer = recognize_speech_vosk()
            if answer is None:
                continue
            answer = answer.lower()
            if "yes" in answer:
                break  # Continue loop for another navigation
            elif "no" in answer:
                speak("Goodbye!")
                cap.release()
                cv2.destroyAllWindows()
                return
            else:
                speak("Please say 'yes' or 'no'.")

if __name__ == "__main__":
    main()
