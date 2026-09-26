class_name Crusher
extends AnimatableBody3D
## A heavy bronze drum-block that hovers, shivers and slams down. You can ride on its top.

var rest_y := 0.0 ## ground level under it
var lift := 4.2
var period := 3.4
var phase := 0.0
var _t := 0.0
var _visual: Node3D
var _state := 0 ## 0 up, 1 shiver, 2 falling, 3 down, 4 rising
var _vel := 0.0
var _hurt: Area3D


func _ready() -> void:
	sync_to_physics = false
	collision_layer = 1
	collision_mask = 0
	# the model is a bronze drum standing on its rim, face toward +Z
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(1.78, 1.8, 0.9)
	cs.shape = box
	cs.position.y = 0.9
	add_child(cs)
	_visual = Props.make("crusher")
	add_child(_visual)
	_hurt = Area3D.new()
	_hurt.collision_layer = 0
	_hurt.collision_mask = 2
	var hs := CollisionShape3D.new()
	var b := BoxShape3D.new()
	b.size = Vector3(1.7, 0.5, 0.95)
	hs.shape = b
	hs.position.y = -0.15
	_hurt.add_child(hs)
	add_child(_hurt)
	global_position.y = rest_y + lift
	_t = phase


func _physics_process(delta: float) -> void:
	_t += delta
	var y := global_position.y
	match _state:
		0:
			if _t >= period * 0.45:
				_state = 1
				_t = 0.0
		1:
			_visual.position.x = sin(_t * 90.0) * 0.05
			if _t >= 0.45:
				_visual.position.x = 0
				_state = 2
				_vel = 0.0
		2:
			_vel += 70.0 * delta
			y -= _vel * delta
			for b in _hurt.get_overlapping_bodies():
				if b is Player:
					(b as Player).damage(global_position + Vector3(0, 2, 0))
			if y <= rest_y:
				y = rest_y
				_state = 3
				_t = 0.0
				Sound.play_at("crusher_slam", global_position, 2.0)
				Fx.dust(Vector3(global_position.x, rest_y, global_position.z), 10, 1.4, 0.3, 0.5)
				Fx.ring(Vector3(global_position.x, rest_y + 0.05, global_position.z), Color(1, 1, 1, 1), 4.0, 0.4)
				var p := get_tree().get_first_node_in_group("player") as Node3D
				if p and p.global_position.distance_to(global_position) < 14.0:
					Fx.shake(0.35 * (1.0 - p.global_position.distance_to(global_position) / 14.0), 0.25)
		3:
			if _t >= 1.0:
				_state = 4
		4:
			y = move_toward(y, rest_y + lift, 2.2 * delta)
			if y >= rest_y + lift:
				_state = 0
				_t = 0.0
	global_position.y = y
