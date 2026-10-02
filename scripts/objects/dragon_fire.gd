class_name DragonFire
extends Node3D
## Dragon Bridge's party trick: every few seconds the golden head roars, breathes a jet of
## fire, then sprays water. The fire hurts anyone standing in front of the mouth.

var period := 7.0
var phase := 0.0
var reach := 7.0 ## metres the jet carries forward (local −Z)
var _t := 0.0
var _fire: GPUParticles3D
var _water: GPUParticles3D
var _hurt: Area3D
var _light: OmniLight3D
var _burning := false


func _ready() -> void:
	_t = phase
	_fire = _jet(Color(1.0, 0.78, 0.30), Color(1.0, 0.32, 0.08), 140, 13.0, 1.7, true)
	_water = _jet(Color(0.92, 0.97, 1.0), Color(0.62, 0.86, 1.0), 150, 14.0, 1.3, false)
	_hurt = Area3D.new()
	_hurt.collision_layer = 0
	_hurt.collision_mask = 2
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(2.6, 2.6, reach)
	cs.shape = box
	cs.position = Vector3(0, -0.6, -reach * 0.5)
	_hurt.add_child(cs)
	add_child(_hurt)
	_light = OmniLight3D.new()
	_light.light_color = Color(1.0, 0.6, 0.25)
	_light.omni_range = 10.0
	_light.light_energy = 0.0
	_light.visible = false
	_light.position = Vector3(0, 0, -2.5)
	add_child(_light)


func _jet(c0: Color, c1: Color, amount: int, speed: float, size: float, additive: bool) -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.amount = amount if not Game.is_phone() else int(amount * 0.6)
	p.lifetime = 0.85
	p.emitting = false
	p.local_coords = false
	var pm := ParticleProcessMaterial.new()
	pm.direction = Vector3(0, -0.12, -1)
	pm.spread = 9.0
	pm.initial_velocity_min = speed * 0.75
	pm.initial_velocity_max = speed
	pm.gravity = Vector3(0, -3.0 if additive else -14.0, 0)
	pm.damping_min = 2.0
	pm.damping_max = 4.0
	pm.scale_min = 0.6
	pm.scale_max = 1.3
	var curve := Curve.new()
	curve.add_point(Vector2(0, 0.35))
	curve.add_point(Vector2(0.35, 1.0))
	curve.add_point(Vector2(1, 0.2))
	var ct := CurveTexture.new()
	ct.curve = curve
	pm.scale_curve = ct
	var g := Gradient.new()
	g.colors = PackedColorArray([c0, c1, Color(c1.r, c1.g, c1.b, 0.0)])
	g.offsets = PackedFloat32Array([0.0, 0.6, 1.0])
	var gt := GradientTexture1D.new()
	gt.gradient = g
	pm.color_ramp = gt
	p.process_material = pm
	var quad := QuadMesh.new()
	quad.size = Vector2(size, size)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD if additive else BaseMaterial3D.BLEND_MODE_MIX
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.vertex_color_use_as_albedo = true
	m.albedo_texture = Fx.soft_tex
	quad.material = m
	p.draw_pass_1 = quad
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	p.visibility_aabb = AABB(Vector3(-6, -8, -18), Vector3(12, 14, 20))
	add_child(p)
	return p


func _physics_process(delta: float) -> void:
	_t += delta
	var u := fmod(_t, period)
	var fire := u > period - 4.0 and u < period - 2.2
	var water := u > period - 2.0 and u < period - 0.4
	if fire and not _burning:
		Sound.play_at("dash", global_position, 4.0, 0.55)
		# the roar only shakes the camera when you are near the head
		var cam := get_viewport().get_camera_3d()
		if cam and cam.global_position.distance_to(global_position) < 25.0:
			Fx.shake(0.12, 0.25)
	_burning = fire
	_fire.emitting = fire
	_water.emitting = water
	_light.light_energy = move_toward(_light.light_energy, 3.0 if fire else 0.0, delta * 12.0)
	_light.visible = _light.light_energy > 0.0
	if fire:
		for b in _hurt.get_overlapping_bodies():
			if b is Player:
				(b as Player).damage(global_position)
