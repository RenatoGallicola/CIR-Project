# import libaries
import pygame
import random
import numpy as np

# initialize all modules
pygame.init()

# define constants and variables
WIDTH = 600
HEIGHT = 600
black = (0,0,0) # RGB color value
white = (255,255,255) # RGB color value
grey = (120,120,120) # RGB color value
green = (0, 255, 0) # RGB color value
blue = (0, 0, 255) # RGB color value

fps = 60 # frames per second, how fast the game can run
timer = pygame.time.Clock()

title_font = pygame.font.Font("freesansbold.ttf", 24)
subtitle_font = pygame.font.Font("freesansbold.ttf", 18)

rows = 4 # number of squares in each row
cols = 4 # number of squares in each column
correct = [np.zeros([rows, cols])]
print(correct)
options_list = []
spaces = []
used = []
new_board = True
first_guess = False
second_guess = False
first_guess_num = None
second_guess_num = None
matches = 0

player_score = 0 
computer_score = 0
player_turn = True # player starts

# create screen
screen = pygame.display.set_mode([WIDTH, HEIGHT])

# name window
pygame.display.set_caption("Memory Match 1v1")


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
    title_text = title_font.render("Memory Match Game 1v1", True, white)
    screen.blit(title_text, (10, 20))
    
    # add text to subtitle
    subtitle_text = subtitle_font.render("Instructions: Find the most matches before the guards does!", True, white)
    screen.blit(subtitle_text, (10, 50))
    
    # define bottom menu
    bottom_menu = pygame.draw.rect(screen, black, [0, HEIGHT-100, WIDTH, 100])
    #board_space = pygame.draw.rect(screen, grey, [0, 100, WIDTH, HEIGHT-200])

    # show scores 
    player_score_text = subtitle_font.render(f"Player's Score: {player_score}", True, white)
    screen.blit(player_score_text, (20, HEIGHT-80))
    computer_score_text = subtitle_font.render(f"Guard's score: {computer_score}", True, white)
    screen.blit(computer_score_text, (20, HEIGHT-50))

def board_setup():
    '''
    Assign each square with a number ranging 0-num_of_sqaures/2. 
    Two squares will have the same number indicating a pair.

    Arguments
    ----------
    -

    Returns
    -------
    list of sqaures (cards)

    '''
    # retrieve global variables
    global rows, cols, correct

    board_list = []

    # iterate for each column
    for i in range(cols):
        # iterate for each row
        for j in range(rows):
            square = pygame.draw.rect(screen, grey, [i * 100 + 110, j * 100 + 110, 80, 80], 0, 4)
            
            # saves every square in the matrix
            board_list.append(square)

            # write assigned number to each square
            # sqaure_text = subtitle_font.render(f'{spaces[i * rows + j]}', True, black)
            # screen.blit(sqaure_text, (i * 100 + 145, j * 100 + 141))

    for r in range(rows):
        for c in range(cols):
            if correct[0][r][c] == 1:
                pygame.draw.rect(screen, green, [c * 100 + 108, r * 100 + 108, 84, 84], 3, 4)
                sqaure_text = subtitle_font.render(f'{spaces[c * rows + r]}', True, black)
                screen.blit(sqaure_text, (c * 100 + 145, r * 100 + 141))


    return board_list

def generate_board():
    '''
    Assign each square a number from 0-len()

    Arguments
    ----------
    -

    Returns
    -------
    -

    '''
    global options_list, spaces, used

    for item in range(rows * cols // 2):
        options_list.append(item)

    # assign number to each sqaure
    for item in range(rows * cols):
        square = options_list[random.randint(0, len(options_list)-1)]
        spaces.append(square)
        
        # keep track of what squares are already filled up
        if square in used: # used: keeps track of single used pieces
            used.remove(square)
            options_list.remove(square)
        else:
            used.append(square)

def check_guesses(first, second):
    '''
    Check if the two guess are macthing 

    Arguments
    ----------
    first: int
    second: int

    Returns
    -------
    -

    '''
    global spaces, correct, matches

    if spaces[first] == spaces[second]:
        # identifying position of the sqaure that is clicked on
        col1 = first // rows
        col2 = second // rows
        row1 = first - (first // rows * rows)
        row2 = second - (second // rows * rows)

        # update correct matrix to identify correct guess
        correct[0][row1][col1] = 1
        correct[0][row2][col2] = 1

        matches += 1
        # print(correct)


running = True
while running:
    timer.tick(fps)
    screen.fill(white)
    if new_board:
        generate_board()
        # print(spaces)
        new_board = False

    background_setup()
    board = board_setup()

    if first_guess and second_guess:
        check_guesses(first_guess_num, second_guess_num)
        pygame.time.delay(1000)
        first_guess = False
        second_guess = False


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
             running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i in range(len(board)):
                button = board[i]
                if button.collidepoint(event.pos) and not first_guess:
                    first_guess = True
                    first_guess_num = i
                    # print(i)
                
                if button.collidepoint(event.pos) and not second_guess and first_guess and i != first_guess_num:
                    second_guess = True
                    second_guess_num = i
                    # print(i)

    # mark first guess in blue
    if first_guess:
        sqaure_text = subtitle_font.render(f'{spaces[first_guess_num]}', True, blue)
        location = (first_guess_num // rows * 100 + 145, (first_guess_num - (first_guess_num // rows * rows)) * 100 + 141)
        screen.blit(sqaure_text, (location))

    # mark second guess in blue
    if second_guess:
        sqaure_text = subtitle_font.render(f'{spaces[second_guess_num]}', True, blue)
        location = (second_guess_num // rows * 100 + 145, (second_guess_num - (second_guess_num // rows * rows)) * 100 + 141)
        screen.blit(sqaure_text, (location))

    # if all matches has been found and game is done
    if matches == rows*cols // 2:
        game_finish = pygame.draw.rect(screen, black, [10, HEIGHT - 350, WIDTH - 20, 50], 0, 5)
        game_finish_text = title_font.render("Congrats! You completed the game", True, white)
        screen.blit(game_finish_text, (100, HEIGHT - 341))

    pygame.display.flip()
pygame.quit()