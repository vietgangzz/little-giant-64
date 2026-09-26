class_name Star
extends Area3D
## A bronze Đông Sơn star. Hidden stars wait in a group and appear when their challenge is done
## (`reveal`). Stars already owned from a previous save show as a pale "ghost" star.

var id := ""
var hidden_until := "" ## group name that reveals it: lantern_star / coin_star / crab_star
var _visual: Node3D
var _beam: MeshInstance3D
var _glow: OmniLight3D
var _t := 0.0
var _taken := false
var _active := true


func _ready() -> void:
	add_to_group("star")
	collision_layer = 0
	collision_mask = 2
	monitorable = false
	var cs := CollisionShape3D.new()
	var s := SphereShape3D.new()
	s.radius = 0.9
	cs.shape = s
	cs.position.y = 0.6
	add_child(cs)
	_visual = Props.make("star", true, Game.has_star(id))
	_visual.scale = Vector3.ONE * 1.25
	add_child(_visual)
	if Game.has_star(id):
		_ghost()
	_beam = Fx.beam(self, 16.0, 0.8, Color(1.0, 0.86, 0.45))
	_glow = OmniLight3D.new()
	_glow.light_color = Color(1.0, 0.85, 0.5)
	_glow.light_energy = 1.6
	_glow.omni_range = 5.0
	_glow.position.y = 0.6
	add_child(_glow)
	_add_twinkles()
	body_entered.connect(_on_body)
	if hidden_until != "":
		add_to_group(hidden_until)
		_set_active(false)


func _ghost() -> void:
	for mi in Props._meshes(_visual):
		for s in mi.mesh.get_surface_count():
			var m := mi.get_surface_override_material(s) as ShaderMaterial
			if m:
				m = m.duplicate()
				m.set_shader_parameter("albedo", Color(0.55, 0.75, 1.0))
				m.set_shader_parameter("emission_color", Color(0.4, 0.6, 1.0))
				m.set_shader_parameter("emission_energy", 0.4)
				mi.set_surface_override_material(s, m)


func _add_twinkles() -> void:
	var p := GPUParticles3D.new()
	p.amount = 14
	p.lifetime = 1.4
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	pm.emission_sphere_radius = 1.1
	pm.gravity = Vector3(0, 0.6, 0)
	pm.scale_min = 0.5
	pm.scale_max = 1.0
	var curve := Curve.new()
	curve.add_point(Vector2(0, 0))
	curve.add_point(Vector2(0.5, 1))
	curve.add_point(Vector2(1, 0))
	var ct := CurveTexture.new()
	ct.curve = curve
	pm.scale_curve = ct
	pm.color = Color(1, 0.92, 0.6)
	p.process_material = pm
	var quad := QuadMesh.new()
	quad.size = Vector2(0.3, 0.3)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.vertex_color_use_as_albedo = true
	m.albedo_texture = Fx.star_tex
	quad.material = m
	p.draw_pass_1 = quad
	p.position.y = 0.6
	add_child(p)


func _set_active(on: bool) -> void:
	_active = on
	visible = on
	monitoring = on


func reveal() -> void:
	if _active or _taken:
		return
	_set_active(true)
	scale = Vector3.ONE * 0.01
	Sound.play("star_appear", 0.0)
	Fx.star_burst(global_position + Vector3.UP * 0.6)
	create_tween().tween_property(self, "scale", Vector3.ONE, 0.8).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
	get_tree().call_group("world", "show_star_reveal", self)


func _process(delta: float) -> void:
	_t += delta
	if _visual and not _taken:
		_visual.rotation.y = _t * 1.8
		_visual.position.y = 0.35 + sin(_t * 2.0) * 0.18
	if _glow:
		_glow.light_energy = 1.4 + sin(_t * 3.0) * 0.4


func _on_body(b: Node) -> void:
	if _taken or not _active or not b.is_in_group("player"):
		return
	_taken = true
	set_deferred("monitoring", false)
	get_tree().call_group("world", "star_cutscene", self, b)


## Called by the cutscene once the star has flown into the player's hands.
func consume() -> void:
	var tw := create_tween().set_parallel(true)
	tw.tween_property(self, "scale", Vector3.ONE * 0.01, 0.35).set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_BACK)
	if _beam:
		tw.tween_property(_beam, "scale", Vector3(0.01, 1, 0.01), 0.3)
	tw.chain().tween_callback(queue_free)
