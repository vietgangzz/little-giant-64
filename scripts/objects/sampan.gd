class_name Sampan
extends AnimatableBody3D
## A boat that ferries the hero between two points, easing at each end and rocking on the swell.

var a := Vector3.ZERO
var b := Vector3.ZERO
var trip := 6.0 ## seconds one way
var pause := 1.2
var phase := 0.0
var prop_name := "sampan"
var deck := Vector3(1.4, 0.5, 3.4) ## collision box
var deck_y := 0.35 ## centre height of the box
var rock := 1.0
var _t := 0.0
var _visual: Node3D


func _ready() -> void:
	add_to_group("unsafe")
	sync_to_physics = false
	collision_layer = 8
	collision_mask = 0
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = deck
	cs.shape = box
	cs.position.y = deck_y
	add_child(cs)
	_visual = Props.make(prop_name)
	add_child(_visual)
	_t = phase
	global_position = a


func _physics_process(delta: float) -> void:
	_t += delta
	var cycle := (trip + pause) * 2.0
	var u := fmod(_t, cycle)
	var k := 0.0
	var going := true
	if u < trip:
		k = u / trip
	elif u < trip + pause:
		k = 1.0
	elif u < trip * 2.0 + pause:
		k = 1.0 - (u - trip - pause) / trip
		going = false
	else:
		k = 0.0
	k = k * k * (3.0 - 2.0 * k)
	var pos := a.lerp(b, k)
	pos.y += sin(_t * 1.6) * 0.06
	global_position = pos
	var dir := (b - a).normalized()
	rotation.y = atan2(dir.x, dir.z)
	_visual.rotation.z = sin(_t * 1.3) * 0.04 * rock
	_visual.rotation.x = sin(_t * 1.1 + 1.0) * 0.025 * rock
