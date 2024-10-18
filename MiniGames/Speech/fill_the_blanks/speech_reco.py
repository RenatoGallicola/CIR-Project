import sys
import time
import threading
import speech_recognition as sr

# Animation function with countdown and spinning animation
def listening_animation(stop_event, timeout):
    animation = "|/-\\"
    idx = 0
    while timeout > 0 and not stop_event.is_set():
        sys.stdout.write(f"\rListening...({timeout}) {animation[idx % len(animation)]}")
        sys.stdout.flush()
        idx += 1
        if idx % 10 == 0:
            timeout -= 1
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * 30 + "\r")  # Clear the line

def recognize_speech(timeout=10):
    stop_event = threading.Event()
    animation_thread = threading.Thread(target=listening_animation, args=(stop_event, timeout))
    animation_thread.start()
    
    recognizer = sr.Recognizer()
    audio = None

    def listen():
        nonlocal audio
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            try:
                audio = recognizer.listen(source, timeout=timeout)
            except sr.WaitTimeoutError:
                pass

    listen_thread = threading.Thread(target=listen)
    listen_thread.start()
    listen_thread.join(timeout=timeout)

    stop_event.set()
    animation_thread.join()

    if listen_thread.is_alive():
        print("\nListening timed out while waiting for phrase to start")
        return None

    if audio is None:
        print("\nSorry, I didn't get that")
        return None

    try:
        word = recognizer.recognize_google(audio)
        print(f"\nYou said: {word}")
        return word.lower()
    except sr.UnknownValueError:
        print("\nSorry, I didn't get that")
        return None
    except sr.RequestError as e:
        print(f"\nSorry, I couldn't request results; {e}")
        return None