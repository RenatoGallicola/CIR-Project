import pygame
import speech_recognition as sr
import threading
import time
import queue
import audioop
import pocketsphinx
from pydub import AudioSegment
from pydub.effects import normalize
from phonetic_comparison import dynamic_phonetic_comparision

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
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Wizard's Riddle Game")
        
        self.font = pygame.font.Font(None, 36)
        
        # Define riddles and their answers
        self.riddles = [
            ("I am heavy, cold, and gray;\nwith a whisper, I pave the way.\nWhat am I?", "stone"),
            ("I am sought by kings, shiny and bold,\nworth more than words, what am I?", "gold"),
            ("Round and small, with stories told,\nin pockets I jingle, both young and old.\nWhat am I?", "coin")
        ]
        self.final_spell = "With stone, gold, and coin now found,\nlet magic turn this stone around!"
        
        self.current_riddle_index = 0
        self.collected_items = []
        
        # Get current riddle text
        self.text = self.riddles[self.current_riddle_index][0]
        self.missing_words = [riddle[1] for riddle in self.riddles]  # ['stone', 'gold', 'coin']
        self.current_word_index = 0
        
        # Game states remain the same
        self.WAITING = "waiting"
        self.LISTENING = "listening"
        self.CONFIRMING = "confirming"
        self.ERROR = "error"
        self.PREPARING = "preparing"
        self.state = self.WAITING
        
        # Other properties remain the same
        self.recognized_word = None
        self.speech_thread = None
        self.start_time = None
        self.audio_level = 0
        self.error_message = ""
        
        # Colors remain the same
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.BLUE = (0, 0, 255)

        # Load images
        self.background = pygame.image.load("MiniGames/Speech/fill_the_blanks/image/background.jpg")
        self.background = pygame.transform.scale(self.background, (self.width, self.height))
        self.wizard = pygame.image.load("MiniGames/Speech/fill_the_blanks/image/wizard_cropped.png")
        # Adjust wizard size
        wizard_height = self.height // 3
        wizard_ratio = wizard_height / self.wizard.get_height()
        wizard_width = int(self.wizard.get_width() * wizard_ratio)
        self.wizard = pygame.transform.scale(self.wizard, (wizard_width, wizard_height))

        # Scroll colors : 
        self.SCROLL_COLOR = (245, 235, 215)  # Light parchment color
        self.SCROLL_ALPHA = 180  # Semi-transparent

    def create_text_background(self, width, height):
        """Create a semi-transparent scroll background for text"""
        scroll = pygame.Surface((width, height))
        scroll.fill(self.SCROLL_COLOR)
        scroll.set_alpha(self.SCROLL_ALPHA)
        return scroll
        
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
        
    def draw(self):
        # Draw background
        self.screen.blit(self.background, (0, 0))
        
        # Draw wizard at bottom left
        wizard_x = 50
        wizard_y = self.height - self.wizard.get_height() - 20
        self.screen.blit(self.wizard, (wizard_x, wizard_y))
        
        # Calculate right side area
        right_x = wizard_x + self.wizard.get_width() + 50
        right_width = self.width - right_x - 50
        
        # Draw riddle text with scroll background
        lines = self.text.split('\n')
        line_height = self.font.get_height()
        
        # First calculate total height and max width needed
        max_width = 0
        rendered_lines = []
        for line in lines:
            text_surface = self.font.render(line, True, self.BLACK)
            rendered_lines.append(text_surface)
            max_width = max(max_width, text_surface.get_width())
        
        # Calculate total height needed
        text_height = (len(lines) * line_height) + 40  # 40 for padding
        # Calculate required width with padding
        text_width = max_width + 40  # 40 for padding
        
        # Create appropriately sized scroll background
        scroll = self.create_text_background(text_width, text_height)
        scroll_x = right_x + (right_width - text_width) // 2  # Center in available space
        text_y = self.height/3 - text_height/2
        
        # Draw scroll background
        self.screen.blit(scroll, (scroll_x, text_y))
        
        # Draw each line centered on the scroll
        for i, text_surface in enumerate(rendered_lines):
            text_rect = text_surface.get_rect(
                centerx=scroll_x + text_width/2,
                y=text_y + 20 + i * line_height
            )
            self.screen.blit(text_surface, text_rect)
        
        # Draw collected items
        if self.collected_items:
            items_text = "Items: " + ", ".join(self.collected_items)
            items_surface = self.font.render(items_text, True, self.BLUE)
            items_bg = self.create_text_background(items_surface.get_width() + 20, items_surface.get_height() + 10)
            self.screen.blit(items_bg, (10, 10))
            self.screen.blit(items_surface, (20, 15))
    
        if self.state == self.LISTENING:
            # Draw timeout bar with background
            bar_bg = self.create_text_background(right_width, 30)
            self.screen.blit(bar_bg, (right_x, self.height/2))
            
            elapsed = time.time() - self.start_time
            progress = min(elapsed / 10.0, 1.0)
            pygame.draw.rect(self.screen, self.GREEN, 
                            (right_x, self.height/2 + 5, right_width * (1-progress), 20))
            
            # Update and draw audio meter
            try:
                while not self.speech_thread.audio_queue.empty():
                    self.audio_level = self.speech_thread.audio_queue.get_nowait()
            except (queue.Empty, AttributeError):
                pass
            
            meter_bg = self.create_text_background(right_width, 30)
            self.screen.blit(meter_bg, (right_x, self.height/2 + 40))
            self.draw_audio_meter(right_x, self.height/2 + 45, right_width, 20)
            
        elif self.state == self.CONFIRMING:
            confirm_text = f"Did you say '{self.recognized_word}'?"
            text_surface = self.font.render(confirm_text, True, self.BLACK)
            bg_width = text_surface.get_width() + 40
            bg_height = text_surface.get_height() + 20
            
            bg_x = right_x + (right_width - bg_width)/2
            bg_y = self.height/2 - bg_height/2
            
            scroll = self.create_text_background(bg_width, bg_height)
            self.screen.blit(scroll, (bg_x, bg_y))
            self.screen.blit(text_surface, (bg_x + 20, bg_y + 10))
            
            yes_surface = self.font.render("Yes", True, self.GREEN)
            no_surface = self.font.render("No", True, self.RED)
            self.screen.blit(yes_surface, (right_x + right_width/3, bg_y + bg_height + 20))
            self.screen.blit(no_surface, (right_x + 2*right_width/3, bg_y + bg_height + 20))
            
        elif self.state == self.WAITING:
            prompt = self.font.render("Press SPACE to start listening", True, self.BLACK)
            bg = self.create_text_background(prompt.get_width() + 40, prompt.get_height() + 20)
            bg_rect = bg.get_rect(center=(right_x + right_width/2, self.height/2))
            self.screen.blit(bg, bg_rect)
            self.screen.blit(prompt, (bg_rect.x + 20, bg_rect.y + 10))
    
        elif self.state == self.ERROR:
            error_surface = self.font.render(self.error_message, True, self.RED)
            bg = self.create_text_background(error_surface.get_width() + 40, error_surface.get_height() + 20)
            bg_rect = bg.get_rect(center=(right_x + right_width/2, self.height/2))
            self.screen.blit(bg, bg_rect)
            self.screen.blit(error_surface, (bg_rect.x + 20, bg_rect.y + 10))
            
            ok_surface = self.font.render("OK", True, self.BLUE)
            ok_rect = ok_surface.get_rect(center=(right_x + right_width/2, bg_rect.bottom + 30))
            ok_bg = self.create_text_background(60, 40)
            self.screen.blit(ok_bg, ok_rect.inflate(20, 10))
            self.screen.blit(ok_surface, ok_rect)
    
        elif self.state == self.PREPARING:
            prep_text = "Preparing microphone..."
            prep_surface = self.font.render(prep_text, True, self.BLUE)
            wait_text = f"Please wait{'.' * (int(time.time() * 2) % 4)}"
            wait_surface = self.font.render(wait_text, True, self.BLACK)
            
            bg_height = prep_surface.get_height() + wait_surface.get_height() + 30
            bg_width = max(prep_surface.get_width(), wait_surface.get_width()) + 40
            
            bg = self.create_text_background(bg_width, bg_height)
            bg_rect = bg.get_rect(center=(right_x + right_width/2, self.height/2))
            self.screen.blit(bg, bg_rect)
            
            self.screen.blit(prep_surface, prep_surface.get_rect(centerx=bg_rect.centerx, y=bg_rect.y + 10))
            self.screen.blit(wait_surface, wait_surface.get_rect(centerx=bg_rect.centerx, y=bg_rect.y + 40))
        
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
                        mouse_x, mouse_y = event.pos
                        # Calculate right side area (same as in draw)
                        wizard_x = 50
                        right_x = wizard_x + self.wizard.get_width() + 50
                        right_width = self.width - right_x - 50
                        
                        # Calculate confirmation box position (same as in draw)
                        confirm_text = f"Did you say '{self.recognized_word}'?"
                        text_surface = self.font.render(confirm_text, True, self.BLACK)
                        bg_width = text_surface.get_width() + 40
                        bg_height = text_surface.get_height() + 20
                        bg_y = self.height/2 - bg_height/2
                        
                        # Button positions and hit boxes
                        yes_x = right_x + right_width/3
                        no_x = right_x + 2*right_width/3
                        buttons_y = bg_y + bg_height + 20
                        
                        # Create button rectangles for collision detection
                        yes_rect = pygame.Rect(yes_x - 20, buttons_y - 10, 40, 40)
                        no_rect = pygame.Rect(no_x - 20, buttons_y - 10, 40, 40)
                        
                        if yes_rect.collidepoint(mouse_x, mouse_y):
                            print("[GAME] Yes clicked")
                            if (self.recognized_word == self.missing_words[self.current_word_index] or
                                dynamic_phonetic_comparision(self.recognized_word, 
                                                        self.missing_words[self.current_word_index])):
                                print("[GAME] Word is correct")
                                # Add item to collected items
                                self.collected_items.append(self.missing_words[self.current_word_index])
                                self.current_word_index += 1
                                
                                if self.current_word_index >= len(self.missing_words):
                                    # All riddles solved, show final spell
                                    print("[GAME] All riddles solved!")
                                    self.text = self.final_spell
                                    running = False
                                else:
                                    # Move to next riddle
                                    print("[GAME] Moving to next riddle")
                                    self.text = self.riddles[self.current_word_index][0]
                                    self.state = self.WAITING
                            else:
                                print("[GAME] Word is incorrect, try again")
                                self.error_message = "Incorrect word! Try again."
                                self.state = self.ERROR
                        elif no_rect.collidepoint(mouse_x, mouse_y):
                            print("[GAME] No clicked")
                            self.error_message = "Try again!"
                            self.state = self.ERROR
                                
                    elif self.state == self.ERROR:
                        x, y = event.pos
                        # Calculate right side area (same as in draw)
                        wizard_x = 50
                        right_x = wizard_x + self.wizard.get_width() + 50
                        right_width = self.width - right_x - 50
                        
                        # Calculate error box position (same as in draw)
                        error_surface = self.font.render(self.error_message, True, self.RED)
                        bg_rect = error_surface.get_rect(center=(right_x + right_width/2, self.height/2))
                        
                        # OK button position
                        ok_rect = pygame.Rect(
                            right_x + right_width/2 - 30,  # center - half button width
                            bg_rect.bottom + 20,           # below error message
                            60,                           # button width
                            40                            # button height
                        )
                        
                        if ok_rect.collidepoint(x, y):
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