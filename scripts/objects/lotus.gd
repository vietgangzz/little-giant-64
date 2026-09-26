class_name LotusPad
extends AnimatableBody3D
## A lotus leaf you can stand on for a moment before it sinks. It comes back up a little later.

var sink_after := 0.7
var _home := Vector3.ZERO
var _standing := 0.0
var _state := 0 ## 0 float, 1 sinking, 2 under, 3 rising
var _t := 0.0
var _visual: Node3D
var _sensor: Area3D
var _phase := randf() * TAU


func _ready() -> void:
	add_to_group("unsafe")
	sync_to_physics = false
	collision_layer = 8
	collision_mask = 0
	var cs := CollisionShape3D.new()
	var cyl := CylinderShape3D.new()
	cyl.radius = 1.0
	cyl.height = 0.3
	cs.shape = cyl
	cs.position.y = 0.0
	add_child(cs)
	_visual = Props.make("lotus_pad")
	add_child(_visual)
	if randf() < 0.35:
		var f := Props.make("lotus_flower")
		f.position = Vector3(0.45, 0.08, -0.2)
		f.scale = Vector3.ONE * 0.7
		_visual.add_child(f)
	_sensor = Area3D.new()
	_sensor.collision_layer = 0
	_sensor.collision_mask = 2
	var ss := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(1.9, 0.6, 1.9)
	ss.shape = box
	ss.position.y = 0.45
	_sensor.add_child(ss)
	add_child(_sensor)
	_home = global_position


func _physics_process(delta: float) -> void:
	_t += delta
	var on := false
	for b in _sensor.get_overlapping_bodies():
		if b is Player:
			on = true
	var y := global_position.y
	match _state:
		0:
			y = _home.y + sin(_t * 1.5 + _phase) * 0.04
			if on:
				_standing += delta
				_visual.rotation.x = sin(_t * 20.0) * 0.03 * _standing
				if _standing > sink_after:
					_state = 1
					Sound.play_at("splash", global_position, -10.0, 1.4)
			else:
				_standing = maxf(_standing - delta, 0.0)
				_visual.rotation.x = 0
		1:
			y -= 1.6 * delta
			if y < _home.y - 1.4:
				_state = 2
				_t = 0.0
		2:
			if _t > 2.5:
				_state = 3
		3:
			y = move_toward(y, _home.y, 1.4 * delta)
			if y >= _home.y:
				_state = 0
				_standing = 0.0
	global_position.y = y
