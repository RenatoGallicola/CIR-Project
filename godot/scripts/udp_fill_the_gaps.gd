extends Node

var server: UDPServer
var message: String = "start"

func _ready() -> void:
	server = UDPServer.new()
	server.listen(4243)

func _decode_image(frame_data: PackedByteArray) -> Image:
	var image = Image.new()
	image.load_jpg_from_buffer(frame_data)
	return image

func _process(delta: float) -> void:
	server.poll()
	
	if WizardDialogueState.check == true:
			if WizardDialogueState.first_word == "coin" \
			and WizardDialogueState.second_word == "fire" \
			and WizardDialogueState.third_word == "emerald":
				WizardDialogueState.correct = true
				message = "stop"
				
	if WizardDialogueState.reset == true:
			WizardDialogueState.first_word = "___"
			WizardDialogueState.second_word = "___"
			WizardDialogueState.third_word = "___"
	
	if WizardDialogueState.white_finished == false and WizardDialogueState.white_started == true:
		activate()
	
func activate() -> void:
	if server.is_connection_available():
		var peer = server.take_connection()
		var data = peer.get_packet()
		if WizardDialogueState.white_waiting == true:
			peer.put_packet(message.to_utf8_buffer())
		else:
			return
		
		var json = JSON.new()
		var parsed_data = json.parse(data.get_string_from_utf8())

		if parsed_data == OK:
			
			var received_data = json.data
			
			var word = received_data["word"]
			var error = received_data["error"]
			
			if error:
				WizardDialogueState.error = true
				return 
				
			WizardDialogueState.error = false
			WizardDialogueState.last_word = word
			
		else:
			print("Failed to parse JSON data.")
