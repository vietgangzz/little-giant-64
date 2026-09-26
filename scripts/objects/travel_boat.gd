class_name TravelBoat
extends StaticBody3D
## A moored junk boat. Stand on its deck for a moment and it sails you to another level.

var destination := "halong"
var deck_height := 1.55 ## junk_boat main deck
var deck_size := Vector3(2.8, 0.3, 8.0)
var _sensor: Area3D
var _on := 0.0
var _leaving := false
var _visual: Node3D
var _label: Label3D
var _t := 0.0


func _ready() -> void:
	collision_layer = 1
	collision_mask = 0
	_visual = Props.make("junk_boat" if Props.exists("junk_boat") else "sampan")
	if not Props.exists("junk_boat"):
		_visual.scale = Vector3(2.2, 1.6, 2.4)
	add_child(_visual)
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = deck_size
	cs.shape = box
	cs.position.y = deck_height - deck_size.y * 0.5
	add_child(cs)
	_sensor = Area3D.new()
	_sensor.collision_layer = 0
	_sensor.collision_mask = 2
	var ss := CollisionShape3D.new()
	var sb := BoxShape3D.new()
	sb.size = Vector3(deck_size.x, 1.2, deck_size.z)
	ss.shape = sb
	ss.position.y = deck_height + 0.6
	_sensor.add_child(ss)
	add_child(_sensor)
	_label = Label3D.new()
	_label.text = "⛵ " + Game.level_name(destination)
	_label.font = UiKit.display_font()
	_label.font_size = 96
	_label.outline_size = 22
	_label.modulate = Color("#fff6d8")
	_label.outline_modulate = Color(0.05, 0.08, 0.2)
	_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_label.pixel_size = 0.01
	_label.position = Vector3(0, deck_height + 5.2, 0)
	add_child(_label)
	Game.language_changed.connect(func(): _label.text = "⛵ " + Game.level_name(destination))


func _physics_process(delta: float) -> void:
	_t += delta
	_visual.rotation.z = sin(_t * 1.1) * 0.02
	_label.position.y = deck_height + 5.2 + sin(_t * 2.0) * 0.15
	if _leaving or Game.in_cutscene:
		return
	var here := false
	for b in _sensor.get_overlapping_bodies():
		if b is Player and (b as Player).is_on_floor():
			here = true
	_on = _on + delta if here else 0.0
	if _on > 1.0:
		_leave()


func _leave() -> void:
	_leaving = true
	Game.in_cutscene = true
	Sound.play("checkpoint", -2.0)
	get_tree().call_group("hud", "toast", Game.t("All aboard! Sailing to %s…", "Lên thuyền! Đi %s…") % Game.level_name(destination), 2.0)
	get_tree().call_group("player", "lock", true)
	var tw := create_tween()
	tw.tween_property(self, "position", position + global_transform.basis.z * -6.0, 1.6).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
	get_tree().call_group("hud", "fade", 1.0, 1.2)
	await get_tree().create_timer(1.6).timeout
	if Game.args.has("trailer"):
		return # the trailer cuts to the next level itself
	Game.save()
	Game.travel(destination)
