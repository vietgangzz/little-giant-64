class_name JellyBlock
extends AnimatableBody3D
## A wobbly rice-cake block (bánh chưng) that drifts along an axis. Landing on it squishes it.

var travel := Vector3(0, 1.6, 0)
var period := 4.0
var phase := 0.0
var size := 1.35 ## scale of the 1.6 m rice cake
var _home := Vector3.ZERO
var _t := 0.0
var _visual: Node3D
var _sensor: Area3D
var _was_on := false


func _ready() -> void:
	add_to_group("unsafe")
	sync_to_physics = false
	collision_layer = 8
	collision_mask = 0
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(1.6, 1.6, 1.6) * size
	cs.shape = box
	cs.position.y = 0.8 * size
	add_child(cs)
	_visual = Props.make("jelly_block")
	_visual.scale = Vector3.ONE * size
	add_child(_visual)
	_sensor = Area3D.new()
	_sensor.collision_layer = 0
	_sensor.collision_mask = 2
	var ss := CollisionShape3D.new()
	var b := BoxShape3D.new()
	b.size = Vector3(1.5 * size, 0.4, 1.5 * size)
	ss.shape = b
	ss.position.y = 1.6 * size + 0.15
	_sensor.add_child(ss)
	add_child(_sensor)
	_home = global_position
	_t = phase


func _physics_process(delta: float) -> void:
	_t += delta
	global_position = _home + travel * (0.5 - 0.5 * cos(_t * TAU / period))
	var on := false
	for body in _sensor.get_overlapping_bodies():
		if body is Player:
			on = true
	if on and not _was_on:
		_visual.scale = Vector3(1.18, 0.8, 1.18) * size
		create_tween().tween_property(_visual, "scale", Vector3.ONE * size, 0.6).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
	_was_on = on
