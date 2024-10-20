# import libaries
import pygame

# initialize all modules
pygame.init()

# define constants and variables
WIDTH = 600
HEIGHT = 600
black = (0,0,0) # RGB color value
white = (255,255,255) # RGB color value
grey = (120,120,120) # RGB color value

fps = 60 # frames per second, how fast the game can run
timer = pygame.time.Clock()

title_font = pygame.font.Font("freesansbold.ttf", 24)
subtitle_font = pygame.font.Font("freesansbold.ttf", 18)

rows = 4 # number of squares in each row
cols = 4 # number of squares in each column
correct = []

# create screen
screen = pygame.display.set_mode([WIDTH, HEIGHT])

# name window
pygame.display.set_caption("Memory Match")


def background_setup():
    '''
    Set up background color, title and subtitle (instructions)

    Arguments
    ----------
    -

    Returns
    -------
    -

    '''
    # define top menu for title and subtitle
    top_menu = pygame.draw.rect(screen, black, [0, 0, WIDTH, 100])
    
    # add text to title
    title_text = title_font.render("Memory Match Game", True, white)
    screen.blit(title_text, (10, 20))
    
    # add text to subtitle
    subtitle_text = subtitle_font.render("Instructions: xzy", True, white)
    screen.blit(subtitle_text, (10, 50))
    
    # define bottom menu
    bottom_menu = pygame.draw.rect(screen, black, [0, HEIGHT-100, WIDTH, 100])
    #board_space = pygame.draw.rect(screen, grey, [0, 100, WIDTH, HEIGHT-200])

def board_setup():
    '''
    Set up board with the squares

    Arguments
    ----------
    -

    Returns
    -------
    list of sqaures (cards)

    '''
    # retrieve global variables
    global rows
    global cols

    board_list = []

    # iterate for each column
    for i in range(cols):
        # iterate for each row
        for j in range(rows):
            square = pygame.draw.rect(screen, grey, [i * 100 + 110, j * 100 + 110, 80, 80], 0, 4)
            
            # saves every square in the matrix
            board_list.append(square)

    return board_list


running = True
while running:
    timer.tick(fps)
    screen.fill(white)
    background_setup()
    board_setup()


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
             running = False

    pygame.display.flip()
pygame.QUIT()