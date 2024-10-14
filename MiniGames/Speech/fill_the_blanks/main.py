import pygame
import sys
from speech_reco import recognize_speech
from phonetic_comparison import dynamic_phonetic_comparision
from ui import init_screen, display_text, get_user_confirmation, wait_for_close_button, display_result, show_start_screen, WINDOW_WIDTH, WINDOW_HEIGHT

# Initialize Pygame
pygame.init()

# Set up the display
screen = init_screen()

# Main game loop
def main():
    # Show the start screen
    show_start_screen(screen)

    text = "The quick brown ___ jumps over the lazy ___."
    missing_words = ["fox", "dog"]  # Add your missing words here

    # Always display the initial text, centered on the top of the screen
    display_text(screen, text, position=(WINDOW_WIDTH // 2, 100), font_size=36)

    for i, correct_word in enumerate(missing_words):
        while True:
            # wait for user to say a word for a maximum of 5 seconds
            user_word = recognize_speech()
            if user_word is None:
                display_text(screen, "Please try again", position=(WINDOW_WIDTH // 2, 200), font_size=36, clear_area=True, area_size=(WINDOW_WIDTH, 60))
                continue
            confirm = get_user_confirmation(screen, user_word)
            if confirm.lower() == "yes":
                if user_word == correct_word or dynamic_phonetic_comparision(user_word, correct_word):
                    display_result(screen, True)
                    text = text.replace("___", correct_word, 1)
                    display_text(screen, text, position=(WINDOW_WIDTH // 2, 100), font_size=36, clear_area=True, area_size=(WINDOW_WIDTH, 60))
                    break
                else:
                    display_result(screen, False)

    display_text(screen, "Congratulations! You've completed the text.", position=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 200), font_size=48)
    display_text(screen, f"Final text: {text}", position=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 150), font_size=36)

    # Wait for the player to click the "Close" button
    wait_for_close_button(screen)

if __name__ == "__main__":
    main()
    pygame.quit()
    sys.exit()