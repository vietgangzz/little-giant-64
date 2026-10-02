class_name Props
extends RefCounted
## Loads the Blender props (assets/models/props/*.glb), converts them to the toon look, and
## optionally gives them collision. When a file is missing a simple stand-in shape is used, so
## the world is always playable.

const DIR := "res://assets/models/props/"

static var _scenes: Dictionary = {}
static var _shapes: Dictionary = {}
static var _tinted: Dictionary = {} ## shared re-coloured materials (see tint)
static var _glowing: Dictionary = {} ## shared glowing copies (see glow)

## Stand-ins: [shape, size, colour]. Shapes are box/cyl/sphere/cone.
const STANDINS := {
	"coin": ["cyl", Vector3(0.55, 0.08, 0.55), Color("#f2c33d")],
	"coin_red": ["sphere", Vector3(0.5, 0.6, 0.5), Color("#e0452b")],
	"star": ["sphere", Vector3(1.0, 1.0, 0.3), Color("#f2b33d")],
	"drum_block": ["box", Vector3(1, 1, 1), Color("#c8923a")],
	"used_block": ["box", Vector3(1, 1, 1), Color("#6f4b2a")],
	"brick_block": ["box", Vector3(1, 1, 1), Color("#c8643c")],
	"bamboo_pipe": ["cyl", Vector3(1.4, 2.0, 1.4), Color("#4caf50")],
	"drum_spring": ["cyl", Vector3(1.4, 0.5, 1.4), Color("#b8863b")],
	"checkpoint": ["cyl", Vector3(0.12, 2.6, 0.12), Color("#e8e0d0")],
	"tree_round": ["sphere", Vector3(2.6, 3.2, 2.6), Color("#5cc45a")],
	"tree_palm": ["cyl", Vector3(0.4, 4.0, 0.4), Color("#a0784a")],
	"bamboo_cluster": ["cyl", Vector3(1.2, 4.0, 1.2), Color("#6cbf4a")],
	"pagoda": ["box", Vector3(3.5, 6.0, 3.5), Color("#b04a32")],
	"lotus_pad": ["cyl", Vector3(2.0, 0.12, 2.0), Color("#56b851")],
	"lotus_flower": ["sphere", Vector3(0.6, 0.5, 0.6), Color("#ff8fb5")],
	"sampan": ["box", Vector3(1.4, 0.7, 3.5), Color("#8a5a35")],
	"lantern": ["sphere", Vector3(0.45, 0.6, 0.45), Color("#e0452b")],
	"rock_karst": ["cone", Vector3(3, 8, 3), Color("#8e9aa6")],
	"cloud": ["sphere", Vector3(4, 1.8, 2.6), Color("#ffffff")],
	"crab": ["sphere", Vector3(0.9, 0.5, 0.6), Color("#e4543a")],
	"crusher": ["cyl", Vector3(1.8, 0.9, 1.8), Color("#8b6a3e")],
	"jelly_block": ["box", Vector3(1.6, 1.6, 1.6), Color("#7fcf6a")],
	"flower_pink": ["sphere", Vector3(0.3, 0.3, 0.3), Color("#ff8fb5")],
	"flower_yellow": ["sphere", Vector3(0.3, 0.3, 0.3), Color("#ffd84a")],
	"grass_tuft": ["cone", Vector3(0.4, 0.4, 0.4), Color("#62c24f")],
	"mushroom": ["sphere", Vector3(0.5, 0.5, 0.5), Color("#e0452b")],
	"fence_bamboo": ["box", Vector3(2.0, 0.8, 0.12), Color("#b9a05a")],
	"bridge_plank": ["box", Vector3(1.0, 0.2, 1.0), Color("#a0703e")],
	"drum_big": ["cyl", Vector3(4.0, 2.2, 4.0), Color("#b8863b")],
	"cong_lang": ["box", Vector3(4, 4, 0.6), Color("#a8442e")],
	"pearl": ["sphere", Vector3(0.55, 0.55, 0.55), Color("#f4f1ff")],
	"junk_boat": ["box", Vector3(3.2, 1.0, 10), Color("#8a5a35")],
	"raft_house": ["box", Vector3(6, 4.5, 6), Color("#6f8fb0")],
	"raft_platform": ["box", Vector3(4, 0.5, 4), Color("#a0703e")],
	"fish_cage_ring": ["cyl", Vector3(3.5, 0.2, 3.5), Color("#e0e0e0")],
	"kayak": ["box", Vector3(0.7, 0.3, 3.8), Color("#ffb020")],
	"stalactite": ["cone", Vector3(0.6, 2.5, 0.6), Color("#d8c39a")],
	"stalagmite": ["cone", Vector3(0.7, 1.8, 0.7), Color("#d8c39a")],
	"crystal_cluster": ["cone", Vector3(0.6, 0.8, 0.6), Color("#6ee8e0")],
	"pavilion_titop": ["box", Vector3(4, 4.5, 4), Color("#c0503a")],
	"dragon_head": ["box", Vector3(1.2, 1.2, 2.2), Color("#2fa56a")],
	"dragon_body": ["cyl", Vector3(1.3, 1.6, 1.3), Color("#2fa56a")],
	"dragon_tail": ["cone", Vector3(1.0, 2.0, 1.0), Color("#2fa56a")],
	"buoy": ["cone", Vector3(0.8, 1.5, 0.8), Color("#e0452b")],
	"seagull": ["box", Vector3(0.9, 0.1, 0.3), Color("#ffffff")],
	"net_rack": ["box", Vector3(3, 2, 0.2), Color("#b9a05a")],
	"vietnam_flag": ["cyl", Vector3(0.1, 3, 0.1), Color("#da251d")],
	# ---- Đà Nẵng – Hội An
	"golden_hand": ["box", Vector3(5, 8.6, 4), Color("#8e9488")],
	"golden_bridge_seg": ["box", Vector3(2.4, 0.3, 2.0), Color("#e7b53c")],
	"chua_cau": ["box", Vector3(4, 5.6, 12), Color("#9e2a1e")],
	"hoian_house": ["box", Vector3(5, 5.6, 6), Color("#e8b93e")],
	"hoian_house_small": ["box", Vector3(4, 3.8, 5), Color("#e8b93e")],
	"hoa_dang": ["sphere", Vector3(0.6, 0.45, 0.6), Color("#ff6fa3")],
	"basket_boat": ["cyl", Vector3(2.2, 0.7, 2.2), Color("#2b2622")],
	"nipa_palm": ["cone", Vector3(2.0, 4.5, 2.0), Color("#5bc24a")],
	"cable_car": ["box", Vector3(2.4, 2.5, 2.4), Color("#d8342c")],
	"cable_tower": ["cyl", Vector3(0.6, 14, 0.6), Color("#9aa3ad")],
	"dragon_bridge_deck": ["box", Vector3(9, 0.4, 10), Color("#4a4e57")],
	"dragon_bridge_pier": ["box", Vector3(3, 6, 3), Color("#c9d1dd")],
	"beach_umbrella": ["cone", Vector3(2.8, 2.6, 2.8), Color("#d8b46a")],
	"beach_chair": ["box", Vector3(0.7, 0.5, 1.8), Color("#a0612f")],
	"lantern_boat": ["box", Vector3(1.6, 0.6, 4.0), Color("#8a5a35")],
	"stupa_tower": ["cone", Vector3(2.4, 5, 2.4), Color("#e9e4da")],
	"banh_mi_cart": ["box", Vector3(1.6, 1.6, 1.0), Color("#3d84c6")],
	"silk_lantern_string": ["box", Vector3(6, 0.2, 0.2), Color("#e0452b")],
}


## How much the wind moves each kind of foliage (0 or missing = still).
const SWAY := {
	"tree_round": 0.35, "tree_palm": 0.45, "bamboo_cluster": 0.55, "grass_tuft": 9.0,
	"flower_pink": 7.0, "flower_yellow": 7.0, "lotus_flower": 2.0, "nipa_palm": 0.5,
}


static func exists(name: String) -> bool:
	return ResourceLoader.exists(DIR + name + ".glb")


## Returns a toonified instance of prop `name`. `outline` adds the ink line.
static func make(name: String, outline := true, unique := false) -> Node3D:
	var path := DIR + name + ".glb"
	var node: Node3D
	if ResourceLoader.exists(path):
		if not _scenes.has(name):
			_scenes[name] = load(path)
		node = (_scenes[name] as PackedScene).instantiate()
		Fx.toonify(node, outline, 0.02, unique, SWAY.get(name, 0.0))
	else:
		node = _standin(name)
	if Game.is_phone() and name in SMALL:
		for mi in _meshes(node):
			mi.visibility_range_end = SMALL_RANGE
			mi.visibility_range_end_margin = 6.0
	node.name = name
	return node


static func _standin(name: String) -> Node3D:
	var spec: Array = STANDINS.get(name, ["box", Vector3.ONE, Color.MAGENTA])
	var root := Node3D.new()
	var mi := MeshInstance3D.new()
	var size: Vector3 = spec[1]
	match spec[0]:
		"box":
			var b := BoxMesh.new()
			b.size = size
			mi.mesh = b
		"cyl":
			var c := CylinderMesh.new()
			c.top_radius = size.x * 0.5
			c.bottom_radius = size.x * 0.5
			c.height = size.y
			mi.mesh = c
		"cone":
			var c := CylinderMesh.new()
			c.top_radius = size.x * 0.15
			c.bottom_radius = size.x * 0.5
			c.height = size.y
			mi.mesh = c
		_:
			var s := SphereMesh.new()
			s.radius = size.x * 0.5
			s.height = size.y
			mi.mesh = s
	mi.position.y = size.y * 0.5
	if name == "coin" or name == "star":
		mi.rotation.x = PI / 2
		mi.position.y = size.x * 0.5
	mi.material_override = Fx.toon_material(spec[2], 0.6 if name in ["coin", "star", "drum_block", "drum_spring", "drum_big"] else 0.0)
	root.add_child(mi)
	return root


## Small set dressing that phones stop drawing past `SMALL_RANGE` metres.
const SMALL := ["flower_pink", "flower_yellow", "grass_tuft", "mushroom", "beach_chair", "lantern",
	"silk_lantern_string", "banh_mi_cart", "kayak", "buoy", "net_rack", "fish_cage_ring"]
const SMALL_RANGE := 55.0


## Re-colours an imported, toonified prop: `f` maps each surface colour to a new one (return
## the same colour to leave a surface alone). `metal` > 0 gives the new surfaces a metal sheen.
## The new materials are shared, like toonify's, and keep the wind and the outline (or its
## absence) of the surface they replace.
static func tint(node: Node, f: Callable, metal := 0.0) -> void:
	for mi in _meshes(node):
		for s in mi.mesh.get_surface_count():
			var m := mi.get_surface_override_material(s) as ShaderMaterial
			if m == null:
				continue
			var c: Color = m.get_shader_parameter("albedo")
			var nc: Color = f.call(c)
			if nc == c:
				continue
			var sway: float = m.get_shader_parameter("sway") if m.get_shader_parameter("sway") != null else 0.0
			var key := "%s|%.2f|%s" % [nc.to_html(), metal, m.next_pass != null]
			if not _tinted.has(key):
				var nm := Fx.toon_material(nc, metal, m.get_shader_parameter("emission_color"), m.get_shader_parameter("emission_energy"), sway).duplicate() as ShaderMaterial
				nm.next_pass = Fx.outline_material(nc.darkened(0.62), 0.02, sway) if m.next_pass != null else null
				_tinted[key] = nm
			mi.set_surface_override_material(s, _tinted[key])


## Makes every surface of a prop glow with its own colour (lanterns at dusk).
static func glow(node: Node, energy := 0.8, only: Callable = Callable()) -> void:
	for mi in _meshes(node):
		for s in mi.mesh.get_surface_count():
			var m := mi.get_surface_override_material(s) as ShaderMaterial
			if m == null:
				continue
			var c: Color = m.get_shader_parameter("albedo")
			if only.is_valid() and not only.call(c):
				continue
			var key := "%d|%.2f" % [m.get_instance_id(), energy]
			if not _glowing.has(key):
				var nm := m.duplicate() as ShaderMaterial
				nm.set_shader_parameter("emission_color", c)
				nm.set_shader_parameter("emission_energy", energy)
				_glowing[key] = nm
			mi.set_surface_override_material(s, _glowing[key])


## Adds trimesh collision for every mesh under `node` (static scenery).
static func solidify(node: Node3D, layer := 1) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.collision_layer = layer
	body.collision_mask = 0
	node.add_child(body)
	for mi in _meshes(node):
		var key := mi.mesh.resource_path + str(mi.mesh.get_rid())
		if not _shapes.has(key):
			_shapes[key] = mi.mesh.create_trimesh_shape()
		var cs := CollisionShape3D.new()
		cs.shape = _shapes[key]
		body.add_child(cs)
		cs.global_transform = mi.global_transform
	return body


## Adds a single primitive collider (cheaper than trimesh for simple things).
static func add_box(parent: Node3D, size: Vector3, offset := Vector3.ZERO, layer := 1) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.collision_layer = layer
	body.collision_mask = 0
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = size
	cs.shape = box
	body.add_child(cs)
	parent.add_child(body)
	# the body sits at the offset so rotating it turns the box in place
	body.position = offset
	return body


static func add_cylinder(parent: Node3D, radius: float, height: float, offset := Vector3.ZERO, layer := 1) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.collision_layer = layer
	body.collision_mask = 0
	var cs := CollisionShape3D.new()
	var cyl := CylinderShape3D.new()
	cyl.radius = radius
	cyl.height = height
	cs.shape = cyl
	body.add_child(cs)
	parent.add_child(body)
	body.position = offset
	return body


static func _meshes(n: Node) -> Array[MeshInstance3D]:
	var out: Array[MeshInstance3D] = []
	if n is MeshInstance3D and (n as MeshInstance3D).mesh:
		out.append(n)
	for c in n.get_children():
		out.append_array(_meshes(c))
	return out


## Plays the first animation found in an imported prop (crab walk, etc.).
static func anim_player(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer:
		return node
	for c in node.get_children():
		var a := anim_player(c)
		if a:
			return a
	return null
