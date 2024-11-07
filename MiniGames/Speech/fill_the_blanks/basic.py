import speech_recognition as sr
import threading
import time
import sys
from phonetic_comparison import dynamic_phonetic_comparision
from pydub import AudioSegment
from pydub.effects import normalize

recognizer = sr.Recognizer()

text = "The quick brown ___ jumps over the lazy ___."
missing_words = ["fox", "dog"]

print("Fill in the blanks in the following text:")
print(text)

# Animation function
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

def preprocess_audio(audio_data):
    audio_segment = AudioSegment(
        data=audio_data.get_wav_data(),
        sample_width=audio_data.sample_width,
        frame_rate=audio_data.sample_rate,
        channels=1
    )
    
    # Normalize the audio
    audio_segment = normalize(audio_segment)
    
    # Apply bandpass filter
    audio_segment = audio_segment.low_pass_filter(3400).high_pass_filter(300)
    
    return audio_segment

def recognize_speech(timeout=10):
    stop_event = threading.Event()
    animation_thread = threading.Thread(target=listening_animation, args=(stop_event, timeout))
    animation_thread.start()
    
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
        print("\nSorry, there was an issue with the audio")
        return None

    # Preprocess the audio
    preprocessed_audio = preprocess_audio(audio)
    
    # Save the preprocessed audio to a temporary file
    preprocessed_audio.export("temp.wav", format="wav")
    
    # Load the preprocessed audio for recognition
    with sr.AudioFile("temp.wav") as source:
        audio = recognizer.record(source)

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
        if user_word is None:
            print("Please try again")
            continue
        confirm = input(f"Did you say '{user_word}'? (yes/no): ")
        if confirm.lower() == "yes":
            if user_word == correct_word or dynamic_phonetic_comparision(user_word, correct_word):
                print("Correct!")
                text = text.replace("___", correct_word, 1)
                print(text)
                break
            else:
                print("Incorrect, try again.")

print("Congratulations! You've completed the text.")
print("Final text:", text)