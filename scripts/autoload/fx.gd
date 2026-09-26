extends Node
## Visual effects and material helpers.
## - `toonify()` converts every imported glTF material into the shared toon shader (+ ink outline).
## - One-shot effects (dust, rings, sparkles, confetti, splashes) are cheap GPUParticles3D or
##   tweened meshes that free themselves.

signal shake_requested(strength: float, duration: float)

const TOON := preload("res://shaders/toon.gdshader")
const OUTLINE := preload("res://shaders/outline.gdshader")
const RING := preload("res://shaders/fx_ring.gdshader")
const BEAM := preload("res://shaders/fx_beam.gdshader")

var noise_tex: NoiseTexture2D
var star_tex: ImageTexture
var soft_tex: ImageTexture
var _toon_cache: Dictionary = {}
var _outline_cache: Dictionary = {}
var _puff_mesh: SphereMesh
var _puff_mat: StandardMaterial3D
var _hitstop_until := 0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	var n := FastNoiseLite.new()
	n.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	n.frequency = 0.012
	n.fractal_octaves = 4
	noise_tex = NoiseTexture2D.new()
	noise_tex.width = 512
	noise_tex.height = 512
	noise_tex.seamless = true
	noise_tex.noise = n
	noise_tex.generate_mipmaps = true
	star_tex = _make_star_texture(96)
	soft_tex = _make_soft_texture(64)
	_puff_mesh = SphereMesh.new()
	_puff_mesh.radius = 0.5
	_puff_mesh.height = 1.0
	_puff_mesh.radial_segments = 12
	_puff_mesh.rings = 6
	_puff_mat = StandardMaterial3D.new()
	_puff_mat.albedo_color = Color(1, 1, 1)
	_puff_mat.vertex_color_use_as_albedo = true
	_puff_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_puff_mat.shading_mode = BaseMaterial3D.SHADING_MODE_PER_PIXEL
	_puff_mat.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON
	_puff_mat.emission_enabled = true
	_puff_mat.emission = Color(0.45, 0.47, 0.55)
	_puff_mat.shadow_to_opacity = false
	_puff_mesh.material = _puff_mat


# ------------------------------------------------------------------ materials

func toon_material(color: Color, metal := 0.0, emission := Color.BLACK, emission_energy := 0.0) -> ShaderMaterial:
	var key := "%s|%.2f|%s|%.2f" % [color.to_html(), metal, emission.to_html(), emission_energy]
	if _toon_cache.has(key):
		return _toon_cache[key]
	var m := ShaderMaterial.new()
	m.shader = TOON
	m.set_shader_parameter("albedo", color)
	m.set_shader_parameter("metal_sheen", metal)
	m.set_shader_parameter("emission_color", emission)
	m.set_shader_parameter("emission_energy", emission_energy)
	if metal > 0.0:
		m.set_shader_parameter("spec_strength", 0.7)
		m.set_shader_parameter("spec_gloss", 60.0)
	_toon_cache[key] = m
	return m


func outline_material(color: Color, width := 0.018) -> ShaderMaterial:
	var key := "%s|%.3f" % [color.to_html(), width]
	if _outline_cache.has(key):
		return _outline_cache[key]
	var m := ShaderMaterial.new()
	m.shader = OUTLINE
	m.set_shader_parameter("color", color)
	m.set_shader_parameter("width", width)
	_outline_cache[key] = m
	return m


## Walks an imported scene and swaps every surface material for the toon shader.
## `outline` adds an ink hull whose colour is a dark shade of the surface.
func toonify(root: Node, outline := true, width := 0.018, unique := false) -> void:
	for mi in _meshes(root):
		var mesh: Mesh = mi.mesh
		if mesh == null:
			continue
		for s in mesh.get_surface_count():
			var src: Material = mi.get_active_material(s)
			var color := Color(0.8, 0.8, 0.8)
			var metal := 0.0
			var emi := Color.BLACK
			var emi_e := 0.0
			var name := ""
			if src is BaseMaterial3D:
				var b := src as BaseMaterial3D
				color = b.albedo_color
				metal = clampf(b.metallic, 0.0, 1.0)
				if b.emission_enabled:
					emi = b.emission
					emi_e = b.emission_energy_multiplier
				name = b.resource_name
			if name.contains("Gold") or name.contains("Bronze") or name.contains("Metal"):
				metal = maxf(metal, 0.8)
			var m: ShaderMaterial = toon_material(color, metal, emi, emi_e)
			if unique:
				m = m.duplicate()
			if outline and not name.contains("Eye") and not name.contains("NoLine"):
				var ink := color.darkened(0.62)
				ink.s = minf(ink.s * 1.2, 1.0)
				m = m.duplicate() if not unique else m
				m.next_pass = outline_material(ink, width)
			mi.set_surface_override_material(s, m)


func _meshes(root: Node) -> Array[MeshInstance3D]:
	var out: Array[MeshInstance3D] = []
	if root is MeshInstance3D:
		out.append(root)
	for c in root.get_children():
		out.append_array(_meshes(c))
	return out


# ------------------------------------------------------------------ one-shots

func _scene_root() -> Node:
	return get_tree().current_scene


## White cloud puffs that swell and fade (footsteps, jumps, landings, dashes).
func dust(where: Vector3, amount := 6, spread := 0.5, rise := 0.6, size := 0.45, color := Color(1, 1, 1, 0.95)) -> void:
	var root := _scene_root()
	if root == null:
		return
	for i in amount:
		var puff := MeshInstance3D.new()
		puff.mesh = _puff_mesh
		puff.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var mat := _puff_mat.duplicate() as StandardMaterial3D
		mat.albedo_color = color
		puff.material_override = mat
		root.add_child(puff)
		var a := TAU * float(i) / amount + randf() * 0.6
		var dir := Vector3(cos(a), 0, sin(a))
		puff.global_position = where + dir * spread * 0.3 + Vector3(0, 0.1, 0)
		var s := size * randf_range(0.7, 1.2)
		puff.scale = Vector3.ONE * s * 0.4
		var life := randf_range(0.35, 0.6)
		var tw := puff.create_tween().set_parallel(true)
		tw.tween_property(puff, "global_position", puff.global_position + dir * spread + Vector3(0, rise * randf_range(0.5, 1.0), 0), life).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_property(puff, "scale", Vector3.ONE * s, life * 0.45).set_ease(Tween.EASE_OUT)
		tw.tween_property(puff, "scale", Vector3.ONE * 0.05, life * 0.55).set_delay(life * 0.45).set_ease(Tween.EASE_IN)
		tw.tween_property(mat, "albedo_color:a", 0.0, life * 0.5).set_delay(life * 0.5)
		tw.chain().tween_callback(puff.queue_free)


## A flat expanding ring lying on `normal`.
func ring(where: Vector3, color := Color(1, 1, 1, 0.9), size := 2.4, duration := 0.45, normal := Vector3.UP) -> void:
	var root := _scene_root()
	if root == null:
		return
	var q := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(size, size)
	q.mesh = pm
	var mat := ShaderMaterial.new()
	mat.shader = RING
	mat.set_shader_parameter("color", color)
	q.material_override = mat
	q.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(q)
	q.global_position = where
	if normal.normalized() != Vector3.UP:
		q.look_at(where + normal, Vector3.UP if absf(normal.normalized().y) < 0.99 else Vector3.FORWARD)
		q.rotate_object_local(Vector3.RIGHT, -PI / 2)
	var tw := q.create_tween()
	tw.tween_method(func(v: float): mat.set_shader_parameter("age", v), 0.0, 1.0, duration)
	tw.tween_callback(q.queue_free)


## Star-shaped sparkles bursting outward (coins, stars, double jumps).
func sparkle(where: Vector3, color := Color(1, 0.9, 0.4), amount := 10, speed := 4.0, size := 0.35, life := 0.7) -> void:
	var root := _scene_root()
	if root == null:
		return
	var p := GPUParticles3D.new()
	p.one_shot = true
	p.explosiveness = 0.95
	p.amount = amount
	p.lifetime = life
	p.local_coords = false
	var pm := ParticleProcessMaterial.new()
	pm.direction = Vector3(0, 1, 0)
	pm.spread = 180.0
	pm.initial_velocity_min = speed * 0.5
	pm.initial_velocity_max = speed
	pm.gravity = Vector3(0, -4, 0)
	pm.damping_min = 2.0
	pm.damping_max = 4.0
	pm.angle_min = -180
	pm.angle_max = 180
	pm.angular_velocity_min = -360
	pm.angular_velocity_max = 360
	pm.scale_min = 0.6
	pm.scale_max = 1.2
	var curve := Curve.new()
	curve.add_point(Vector2(0, 0.2))
	curve.add_point(Vector2(0.15, 1.0))
	curve.add_point(Vector2(1, 0))
	var ct := CurveTexture.new()
	ct.curve = curve
	pm.scale_curve = ct
	pm.color = color
	p.process_material = pm
	var quad := QuadMesh.new()
	quad.size = Vector2(size, size)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.vertex_color_use_as_albedo = true
	m.albedo_texture = star_tex
	quad.material = m
	p.draw_pass_1 = quad
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(p)
	p.global_position = where
	p.emitting = true
	p.finished.connect(p.queue_free)


func star_burst(where: Vector3) -> void:
	sparkle(where, Color(1, 0.88, 0.35), 28, 8.0, 0.55, 1.1)
	sparkle(where, Color(1, 1, 1), 14, 5.0, 0.35, 0.8)
	ring(where, Color(1, 0.92, 0.55, 1), 6.0, 0.6, Vector3.UP)
	ring(where, Color(1, 1, 1, 0.8), 4.0, 0.5, Vector3.BACK)
	shake(0.25, 0.25)


func splash(where: Vector3) -> void:
	dust(Vector3(where.x, 0.05, where.z), 10, 1.2, 1.6, 0.55, Color(0.85, 0.96, 1.0, 0.95))
	ring(Vector3(where.x, 0.08, where.z), Color(1, 1, 1, 0.9), 4.0, 0.7)
	sparkle(Vector3(where.x, 0.3, where.z), Color(0.7, 0.92, 1.0), 16, 6.0, 0.3, 0.9)


## Paper confetti in the brand colours, for ALL STARS.
func confetti(where: Vector3, amount := 160, area := 8.0) -> GPUParticles3D:
	var root := _scene_root()
	var p := GPUParticles3D.new()
	p.one_shot = false
	p.amount = amount
	p.lifetime = 4.0
	p.local_coords = false
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(area, 0.5, area)
	pm.direction = Vector3(0, -1, 0)
	pm.spread = 25.0
	pm.initial_velocity_min = 0.5
	pm.initial_velocity_max = 2.0
	pm.gravity = Vector3(0, -1.6, 0)
	pm.angular_velocity_min = -540
	pm.angular_velocity_max = 540
	pm.angle_min = -180
	pm.angle_max = 180
	pm.turbulence_enabled = true
	pm.turbulence_noise_strength = 1.5
	var grad := Gradient.new()
	grad.offsets = PackedFloat32Array([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
	grad.colors = PackedColorArray([Color("#d5f64b"), Color("#ff7447"), Color("#f2b33d"), Color("#4fc3f7"), Color("#ff5c8a"), Color("#ffffff")])
	var gt := GradientTexture1D.new()
	gt.gradient = grad
	pm.color_initial_ramp = gt
	p.process_material = pm
	var quad := QuadMesh.new()
	quad.size = Vector2(0.18, 0.28)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.vertex_color_use_as_albedo = true
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	quad.material = m
	p.draw_pass_1 = quad
	root.add_child(p)
	p.global_position = where
	p.emitting = true
	return p


func beam(parent: Node3D, height := 14.0, radius := 0.9, color := Color(1, 0.9, 0.5)) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = radius * 0.6
	cyl.bottom_radius = radius
	cyl.height = height
	cyl.cap_top = false
	cyl.cap_bottom = false
	cyl.radial_segments = 24
	mi.mesh = cyl
	var m := ShaderMaterial.new()
	m.shader = BEAM
	m.set_shader_parameter("color", color)
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.position.y = height * 0.5 - 0.5
	parent.add_child(mi)
	return mi


func shake(strength := 0.3, duration := 0.2) -> void:
	shake_requested.emit(strength, duration)


## Freezes gameplay for a few frames: the classic stomp "hit-stop".
func hitstop(seconds := 0.06) -> void:
	if Engine.time_scale < 1.0:
		return
	Engine.time_scale = 0.05
	await get_tree().create_timer(seconds, true, false, true).timeout
	Engine.time_scale = 1.0


# ------------------------------------------------------------------ textures

func _make_star_texture(size: int) -> ImageTexture:
	var img := Image.create(size, size, false, Image.FORMAT_RGBA8)
	var c := Vector2(size, size) * 0.5
	for y in size:
		for x in size:
			var p := (Vector2(x, y) + Vector2(0.5, 0.5) - c) / (size * 0.5)
			var a := atan2(p.y, p.x)
			var r := p.length()
			# four-point sparkle with a soft core
			var arms := pow(absf(cos(a * 2.0)), 18.0) * 0.9 + 0.12
			var v := clampf((arms - r) * 6.0, 0.0, 1.0) + clampf(1.0 - r * 3.2, 0.0, 1.0)
			img.set_pixel(x, y, Color(1, 1, 1, clampf(v, 0.0, 1.0)))
	return ImageTexture.create_from_image(img)


func _make_soft_texture(size: int) -> ImageTexture:
	var img := Image.create(size, size, false, Image.FORMAT_RGBA8)
	for y in size:
		for x in size:
			var d := Vector2(x - size * 0.5, y - size * 0.5).length() / (size * 0.5)
			img.set_pixel(x, y, Color(1, 1, 1, clampf(1.0 - d, 0.0, 1.0) ** 2))
	return ImageTexture.create_from_image(img)
