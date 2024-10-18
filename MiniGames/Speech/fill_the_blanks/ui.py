import pygame
import sys

# Define colors
DARK_BLUE = (10, 20, 30)
LIGHT_BLUE = (100, 150, 200)
TEXT_COLOR = (255, 255, 255)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER_COLOR = (100, 160, 210)
CORRECT_COLOR = (50, 205, 50)
INCORRECT_COLOR = (220, 20, 60)

# Window size
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

def create_gradient_background(screen):
    for y in range(WINDOW_HEIGHT):
        r = int(DARK_BLUE[0] + (LIGHT_BLUE[0] - DARK_BLUE[0]) * y / WINDOW_HEIGHT)
        g = int(DARK_BLUE[1] + (LIGHT_BLUE[1] - DARK_BLUE[1]) * y / WINDOW_HEIGHT)
        b = int(DARK_BLUE[2] + (LIGHT_BLUE[2] - DARK_BLUE[2]) * y / WINDOW_HEIGHT)
        color = (r, g, b)
        pygame.draw.line(screen, color, (0, y), (WINDOW_WIDTH, y))

def display_text(screen, text, position=(WINDOW_WIDTH // 2, 150), font_size=36, color=TEXT_COLOR, clear_area=False, area_size=(WINDOW_WIDTH, 60)):
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=position)
    
    if clear_area:
        clear_rect = pygame.Rect(text_rect.left - (area_size[0] - text_rect.width) // 2,
                                 text_rect.top - (area_size[1] - text_rect.height) // 2,
                                 area_size[0], area_size[1])
        pygame.draw.rect(screen, DARK_BLUE, clear_rect)
        create_gradient_background(screen)
    
    screen.blit(text_surface, text_rect)
    pygame.display.update(text_rect)

def create_button(screen, text, position, size=(200, 60)):
    font = pygame.font.Font(None, 36)
    button_rect = pygame.Rect(0, 0, size[0], size[1])
    button_rect.center = position
    
    mouse_pos = pygame.mouse.get_pos()
    if button_rect.collidepoint(mouse_pos):
        color = BUTTON_HOVER_COLOR
    else:
        color = BUTTON_COLOR
    
    pygame.draw.rect(screen, color, button_rect, border_radius=10)
    pygame.draw.rect(screen, TEXT_COLOR, button_rect, 2, border_radius=10)
    
    text_surface = font.render(text, True, TEXT_COLOR)
    text_rect = text_surface.get_rect(center=button_rect.center)
    screen.blit(text_surface, text_rect)
    
    pygame.display.update(button_rect)
    return button_rect

def get_user_confirmation(screen, user_word):
    display_text(screen, f"Did you say '{user_word}'?", position=(WINDOW_WIDTH // 2, 250), font_size=40)
    yes_button = create_button(screen, "Yes", (WINDOW_WIDTH // 2 - 110, 350))
    no_button = create_button(screen, "No", (WINDOW_WIDTH // 2 + 110, 350))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if yes_button.collidepoint(event.pos):
                    clear_area(screen, (0, 200, WINDOW_WIDTH, 250))
                    return "yes"
                elif no_button.collidepoint(event.pos):
                    clear_area(screen, (0, 200, WINDOW_WIDTH, 250))
                    return "no"
        
        # Update button appearance on hover
        yes_button = create_button(screen, "Yes", (WINDOW_WIDTH // 2 - 110, 350))
        no_button = create_button(screen, "No", (WINDOW_WIDTH // 2 + 110, 350))
        pygame.display.flip()

def wait_for_close_button(screen):
    close_button = create_button(screen, "Close", (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 100))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if close_button.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
        
        # Update button appearance on hover
        close_button = create_button(screen, "Close", (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 100))
        pygame.display.flip()

def clear_area(screen, rect):
    pygame.draw.rect(screen, DARK_BLUE, rect)
    create_gradient_background(screen)
    pygame.display.update(rect)

def display_result(screen, is_correct, position=(WINDOW_WIDTH // 2, 300)):
    if is_correct:
        display_text(screen, "Correct!", position=position, font_size=48, color=CORRECT_COLOR, clear_area=True, area_size=(WINDOW_WIDTH, 50))
    else:
        display_text(screen, "Incorrect, try again.", position=position, font_size=48, color=INCORRECT_COLOR)

def init_screen():
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Speech Recognition Game")
    create_gradient_background(screen)
    return screen

def show_start_screen(screen):
    create_gradient_background(screen)
    display_text(screen, "Speech Recognition Game", position=(WINDOW_WIDTH // 2, 200), font_size=60)
    display_text(screen, "Fill in the blanks by speaking the missing words", position=(WINDOW_WIDTH // 2, 300), font_size=36)
    start_button = create_button(screen, "Start Game", (WINDOW_WIDTH // 2, 450))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos):
                    return
        
        # Update button appearance on hover
        start_button = create_button(screen, "Start Game", (WINDOW_WIDTH // 2, 450))
        pygame.display.flip()