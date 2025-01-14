import sys
import os
import sys
import socket
module_dir = os.path.dirname(__file__)
module_path = os.path.join(module_dir, '../../../Utils')
sys.path.append(module_path)
from constants import SERVER_IP, SERVER_PORT_FTB
import json
import speech_recognition as sr
import threading
import time
import sys
from phonetic_comparison import dynamic_phonetic_comparision
from pydub import AudioSegment
from pydub.effects import normalize
import keyboard

class FillTheBlanks:
    def __init__(self):
        self.__thread_list = []
        self.__client_socket = None
        self.__recognizer = sr.Recognizer()  
        self.__text = "With ___, ___, and ___ now found, let magic turn this stone around!"
        self.__missing_words = ["coin", "fire", "emerald"]
    
    def __manage_thread(self):
        for t in self.__thread_list:
            t.join()

    def __listening_animation(self, stop_event, timeout):
        animation = "|/-\\"
        idx = 0
        while timeout > 0 and not stop_event.is_set():
            sys.stdout.write(f"\rListening...({timeout}) {animation[idx % len(animation)]}")
            sys.stdout.flush()
            idx += 1
            if idx % 10 == 0:
                timeout -= 1
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * 30 + "\r")

    def __preprocess_audio(self, audio_data):
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

    def __recognize_speech(self, timeout=100):
        stop_event = threading.Event()
        animation_thread = threading.Thread(target=self.__listening_animation, args=(stop_event, timeout))
        animation_thread.start()

        audio = None
        def listen():
            nonlocal audio
            with sr.Microphone() as source:
                self.__recognizer.adjust_for_ambient_noise(source)
                try:
                    audio = self.__recognizer.listen(source, timeout=timeout)
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
        preprocessed_audio = self.__preprocess_audio(audio)
        
        # Save the preprocessed audio to a temporary file
        preprocessed_audio.export("temp.wav", format="wav")
        
        # Load the preprocessed audio for recognition
        with sr.AudioFile("temp.wav") as source:
            audio = self.__recognizer.record(source)

        try:
            word = self.__recognizer.recognize_google(audio)
            print(f"\nYou said: {word}")
            return word.lower()
        except sr.UnknownValueError:
            print("\nSorry, I didn't get that")
            return "None"
        except sr.RequestError as e:
            print(f"\nSorry, I couldn't request results; {e}")
            return "None"

    def __send_data(self, word, error):

        payload = {
            "word": word,
            "error": error
        }

        data = json.dumps(payload).encode('utf-8')

        if len(data) <= 65507:
            self.__client_socket.sendto(data, (SERVER_IP, SERVER_PORT_FTB))
        else:
            print("Data size exceeds the maximum allowed size for a UDP packet.")

    def start(self):
        self.__client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__client_socket.settimeout(1)

        running = True

        # while True:
        #     user_word = self.__recognize_speech()
        #     if user_word is "None":
        #         self.__send_data("", True)
        #         continue
        #     if user_word is None:
        #         continue
        #     self.__send_data(user_word, False)
        #     print(user_word)


        while running:
            try:
                print("Listening...")
                self.__client_socket.sendto("Running...".encode(), (SERVER_IP, SERVER_PORT_FTB))
                data, (_, _) = self.__client_socket.recvfrom(1024)
                if data.decode() == "start":
                    user_word = self.__recognize_speech()
                    if user_word is "None":
                        self.__send_data("", True)
                        continue
                    if user_word is None:
                        continue
                    self.__send_data(user_word, False)
                    print(user_word)
                if data.decode() == "stop":
                    running = False
            except ConnectionResetError:
                pass
            except socket.timeout:
                pass
        
        self.__client_socket.close()
        self.__manage_thread()
        sys.exit()


game = FillTheBlanks()
game.start()