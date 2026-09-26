class_name Props
extends RefCounted
## Loads the Blender props (assets/models/props/*.glb), converts them to the toon look, and
## optionally gives them collision. When a file is missing a simple stand-in shape is used, so
## the world is always playable.

const DIR := "res://assets/models/props/"

static var _scenes: Dictionary = {}
static var _shapes: Dictionary = {}

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
		Fx.toonify(node, outline, 0.02, unique)
	else:
		node = _standin(name)
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
