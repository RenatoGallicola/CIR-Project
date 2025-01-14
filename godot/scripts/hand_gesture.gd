extends TextureRect

var server: UDPServer

func _ready() -> void:
	server = UDPServer.new()
	server.listen(4242)

func _decode_image(frame_data: PackedByteArray) -> Image:
	var image = Image.new()
	image.load_jpg_from_buffer(frame_data)
	return image

func _process(delta: float) -> void:
	server.poll()
	if GuardDialogueState.guard_finished == false and GuardDialogueState.guard_started == true:
		activate()
	
func activate() -> void:
	if server.is_connection_available():
		var peer = server.take_connection()
		var data = peer.get_packet()
		var json = JSON.new()
		var parsed_data = json.parse(data.get_string_from_utf8())
		
		if parsed_data == OK:
			var received_data = json.data
			
			var image_data = received_data["image"]
			var result = received_data["result"]
			var move = received_data["move"]
			var outcome = received_data["outcome"]
			var image = null
			if image_data != null:
				var decoded_image = Marshalls.base64_to_raw(image_data)
				image = _decode_image(decoded_image)

			if image != null:
				texture = ImageTexture.create_from_image(image)
			
			if !GuardDialogueState.processing:
				GuardDialogueState.round_score = result
				GuardDialogueState.player_move = move[0]
				GuardDialogueState.guard_move = move[1]
				GuardDialogueState.outcome = outcome
		else:
			print("Failed to parse JSON data.")
