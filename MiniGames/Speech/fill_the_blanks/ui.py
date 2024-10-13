import pygame
import sys

def display_text(screen, text, position=(400, 100), clear_area=False, area_size=(800, 50)):
    font = pygame.font.Font(None, 36)
    text_surface = font.render(text, True, (255, 255, 255))
    if clear_area:
        clear_rect = pygame.Rect(position[0] - area_size[0] // 2, position[1], area_size[0], area_size[1])
        pygame.draw.rect(screen, (0, 0, 0), clear_rect)
    screen.blit(text_surface, (position[0] - text_surface.get_width() // 2, position[1]))
    pygame.display.flip()

def create_button(screen, text, position, size=(100, 50)):
    font = pygame.font.Font(None, 36)
    button_rect = pygame.Rect(position, size)
    pygame.draw.rect(screen, (0, 0, 255), button_rect)
    text_surface = font.render(text, True, (255, 255, 255))
    screen.blit(text_surface, (position[0] + (size[0] - text_surface.get_width()) // 2, position[1] + (size[1] - text_surface.get_height()) // 2))
    pygame.display.flip()
    return button_rect

def get_user_confirmation(screen, user_word):
    display_text(screen, f"Did you say {user_word}?", position=(400, 200))
    yes_button = create_button(screen, "Yes", (300, 300))
    no_button = create_button(screen, "No", (400, 300))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if yes_button.collidepoint(event.pos):
                    display_text(screen, "", position=(400, 200), clear_area=True, area_size=(800, 100))  # Clear confirmation area
                    return "yes"
                elif no_button.collidepoint(event.pos):
                    display_text(screen, "", position=(400, 200), clear_area=True, area_size=(800, 100))  # Clear confirmation area
                    return "no"

def wait_for_close_button(screen):
    close_button = create_button(screen, "Close", (350, 400))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if close_button.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()