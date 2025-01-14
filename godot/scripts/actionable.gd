extends Area2D

@export var dialogue_resource: DialogueResource
@export var dialogue_start: String = "start"
@export var dialogue_character: String
@export var colliders: Array[CollisionShape2D]
@export var dialogue: bool = true
@export var switch_scene: bool = false
@export var scene: PackedScene

func action() -> void:
	if dialogue:
		DialogueManager.show_example_dialogue_balloon(dialogue_resource, dialogue_start)
	elif switch_scene == true:
		get_tree().change_scene_to_packed(scene)
	else:
		WizardDialogueState.wizard_finished = false
		WizardDialogueState.wizard_started = false
		if WizardDialogueState.correct == true:
			deactivate_colliders()
			return
		activate_colliders()
		
func get_character() -> String:
	return dialogue_character
	
func deactivate_colliders() -> void:
	for c in colliders:
		c.disabled = true

func activate_colliders() -> void:
	for c in colliders:
		c.disabled = false
