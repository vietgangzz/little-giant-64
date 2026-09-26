@tool
class_name CaveDome
extends StaticBody3D
## A hollow limestone hill: a thick dome shell with an entrance arch cut into one side and a
## skylight at the top. The outside is Hạ Long karst, the inside warm cave stone.

@export var radius := 13.0
@export var height := 11.0
@export var thickness := 1.6
@export var entrance_yaw := 0.0 ## radians; the entrance faces this direction (0 = +Z)
@export var entrance_width := 0.45 ## half-angle in radians
@export var entrance_height := 5.5
@export var skylight := 0.16 ## radians around the top left open
@export var seed := 7

const RINGS := 22
const SEGS := 72


func _ready() -> void:
	build()


func _point(theta: float, phi: float, r: float, h: float, noise: FastNoiseLite) -> Vector3:
	var n := noise.get_noise_3d(cos(phi) * 30.0, theta * 20.0, sin(phi) * 30.0)
	var rr := r * (1.0 + n * 0.08)
	return Vector3(sin(theta) * cos(phi) * rr, cos(theta) * h * (1.0 + n * 0.05), sin(theta) * sin(phi) * rr)


func _open(theta: float, phi: float) -> bool:
	if theta < skylight:
		return true
	var y := cos(theta) * height
	var d := absf(wrapf(phi - (PI / 2.0 - entrance_yaw), -PI, PI))
	# a rounded arch: wider at the bottom
	var w := entrance_width * sqrt(clampf(1.0 - y / entrance_height, 0.0, 1.0))
	return d < w


func build() -> void:
	for c in get_children():
		c.queue_free()
	var noise := FastNoiseLite.new()
	noise.seed = seed
	noise.frequency = 0.05
	var outer := _shell(noise, radius + thickness, height + thickness, false)
	var inner := _shell(noise, radius, height, true)
	for pair in [[outer, Island.material_for(Island.Kind.KARST)], [inner, Island.material_for(Island.Kind.CAVE)]]:
		var mi := MeshInstance3D.new()
		mi.mesh = pair[0]
		mi.material_override = pair[1]
		add_child(mi)
		var cs := CollisionShape3D.new()
		var shape: ConcavePolygonShape3D = (pair[0] as ArrayMesh).create_trimesh_shape()
		shape.backface_collision = true
		cs.shape = shape
		add_child(cs)
	collision_layer = 1
	collision_mask = 0


func _shell(noise: FastNoiseLite, r: float, h: float, inward: bool) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for j in RINGS:
		var t0 := (PI / 2.0) * j / RINGS
		var t1 := (PI / 2.0) * (j + 1) / RINGS
		for i in SEGS:
			var p0 := TAU * i / SEGS
			var p1 := TAU * (i + 1) / SEGS
			var tm := (t0 + t1) * 0.5
			var pm := (p0 + p1) * 0.5
			if _open(tm, pm):
				continue
			var a := _point(t0, p0, r, h, noise)
			var b := _point(t0, p1, r, h, noise)
			var c := _point(t1, p0, r, h, noise)
			var d := _point(t1, p1, r, h, noise)
			if inward:
				st.add_vertex(a); st.add_vertex(b); st.add_vertex(c)
				st.add_vertex(b); st.add_vertex(d); st.add_vertex(c)
			else:
				st.add_vertex(a); st.add_vertex(c); st.add_vertex(b)
				st.add_vertex(b); st.add_vertex(c); st.add_vertex(d)
	st.index()
	st.generate_normals()
	return st.commit()
