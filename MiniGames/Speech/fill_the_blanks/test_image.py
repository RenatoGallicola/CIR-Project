import pygame
import speech_recognition as sr
import threading
import time
import queue
import audioop
from pydub import AudioSegment
from pydub.effects import normalize
from phonetic_comparison import dynamic_phonetic_comparision
import os

class TextPanel:
    def __init__(self, x, y, width, height, color=(255, 255, 255, 200)):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.padding = 20
        
    def draw(self, screen, text, font, text_color=(0, 0, 0)):
        # Draw semi-transparent panel
        surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(surface, self.color, surface.get_rect(), border_radius=10)
        screen.blit(surface, self.rect)
        
        # Draw text
        text_surface = font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=(
            self.rect.centerx,
            self.rect.centery
        ))
        screen.blit(text_surface, text_rect)

class SpeechThread(threading.Thread):
    def __init__(self, timeout=10):
        super().__init__()
        self.timeout = timeout
        self.queue = queue.Queue()
        self.audio_queue = queue.Queue()
        self.ready_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.is_listening = False
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        
    def cleanup(self):
        self.stop_event.set()
        self.is_listening = False
        
    def run(self):
        print("[THREAD] Starting speech recognition thread")
        try:
            with sr.Microphone() as source:
                print("[THREAD] Adjusting for ambient noise")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                self.is_listening = True
                print("[THREAD] Listening for speech")
                self.ready_queue.put(True)
                self.stop_event.clear()
               
                # Thread pour la capture du niveau audio
                def audio_level_thread():
                    while not self.stop_event.is_set():
                        try:
                            data = source.stream.read(4096)
                            rms = audioop.rms(data, 2)
                            self.audio_queue.put(rms)
                            time.sleep(0.05)
                        except Exception:
                            continue
    
                level_thread = threading.Thread(target=audio_level_thread)
                level_thread.daemon = True
                level_thread.start()
    
                try:
                    print("[THREAD] Waiting for speech")
                    audio = self.recognizer.listen(source, timeout=self.timeout, phrase_time_limit=self.timeout)
                    print("[THREAD] Speech detected")
                    if self.stop_event.is_set():
                        print("[THREAD] Stopping due to event")
                        return
    
                    # Process audio
                    audio_segment = AudioSegment(
                        data=audio.get_wav_data(),
                        sample_width=audio.sample_width,
                        frame_rate=audio.sample_rate,
                        channels=1
                    )
                    audio_segment = normalize(audio_segment)
                    audio_segment = audio_segment.low_pass_filter(3400).high_pass_filter(300)
                    audio_segment.export("temp.wav", format="wav")
                    
                    with sr.AudioFile("temp.wav") as source:
                        audio = self.recognizer.record(source)
                    
                    # Try Google first
                    try:
                        print("[THREAD] Attempting Google recognition...")
                        word_google = self.recognizer.recognize_google(audio)
                        print(f"[THREAD] Google successful: {word_google}")
                        self.queue.put(("success", word_google.lower()))
                        return
                    except Exception as e:
                        print(f"[THREAD] Google recognition failed: {str(e)}")
                    
                    # Try Wit.ai second
                    try:
                        print("[THREAD] Attempting Wit.ai recognition...")
                        word_wit = self.recognizer.recognize_wit(audio, key="WRZSTAKXPTAXODU7II5ZAYBZAIRUGNMO")
                        print(f"[THREAD] Wit.ai successful: {word_wit}")
                        self.queue.put(("success", word_wit.lower()))
                        return
                    except Exception as e:
                        print(f"[THREAD] Wit.ai recognition failed: {str(e)}")
                    
                    # Try Sphinx last (offline fallback)
                    try:
                        print("[THREAD] Attempting Sphinx recognition...")
                        word_sphinx = self.recognizer.recognize_sphinx(audio)
                        print(f"[THREAD] Sphinx successful: {word_sphinx}")
                        self.queue.put(("success", word_sphinx.lower()))
                        return
                    except Exception as e:
                        print(f"[THREAD] Sphinx recognition failed: {str(e)}")
                    
                    # If all recognizers fail
                    print("[THREAD] All recognition attempts failed")
                    self.queue.put(("unknown", None))
                    
                except sr.WaitTimeoutError:
                    print("[THREAD] Timeout while listening for speech")
                    self.queue.put(("timeout", None))
                except sr.UnknownValueError:
                    print("[THREAD] Unknown value error")
                    self.queue.put(("unknown", None))
                except Exception as e:
                    print(f"[THREAD] Error occurred: {str(e)}")
                    self.queue.put(("error", str(e)))
                    
        except Exception as e:
            print(f"[THREAD] Microphone error: {str(e)}")
            self.queue.put(("error", f"Microphone error: {str(e)}"))
        finally:
            self.is_listening = False

class Game:
    def __init__(self):
        pygame.init()
        self.width = 1024  # Increased for better layout
        self.height = 768
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Speech Recognition Game")
        
        # Load images
        self.load_images()
        
        self.font = pygame.font.Font(None, 36)
        self.text = "The quick brown ___ jumps over the lazy ___."
        self.missing_words = ["fox", "dog"]
        self.current_word_index = 0
        
        # Create panels
        self.main_panel = TextPanel(
            self.width//2 - 300, 
            self.height//3 - 50,
            600, 100
        )
        self.status_panel = TextPanel(
            self.width//2 - 200,
            self.height//2 - 25,
            400, 50
        )

        # States
        self.WAITING = "waiting"
        self.LISTENING = "listening"
        self.CONFIRMING = "confirming"
        self.ERROR = "error"
        self.PREPARING = "preparing"
        self.state = self.WAITING
        
        self.recognized_word = None
        self.speech_thread = None
        self.start_time = None
        self.audio_level = 0
        self.error_message = ""
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.BLUE = (0, 0, 255)

    def load_images(self):
        # Load and scale background
        # MiniGames\Speech\fill_the_blanks\image\background.jpg
        script_dir = os.path.dirname(os.path.abspath(__file__))
        print(script_dir)

        self.background = pygame.image.load(os.path.join(script_dir, "image", "background.jpg"))
        self.background = pygame.transform.scale(self.background, (self.width, self.height))
        
        # Load and scale wizard
        self.wizard = pygame.image.load(os.path.join(script_dir, "image", "wizard.png"))
        # Scale to 65% of screen height (instead of 80%)
        wizard_height = self.height * 1
        wizard_width = self.wizard.get_width() * (wizard_height / self.wizard.get_height())
        scaled_wizard = pygame.transform.scale(self.wizard, (int(wizard_width), int(wizard_height)))
        
        # Get only top 50% of the scaled image
        crop_height = int(wizard_height * 0.6)
        self.wizard = scaled_wizard.subsurface((0, 0, int(wizard_width), crop_height))
    def draw(self):
        # Draw background
        self.screen.blit(self.background, (0, 0))
        
        # Draw wizard on left side
        wizard_x = -150
        wizard_y = self.height - self.wizard.get_height()
        self.screen.blit(self.wizard, (wizard_x, wizard_y))
        
        # Draw main text panel
        self.main_panel.draw(self.screen, self.text, self.font)
        
        if self.state == self.LISTENING:
            # Draw timeout bar inside status panel
            elapsed = time.time() - self.start_time
            progress = min(elapsed / 10.0, 1.0)
            
            # Draw audio level bar
            try:
                while not self.speech_thread.audio_queue.empty():
                    self.audio_level = self.speech_thread.audio_queue.get_nowait()
            except (queue.Empty, AttributeError):
                pass
            
            self.draw_audio_meter(100, self.height/2 + 40, self.width-200, 20)

            # Draw progress bar
            pygame.draw.rect(self.screen, self.GREEN, 
            (self.status_panel.rect.x + 10,
                self.status_panel.rect.y + 10,
                (self.status_panel.rect.width - 20) * (1-progress),
                20))
            
        elif self.state == self.CONFIRMING:
            confirm_text = f"Did you say '{self.recognized_word}'?"
            self.status_panel.draw(self.screen, confirm_text, self.font)
            
            # Draw Yes/No buttons
            yes_surface = self.font.render("Yes", True, self.GREEN)
            no_surface = self.font.render("No", True, self.RED)
            self.screen.blit(yes_surface, (self.width/3, 2*self.height/3))
            self.screen.blit(no_surface, (2*self.width/3, 2*self.height/3))
            
        elif self.state == self.WAITING:
            self.status_panel.draw(self.screen, "Press SPACE to start listening", self.font)

        elif self.state == self.ERROR:
            self.status_panel.draw(self.screen, self.error_message, self.font, self.RED)
            
            # Draw OK button
            ok_surface = self.font.render("OK", True, self.BLUE)
            ok_rect = ok_surface.get_rect(center=(self.width/2, 2*self.height/3))
            pygame.draw.rect(self.screen, self.BLACK, ok_rect.inflate(20, 10), 2)
            self.screen.blit(ok_surface, ok_rect)

        elif self.state == self.PREPARING:
            prep_text = "Preparing microphone..."
            self.status_panel.draw(self.screen, prep_text, self.font, self.BLUE)
            
            # Add waiting animation
            dots = "." * (int(time.time() * 2) % 4)
            wait_text = f"Please wait{dots}"
            wait_surface = self.font.render(wait_text, True, self.BLACK)
            wait_rect = wait_surface.get_rect(center=(self.width/2, self.height/2 + 40))
            self.screen.blit(wait_surface, wait_rect)
    
        pygame.display.flip()

    def draw_audio_meter(self, x, y, width, height):
        # Draw background
        pygame.draw.rect(self.screen, (200, 200, 200), (x, y, width, height))
        # Draw level bars with gradient colors
        num_bars = 20
        bar_width = width // num_bars
        normalized_level = min(self.audio_level / 3000.0, 1.0)
        active_bars = int(normalized_level * num_bars)
        
        for i in range(num_bars):
            if i < active_bars:
                # Gradient from green to red
                color = (min(255, i * 25), max(0, 255 - i * 25), 0)
                pygame.draw.rect(self.screen, color, 
                            (x + i * bar_width, y, bar_width-1, height))
                
    def start_listening(self):
        print("\n[GAME] Starting listening state")
        if self.speech_thread:
            print("[GAME] Cleaning up previous thread")
            self.speech_thread.cleanup()
            self.speech_thread.join(timeout=1)
        
        self.speech_thread = SpeechThread()
        self.speech_thread.start()
        self.start_time = time.time()
        self.state = self.PREPARING
        print("[GAME] Started listening thread")

    def run(self):
        running = True
        print("[GAME] Starting game loop")
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("[GAME] Quitting game")
                    running = False
                    
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and self.state == self.WAITING:
                        print("[GAME] Space pressed, starting listening")
                        self.start_listening()
                    elif event.key == pygame.K_ESCAPE:
                        # Cancel current action
                        self.state = self.WAITING
                        
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == self.CONFIRMING:
                        x, y = event.pos
                        if y > 2*self.height/3:
                            if x < self.width/2:  # Yes clicked
                                print("[GAME] Yes clicked")
                                # No need to check again since we already validated
                                self.text = self.text.replace("___", self.recognized_word, 1)
                                self.current_word_index += 1
                                if self.current_word_index >= len(self.missing_words):
                                    print("[GAME] Game completed!")
                                    running = False
                                else:
                                    print("[GAME] Moving to next word")
                                    self.state = self.WAITING
                            else:  # No clicked
                                print("[GAME] No clicked")
                                self.state = self.WAITING
                                
                    elif self.state == self.ERROR:
                        x, y = event.pos
                        if (self.height/2 + 50 < y < 2*self.height/3 + 20 and 
                            self.width/2 - 50 < x < self.width/2 + 50):
                            print("[GAME] Error acknowledged")
                            self.state = self.WAITING
    
            if self.state == self.PREPARING:
                try:
                    if self.speech_thread.ready_queue.get_nowait():
                        print("[GAME] Microphone ready, starting to listen")
                        self.start_time = time.time()
                        self.state = self.LISTENING
                except queue.Empty:
                    pass
                    
            elif self.state == self.LISTENING:
                if self.speech_thread and not self.speech_thread.is_alive():
                    try:
                        while not self.speech_thread.queue.empty():
                            result_type, word = self.speech_thread.queue.get_nowait()
                            print(f"[GAME] Raw recognition result: {result_type}, {word}")
                            
                            if result_type == "success":
                                # Check phonetic similarity first
                                correct_word = self.missing_words[self.current_word_index]
                                if (word == correct_word or 
                                    dynamic_phonetic_comparision(word, correct_word)):
                                    print(f"[GAME] Phonetically matched '{word}' to '{correct_word}'")
                                    self.recognized_word = correct_word  # Use correct word
                                else:
                                    print(f"[GAME] No phonetic match for '{word}'")
                                    self.recognized_word = word  # Use recognized word
                                self.state = self.CONFIRMING
                                break
                                
                            elif result_type == "error":
                                print(f"[GAME] Error occurred: {word}")
                                self.error_message = f"Error: {word}"
                                self.state = self.ERROR
                                break
                            else:
                                print("[GAME] No word recognized")
                                self.error_message = "Sorry, I didn't catch that. Please try again."
                                self.state = self.ERROR
                    except queue.Empty:
                        pass
                    
                if time.time() - self.start_time > 10:
                    print("[GAME] Timeout reached")
                    if self.speech_thread:
                        self.speech_thread.cleanup()
                    self.error_message = "Time's up! Press SPACE to try again."
                    self.state = self.ERROR
                    
            self.draw()
            
        print("[GAME] Game ended")
        pygame.quit()
        

if __name__ == "__main__":
    game = Game()
    game.run()

