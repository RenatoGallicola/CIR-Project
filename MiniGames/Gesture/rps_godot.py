import sys
import cv2
import threading
import os
import sys
module_dir = os.path.dirname(__file__)
module_path = os.path.join(module_dir, '../../Utils/Gesture')
sys.path.append(module_path)
from hand_gesture_recognition import HandGesture
import random
import socket
from constants import SERVER_IP, SERVER_PORT
import json
import math
import base64

class RockPaperScissorsStandard:
    def __init__(self):
        self.__cap = None
        self.__hand_gesture = None
        self.__thread_list = []
        self.__curr_score = [0, 0]
        self.__client_socket = None
    
    def __manage_thread(self):
        for t in self.__thread_list:
            t.join()

    def __launch_hand_gesture(self):
        self.__cap = cv2.VideoCapture(0)
        num_hands = 1 
        show_fps = False
        show_bounding_box = True
        show_info_box = True
        show_hand_label = False
        valid_gestures = {'Fist':'Rock', 'Open':'Paper', 'Peace':'Scissors'}

        self.__hand_gesture = HandGesture(num_hands=num_hands, show_bounding_box=show_bounding_box, show_fps=show_fps, show_info_box=show_info_box, show_hand_label=show_hand_label,cap=self.__cap, valid_gestures=valid_gestures)

        thread_hand = threading.Thread(target=self.__hand_gesture.start)
        thread_hand.start()
        self.__thread_list.append(thread_hand)

    def __prepare_capture(self):
        frame = self.__hand_gesture.get_current_frame()
        if frame is None:
            return None
        frame = cv2.resize(frame, (400, 300))
        _, encoded_frame = cv2.imencode(".jpg", frame)
        return encoded_frame
    
    def __compute_outcome(self, move, opp_move):
        if move == "Rock" and opp_move == "Scissors" or move == "Paper" and opp_move == "Rock" or move == "Scissors" and opp_move == "Paper":
            return "Wins!", 1
        elif move == "Rock" and opp_move == "Paper" or move == "Paper" and opp_move == "Scissors" or move == "Scissors" and opp_move == "Rock":
            return "Loses...", -1
        else:
            return "Ties", 0

    def __send_data(self):
        image_data = self.__prepare_capture()
        if image_data is not None:
            image_data = base64.b64encode(image_data).decode("utf-8")
        
        move = self.__hand_gesture.get_current_gesture()
        if move is None:
            move = "Invalid move"
        opp_move = random.choice(["Rock", "Paper", "Scissors", "Scissors", "Scissors"])
        # opp_move = random.choice(["Scissors"])
        outcome, score = self.__compute_outcome(move, opp_move)

        payload = {
            "image": image_data,
            "result": score,
            "move": [move, opp_move],
            "outcome": outcome
        }

        data = json.dumps(payload).encode('utf-8')

        if len(data) <= 65507:
            self.__client_socket.sendto(data, (SERVER_IP, SERVER_PORT))
        else:
            print("Data size exceeds the maximum allowed size for a UDP packet.")

    def start(self):
        self.__client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__launch_hand_gesture()
        running = True
        while running:
            self.__send_data()
            if cv2.waitKey(1) & 0xFF == ord('q'):
                running = False
        
        self.__client_socket.close()
        self.__cap.release()
        self.__manage_thread()
        sys.exit()


game = RockPaperScissorsStandard()
game.start()