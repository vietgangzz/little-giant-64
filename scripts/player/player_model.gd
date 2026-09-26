class_name PlayerModel
extends Node3D
## The Blender mascot (assets/models/mascot.glb) with its clips, plus what code adds on top:
## facing, lean into turns, squash-and-stretch springs, blinks, and spring-bone physics on the
## rays and the cape.

const MASCOT := "res://assets/models/mascot.glb"
const LOOPS := ["idle", "walk", "run", "fall", "wall_slide", "dance", "sleep"]
const FALLBACK := {
	"idle_look": "idle", "sleep": "idle", "wall_slide": "fall", "ground_pound_land": "land",
	"star_get": "wave", "dance": "idle", "hurt": "fall", "wave": "idle", "double_jump": "jump",
	"dash": "run", "ground_pound": "fall",
}

var anim: AnimationPlayer
var skeleton: Skeleton3D
var current := ""
var tilt: Node3D
var body: Node3D
var springs: SpringBoneSimulator3D

var _squash := Vector3.ONE
var _squash_vel := Vector3.ZERO
var _yaw := 0.0
var _bank := 0.0
var _pitch := 0.0
var _last_facing := Vector3.BACK


func _ready() -> void:
	tilt = Node3D.new()
	tilt.name = "Tilt"
	add_child(tilt)
	if ResourceLoader.exists(MASCOT):
		var scene: PackedScene = load(MASCOT)
		body = scene.instantiate()
		tilt.add_child(body)
		Fx.toonify(body, true, 0.014, true)
		anim = _find(body, "AnimationPlayer") as AnimationPlayer
		skeleton = _find(body, "Skeleton3D") as Skeleton3D
		_setup_anims()
		_setup_springs()
		set_cape(Game.cape)
	else:
		body = _placeholder()
		tilt.add_child(body)
	play("idle", 0.0)


func _find(n: Node, cls: String) -> Node:
	if n.get_class() == cls:
		return n
	for c in n.get_children():
		var f := _find(c, cls)
		if f:
			return f
	return null


func _setup_anims() -> void:
	if anim == null:
		return
	for lib_name in anim.get_animation_library_list():
		var lib := anim.get_animation_library(lib_name)
		for n in lib.get_animation_list():
			var a := lib.get_animation(n)
			a.loop_mode = Animation.LOOP_LINEAR if String(n) in LOOPS else Animation.LOOP_NONE
	anim.playback_default_blend_time = 0.15


func has_anim(n: String) -> bool:
	return anim != null and anim.has_animation(n)


## Cross-fades to `n`. Looping clips keep playing if already current (only the speed changes);
## one-shots restart.
func play(n: String, blend := 0.15, speed := 1.0) -> void:
	if anim == null:
		current = n
		return
	var target := n
	while not anim.has_animation(target) and FALLBACK.has(target):
		target = FALLBACK[target]
	if not anim.has_animation(target):
		return
	if current == n and n in LOOPS and anim.is_playing():
		anim.speed_scale = speed
		return
	current = n
	anim.speed_scale = speed
	anim.play(target, blend)


func is_playing_oneshot() -> bool:
	return anim != null and anim.is_playing() and not (current in LOOPS)


func finished_current() -> bool:
	if anim == null:
		return true
	if not anim.is_playing():
		return true
	return anim.current_animation_position >= anim.current_animation_length - 0.02


## Holds a prop in the right hand (the star during STAR GET). Returns the attachment.
func hold(node: Node3D) -> BoneAttachment3D:
	if skeleton == null or skeleton.find_bone("hand.R") < 0:
		add_child(node)
		node.position = Vector3(0.4, 1.6, 0)
		return null
	var att := BoneAttachment3D.new()
	att.bone_name = "hand.R"
	skeleton.add_child(att)
	att.add_child(node)
	node.position = Vector3(0, 0.12, 0)
	return att


func squash(s: Vector3) -> void:
	_squash = s
	_squash_vel = Vector3.ZERO


func set_cape(on: bool) -> void:
	if body == null:
		return
	for mi in _all_meshes(body):
		if mi.name.to_lower().contains("cape"):
			mi.visible = on


func _all_meshes(n: Node) -> Array[MeshInstance3D]:
	var out: Array[MeshInstance3D] = []
	if n is MeshInstance3D:
		out.append(n)
	for c in n.get_children():
		out.append_array(_all_meshes(c))
	return out


func update_visual(p: Player, delta: float) -> void:
	var f := p.facing
	var target_yaw := atan2(f.x, f.z)
	_yaw = lerp_angle(_yaw, target_yaw, clampf(delta * 18.0, 0.0, 1.0))
	rotation.y = _yaw
	# bank into turns and lean into speed
	var turn := _last_facing.signed_angle_to(f, Vector3.UP) / maxf(delta, 0.0001)
	_last_facing = f
	var hs := Vector2(p.velocity.x, p.velocity.z).length()
	var on_ground := p.state == Player.S.GROUND
	var bank_target := clampf(-turn * 0.05 * hs / Player.RUN_SPEED, -0.35, 0.35) if on_ground else 0.0
	var pitch_target := clampf(hs / Player.RUN_SPEED, 0.0, 1.2) * 0.1 if on_ground else 0.0
	_bank = lerpf(_bank, bank_target, clampf(delta * 8.0, 0.0, 1.0))
	_pitch = lerpf(_pitch, pitch_target, clampf(delta * 6.0, 0.0, 1.0))
	tilt.rotation = Vector3(_pitch, 0.0, _bank)
	# a critically-damped-ish spring pulls the squash back to 1
	var k := 320.0
	var damp := 18.0
	_squash_vel += (Vector3.ONE - _squash) * k * delta - _squash_vel * damp * delta
	_squash += _squash_vel * delta
	tilt.scale = _squash
	if springs:
		# wind from motion: the cape streams back when running
		springs.external_force = -p.velocity * 0.012


# ------------------------------------------------------------------ spring bones

func _setup_springs() -> void:
	if skeleton == null:
		return
	springs = SpringBoneSimulator3D.new()
	springs.name = "Springs"
	skeleton.add_child(springs)
	var chains := []
	for i in [1, 2, 3]:
		chains.append({"root": "ray.%d" % i, "end": "ray.%d.tip" % i, "stiff": 3.2, "drag": 0.35, "grav": 0.0, "radius": 0.04})
	for side in ["L", "M", "R"]:
		chains.append({"root": "cape.%s.1" % side, "end": "cape.%s.3" % side, "stiff": 0.9, "drag": 0.3, "grav": 1.4, "radius": 0.05, "extend": 0.12})
	var valid := chains.filter(func(c): return skeleton.find_bone(c["root"]) >= 0 and skeleton.find_bone(c["end"]) >= 0)
	springs.setting_count = valid.size()
	for i in valid.size():
		var c: Dictionary = valid[i]
		springs.set_root_bone_name(i, c["root"])
		springs.set_end_bone_name(i, c["end"])
		if c.has("extend"):
			springs.set_extend_end_bone(i, true)
			springs.set_end_bone_length(i, c["extend"])
		springs.set_stiffness(i, c["stiff"])
		springs.set_drag(i, c["drag"])
		springs.set_gravity(i, c["grav"])
		springs.set_gravity_direction(i, Vector3.DOWN)
		springs.set_radius(i, c["radius"])
	# the body is a sphere the cape can't swing through
	if skeleton.find_bone("spine") >= 0:
		var col := SpringBoneCollisionSphere3D.new()
		col.bone_name = "spine"
		col.radius = 0.36
		col.position_offset = Vector3(0, 0.0, 0.0)
		springs.add_child(col)
	if skeleton.find_bone("hips") >= 0:
		var col2 := SpringBoneCollisionSphere3D.new()
		col2.bone_name = "hips"
		col2.radius = 0.44
		springs.add_child(col2)


# ------------------------------------------------------------------ fallback

## Used until the Blender export exists: a lime pebble with the brand colours.
func _placeholder() -> Node3D:
	var root := Node3D.new()
	var b := MeshInstance3D.new()
	var s := SphereMesh.new()
	s.radius = 0.55
	s.height = 1.1
	b.mesh = s
	b.position.y = 0.6
	b.scale = Vector3(1.0, 1.0, 0.65)
	b.material_override = Fx.toon_material(Color("#d5f64b"))
	root.add_child(b)
	for x in [-0.18, 0.18]:
		var e := MeshInstance3D.new()
		var em := SphereMesh.new()
		em.radius = 0.07
		em.height = 0.14
		e.mesh = em
		e.position = Vector3(x, 0.7, 0.34)
		e.material_override = Fx.toon_material(Color("#234d37"))
		root.add_child(e)
	return root
