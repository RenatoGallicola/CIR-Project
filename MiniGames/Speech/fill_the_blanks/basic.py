import speech_recognition as sr
import threading
import time
import sys

recognizer = sr.Recognizer()

text = "The quick brown ___ jumps over the lazy ___."
missing_words = ["fox", "dog"]

print("Fill in the blanks in the following text:")
print(text)

# Animation function
def listening_animation(stop_event):
    animation = "|/-\\"
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write("\rListening... " + animation[idx % len(animation)])
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * 20 + "\r")  # Clear the line

def recognize_speech():
    stop_event = threading.Event()
    animation_thread = threading.Thread(target=listening_animation, args=(stop_event,))
    animation_thread.start()
    
    with sr.Microphone() as source:
        try:
            audio = recognizer.listen(source, timeout=5)
            print("Audio captured")
        except sr.WaitTimeoutError:
            stop_event.set()
            animation_thread.join()
            print("\nListening timed out while waiting for phrase to start")
            return -1
        stop_event.set()
        animation_thread.join()
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
        

for i, correct_word in enumerate(missing_words):
    while True:
        user_word = recognize_speech()
        if user_word == -1:
            # Timeout, stop the game and wait for user to manually continue
            print("Time's up! Do you want to retry? (yes/no)")
            retry = input()
            if retry.lower() == "yes":
                break
            else:
                sys.exit(0)
        if user_word is None:
            print("Please try again")
            continue
        confirm = input(f"Did you say {user_word}? (yes/no): ")
        if confirm.lower() == "yes":
            if user_word == correct_word:
                print("Correct!")
                text = text.replace("___", correct_word, 1)
                print(text)
                break
            else:
                print("Incorrect, try again.")

print("Congratulations! You've completed the text.")
print("Final text:", text)