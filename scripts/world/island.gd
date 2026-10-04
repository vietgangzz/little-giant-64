@tool
class_name Island
extends StaticBody3D
## A procedural island: a noisy outline, a gently domed top that rolls over a rounded lip, and
## sides that run down into the sea (or taper to a rocky point when `floating`). The same
## generator makes grass islands, rice-terrace tiers, sand bars, limestone karst towers and the
## pale marble peaks of Ngũ Hành Sơn.

enum Kind { GRASS, SAND, STONE, PADDY, KARST, CAVE, MARBLE, PAVED }

const SHADER := preload("res://shaders/island.gdshader")
const CAVE_SHADER := preload("res://shaders/island_cave.gdshader")

@export var radius := 8.0: set = _set_radius
@export var top := 2.0: set = _set_top
@export var bottom := -4.0: set = _set_bottom
@export var kind: Kind = Kind.GRASS: set = _set_kind
@export var stretch := Vector2.ONE: set = _set_stretch ## x/z scale of the outline
@export var wobble := 0.12: set = _set_wobble ## outline noise amount
@export var dome := 0.35: set = _set_dome ## how much the top bulges up in the middle
@export var lip := 0.55: set = _set_lip ## rounded edge radius
@export var bulge := 0.0: set = _set_bulge ## sides swell outward (karsts)
@export var taper := 0.0: set = _set_taper ## >0 narrows the sides toward the top
@export var floating := false: set = _set_floating
@export var seed := 1: set = _set_seed
@export var collide := true
@export var segments := 56

var _built := false
var _mesh_instance: MeshInstance3D
static var _materials: Dictionary = {}


func _set_radius(v): radius = v; _queue()
func _set_top(v): top = v; _queue()
func _set_bottom(v): bottom = v; _queue()
func _set_kind(v): kind = v; _queue()
func _set_stretch(v): stretch = v; _queue()
func _set_wobble(v): wobble = v; _queue()
func _set_dome(v): dome = v; _queue()
func _set_lip(v): lip = v; _queue()
func _set_bulge(v): bulge = v; _queue()
func _set_taper(v): taper = v; _queue()
func _set_floating(v): floating = v; _queue()
func _set_seed(v): seed = v; _queue()


func _queue() -> void:
	if _built and is_inside_tree():
		build()


func _ready() -> void:
	build()


func build() -> void:
	_built = true
	for c in get_children():
		c.queue_free()
	var mesh := _make_mesh()
	_mesh_instance = MeshInstance3D.new()
	_mesh_instance.mesh = mesh
	_mesh_instance.material_override = material_for(kind)
	add_child(_mesh_instance)
	if collide:
		var cs := CollisionShape3D.new()
		cs.shape = mesh.create_trimesh_shape()
		add_child(cs)
	collision_layer = 1
	collision_mask = 0


static func material_for(k: Kind) -> ShaderMaterial:
	if _materials.has(k):
		return _materials[k]
	var m := ShaderMaterial.new()
	m.shader = CAVE_SHADER if k == Kind.CAVE else SHADER
	m.set_shader_parameter("kind", int(k))
	m.set_shader_parameter("spec_strength", 0.0)
	m.set_shader_parameter("rim_strength", 0.12)
	m.set_shader_parameter("shadow_floor", 0.5)
	if k == Kind.CAVE:
		m.set_shader_parameter("self_light", 0.6)
	var tex := NoiseTexture2D.new()
	var n := FastNoiseLite.new()
	n.frequency = 0.012
	n.fractal_octaves = 4
	tex.noise = n
	tex.seamless = true
	tex.width = 512
	tex.height = 512
	tex.generate_mipmaps = true
	m.set_shader_parameter("noise", tex)
	_materials[k] = m
	return m


## Outline radius at angle `a`, before stretch.
func _edge(a: float, noise: FastNoiseLite) -> float:
	var n := noise.get_noise_2d(cos(a) * 60.0, sin(a) * 60.0)
	return radius * (1.0 + n * wobble * 2.0)


func _make_mesh() -> ArrayMesh:
	var noise := FastNoiseLite.new()
	noise.seed = seed
	noise.frequency = 0.02
	noise.fractal_octaves = 2
	var n := segments
	var rings: Array = [] ## each ring: Array[Vector3] of n points
	var edge := PackedFloat32Array()
	for i in n:
		edge.append(_edge(TAU * i / n, noise))
	var lip_r := minf(lip, radius * 0.4)
	var inner := 7
	# top: center to lip start
	for j in range(0, inner + 1):
		var f := float(j) / inner
		var ring: Array[Vector3] = []
		for i in n:
			var a := TAU * i / n
			var r := (edge[i] - lip_r) * f
			var h := top + dome * (1.0 - f * f) + noise.get_noise_2d(cos(a) * r * 3.0, sin(a) * r * 3.0) * 0.12 * f
			ring.append(Vector3(cos(a) * r * stretch.x, h, sin(a) * r * stretch.y))
		rings.append(ring)
	# rounded lip
	var lip_steps := 4
	for j in range(1, lip_steps + 1):
		var ang := (PI / 2.0) * float(j) / lip_steps
		var ring: Array[Vector3] = []
		for i in n:
			var a := TAU * i / n
			var r := edge[i] - lip_r + sin(ang) * lip_r
			var h := top - (1.0 - cos(ang)) * lip_r
			ring.append(Vector3(cos(a) * r * stretch.x, h, sin(a) * r * stretch.y))
		rings.append(ring)
	# sides
	var side_top := top - lip_r
	var side_steps := maxi(4, int((side_top - bottom) / 1.2))
	for j in range(1, side_steps + 1):
		var f := float(j) / side_steps ## 0 at the lip, 1 at the bottom
		var y := lerpf(side_top, bottom, f)
		var ring: Array[Vector3] = []
		for i in n:
			var a := TAU * i / n
			var r := edge[i]
			r *= 1.0 + bulge * sin(f * PI) + taper * f
			r += noise.get_noise_2d(cos(a) * 30.0 + y * 4.0, sin(a) * 30.0) * radius * 0.05 * (1.0 if kind == Kind.STONE else 0.4)
			if floating:
				var k := pow(f, 1.4)
				r *= lerpf(1.0, 0.08, k)
				y = lerpf(side_top, bottom, f) - noise.get_noise_2d(cos(a) * 20.0, sin(a) * 20.0) * 0.8 * k
			ring.append(Vector3(cos(a) * r * stretch.x, y, sin(a) * r * stretch.y))
		rings.append(ring)
	# close the bottom
	var bottom_ring: Array[Vector3] = []
	for i in n:
		bottom_ring.append(Vector3(0, bottom - (0.6 if floating else 0.0), 0))
	rings.append(bottom_ring)

	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for ring in rings:
		for v in ring:
			st.add_vertex(v)
	for j in rings.size() - 1:
		for i in n:
			var a := j * n + i
			var b := j * n + (i + 1) % n
			var c := (j + 1) * n + i
			var d := (j + 1) * n + (i + 1) % n
			# Godot treats clockwise (seen from outside) as the front face
			st.add_index(a)
			st.add_index(c)
			st.add_index(b)
			st.add_index(b)
			st.add_index(c)
			st.add_index(d)
	st.generate_normals()
	return st.commit()
