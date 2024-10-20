import keyboard
import threading
import time
from hand_gesture_recognition import HandGesture as hg

# Function to quit the testbed by pressing the "q" key
def quit_testbed(hand_gesture):
    while hand_gesture.is_running():
        if keyboard.read_key() == "q":
            hand_gesture.stop() # Use this command to stop the thread and release the camera if enable_esc_exit is set to False
            break

num_hands=2 # Set the number of hands to be detected
enable_pointer=False # Set to True to enable the pointer gestures
show_fps=True # Set to True to show the FPS on the screen
show_bounding_box=True # Set to True to show the bounding box around the hands
show_info_box=True # Set to True to show the information box on the screen
enable_csv_update = False # Set to True to update the csv file with the gesture data
enable_esc_exit = True # Set to True to enable the ESC key to exit the program

hand_gesture = hg(num_hands,enable_pointer, show_fps, show_bounding_box, show_info_box, enable_csv_update, enable_esc_exit)

thread_hand = threading.Thread(target=hand_gesture.start)
thread_hand.start()

thread_quit = threading.Thread(target=lambda: quit_testbed(hand_gesture))
thread_quit.start()

gesture = {"Right": None, "Left": None}
sleep_time = 0.1
while hand_gesture.is_running():
    curr = hand_gesture.get_current_gesture()
    if curr is not None and curr["Right"] != gesture["Right"] or curr["Left"] != gesture["Left"]:
        gesture["Right"] = curr["Right"]
        gesture["Left"] = curr["Left"]
        print("Right:", gesture["Right"], "    Left:", gesture["Left"])
    time.sleep(sleep_time)

thread_hand.join()
thread_quit.join()