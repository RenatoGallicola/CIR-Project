import pygame
import sys
import cv2
import ctypes
import threading
import os
import sys
module_dir = os.path.dirname(__file__)
module_path = os.path.join(module_dir, '../../Utils/Gesture')
sys.path.append(module_path)
from hand_gesture_recognition import HandGesture
import random

class RockPaperScissorsStandard:
    def __init__(self):
        infoObject = pygame.display.Info()
        self.__width, self.__height = infoObject.current_w, infoObject.current_h
        self.__window = pygame.display.set_mode((self.__width, self.__height), pygame.RESIZABLE)
        if sys.platform == "win32":
            win_info = pygame.display.get_wm_info()['window']
            SW_MAXIMIZE = 3
            ctypes.windll.user32.ShowWindow(win_info, SW_MAXIMIZE)
        self.__cap = None
        self.__hand_gesture = None
        self.__dialogue_frame_rect = None
        self.__font_size = 36
        self.__thread_list = []
    
    def __manage_thread(self):
        for t in self.__thread_list:
            t.join()

    def __launch_hand_gesture(self):
        self.__cap = cv2.VideoCapture(0)
        num_hands = 1 
        show_fps = True
        show_bounding_box = True
        show_info_box = True
        show_hand_label = False
        valid_gestures = {'Fist':'Rock', 'Open':'Paper', 'Peace':'Scissors'}

        self.__hand_gesture = HandGesture(num_hands=num_hands, show_fps=show_fps, show_bounding_box=show_bounding_box, show_info_box=show_info_box, show_hand_label=show_hand_label,cap=self.__cap, valid_gestures=valid_gestures)

        thread_hand = threading.Thread(target=self.__hand_gesture.start)
        thread_hand.start()
        self.__thread_list.append(thread_hand)

    def __show_camera(self):
        frame = self.__hand_gesture.get_current_frame()
        if frame is None:
            return
        
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        frame_surface = pygame.surfarray.make_surface(frame)
        frame_surface = pygame.transform.rotate(frame_surface, -90)
        frame_surface = pygame.transform.flip(frame_surface, True, False)

        camera_scale = 1.5
        camera_width, camera_height = frame.shape[1]/camera_scale, frame.shape[0]/camera_scale
        frame_surface = pygame.transform.scale(frame_surface, (camera_width, camera_height))

        self.__window.blit(frame_surface, (self.__width - camera_width, 0))

    def __dialogue_text(self,text):
        font = pygame.font.Font(None, self.__font_size)
        text_color = pygame.Color("#5C4B51")
        for i,line in enumerate(text):
            text_surface = font.render(line, True, text_color)
            offset = len(text)//2 + 1 - (i+1)
            text_rect = text_surface.get_rect(center=(self.__dialogue_frame_rect.centerx, self.__dialogue_frame_rect.centery - offset*self.__font_size))
            self.__window.blit(text_surface, text_rect)

    def __draw_dialogue_frame(self):
        dialogue_frame = pygame.image.load("Assets/dialogue_frame.png")
        frame_scale_factor = self.__width / dialogue_frame.get_width()
        dialogue_frame = pygame.transform.scale(dialogue_frame, (frame_scale_factor*dialogue_frame.get_width(), frame_scale_factor*dialogue_frame.get_height()))
        bottom_offset = 10
        self.__dialogue_frame_rect = dialogue_frame.get_rect(topleft=(0, self.__height-dialogue_frame.get_height()-bottom_offset))
        self.__window.blit(dialogue_frame, self.__dialogue_frame_rect)

    def __compute_outcome(self, move, opp_move):
        if move == "Rock" and opp_move == "Scissors" or move == "Paper" and opp_move == "Rock" or move == "Scissors" and opp_move == "Paper":
            return "Win"
        elif move == "Rock" and opp_move == "Paper" or move == "Paper" and opp_move == "Scissors" or move == "Scissors" and opp_move == "Rock":
            return "Lose"
        else:
            return "Tie"

    def __dialogue_manager(self):
        curr_count = 3
        while True:
            if curr_count > 0:
                self.__draw_dialogue_frame()
                self.__dialogue_text(str(curr_count))
                curr_count -= 1
                pygame.time.wait(1000)
            else:
                self.__draw_dialogue_frame()
                move = self.__hand_gesture.get_current_gesture()
                if move is None:
                    move = "Invalid move"
                opp_move = random.choice(["Rock", "Paper", "Scissors"])
                self.__dialogue_text(["Your move: " + move,
                                      "Opponent's move: " + opp_move,
                                      "You " + self.__compute_outcome(move, opp_move)])
                curr_count = 3
                pygame.time.wait(2000)

    def start(self):
        self.__launch_hand_gesture()
        thread_dialogue = threading.Thread(target=self.__dialogue_manager)
        thread_dialogue.start()
        self.__thread_list.append(thread_dialogue)
        self.__window.fill((0, 0, 0))
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            self.__show_camera()
            pygame.display.flip()

        self.__cap.release()
        pygame.quit()
        self.__manage_thread()
        sys.exit()
    

pygame.init()
pygame.display.set_caption('Rock Paper Scissors Standard')
game = RockPaperScissorsStandard()
game.start()