class_name AmbientLife
extends Node3D
## Small moving things that make a level feel alive and cost almost nothing: gull flocks
## wheeling overhead, butterflies over the flowers, fish leaping near the hero, kites tugging
## on their strings and junks sailing along the horizon. Phones get fewer of each.

var _gulls: Array = [] ## [node, center, radius, height, speed, angle]
var _flies: Array = [] ## [node, home, target, t, wings]
var _kites: Array = [] ## [kite, anchor, base, phase, string, tail bows]
var _sails: Array = [] ## [node, radius, angle, speed]
var _fish_areas: Array = [] ## [center, radius]
var _fish_t := 3.0
var _t := 0.0
var _rng := RandomNumberGenerator.new()


func _init() -> void:
	name = "AmbientLife"
	_rng.seed = 2026


func _phone_cut(n: int) -> int:
	return maxi(1, int(ceil(n * 0.6))) if Game.is_phone() else n


## A flock of gulls circling `center` at `height`, each on its own radius and speed.
func gulls(center: Vector3, radius: float, height: float, count := 6) -> void:
	for i in _phone_cut(count):
		var g := Props.make("seagull", false)
		g.scale = Vector3.ONE * _rng.randf_range(0.9, 1.3)
		_no_shadow(g)
		add_child(g)
		var r := radius * _rng.randf_range(0.6, 1.2)
		var speed := _rng.randf_range(0.18, 0.32) * (1.0 if i % 3 else -1.0)
		_gulls.append([g, center, r, height + _rng.randf_range(-3.0, 3.0), speed, _rng.randf() * TAU])


## Butterflies drifting over a patch of flowers at ground height `y`.
func butterflies(center: Vector3, radius: float, y: float, count := 5) -> void:
	var colors := [Color("#ffd23f"), Color("#ff8fb5"), Color("#ffffff"), Color("#ff9f43"), Color("#9be15d")]
	for i in _phone_cut(count):
		var root := Node3D.new()
		var mat := StandardMaterial3D.new()
		mat.albedo_color = colors[i % colors.size()]
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		var wings: Array[Node3D] = []
		for side in [-1.0, 1.0]:
			var hinge := Node3D.new()
			var w := MeshInstance3D.new()
			var q := QuadMesh.new()
			q.size = Vector2(0.16, 0.13)
			w.mesh = q
			w.material_override = mat
			w.rotation.x = -PI / 2
			w.position.x = 0.08 * side
			w.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			hinge.add_child(w)
			root.add_child(hinge)
			hinge.set_meta("side", side)
			wings.append(hinge)
		add_child(root)
		var home := center + Vector3(_rng.randf_range(-radius, radius), y + 0.6, _rng.randf_range(-radius, radius))
		root.position = home
		_flies.append([root, home, home, _rng.randf() * 3.0, wings, radius])


## Fish that now and then leap out of the water near the hero, inside these circles.
func fish_area(center: Vector3, radius: float) -> void:
	_fish_areas.append([center, radius])


## A Vietnamese diamond kite on a string tied to `anchor`, flying `up` metres above it.
func kite(anchor: Vector3, up: float, color: Color, tail_color := Color("#ffd23f")) -> void:
	var kite := Node3D.new()
	var mi := MeshInstance3D.new()
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var pts := [Vector3(0, 0.75, 0), Vector3(0.55, 0, 0), Vector3(0, -0.95, 0), Vector3(-0.55, 0, 0)]
	for tri in [[0, 1, 2], [0, 2, 3]]:
		for k in tri:
			st.add_vertex(pts[k])
	mi.mesh = st.commit()
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mi.material_override = mat
	kite.add_child(mi)
	# a gold star in the middle and a ribbon tail
	var star := MeshInstance3D.new()
	var sp := SphereMesh.new()
	sp.radius = 0.13
	sp.height = 0.06
	star.mesh = sp
	star.material_override = Fx.toon_material(Color("#ffd23f"), 0.0, Color("#ffd23f"), 0.4)
	star.position = Vector3(0, -0.05, 0.02)
	star.rotation.x = PI / 2
	kite.add_child(star)
	var tmat := StandardMaterial3D.new()
	tmat.albedo_color = tail_color
	tmat.cull_mode = BaseMaterial3D.CULL_DISABLED
	tmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	var bows: Array[Node3D] = []
	for i in 6:
		var bow := MeshInstance3D.new()
		var q := QuadMesh.new()
		q.size = Vector2(0.22, 0.08)
		bow.mesh = q
		bow.material_override = tmat
		bow.position = Vector3(0, -1.1 - i * 0.32, 0)
		kite.add_child(bow)
		bows.append(bow)
	_no_shadow(kite)
	add_child(kite)
	var string := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.012
	cyl.bottom_radius = 0.012
	cyl.height = 1.0
	cyl.radial_segments = 4
	cyl.rings = 1
	string.mesh = cyl
	var smat := StandardMaterial3D.new()
	smat.albedo_color = Color(1, 1, 1, 0.7)
	smat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	string.material_override = smat
	string.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(string)
	var base := anchor + Vector3(-up * 0.35, up, up * 0.2)
	_kites.append([kite, anchor, base, _rng.randf() * TAU, string, bows])


## Junk boats sailing slowly round the horizon at `radius`.
func horizon_sails(radius: float, count := 4) -> void:
	if not Props.exists("junk_boat"):
		return
	for i in _phone_cut(count):
		var b := Props.make("junk_boat", false)
		b.scale = Vector3.ONE * 1.4
		_no_shadow(b)
		add_child(b)
		_sails.append([b, radius * _rng.randf_range(0.85, 1.1), TAU * i / count + _rng.randf() * 0.5, _rng.randf_range(0.004, 0.008)])


func _no_shadow(n: Node) -> void:
	if n is GeometryInstance3D:
		(n as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for c in n.get_children():
		_no_shadow(c)


func _process(delta: float) -> void:
	_t += delta
	for g in _gulls:
		var n: Node3D = g[0]
		g[5] += g[4] * delta
		var a: float = g[5]
		var c: Vector3 = g[1]
		n.position = c + Vector3(cos(a) * g[2], g[3] + sin(_t * 0.7 + a * 3.0) * 0.6, sin(a) * g[2])
		var dir := Vector3(-sin(a), 0, cos(a)) * signf(g[4])
		n.rotation.y = atan2(dir.x, dir.z)
		n.rotation.z = -0.35 * signf(g[4]) + sin(_t * 2.0 + a) * 0.08
	for f in _flies:
		var n: Node3D = f[0]
		f[3] -= delta
		if f[3] <= 0.0:
			f[3] = _rng.randf_range(1.5, 3.5)
			var r: float = f[5] * 0.5
			f[2] = (f[1] as Vector3) + Vector3(_rng.randf_range(-r, r), _rng.randf_range(-0.3, 0.9), _rng.randf_range(-r, r))
		var to: Vector3 = f[2] - n.position
		n.position += to.limit_length(1.2 * delta) + Vector3(0, sin(_t * 9.0 + f[1].x) * 0.25 * delta, 0)
		if to.length() > 0.05:
			n.rotation.y = lerp_angle(n.rotation.y, atan2(to.x, to.z), 4.0 * delta)
		var flap := sin(_t * 26.0 + f[1].z) * 1.1
		for w in f[4]:
			(w as Node3D).rotation.z = flap * float(w.get_meta("side"))
	for k in _kites:
		var kite: Node3D = k[0]
		var ph: float = k[3]
		var p: Vector3 = k[2] + Vector3(sin(_t * 0.5 + ph) * 1.8, sin(_t * 0.8 + ph) * 0.9, cos(_t * 0.4 + ph) * 1.2)
		kite.position = p
		kite.rotation = Vector3(0.25, sin(_t * 0.3 + ph) * 0.4 - 0.6, sin(_t * 1.1 + ph) * 0.25)
		var bows: Array[Node3D] = k[5]
		for i in bows.size():
			bows[i].position.x = sin(_t * 3.0 - i * 0.7 + ph) * 0.08 * i
		var s: MeshInstance3D = k[4]
		var a: Vector3 = k[1]
		var mid := (a + p) * 0.5
		var d := p - a
		s.global_transform = Transform3D(Basis(), mid)
		s.look_at(p, Vector3.UP if absf(d.normalized().y) < 0.99 else Vector3.FORWARD)
		s.rotate_object_local(Vector3.RIGHT, PI / 2)
		s.scale = Vector3(1, d.length(), 1)
	for b in _sails:
		var n: Node3D = b[0]
		b[2] += b[3] * delta
		var a: float = b[2]
		n.position = Vector3(cos(a) * b[1], sin(_t * 0.6 + a) * 0.15, sin(a) * b[1])
		n.rotation.y = atan2(-sin(a), cos(a)) + PI
		n.rotation.z = sin(_t * 0.8 + a * 5.0) * 0.03
	_fish(delta)


func _fish(delta: float) -> void:
	if _fish_areas.is_empty():
		return
	_fish_t -= delta
	if _fish_t > 0.0:
		return
	_fish_t = _rng.randf_range(2.5, 5.5)
	var cam := get_viewport().get_camera_3d()
	if cam == null:
		return
	# somewhere in view, 8–30 m in front of the camera, over open water inside an area
	for attempt in 6:
		var fwd := -cam.global_transform.basis.z * Vector3(1, 0, 1)
		if fwd.length() < 0.1:
			return
		fwd = fwd.normalized().rotated(Vector3.UP, _rng.randf_range(-0.6, 0.6))
		var p := cam.global_position * Vector3(1, 0, 1) + fwd * _rng.randf_range(8.0, 30.0)
		var inside := false
		for a in _fish_areas:
			inside = inside or Vector2(p.x - a[0].x, p.z - a[0].z).length() < a[1]
		if inside and _open_water(p):
			_leap(p, fwd.rotated(Vector3.UP, _rng.randf_range(-1.2, 1.2)))
			return


func _open_water(p: Vector3) -> bool:
	var space := get_world_3d().direct_space_state
	var q := PhysicsRayQueryParameters3D.create(p + Vector3.UP * 30.0, p + Vector3.DOWN * 2.0, 1)
	return space.intersect_ray(q).is_empty()


func _leap(at: Vector3, dir: Vector3) -> void:
	var fish := MeshInstance3D.new()
	var cap := CapsuleMesh.new()
	cap.radius = 0.11
	cap.height = 0.5
	cap.radial_segments = 8
	cap.rings = 2
	fish.mesh = cap
	fish.material_override = Fx.toon_material(Color("#ffb347") if _rng.randf() < 0.4 else Color("#c9d6e3"), 0.4)
	fish.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(fish)
	var from := at
	var to := at + dir * 2.2
	var h := _rng.randf_range(0.9, 1.6)
	Fx.ring(Vector3(from.x, 0.08, from.z), Color(1, 1, 1, 0.8), 1.4, 0.5)
	var tw := fish.create_tween()
	tw.tween_method(func(k: float):
		var p := from.lerp(to, k) + Vector3.UP * (4.0 * h * k * (1.0 - k) - 0.2)
		fish.global_position = p
		var tangent := (to - from) + Vector3.UP * (4.0 * h * (1.0 - 2.0 * k))
		fish.look_at(p + tangent, Vector3.UP)
		fish.rotate_object_local(Vector3.RIGHT, PI / 2), 0.0, 1.0, 0.9)
	tw.tween_callback(func():
		Fx.ring(Vector3(to.x, 0.08, to.z), Color(1, 1, 1, 0.8), 1.2, 0.5)
		fish.queue_free())
