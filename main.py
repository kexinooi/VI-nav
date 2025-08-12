import cv2
from pyzbar.pyzbar import decode
from indoor_navigation.indoorNav import dijkstra, find_edge_instruction
from audio_module.audio import speak, speak_instructions
from colored_qr_detector import detect_color
import speech_recognition as sr
import json
import difflib

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

def detect_any_color(frame):
    for color in ['red', 'green', 'blue']:
        filtered = detect_color(frame, color)
        gray = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
        decoded_objs = decode(gray)
        if decoded_objs:
            return decoded_objs
    # Fallback to normal grayscale decoding
    decoded_objs = decode(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
    return decoded_objs

def recognize_speech(prompt=None):
    r = sr.Recognizer()
    mic = sr.Microphone()

    if prompt:
        speak(prompt)
        print(prompt)

    with mic as source:
        r.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=4)
        except sr.WaitTimeoutError:
            speak("Listening timed out, please try again.")
            return None

    try:
        text = r.recognize_google(audio).lower()
        print(f"Recognized speech: {text}")

        # Convert word to digit if possible
        if text in word_to_digit:
            text = word_to_digit[text]
            print(f"Converted '{text}' to digit '{text}'")

        return text

    except sr.UnknownValueError:
        speak("Sorry, I did not catch that. Please speak clearly and try again.")
        return None
    except sr.RequestError:
        speak("Could not request results; check your internet connection.")
        return None

def scan_current_position(cap):
    speak("Please rotate the camera to scan the nearest QR code.")
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        decoded_objs = detect_any_color(frame)

        for obj in decoded_objs:
            scanned_node = obj.data.decode('utf-8').strip().upper()
            if scanned_node in graph['nodes']:
                speak(f"Location detected: node {scanned_node}")
                print(scanned_node)
                return scanned_node

        cv2.imshow("Scan Current Position", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            speak("Quitting.")
            exit()

def match_room_spoken(room_spoken, room_list):
    matches = difflib.get_close_matches(room_spoken, room_list, n=1, cutoff=0.6)
    return matches[0] if matches else None

def get_destination_node():
    speak("Where do you want to go? Please say your destination room number now.")
    while True:
        room_spoken = recognize_speech()
        if room_spoken:
            response = room_spoken.lower()
            matched_room = match_room_spoken(response, room_to_node.keys())
            if matched_room:
                node = room_to_node[matched_room]
                speak(f"Destination set to {matched_room}.")
                return node
            else:
                speak("Room not recognized. Please say again.")
        else:
            speak("I didn't catch that. Please say again.")

def get_user_action():
    speak("Say 'nearest' to scan nearest QR code or 'destination' to say where you want to go.")
    while True:
        response = recognize_speech()
        if response is None:
            continue
        response = response.lower()
        if "nearest" in response or response == "1":
            return "nearest"
        elif "destination" in response or response == "2":
            return "destination"
        else:
            speak("I didn't get that. Please say 'nearest' or 'destination'.")

def scan_qr_code_from_webcam(cap):
    speak("Please rotate the camera to scan the nearest QR code.")
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        decoded_objs = detect_any_color(frame)

        for obj in decoded_objs:
            scanned_node = obj.data.decode('utf-8').strip().upper()
            if scanned_node in graph['nodes']:
                speak(f"Location detected: node {scanned_node}")
                print(scanned_node)
                return scanned_node

        cv2.imshow("Scan Current Position", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            speak("Quitting.")
            cap.release()
            cv2.destroyAllWindows()
            exit()

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

    speak(f"Starting navigation from {start} to {end}")

    for i in range(len(path) - 1):
        current_node = path[i]
        next_node = path[i + 1]

        instructions = find_edge_instruction(graph, current_node, next_node)
        print(f"Instructions from {current_node} to {next_node}:", instructions)

        if instructions:
            speak_instructions(instructions, pause_seconds)
        else:
            speak(f"Walk from {current_node} to {next_node}")

        speak(f"Please scan the QR code at node {next_node} to continue.")

        while True:
            scanned_node = scan_qr_code_from_webcam(cap)
            if scanned_node == next_node:
                speak(f"Node {next_node} confirmed. Proceeding...")
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
        speak("Please scan the nearest QR code to locate your current position.")
        current_node = scan_current_position(cap)
        action = get_user_action()

        if action == "nearest":
            destination_node = scan_current_position(cap)
        else:
            destination_node = get_destination_node()
        
        simulate_navigation_with_audio(current_node, destination_node)

        # After finishing navigation
        speak("Navigation completed. Do you want to start another navigation? Say 'yes' to continue or 'no' to exit.")
        while True:
            answer = recognize_speech()
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
