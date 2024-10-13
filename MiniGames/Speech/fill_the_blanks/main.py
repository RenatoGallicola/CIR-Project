import pygame
import sys
from speech_reco import recognize_speech
from phonetic_comparison import is_phonetically_similar
from ui import display_text, get_user_confirmation, wait_for_close_button

# Initialize Pygame
pygame.init()

# Set up the display
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Speech Recognition Game")

# Main game loop
def main():
    text = "The quick brown ___ jumps over the lazy ___."
    missing_words = ["fox", "dog"]  # Add your missing words here

    # Always display the initial text, centered on the top of the screen
    display_text(screen, text, position=(400, 100))

    for i, correct_word in enumerate(missing_words):
        while True:
            # wait for user to say a word for a maximum of 5 seconds
            user_word = recognize_speech()
            if user_word is None:
                display_text(screen, "Please try again", position=(400, 200), clear_area=True, area_size=(800, 50))
                continue
            confirm = get_user_confirmation(screen, user_word)
            if confirm.lower() == "yes":
                if user_word == correct_word or is_phonetically_similar(user_word, correct_word):
                    display_text(screen, "Correct!", position=(400, 200), clear_area=True, area_size=(800, 50))
                    text = text.replace("___", correct_word, 1)
                    display_text(screen, text, position=(400, 100), clear_area=True, area_size=(800, 50))
                    break
                else:
                    display_text(screen, "Incorrect, try again.", position=(400, 200), clear_area=True, area_size=(800, 50))

    display_text(screen, "Congratulations! You've completed the text.", position=(400, 300))
    display_text(screen, f"Final text: {text}", position=(400, 350))

    # Wait for the player to click the "Close" button
    wait_for_close_button(screen)

if __name__ == "__main__":
    main()
    pygame.quit()
    sys.exit()