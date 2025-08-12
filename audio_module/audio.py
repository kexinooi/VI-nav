import pyttsx3
import time

def speak(text):
    engine = pyttsx3.init()
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate - 50)
    engine.say(text)
    engine.runAndWait()
    engine.stop()  # make sure to stop engine after each phrase

def speak_instructions(instructions, pause_seconds=3):
    for step in instructions:
        print(f"Speaking: {step}")
        speak(step)
        time.sleep(pause_seconds)
