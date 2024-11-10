import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import argparse
import cv2 as cv
import mediapipe as mp
import csv
from collections import deque
import copy
import numpy as np
import itertools
from Keypoint.keypoint_classifier import KeypointClassifier
from History.history_classifier import HistoryClassifier
from collections import Counter
import threading
import time

class _FpsCounter:
    def __init__(self, buffer_len=1):
        self._start_tick = cv.getTickCount()
        self._freq = 1000.0 / cv.getTickFrequency()
        self._difftimes = deque(maxlen=buffer_len)

    def get(self):
        current_tick = cv.getTickCount()
        different_time = (current_tick - self._start_tick) * self._freq
        self._start_tick = current_tick

        self._difftimes.append(different_time)

        fps = 1000.0 / (sum(self._difftimes) / len(self._difftimes))
        fps_rounded = round(fps, 2)

        return fps_rounded

class HandGesture(object):
    def __init__(
        self,
        num_hands = 2, 
        enable_pointer = False, 
        show_fps = False, 
        show_bounding_box = True, 
        show_info_box = True, 
        show_landmarks = False,
        show_hand_label = True,
        enable_csv_update = False,
        enable_esc_exit = None,
        register_gesture_unit = 0,
        cap = cv.VideoCapture(0),
        valid_gestures = {"Fist":"Fist", "OK":"OK", "Index":"Index", "ThumbsUp":"ThumbsUp", "Peace":"Peace", "Salute":"Salute", "Scout":"Scout", "StarTrek":"StarTrek", "Open":"Open", "ThumbsDown":"ThumbsDown", "Neutral":"Neutral", "MammaMia":"MammaMia"}
    ):
        self.__num_hands = num_hands
        self.__enable_pointer = enable_pointer
        self.__show_fps = show_fps 
        self.__show_bounding_box = show_bounding_box 
        self.__show_info_box = show_info_box 
        self.__show_landmarks = show_landmarks
        self.__show_hand_label = show_hand_label
        self.__enable_csv_update = enable_csv_update
        self.__enable_esc_exit = enable_esc_exit
        self.__register_gesture_unit = register_gesture_unit
        self.__cap = cap
        self.__valid_gesture = valid_gestures

        self.__history_length = 16
        if self.__num_hands == 2:
            self.__current_gesture = {"Right": None, "Left": None}
        else:
            self.__current_gesture = None
        self.__gesture_lock = threading.Lock()
        self.__stop_flag = threading.Event()
        self.__is_running = False
        self.__current_frame = None
        self.__frame_lock = threading.Lock()
        self.__sleep_time = 0

    def __get_args():
        parser = argparse.ArgumentParser()

        parser.add_argument("--device", type=int, default=0)
        parser.add_argument("--width", help='cap width', type=int, default=960)
        parser.add_argument("--height", help='cap height', type=int, default=540)

        parser.add_argument('--use_static_image_mode', action='store_true')
        parser.add_argument("--min_detection_confidence",
                            help='min_detection_confidence',
                            type=float,
                            default=0.7)
        parser.add_argument("--min_tracking_confidence",
                            help='min_tracking_confidence',
                            type=int,
                            default=0.5)

        args = parser.parse_args()

        return args

    def __select_mode(key, mode):
        number = -1
        if 48 <= key <= 57:  # 0 - 9
            number = key - 48
        if key == 110:  # N
            mode = 0
        if key == 107:  # K
            mode = 1
        if key == 104:  # H
            mode = 2
        return number, mode

    def __calc_bounding_box(image, landmarks):
        image_width, image_height = image.shape[1], image.shape[0]

        landmark_array = np.empty((0, 2), int)

        for _, landmark in enumerate(landmarks.landmark):
            landmark_x = min(int(landmark.x * image_width), image_width - 1)
            landmark_y = min(int(landmark.y * image_height), image_height - 1)

            landmark_point = [np.array((landmark_x, landmark_y))]

            landmark_array = np.append(landmark_array, landmark_point, axis=0)

        x, y, w, h = cv.boundingRect(landmark_array)

        return [x, y, x + w, y + h]

    def __calc_landmark_list(image, landmarks):
        image_width, image_height = image.shape[1], image.shape[0]

        landmark_point = []

        for _, landmark in enumerate(landmarks.landmark):
            landmark_x = min(int(landmark.x * image_width), image_width - 1)
            landmark_y = min(int(landmark.y * image_height), image_height - 1)

            landmark_point.append([landmark_x, landmark_y])

        return landmark_point

    def __pre_process_landmark(landmark_list):
        temp_landmark_list = copy.deepcopy(landmark_list)

        # Convert to relative coordinates
        base_x, base_y = 0, 0
        for index, landmark_point in enumerate(temp_landmark_list):
            if index == 0:
                base_x, base_y = landmark_point[0], landmark_point[1]

            temp_landmark_list[index][0] = temp_landmark_list[index][0] - base_x
            temp_landmark_list[index][1] = temp_landmark_list[index][1] - base_y

        # Convert to a one-dimensional list
        temp_landmark_list = list(itertools.chain.from_iterable(temp_landmark_list))

        # Normalization
        max_value = max(list(map(abs, temp_landmark_list)))

        def normalize_(n):
            return n / max_value

        temp_landmark_list = list(map(normalize_, temp_landmark_list))

        return temp_landmark_list

    def __pre_process_point_history(image, point_history):
        image_width, image_height = image.shape[1], image.shape[0]

        temp_point_history = copy.deepcopy(point_history)

        # Convert to relative coordinates
        base_x, base_y = 0, 0
        for index, point in enumerate(temp_point_history):
            if index == 0:
                base_x, base_y = point[0], point[1]

            temp_point_history[index][0] = (temp_point_history[index][0] - base_x) / image_width
            temp_point_history[index][1] = (temp_point_history[index][1] - base_y) / image_height

        # Convert to a one-dimensional list
        temp_point_history = list(itertools.chain.from_iterable(temp_point_history))

        return temp_point_history

    def __update_csv(self, number, mode, landmark_list, point_history_list):
        if mode == 0:
            pass
        if mode == 1 and (0 <= number <= 9):
            csv_path = 'Utils/Gesture/Keypoint/keypoint_samples.csv'
            with open(csv_path, 'a', newline="") as f:
                num = self.__register_gesture_unit * 10 + number
                writer = csv.writer(f)
                writer.writerow([num, *landmark_list])
        if mode == 2 and (0 <= number <= 9) and point_history_list is not None:
            csv_path = 'Utils/Gesture/Keypoint/keypoint__history.csv'
            with open(csv_path, 'a', newline="") as f:
                writer = csv.writer(f)
                writer.writerow([number, *point_history_list])
        return

    def __get_pointer_idx():
        path = 'Utils/Gesture/Keypoint/keypoint_labels.csv'
        with open(path, mode='r', newline='') as file:
            reader = csv.reader(file)
            for index, row in enumerate(reader):
                if row and row[0] == "Pointer":
                    return index
        return -1

    def __draw_bounding_box(image, box):
        cv.rectangle(image, (box[0], box[1]), (box[2], box[3]), (0, 0, 0), 1)
        return image

    def __draw_landmarks(image, landmark_point):
        if len(landmark_point) > 0:
            # Thumb
            cv.line(image, tuple(landmark_point[2]), tuple(landmark_point[3]), (0, 0, 0), 6)
            cv.line(image, tuple(landmark_point[2]), tuple(landmark_point[3]), (255, 255, 255), 2)
            cv.line(image, tuple(landmark_point[3]), tuple(landmark_point[4]), (0, 0, 0), 6)
            cv.line(image, tuple(landmark_point[3]), tuple(landmark_point[4]), (255, 255, 255), 2)

            # Index finger
            cv.line(image, tuple(landmark_point[5]), tuple(landmark_point[6]), (0, 0, 0), 6)
            cv.line(image, tuple(landmark_point[5]), tuple(landmark_point[6]), (255, 255, 255), 2)
            cv.line(image, tuple(landmark_point[6]), tuple(landmark_point[7]), (0, 0, 0), 6)
            cv.line(image, tuple(landmark_point[6]), tuple(landmark_point[7]), (255, 255, 255), 2)
            cv.line(image, tuple(landmark_point[7]), tuple(landmark_point[8]), (0, 0, 0), 6)
            cv.line(image, tuple(landmark_point[7]), tuple(landmark_point[8]), (255, 255, 255), 2)

            # Middle finger
            cv.line(image, tuple(landmark_point[9]), tuple(landmark_point[10]), (0, 0, 0), 6)
            cv.line(image, tuple(landmark_point[9]), tuple(landmark_point[10]), (255, 255, 255), 2)
            cv.line(image, tuple(landmark_point[10]), tuple(landmark_point[11]), (0, 0, 0), 6)
            cv.line(image, tuple(landmark_point[10]), tuple(landmark_point[11]), (255, 255, 255), 2)
            cv.line(image, tuple(landmark_point[11]), tuple(landmark_point[12]), (0, 0, 0), 6)
            cv.line(image, tuple(landmark_point[11]), tuple(landmark_point[12]), (255, 255, 255), 2)

            # Ring finger
            cv.line(image, tuple(landmark_point[13]), tuple(landmark_point[14]), (0, 0, 0), 6)
            cv.line(image, tuple(landmark_point[13]), tuple(landmark_point[14]), (255, 255, 255), 2)
            cv.line(image, tuple(landmark_point[14]), tuple(landmark_point[15]), (0, 0, 0), 6)
            cv.line(image, tuple(landmark_point[14]), tuple(landmark_point[15]), (255, 255, 255), 2)
            cv.line(image, tuple(landmark_point[15]), tuple(landmark_point[16]), (0, 0, 0), 6)
            cv.line(image, tuple(landmark_point[15]), tuple(landmark_point[16]), (255, 255, 255), 2)

            # Pinky
            cv.line(image, tuple(landmark_point[17]), tuple(landmark_point[18]), (0, 0, 0), 6)
            cv.line(image, tuple(landmark_point[17]), tuple(landmark_point[18]), (255, 255, 255), 2)
            cv.line(image, tuple(landmark_point[18]), tuple(landmark_point[19]), (0, 0, 0), 6)
            cv.line(image, tuple(landmark_point[18]), tuple(landmark_point[19]), (255, 255, 255), 2)
            cv.line(image, tuple(landmark_point[19]), tuple(landmark_point[20]), (0, 0, 0), 6)
            cv.line(image, tuple(landmark_point[19]), tuple(landmark_point[20]), (255, 255, 255), 2)

            # Palm
            cv.line(image, tuple(landmark_point[0]), tuple(landmark_point[1]), (0, 0, 0), 6)
            cv.line(image, tuple(landmark_point[0]), tuple(landmark_point[1]), (255, 255, 255), 2)
            cv.line(image, tuple(landmark_point[1]), tuple(landmark_point[2]), (0, 0, 0), 6)
            cv.line(image, tuple(landmark_point[1]), tuple(landmark_point[2]), (255, 255, 255), 2)
            cv.line(image, tuple(landmark_point[2]), tuple(landmark_point[5]), (0, 0, 0), 6)
            cv.line(image, tuple(landmark_point[2]), tuple(landmark_point[5]), (255, 255, 255), 2)
            cv.line(image, tuple(landmark_point[5]), tuple(landmark_point[9]), (0, 0, 0), 6)
            cv.line(image, tuple(landmark_point[5]), tuple(landmark_point[9]), (255, 255, 255), 2)
            cv.line(image, tuple(landmark_point[9]), tuple(landmark_point[13]), (0, 0, 0), 6)
            cv.line(image, tuple(landmark_point[9]), tuple(landmark_point[13]), (255, 255, 255), 2)
            cv.line(image, tuple(landmark_point[13]), tuple(landmark_point[17]), (0, 0, 0), 6)
            cv.line(image, tuple(landmark_point[13]), tuple(landmark_point[17]), (255, 255, 255), 2)
            cv.line(image, tuple(landmark_point[17]), tuple(landmark_point[0]), (0, 0, 0), 6)
            cv.line(image, tuple(landmark_point[17]), tuple(landmark_point[0]), (255, 255, 255), 2)

        # Key Points
        for index, landmark in enumerate(landmark_point):
            if index == 0:
                cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 1: 
                cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 2:
                cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 3: 
                cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 4: 
                cv.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
            if index == 5: 
                cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 6: 
                cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 7:  
                cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 8: 
                cv.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
            if index == 9:
                cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 10:  
                cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 11:  
                cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 12:  
                cv.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
            if index == 13:  
                cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 14: 
                cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 15:  
                cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 16:  
                cv.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
            if index == 17:  
                cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 18: 
                cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 19:  
                cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 20: 
                cv.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255), -1)
                cv.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)

        return image

    def __draw_info_box(self, image, box, handedness, hand_sign_text, pointer_gesture_text, enable_pointer, is_pointer):
        if hand_sign_text in self.__valid_gesture:
            info_text = self.__valid_gesture.get(hand_sign_text)
            if self.__show_hand_label:
                info_text = handedness.classification[0].label[0:] + ':' + info_text
            text_size = cv.getTextSize(info_text, cv.FONT_HERSHEY_SIMPLEX, 0.6, 1)[0]
            text_margin_left = 5
            text_margin_bottom = 10
            label_width = max(text_size[0] + text_margin_left * 2, box[2] - box[0])
            label_height = text_size[1] + text_margin_bottom * 2
            cv.rectangle(image, (box[0], box[1]), (box[0] + label_width, box[1] - label_height), (0, 0, 0), -1)
            cv.putText(image, info_text, (box[0] + text_margin_left, box[1] - text_margin_bottom), cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv.LINE_AA)

        if enable_pointer and is_pointer:
            if pointer_gesture_text != "":
                cv.putText(image, "Pointer Gesture:" + pointer_gesture_text, (10, 60), cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 4, cv.LINE_AA)
                cv.putText(image, "Pointer Gesture:" + pointer_gesture_text, (10, 60), cv.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv.LINE_AA)
    
        return image

    def __draw_point_history(image, point_history):
        for index, point in enumerate(point_history):
            if point[0] != 0 and point[1] != 0:
                cv.circle(image, (point[0], point[1]), 1 + int(index / 2), (152, 251, 152), 2)
        return image

    def __draw_info(image, fps, mode, number, show_fps):
        if show_fps:
            cv.putText(image, "FPS:" + str(fps), (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 4, cv.LINE_AA)
            cv.putText(image, "FPS:" + str(fps), (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv.LINE_AA)

        mode_string = ['Logging Key Point', 'Logging Point History']
        if 1 <= mode <= 2:
            cv.putText(image, "MODE : " + mode_string[mode - 1], (10, 90), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2, cv.LINE_AA)
            cv.putText(image, "MODE : " + mode_string[mode - 1], (10, 90), cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv.LINE_AA)
            if 0 <= number <= 9:
                cv.putText(image, "NUM : " + str(number), (10, 110), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2, cv.LINE_AA)
                cv.putText(image, "NUM : " + str(number), (10, 110), cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv.LINE_AA)
        return image

    def __set_current_gesture(self, gesture):
        self.__gesture_lock.acquire()
        try:
            if self.__num_hands == 2:
                # self.__current_gesture["Right"] = gesture["Right"]
                # self.__current_gesture["Left"] = gesture["Left"]
                if gesture["Right"] in self.__valid_gesture:
                    self.__current_gesture["Right"] = self.__valid_gesture[gesture["Right"]]
                else:
                    self.__current_gesture["Right"] = None
                if gesture["Left"] in self.__valid_gesture:
                    self.__current_gesture["Left"] = self.__valid_gesture[gesture["Left"]]
                else:
                    self.__current_gesture["Left"] = None
            else:
                # self.__current_gesture = gesture
                if gesture in self.__valid_gesture:
                    self.__current_gesture = self.__valid_gesture[gesture]
                else:
                    self.__current_gesture = None
        finally:
            self.__gesture_lock.release()

    def get_current_gesture(self):
        self.__gesture_lock.acquire()
        try:
            return self.__current_gesture
        finally:
            self.__gesture_lock.release()

    def __set_current_frame(self, frame):
        self.__frame_lock.acquire()
        try:
            self.__current_frame = frame
        finally:
            self.__frame_lock.release()

    def get_current_frame(self):
        self.__frame_lock.acquire()
        try:
            return self.__current_frame
        finally:
            self.__frame_lock.release()

    def stop(self):
        self.__stop_flag.set()

    def is_running(self):
        return self.__is_running
    
    def start(self):
        self.__is_running = True

        # Argument parsing
        args = HandGesture.__get_args()

        use_static_image_mode = args.use_static_image_mode
        min_detection_confidence = args.min_detection_confidence
        min_tracking_confidence = args.min_tracking_confidence

        # Camera should be managed by the caller
        # cap_device = args.device
        # cap_width = args.width
        # cap_height = args.height
        # cap = cv.VideoCapture(cap_device)
        # cap.set(cv.CAP_PROP_FRAME_WIDTH, cap_width)
        # cap.set(cv.CAP_PROP_FRAME_HEIGHT, cap_height)

        # Pointer works with only one hand
        if self.__enable_pointer:
            self.__num_hands = 1

        # Load model
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(
            static_image_mode=use_static_image_mode,
            max_num_hands=self.__num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

        keypoint_classifier = KeypointClassifier()

        with open('Utils/Gesture/Keypoint/keypoint_labels.csv', encoding='utf-8-sig') as f:
            keypoint_classifier_labels = csv.reader(f)
            keypoint_classifier_labels = [row[0] for row in keypoint_classifier_labels]

        # FPS Measurement 
        if self.__show_fps:
            FpsCount = _FpsCounter(buffer_len=10)

        # Initialize mode
        mode = 0
        
        # Manage pointer
        if self.__enable_pointer:
            history_classifier = HistoryClassifier()
            
            with open('Utils/Gesture/History/history_labels.csv', encoding='utf-8-sig') as f:
                point_history_classifier_labels = csv.reader(f)
                point_history_classifier_labels = [row[0] for row in point_history_classifier_labels]

            # History
            point_history = deque(maxlen=self.__history_length)
            pointer_gesture_history = deque(maxlen=self.__history_length)

        while True and not self.__stop_flag.is_set():
            if self.__show_fps:
                fps = FpsCount.get()

            # Close camera
            key = cv.waitKey(10)
            if self.__enable_esc_exit and key == 27: # 27 = ESC
                break
            
            if self.__enable_csv_update:
                number, mode = HandGesture.__select_mode(key, mode)
            else:
                number, mode = -1, 0

            # Frame capture
            ret, image = self.__cap.read()
            if not ret:
                break
            image = cv.flip(image, 1)
            debug_image = copy.deepcopy(image)

            # Mediapipe processing
            image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = hands.process(image)
            image.flags.writeable = True

            if self.__num_hands == 2:
                temp_gesture = {"Right": None, "Left": None}
            else:
                temp_gesture = None
            if results.multi_hand_landmarks is not None:
                for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    # Bounding box calculation
                    if self.__show_bounding_box:
                        bound_box = HandGesture.__calc_bounding_box(debug_image, hand_landmarks)
                    
                    # Landmarks calculation
                    landmark_list = HandGesture.__calc_landmark_list(debug_image, hand_landmarks)

                    # Normalize landmarks
                    pre_processed_landmark_list = HandGesture.__pre_process_landmark(landmark_list)

                    if self.__enable_pointer:
                        pre_processed_point_history_list = HandGesture.__pre_process_point_history(debug_image, point_history)
                    else:
                        pre_processed_point_history_list = None
                    
                    # Update dataset file
                    self.__update_csv(number, mode, pre_processed_landmark_list,pre_processed_point_history_list)

                    # Hand sign classification
                    hand_sign_id = keypoint_classifier(pre_processed_landmark_list)
                    
                    if self.__enable_pointer:
                        if hand_sign_id == HandGesture.__get_pointer_idx():  
                            point_history.append(landmark_list[8])
                        else:
                            point_history.append([0, 0])
                        
                        # Finger gesture
                        pointer_gesture_id = 0
                        pointer_history_len = len(pre_processed_point_history_list)
                        if pointer_history_len == (self.__history_length * 2):
                            pointer_gesture_id = history_classifier(pre_processed_point_history_list)

                        # Gesture IDs
                        pointer_gesture_history.append(pointer_gesture_id)
                        most_common_pointer_id = Counter(pointer_gesture_history).most_common()

                    # Drawing elements
                    if self.__show_bounding_box:
                        debug_image = HandGesture.__draw_bounding_box(debug_image, bound_box)

                    if self.__show_landmarks:
                        debug_image = HandGesture.__draw_landmarks(debug_image, landmark_list)
                    
                    is_pointer = hand_sign_id == HandGesture.__get_pointer_idx()

                    if self.__enable_pointer and is_pointer:
                        history_label = point_history_classifier_labels[most_common_pointer_id[0][0]]
                    else:
                        history_label = None

                    if self.__show_info_box:
                        debug_image = self.__draw_info_box(
                            debug_image,
                            bound_box,
                            handedness,
                            keypoint_classifier_labels[hand_sign_id],
                            history_label,
                            self.__enable_pointer,
                            is_pointer
                        )
                    if self.__num_hands == 2:
                        temp_gesture[handedness.classification[0].label[0:]] = keypoint_classifier_labels[hand_sign_id]
                    else:
                        temp_gesture = keypoint_classifier_labels[hand_sign_id]
            else:
                if self.__enable_pointer:
                    point_history.append([0, 0])

            if self.__enable_pointer:
                debug_image = HandGesture.__draw_point_history(debug_image, point_history)
            
            if self.__show_info_box:
                debug_image = HandGesture.__draw_info(debug_image, fps, mode, number, self.__show_fps)

            # Frame should be managed by the caller
            # cv.imshow('Hand Gesture Recognition', debug_image)

            self.__set_current_gesture(temp_gesture)
            self.__set_current_frame(debug_image)

            time.sleep(self.__sleep_time)

        # Camera and window should be managed by the caller
        # self.__cap.release()
        # cv.destroyAllWindows()

        self.__is_running = False
        self.stop() # Stop the thread when the loop ends due to a esc key press