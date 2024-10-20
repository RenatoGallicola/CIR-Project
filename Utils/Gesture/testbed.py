from hand_gesture_recognition import HandGesture as hg

num_hands=2 # Set the number of hands to be detected
enable_pointer=True # Set to True to enable the pointer gestures
show_fps=True # Set to True to show the FPS on the screen
show_bounding_box=True # Set to True to show the bounding box around the hands
show_info_box=True # Set to True to show the information box on the screen
enable_csv_update = False # Set to True to update the csv file with the gesture data

hg.start(num_hands,enable_pointer, show_fps, show_bounding_box, show_info_box, enable_csv_update)