class_name Dragon
extends Node3D
## Rồng: a long friendly dragon flying a closed loop over the bay. Every body segment is a
## moving platform, so the hero can ride its back, run up to the head, and jump off at the top.

var path: Curve3D
var segments := 14
var spacing := 1.6 ## body segment length (joints at ±0.8)
var slow_speed := 2.2 ## over the boarding stretch (low)
var fast_speed := 6.5
var top_offset := 0.56 ## saddle height above the spine (from the Blender prop)
var head: Node3D
var _parts: Array[Node3D] = []
var _s := 0.0
var _length := 0.0
var _baked: PackedVector3Array


func _ready() -> void:
	add_to_group("dragon")
	_length = path.get_baked_length()
	var names := ["dragon_head"]
	for i in segments:
		names.append("dragon_body")
	names.append("dragon_tail")
	for i in names.size():
		var body := AnimatableBody3D.new()
		body.sync_to_physics = false
		body.collision_layer = 8
		body.collision_mask = 0
		body.add_to_group("unsafe")
		var visual := Props.make(names[i])
		if not Props.exists(names[i]):
			visual.scale = Vector3.ONE * 0.9
		# Blender −Y front arrives as +Z; the chain faces its direction of travel (−Z)
		visual.rotation.y = PI
		body.add_child(visual)
		var cs := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = Vector3(2.0, 0.5, spacing + 0.35)
		cs.shape = box
		cs.position.y = top_offset - 0.25
		# the head reaches forward from the neck joint, the tail back from the last joint
		if i == 0:
			box.size.z = 1.6
			cs.position.z = -0.7
		elif i == names.size() - 1:
			box.size.z = 1.8
			cs.position.z = 0.9
		body.add_child(cs)
		add_child(body)
		_parts.append(body)
		if i % 4 == 2 and names[i] == "dragon_body" and Props.exists("dragon_leg"):
			for side in [-1.0, 1.0]:
				var leg := Props.make("dragon_leg")
				leg.position = Vector3(0.6 * side, -0.3, 0)
				leg.scale.x = side
				visual.add_child(leg)
	head = _parts[0]
	_s = _length * 0.02


func _speed_at(s: float) -> float:
	var p := path.sample_baked(fmod(s, _length))
	return lerpf(slow_speed, fast_speed, clampf((p.y - 1.5) / 6.0, 0.0, 1.0))


func _physics_process(delta: float) -> void:
	_s = fmod(_s + _speed_at(_s) * delta, _length)
	var t := Time.get_ticks_msec() / 1000.0
	for i in _parts.size():
		var s := fmod(_s - _offset(i) + _length * 4.0, _length)
		var p := path.sample_baked(s, true)
		var ahead := path.sample_baked(fmod(s + 0.8, _length), true)
		var dir := (ahead - p).normalized()
		# a gentle sine wiggle travelling down the body
		var side := dir.cross(Vector3.UP).normalized()
		p += side * sin(t * 2.2 - i * 0.55) * 0.18 * (0.3 if i < 2 else 1.0)
		var basis := Basis.looking_at(dir, Vector3.UP)
		_parts[i].global_transform = Transform3D(basis, global_position + p)


## Distance behind the head's neck joint for part i (head 0, bodies, tail last).
func _offset(i: int) -> float:
	if i == 0:
		return 0.0
	if i == _parts.size() - 1:
		return spacing * 0.5 + (segments - 1) * spacing + spacing * 0.5
	return spacing * 0.5 + (i - 1) * spacing


## Where along the path the head is (world space) — the bot uses it.
func head_position() -> Vector3:
	return head.global_position
