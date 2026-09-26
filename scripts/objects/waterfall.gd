class_name Waterfall
extends Node3D
## A falling sheet of water with mist and a splash ring where it meets the sea (or a ledge).

const SHADER := preload("res://shaders/waterfall.gdshader")

var width := 4.0
var height := 10.0
var curve_out := 1.2


func _ready() -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var rows := 12
	var cols := 6
	for j in rows + 1:
		for i in cols + 1:
			var u := float(i) / cols
			var v := float(j) / rows
			# the sheet leaves the lip horizontally and curves down
			var z := curve_out * sqrt(v) 
			st.set_uv(Vector2(u, v * height / width))
			st.set_normal(Vector3(0, 0, 1))
			st.add_vertex(Vector3((u - 0.5) * width * (1.0 + v * 0.15), -v * height, z))
	for j in rows:
		for i in cols:
			var a := j * (cols + 1) + i
			var b := a + 1
			var c := a + cols + 1
			var d := c + 1
			st.add_index(a); st.add_index(b); st.add_index(c)
			st.add_index(b); st.add_index(d); st.add_index(c)
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	var m := ShaderMaterial.new()
	m.shader = SHADER
	m.set_shader_parameter("noise", Fx.noise_tex)
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)
	# mist at the foot
	var p := GPUParticles3D.new()
	p.amount = 40
	p.lifetime = 1.6
	p.position = Vector3(0, -height + 0.2, curve_out)
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(width * 0.5, 0.1, 0.4)
	pm.direction = Vector3(0, 1, 0.4)
	pm.spread = 40.0
	pm.initial_velocity_min = 1.0
	pm.initial_velocity_max = 2.5
	pm.gravity = Vector3(0, -0.8, 0)
	pm.scale_min = 0.6
	pm.scale_max = 1.4
	var curve := Curve.new()
	curve.add_point(Vector2(0, 0.3))
	curve.add_point(Vector2(0.4, 1))
	curve.add_point(Vector2(1, 0))
	var ct := CurveTexture.new()
	ct.curve = curve
	pm.scale_curve = ct
	pm.color = Color(1, 1, 1, 0.8)
	p.process_material = pm
	var quad := QuadMesh.new()
	quad.size = Vector2(1.4, 1.4)
	var qm := StandardMaterial3D.new()
	qm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	qm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	qm.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	qm.vertex_color_use_as_albedo = true
	qm.albedo_texture = Fx.soft_tex
	quad.material = qm
	p.draw_pass_1 = quad
	add_child(p)
	var snd := Sound.loop_at("waterfall", self, -2.0, 7.0)
	if snd:
		snd.position = Vector3(0, -height * 0.7, curve_out)
