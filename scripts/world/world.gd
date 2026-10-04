class_name World
extends Node3D
## Hạ Long Skies: the whole open world, built in code. Home island with the great bronze drum
## in the middle; the rice terraces east, the waterfall cliff north-east, the One Pillar Pagoda
## west, the karst towers north, crab beach south-west and the lotus lagoon south-east.

signal star_sequence_done

var player: Player
var camera: GameCamera
var sun: DirectionalLight3D
var env: Environment
var spawn_point := Vector3(0, 2.6, 8.0)
var star_points: Dictionary = {} ## id -> Vector3 (for warps and the map)
var _crabs_left: Dictionary = {}
var _drum_rings: Array[MeshInstance3D] = []
var life: AmbientLife
var _drifting: Array[Node] = [] ## the drifting clouds, gathered once


## Look settings a level can override before _ready.
var sky_top := Color(0.25, 0.56, 0.93)
var sky_horizon := Color(0.78, 0.92, 1.0)
var fog_color := Color(0.66, 0.84, 0.98)
var fog_begin := 110.0
var fog_end := 520.0
var sea_deep := Color(0.10, 0.45, 0.82)
var sea_mid := Color(0.20, 0.66, 0.92)
var sea_shallow := Color(0.55, 0.90, 0.96)
var sun_rotation := Vector3(-52, -38, 0)
var sun_color := Color(1.0, 0.96, 0.88)
var title_focus := Vector3(0, 4.6, -6.5) ## where the title camera circles
var music := "world"
var ambient_energy := 0.82
var exposure := 1.08


func _ready() -> void:
	add_to_group("world")
	_environment()
	_sea()
	build()
	life = AmbientLife.new()
	add_child(life)
	ambient_life(life)
	Game.coin_total = get_tree().get_nodes_in_group("coin").size()
	if Game.args.has("count"):
		print("coins placed: ", Game.coin_total, "  red: ", get_tree().get_nodes_in_group("red_coin").size(), "  stars: ", star_points.size())
	ambience()


## Hạ Long Skies. Other levels override build(), ambience() and finale().
func build() -> void:
	_backdrop()
	_home()
	_terraces()
	_waterfall_cliff()
	_pagoda()
	_karsts()
	_beach()
	_lagoon()
	_sky_islands()
	_clouds()
	_travel_boat(Vector3(6.5, 0.0, 18.5), -2.5, "halong")


## Camera framings for the --tour screenshot pass: [name, eye, target].
func tour_views() -> Array:
	return [
		["home", Vector3(14, 12, 22), Vector3(0, 2, -2)],
		["drum", Vector3(4, 7.5, 2), Vector3(0, 4, -6.5)],
		["terraces", Vector3(28, 14, 16), Vector3(49, 7, -9)],
		["waterfall", Vector3(28, 7, -16), Vector3(28, 6, -38)],
		["pagoda", Vector3(-24, 9, 2), Vector3(-41, 5, -16)],
		["karsts", Vector3(0, 14, -30), Vector3(-15, 12, -54)],
		["beach", Vector3(-22, 10, 18), Vector3(-40, 1, 36)],
		["lagoon", Vector3(22, 10, 8), Vector3(40, 1, 35)],
		["overview", Vector3(60, 70, 90), Vector3(0, 0, -5)],
		["behind_hero", Vector3.ZERO, Vector3.ZERO],
	]


## Birds, butterflies, leaping fish, kites and far-off sails.
func ambient_life(l: AmbientLife) -> void:
	l.gulls(Vector3(0, 0, -5), 34.0, 20.0, 7)
	l.gulls(Vector3(-40, 0, 36), 14.0, 12.0, 3)
	l.butterflies(Vector3(0, 0, 2), 9.0, 2.3, 6)
	l.butterflies(Vector3(-40, 0, -14), 9.0, 2.45, 4)
	l.butterflies(Vector3(58, 0, 52), 5.0, 1.6, 3)
	l.fish_area(Vector3.ZERO, 110.0)
	l.kite(Vector3(-7.5, 2.4, -1.5), 15.0, Color("#e0452b"))
	l.kite(Vector3(44.0, 2.7, 4.0), 13.0, Color("#3d84c6"), Color("#ffffff"))
	l.kite(Vector3(-36.0, 1.6, 40.0), 11.0, Color("#ffd23f"), Color("#e0452b"))
	l.horizon_sails(150.0, 5)


func ambience() -> void:
	Sound.ambient("ambient_sea", -12.0)
	Sound.ambient("ambient_birds", -18.0)


## A junk boat moored at the shore that sails the hero to another level.
func _travel_boat(pos: Vector3, rot: float, to: String) -> void:
	var t := TravelBoat.new()
	t.destination = to
	t.position = pos
	t.rotation.y = rot
	add_child(t)


# =================================================================== environment

func _environment() -> void:
	var we := WorldEnvironment.new()
	env = Environment.new()
	var sky := Sky.new()
	var sm := ShaderMaterial.new()
	sm.shader = preload("res://shaders/sky.gdshader")
	sm.set_shader_parameter("noise", Fx.noise_tex)
	sm.set_shader_parameter("top_color", sky_top)
	sm.set_shader_parameter("horizon_color", sky_horizon)
	sky.sky_material = sm
	sky.radiance_size = Sky.RADIANCE_SIZE_128
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = ambient_energy
	env.ambient_light_sky_contribution = 0.7
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.tonemap_exposure = exposure
	env.tonemap_white = 6.0
	env.glow_enabled = not Game.args.has("noglow")
	env.glow_intensity = 0.55
	env.glow_bloom = 0.06
	env.glow_hdr_threshold = 1.1
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	env.ssao_enabled = not Game.is_phone() # Forward+ only
	env.ssao_radius = 1.4
	env.ssao_intensity = 1.6
	env.ssao_light_affect = 0.15
	env.fog_enabled = not Game.args.has("nofog")
	env.fog_mode = Environment.FOG_MODE_DEPTH
	env.fog_light_color = fog_color
	env.fog_density = 1.0
	env.fog_depth_begin = fog_begin
	env.fog_depth_end = fog_end
	env.fog_depth_curve = 1.6
	env.fog_sky_affect = 0.0
	env.adjustment_enabled = true
	env.adjustment_saturation = 1.22
	env.adjustment_contrast = 1.04
	we.environment = env
	add_child(we)
	sun = DirectionalLight3D.new()
	sun.rotation_degrees = sun_rotation
	sun.light_color = sun_color
	sun.light_energy = 1.35
	sun.shadow_enabled = true
	sun.shadow_bias = 0.04
	sun.shadow_normal_bias = 1.2
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS if Game.is_phone() else DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_max_distance = 80.0 if Game.is_phone() else 110.0
	sun.directional_shadow_blend_splits = true
	sun.light_angular_distance = 0.6
	add_child(sun)


func _sea() -> void:
	var mi := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(1600, 1600)
	pm.subdivide_width = 220
	pm.subdivide_depth = 220
	mi.mesh = pm
	var m := ShaderMaterial.new()
	m.shader = preload("res://shaders/water.gdshader")
	m.set_shader_parameter("noise", Fx.noise_tex)
	m.set_shader_parameter("deep", sea_deep)
	m.set_shader_parameter("mid", sea_mid)
	m.set_shader_parameter("shallow", sea_shallow)
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.name = "Sea"
	add_child(mi)


## Far-off pale islands and karst silhouettes that fade into the haze.
func _backdrop() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 64
	for i in 26:
		var a := TAU * i / 26.0 + rng.randf_range(-0.08, 0.08)
		var d := rng.randf_range(170.0, 300.0)
		var isl := Island.new()
		isl.collide = false
		isl.segments = 32
		if rng.randf() < 0.55:
			# Hạ Long limestone towers fading into the haze
			isl.kind = Island.Kind.KARST
			isl.radius = rng.randf_range(6.0, 13.0)
			isl.top = rng.randf_range(18.0, 46.0)
			isl.bulge = rng.randf_range(0.05, 0.25)
			isl.taper = rng.randf_range(-0.35, 0.0)
			isl.dome = isl.radius * 0.35
			isl.lip = isl.radius * 0.4
			isl.wobble = 0.18
		else:
			isl.kind = Island.Kind.GRASS
			isl.radius = rng.randf_range(18.0, 40.0)
			isl.top = rng.randf_range(4.0, 12.0)
			isl.dome = rng.randf_range(4.0, 10.0)
			isl.lip = 4.0
		isl.bottom = -6.0
		isl.seed = i + 100
		isl.position = Vector3(cos(a) * d, 0, sin(a) * d)
		add_child(isl)


# =================================================================== builders

func island(pos: Vector3, radius: float, top: float, kind := Island.Kind.GRASS, opts := {}) -> Island:
	var isl := Island.new()
	isl.radius = radius
	isl.top = top
	isl.kind = kind
	isl.bottom = opts.get("bottom", -5.0)
	isl.dome = opts.get("dome", 0.3)
	isl.lip = opts.get("lip", 0.6)
	isl.wobble = opts.get("wobble", 0.1)
	isl.bulge = opts.get("bulge", 0.0)
	isl.taper = opts.get("taper", 0.0)
	isl.floating = opts.get("floating", false)
	isl.stretch = opts.get("stretch", Vector2.ONE)
	isl.seed = opts.get("seed", int(pos.x * 7 + pos.z * 13))
	isl.position = Vector3(pos.x, pos.y, pos.z)
	add_child(isl)
	return isl


func prop(name: String, pos: Vector3, rot := 0.0, s := 1.0, solid := false) -> Node3D:
	var p := Props.make(name)
	p.position = pos
	p.rotation.y = rot
	p.scale = Vector3.ONE * s
	add_child(p)
	if solid:
		Props.solidify(p)
	return p


func tree(pos: Vector3, s := 1.0, kind := "tree_round") -> void:
	var t := prop(kind, pos, randf() * TAU, s)
	Props.add_cylinder(t, 0.28, 2.4, Vector3(0, 1.2, 0))


func coin(pos: Vector3) -> Coin:
	var c := Coin.new()
	c.position = pos
	add_child(c)
	return c


func red_coin(pos: Vector3) -> Coin:
	var c := Coin.new(true)
	c.position = pos
	add_child(c)
	return c


func coin_ring(center: Vector3, r: float, n := 8) -> void:
	for i in n:
		var a := TAU * i / n
		coin(center + Vector3(cos(a) * r, 0, sin(a) * r))


func coin_line(a: Vector3, b: Vector3, n := 5) -> void:
	for i in n:
		coin(a.lerp(b, float(i) / maxf(n - 1, 1)))


func coin_arc(a: Vector3, b: Vector3, h: float, n := 5) -> void:
	for i in n:
		var t := float(i) / maxf(n - 1, 1)
		coin(a.lerp(b, t) + Vector3.UP * (4.0 * h * t * (1.0 - t)))


func star(id: String, pos: Vector3, hidden_until := "") -> Star:
	var s := Star.new()
	s.id = id
	s.hidden_until = hidden_until
	s.position = pos
	add_child(s)
	star_points[id] = pos
	return s


func block(pos: Vector3, drum := true, coins := 1) -> Block:
	var b := Block.new()
	b.type = Block.Type.DRUM if drum else Block.Type.BRICK
	b.coins = coins
	b.position = pos
	add_child(b)
	return b


func spring(pos: Vector3, power := 19.0) -> SpringDrum:
	var s: SpringDrum = SpringDrum.new()
	s.power = power
	s.position = pos
	add_child(s)
	return s


func checkpoint(pos: Vector3, rot := 0.0) -> Checkpoint:
	var c := Checkpoint.new()
	c.position = pos
	c.rotation.y = rot
	add_child(c)
	return c


func crab(pos: Vector3, wander := 5.0, tag := "") -> Crab:
	var c := Crab.new()
	c.wander = wander
	c.group_tag = tag
	c.position = pos
	add_child(c)
	if tag != "":
		_crabs_left[tag] = _crabs_left.get(tag, 0) + 1
	return c


func pipe(pos: Vector3, height: float) -> void:
	var p := prop("bamboo_pipe", pos, randf() * TAU)
	p.scale = Vector3(1.8, height / 2.0, 1.8)
	var body := Props.add_cylinder(self, 1.26, height, pos + Vector3(0, height * 0.5, 0))
	body.name = "PipeBody"


func plank_bridge(a: Vector3, b: Vector3, gap_at := -1.0) -> void:
	var d := b - a
	var n := int(d.length() / 1.0)
	var yaw := atan2(d.x, d.z)
	var gap := 1.25 / d.length()
	for i in n:
		var t := (i + 0.5) / n
		if gap_at >= 0.0 and absf(t - gap_at) < gap:
			continue
		var pos := a.lerp(b, t)
		var p := prop("bridge_plank", pos, yaw + randf_range(-0.03, 0.03))
		p.position.y = pos.y - 0.21
	# one smooth deck per stretch, so the planks never leave little steps that stop the hero
	var spans := [[0.0, 1.0]]
	if gap_at >= 0.0:
		spans = [[0.0, gap_at - gap], [gap_at + gap, 1.0]]
	# a short ramp dips from each end into the island, so stepping on or off never meets a
	# little wall where the island's rounded edge has already dropped away
	var ext := d.normalized() * 1.8
	spans.append([a - ext + Vector3.DOWN * 0.7, a])
	spans.append([b, b + ext + Vector3.DOWN * 0.7])
	for sp in spans:
		var p0: Vector3 = sp[0] if sp[0] is Vector3 else a.lerp(b, sp[0])
		var p1: Vector3 = sp[1] if sp[1] is Vector3 else a.lerp(b, sp[1])
		var body := StaticBody3D.new()
		body.collision_layer = 1
		body.collision_mask = 0
		var cs := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = Vector3(1.5, 0.3, p0.distance_to(p1))
		cs.shape = box
		cs.position.y = -0.15
		body.add_child(cs)
		add_child(body)
		body.global_transform = Transform3D(Basis.looking_at(p1 - p0, Vector3.UP), (p0 + p1) * 0.5)
	for side in [-1.0, 1.0]:
		var off: Vector3 = Vector3(cos(yaw), 0, -sin(yaw)) * 0.62 * float(side)
		for i in range(0, n, 2):
			var t := (i + 1.0) / n
			if gap_at >= 0.0 and absf(t - gap_at) < 2.0 / d.length():
				continue
			var pos: Vector3 = a.lerp(b, t) + off
			var f := prop("fence_bamboo", pos + Vector3(0, -0.1, 0), yaw + PI / 2.0, 0.9)
			f.scale.x = 0.9


func lotus(pos: Vector3) -> LotusPad:
	var l := LotusPad.new()
	l.position = pos
	add_child(l)
	return l


func sampan(a: Vector3, b: Vector3, trip := 6.0, phase := 0.0) -> Sampan:
	var s := Sampan.new()
	s.a = a
	s.b = b
	s.trip = trip
	s.phase = phase
	add_child(s)
	return s


func jelly(pos: Vector3, travel: Vector3, period := 4.0, phase := 0.0) -> JellyBlock:
	var j := JellyBlock.new()
	j.position = pos
	j.travel = travel
	j.period = period
	j.phase = phase
	add_child(j)
	return j


func crusher(pos: Vector3, lift := 4.2, period := 3.4, phase := 0.0) -> Crusher:
	var c := Crusher.new()
	c.rest_y = pos.y
	c.lift = lift
	c.period = period
	c.phase = phase
	c.position = pos
	add_child(c)
	return c


func scatter(center: Vector3, radius: float, count: int, top_y: float, names: Array, seed := 1) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	for i in count:
		var a := rng.randf() * TAU
		var r := sqrt(rng.randf()) * radius
		var p := center + Vector3(cos(a) * r, 0, sin(a) * r)
		p.y = top_y
		prop(names[rng.randi() % names.size()], p, rng.randf() * TAU, rng.randf_range(0.8, 1.3), false)


# =================================================================== areas

func _home() -> void:
	island(Vector3.ZERO, 15.0, 2.0, Island.Kind.GRASS, {"dome": 0.4, "seed": 3})
	# the great bronze drum: the finale stage
	prop("drum_big", Vector3(0, 2.3, -6.5), 0.0, 1.0)
	Props.add_cylinder(self, 2.05, 2.2, Vector3(0, 3.4, -6.5))
	_add_drum_glow()
	coin_ring(Vector3(0, 6.3, -6.5), 1.5, 6)
	checkpoint(Vector3(4.5, 2.35, 6.0), -0.4)
	for p in [Vector3(-10, 2.1, -6), Vector3(10.5, 2.1, -4), Vector3(-12, 2.1, 3), Vector3(9, 2.1, 9), Vector3(-6.5, 2.1, 12.0), Vector3(12, 2.1, 3)]:
		tree(p, randf_range(0.9, 1.2))
	prop("cong_lang", Vector3(-10.2, 2.25, 9.6), -0.85, 1.0, true)
	scatter(Vector3.ZERO, 12.0, 40, 2.3, ["flower_pink", "flower_yellow", "grass_tuft", "grass_tuft"], 11)
	coin_ring(Vector3(0, 2.9, 3.5), 4.5, 8)
	coin_line(Vector3(-11, 2.9, -2), Vector3(-11, 2.9, 4), 4)
	coin_line(Vector3(8, 2.9, -10), Vector3(12, 2.9, -6), 3)
	block(Vector3(-5, 5.4, 4), true, 5)
	block(Vector3(-4, 5.4, 4), false, 0)
	block(Vector3(-6, 5.4, 4), false, 1)
	block(Vector3(6, 5.4, -1), true, 1)
	spring(Vector3(-8.5, 2.2, 11.0))
	prop("mushroom", Vector3(7.5, 2.3, 7.5), 0.3)
	prop("lantern", Vector3(-3.0, 2.3, 11.8), 0.0, 1.0)
	prop("lantern", Vector3(3.0, 2.3, 11.8), 0.0, 1.0)
	red_coin(Vector3(0, 5.5, -6.5)) # 1: on top of the big drum


func _add_drum_glow() -> void:
	# eight rings of light on the drum face; one lights up per star
	for i in 8:
		var r := MeshInstance3D.new()
		var t := TorusMesh.new()
		t.inner_radius = 0.2 + i * 0.22
		t.outer_radius = 0.26 + i * 0.22
		t.rings = 48
		t.ring_segments = 6
		r.mesh = t
		r.position = Vector3(0, 4.53, -6.5)
		r.scale = Vector3(1, 0.2, 1)
		var lit := Game.has_star(Game.STARS[i]["id"])
		r.material_override = Fx.toon_material(Color(1.0, 0.85, 0.4), 0.0, Color(1.0, 0.7, 0.3), 3.0 if lit else 0.0)
		r.visible = lit
		add_child(r)
		_drum_rings.append(r)


func _refresh_drum() -> void:
	# only Hạ Long Skies has the drum; the other levels leave the ring list empty
	for i in _drum_rings.size():
		var lit := Game.has_star(Game.STARS[i]["id"])
		if lit and not _drum_rings[i].visible:
			_drum_rings[i].visible = true
			_drum_rings[i].scale = Vector3(0.01, 0.2, 0.01)
			create_tween().tween_property(_drum_rings[i], "scale", Vector3(1, 0.2, 1), 0.6).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
			_drum_rings[i].material_override = Fx.toon_material(Color(1.0, 0.85, 0.4), 0.0, Color(1.0, 0.7, 0.3), 3.0)


func _terraces() -> void:
	# stepping stones from home
	island(Vector3(19.5, 0, -2.0), 2.2, 1.6, Island.Kind.GRASS, {"seed": 21})
	island(Vector3(24.0, 0, -3.5), 2.0, 2.0, Island.Kind.GRASS, {"seed": 22})
	coin_arc(Vector3(15.5, 2.8, -1), Vector3(19.5, 2.4, -2), 1.2, 3)
	coin_arc(Vector3(20.5, 2.4, -2.3), Vector3(24, 2.8, -3.5), 1.2, 3)
	# six rice-paddy tiers, each 1.8 m above the last
	var tiers := [
		[Vector3(46, 0, -6), 17.0, 2.5], [Vector3(47.5, 0, -7.5), 13.5, 4.1],
		[Vector3(49, 0, -9), 10.5, 5.7], [Vector3(50, 0, -10.5), 8.0, 7.3],
		[Vector3(51, 0, -12), 5.5, 8.9], [Vector3(51.5, 0, -13), 3.2, 10.5],
	]
	for i in tiers.size():
		var t: Array = tiers[i]
		var kind := Island.Kind.PADDY if i in [1, 3] else Island.Kind.GRASS
		island(t[0], t[1], t[2], kind, {"dome": 0.1, "lip": 0.35, "wobble": 0.03, "seed": 30 + i, "bottom": -5.0 if i == 0 else t[2] - 3.0})
	checkpoint(Vector3(33, 2.9, -3), PI * 0.5)
	for i in range(1, tiers.size()):
		var t: Array = tiers[i]
		var c: Vector3 = t[0]
		var a := -0.6 + i * 0.9
		coin(c + Vector3(cos(a) * (t[1] - 1.2), t[2] + 0.8, sin(a) * (t[1] - 1.2)))
	star("terraces", Vector3(51.5, 11.3, -13))
	tree(Vector3(41, 2.6, 8.5), 1.1, "tree_palm")
	tree(Vector3(56, 2.6, 4), 1.0)
	scatter(Vector3(44, 0, 0), 5.0, 12, 2.7, ["grass_tuft", "flower_yellow"], 31)
	coin_ring(Vector3(34.5, 3.3, 6.5), 2.0, 6)
	coin_line(Vector3(52, 3.3, 7), Vector3(58, 3.3, 3), 4)
	prop("bamboo_cluster", Vector3(40, 2.5, -18), 0.0, 1.0)
	red_coin(Vector3(61.5, 3.5, -3)) # 2: on the far edge of the lowest terrace
	crab(Vector3(40, 2.7, 2), 4.0)


func _waterfall_cliff() -> void:
	# base island in front of the falls, linked to the terraces by two stones
	island(Vector3(28, 0, -32), 10.0, 1.8, Island.Kind.GRASS, {"seed": 41})
	island(Vector3(33.5, 0, -22.5), 1.8, 2.0, Island.Kind.GRASS, {"seed": 42})
	island(Vector3(37.5, 0, -20.0), 1.6, 2.2, Island.Kind.GRASS, {"seed": 43})
	# two stone pillars, a back wall and a roof make an alcove hidden behind the falls
	island(Vector3(21.3, 0, -40), 4.2, 13.0, Island.Kind.STONE, {"lip": 1.2, "bulge": 0.08, "seed": 44})
	island(Vector3(34.7, 0, -40), 4.2, 13.0, Island.Kind.STONE, {"lip": 1.2, "bulge": 0.08, "seed": 45})
	island(Vector3(28, 0, -46.2), 4.6, 13.5, Island.Kind.STONE, {"lip": 1.2, "seed": 46})
	island(Vector3(28, 9.5, -40.5), 5.6, 3.8, Island.Kind.GRASS, {"floating": true, "bottom": -1.2, "lip": 0.8, "stretch": Vector2(1.25, 1.0), "seed": 47})
	# the ledge in the alcove, and the star waiting on it
	island(Vector3(28, 0, -39.8), 2.4, 3.0, Island.Kind.STONE, {"lip": 0.4, "seed": 48})
	star("waterfall", Vector3(28, 3.4, -39.8))
	var wf := Waterfall.new()
	wf.width = 4.2
	wf.height = 13.2
	wf.curve_out = 1.3
	wf.position = Vector3(28, 13.2, -35.6)
	add_child(wf)
	coin_line(Vector3(28, 2.6, -24), Vector3(28, 2.6, -32), 5)
	coin_arc(Vector3(33.5, 2.8, -22.5), Vector3(37.5, 3.0, -20), 1.5, 3)
	tree(Vector3(22, 1.9, -27), 1.0)
	tree(Vector3(35, 1.9, -30), 0.9, "tree_palm")
	checkpoint(Vector3(31.5, 2.2, -27), PI)
	prop("rock_karst", Vector3(18, 1.6, -33), 0.4, 0.6, true)


func _pagoda() -> void:
	island(Vector3(-40, 0, -14), 15.0, 2.2, Island.Kind.GRASS, {"dome": 0.25, "seed": 51})
	# the bridge from home with a gap in the middle
	plank_bridge(Vector3(-14.3, 2.05, -5.0), Vector3(-26.6, 2.25, -7.2), 0.55)
	coin_line(Vector3(-16, 2.9, -5.3), Vector3(-19, 2.9, -5.8), 3)
	coin_arc(Vector3(-19.5, 3.0, -5.9), Vector3(-22.5, 3.0, -6.4), 1.8, 4)
	var pagoda := prop("pagoda", Vector3(-42, 2.4, -16), 0.25, 1.0, true)
	pagoda.name = "Pagoda"
	# bamboo steps climbing toward the roof
	var steps := [[Vector3(-36, 2.2, -12), 1.6], [Vector3(-35.5, 2.2, -16.5), 3.4], [Vector3(-37.5, 2.2, -20.5), 5.2], [Vector3(-41.5, 2.2, -22.0), 7.0]]
	for s in steps:
		pipe(s[0], s[1])
		coin((s[0] as Vector3) + Vector3(0, float(s[1]) + 0.9, 0))
	spring(Vector3(-46.5, 2.3, -12.5), 20.0)
	# a golden lotus crowns the roof: the landing spot for the star
	var crown := prop("lotus_flower", Vector3(-42, 8.05, -16), 0.4, 2.4)
	crown.name = "LotusCrown"
	Props.add_cylinder(self, 1.25, 0.3, Vector3(-42, 8.2, -16))
	star("pagoda", Vector3(-42, 8.7, -16))
	star("lanterns", Vector3(-38.5, 2.9, -10.5), "lantern_star")
	checkpoint(Vector3(-30, 2.5, -9), -PI * 0.5)
	for p in [Vector3(-50, 2.3, -6), Vector3(-47, 2.3, -26), Vector3(-30, 2.3, -22), Vector3(-52, 2.3, -18)]:
		tree(p, randf_range(0.9, 1.2))
	for p in [Vector3(-33, 2.3, -3), Vector3(-45, 2.3, -3)]:
		prop("bamboo_cluster", p, randf() * TAU, 1.0)
	prop("lantern", Vector3(-38, 2.4, -9.5), 0.0, 1.0)
	prop("lantern", Vector3(-46, 2.4, -9.5), 0.0, 1.0)
	scatter(Vector3(-40, 0, -14), 12.0, 30, 2.45, ["flower_pink", "grass_tuft", "flower_yellow"], 52)
	coin_ring(Vector3(-47, 3.0, -8), 2.2, 6)
	coin_line(Vector3(-50, 3.0, -14), Vector3(-50, 3.0, -21), 4)
	red_coin(Vector3(-41.5, 10.6, -22.0)) # 3: above the highest bamboo step
	crab(Vector3(-31.5, 2.6, -5.0), 1.5)


func _karsts() -> void:
	island(Vector3(-14, 0, -42), 9.0, 1.5, Island.Kind.GRASS, {"seed": 61})
	# long bamboo causeway from home, guarded by crushers
	plank_bridge(Vector3(-5.2, 2.05, -14.0), Vector3(-10.6, 1.6, -33.4))
	for c in [[Vector3(-6.6, 2.2, -19.0), 0.0], [Vector3(-8.0, 2.3, -24.0), 1.1], [Vector3(-9.4, 2.1, -29.0), 2.2]]:
		crusher(c[0], 4.2, 3.2, c[1]).rotation.y = 0.27
	coin_line(Vector3(-6.2, 2.9, -17), Vector3(-9.8, 2.7, -31), 7)
	checkpoint(Vector3(-11, 1.8, -36.5), PI * 0.1)
	# the towers
	island(Vector3(-20, 0, -50), 3.0, 10.0, Island.Kind.STONE, {"lip": 0.7, "bulge": 0.12, "wobble": 0.08, "seed": 62})
	island(Vector3(-12.5, 0, -50.5), 2.5, 16.0, Island.Kind.STONE, {"lip": 0.6, "bulge": 0.1, "wobble": 0.08, "seed": 63})
	island(Vector3(-16, 0, -56.5), 3.0, 22.0, Island.Kind.STONE, {"lip": 0.7, "bulge": 0.1, "wobble": 0.08, "seed": 64})
	island(Vector3(-8, 0, -58), 2.6, 7.0, Island.Kind.STONE, {"lip": 0.6, "bulge": 0.15, "seed": 65})
	spring(Vector3(-16, 1.7, -46.5), 21.0)
	island(Vector3(-8.8, 0, -52), 1.5, 3.6, Island.Kind.STONE, {"lip": 0.4, "seed": 66})
	spring(Vector3(-20, 10.2, -50), 20.0)
	spring(Vector3(-12.5, 16.2, -50.5), 21.0)
	coin_line(Vector3(-20, 11.5, -50), Vector3(-20, 14.5, -50), 3)
	coin_ring(Vector3(-14, 2.3, -42), 3.0, 6)
	coin_ring(Vector3(-12.5, 17.0, -50.5), 1.2, 5)
	star("karst", Vector3(-16, 23.0, -56.5))
	coin_arc(Vector3(-13.2, 18.5, -51.8), Vector3(-15.5, 23.0, -55.6), 2.0, 4)
	red_coin(Vector3(-8, 7.9, -58)) # 4: top of the short tower
	for p in [Vector3(-8, 1.8, -38), Vector3(-19, 1.8, -36)]:
		prop("bamboo_cluster", p, randf() * TAU, 0.9)
	prop("rock_karst", Vector3(-4, 1.4, -46), 0.2, 0.55, true)


func _beach() -> void:
	# a sandbar path from home
	for p in [Vector3(-14.5, 0, 14.0), Vector3(-19.0, 0, 18.0), Vector3(-23.5, 0, 21.5)]:
		island(p, 2.6, 0.9, Island.Kind.SAND, {"dome": 0.15, "seed": int(p.x)})
	coin_line(Vector3(-14.5, 1.7, 14), Vector3(-23.5, 1.7, 21.5), 5)
	island(Vector3(-40, 0, 36), 16.0, 1.2, Island.Kind.SAND, {"dome": 0.5, "wobble": 0.14, "seed": 71})
	for p in [Vector3(-47, 1.4, 28), Vector3(-33, 1.4, 44), Vector3(-50, 1.4, 42), Vector3(-30, 1.4, 30), Vector3(-42, 1.4, 48)]:
		tree(p, randf_range(0.9, 1.2), "tree_palm")
	for i in 5:
		var a := TAU * i / 5.0 + 0.4
		crab(Vector3(-40 + cos(a) * 7.0, 1.8, 36 + sin(a) * 7.0), 4.0, "beach_crab")
	star("crabs", Vector3(-40, 2.2, 36), "crab_star")
	checkpoint(Vector3(-30, 1.5, 27), PI * 0.75)
	coin_ring(Vector3(-40, 2.1, 36), 10.0, 10)
	coin_line(Vector3(-46, 2.3, 30), Vector3(-34, 2.3, 42), 5)
	red_coin(Vector3(-52, 2.2, 36)) # 5: far end of the beach
	sampan(Vector3(-27, 0.0, 49), Vector3(-17, 0.0, 55), 7.0) # a lazy boat with coins on it
	coin_line(Vector3(-22, 1.5, 52), Vector3(-16, 1.5, 55.5), 3)
	prop("rock_karst", Vector3(-55, 0.6, 24), 1.2, 0.5, true)


func _lagoon() -> void:
	for p in [Vector3(15.5, 0.15, 13.0), Vector3(19.5, 0.15, 16.8), Vector3(23.8, 0.15, 20.2)]:
		lotus(p)
		coin(p + Vector3(0, 1.2, 0))
	# a little sand jetty to wait for the ferry on
	island(Vector3(28.0, 0, 23.6), 1.9, 0.7, Island.Kind.SAND, {"dome": 0.1, "seed": 82})
	prop("lantern", Vector3(28.6, 0.8, 22.8), 0.0, 0.9)
	sampan(Vector3(31.8, 0.0, 26.6), Vector3(40.5, 0.0, 34.0), 5.5)
	red_coin(Vector3(36, 3.2, 30.2)) # 6: above the ferry's route
	jelly(Vector3(43.5, 0.2, 37.5), Vector3(0, 2.2, 0), 3.6)
	jelly(Vector3(46.8, 1.2, 40.0), Vector3(2.4, 0, 0), 4.2, 1.0)
	# a sand step between the last jelly and the island
	island(Vector3(51.0, 0, 43.6), 1.9, 1.2, Island.Kind.SAND, {"dome": 0.1, "seed": 83})
	prop("lotus_flower", Vector3(53.2, 0.15, 45.2), 0.7, 1.1)
	island(Vector3(58, 0, 52), 8.0, 1.5, Island.Kind.GRASS, {"seed": 81})
	star("lagoon", Vector3(58, 2.3, 52))
	coin_ring(Vector3(58, 2.3, 52), 4.0, 8)
	checkpoint(Vector3(55.5, 1.8, 47.5), PI * 0.8)
	tree(Vector3(61, 1.6, 55), 1.0)
	tree(Vector3(55, 1.6, 57), 0.9, "tree_palm")
	for i in 6:
		var a := TAU * i / 6.0
		prop("lotus_flower", Vector3(58 + cos(a) * 11.0, 0.15, 52 + sin(a) * 11.0), a, 1.2)
	for i in 10:
		var a := randf() * TAU
		var d := randf_range(4.0, 14.0)
		prop("lotus_pad", Vector3(33 + cos(a) * d, 0.1, 32 + sin(a) * d), a, randf_range(0.6, 1.0))


func _sky_islands() -> void:
	# above home: reached with the spring by the gate
	island(Vector3(-10, 8.5, 16), 3.0, 0.8, Island.Kind.GRASS, {"floating": true, "bottom": -3.0, "seed": 91})
	coin_ring(Vector3(-10, 10.0, 16), 1.6, 5)
	island(Vector3(-16.5, 9.5, 21.5), 2.6, 0.8, Island.Kind.GRASS, {"floating": true, "bottom": -2.5, "seed": 92})
	red_coin(Vector3(-16.5, 11.3, 21.5)) # 7
	island(Vector3(-11.5, 11.5, 28.0), 2.4, 0.8, Island.Kind.GRASS, {"floating": true, "bottom": -2.5, "seed": 93})
	block(Vector3(-11.5, 15.2, 28.0), true, 8)
	tree(Vector3(-10.8, 9.3, 15.2), 0.7)
	# a jelly staircase east of home to a floating garden
	jelly(Vector3(8, 2.1, -12), Vector3(0, 1.2, 0), 3.0)
	jelly(Vector3(11, 4.0, -15), Vector3(0, 1.2, 0), 3.0, 1.0)
	jelly(Vector3(14, 6.0, -18), Vector3(0, 1.2, 0), 3.0, 2.0)
	island(Vector3(18, 8.0, -23), 3.6, 1.0, Island.Kind.GRASS, {"floating": true, "bottom": -3.5, "seed": 94})
	red_coin(Vector3(18, 10.2, -23)) # 8
	coin_ring(Vector3(18, 9.8, -23), 2.2, 6)
	prop("mushroom", Vector3(19.5, 9.1, -22), 0.0, 1.3)
	# a lone floating rock over the lagoon with a drum block
	island(Vector3(14, 8.0, 20), 2.6, 0.8, Island.Kind.GRASS, {"floating": true, "bottom": -2.5, "seed": 95})
	spring(Vector3(9.5, 2.2, 9.0), 21.0)
	block(Vector3(14, 12.4, 20), true, 6)
	coin_arc(Vector3(10, 6, 10.5), Vector3(13.2, 10.2, 18.2), 3.0, 5)
	# stars for the hundred coins appear over the hero's head
	var cs := star("coins", Vector3(0, 6.5, 3.5), "coin_star")
	cs.name = "CoinStar"


func _clouds() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	for i in 22:
		var a := rng.randf() * TAU
		var d := rng.randf_range(20.0, 120.0)
		var c := prop("cloud", Vector3(cos(a) * d, rng.randf_range(16.0, 34.0), sin(a) * d), rng.randf() * TAU, rng.randf_range(1.2, 3.2))
		c.set_meta("drift", rng.randf_range(0.3, 0.8))
		_no_shadow(c)
		c.add_to_group("cloud")
	for i in 14:
		var a := rng.randf() * TAU
		var d := rng.randf_range(70.0, 160.0)
		_no_shadow(prop("cloud", Vector3(cos(a) * d, rng.randf_range(0.8, 3.0), sin(a) * d), rng.randf() * TAU, rng.randf_range(2.5, 5.0)))


## A name board floating over a landmark. It hides when the camera is close (it would sit on
## the HUD) and follows language changes.
func sign_board(text_en: String, text_vi: String, at: Vector3, size := 90) -> Label3D:
	var l := Label3D.new()
	l.text = Game.t(text_en, text_vi)
	l.font = UiKit.display_font()
	l.font_size = size
	l.outline_size = 20
	l.modulate = Color("#fff6d8")
	l.outline_modulate = Color(0.12, 0.06, 0.12)
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.pixel_size = 0.01
	l.position = at
	l.visibility_range_begin = 14.0
	l.visibility_range_begin_margin = 3.0
	l.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
	l.add_to_group("sign_board")
	add_child(l)
	Game.language_changed.connect(func(): l.text = Game.t(text_en, text_vi))
	return l


func _no_shadow(n: Node) -> void:
	if n is GeometryInstance3D:
		(n as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for c in n.get_children():
		_no_shadow(c)


func _process(delta: float) -> void:
	if _drifting.is_empty():
		_drifting = get_tree().get_nodes_in_group("cloud")
	for c in _drifting:
		var n := c as Node3D
		n.position.x += n.get_meta("drift", 0.5) * delta
		if n.position.x > 140.0:
			n.position.x = -140.0


# =================================================================== events

func on_crab_defeated(tag: String) -> void:
	if tag == "":
		return
	_crabs_left[tag] = _crabs_left.get(tag, 1) - 1
	get_tree().call_group("hud", "toast", Game.t("Crabs left: %d", "Còn %d con cua") % _crabs_left[tag])
	if _crabs_left[tag] <= 0 and tag == "beach_crab":
		get_tree().call_group("crab_star", "reveal")


func show_star_reveal(s: Star) -> void:
	if s.hidden_until == "coin_star" and player:
		s.global_position = player.star_spot() + player.facing * 1.2
	get_tree().call_group("hud", "toast", Game.t("A star appeared!", "Một ngôi sao đã xuất hiện!"))


## The STAR GET moment: freeze, face the camera, lift the star high, fanfare, banner.
func star_cutscene(s: Star, who: Node) -> void:
	var p := who as Player
	var id := s.id ## the star frees itself mid-cutscene
	Game.in_cutscene = true
	p.lock(true)
	var first := not Game.has_star(id)
	Game.collect_star(id)
	Sound.play("star_collect", 0.0)
	Fx.star_burst(s.global_position + Vector3.UP * 0.6)
	Fx.hitstop(0.08)
	s.consume()
	await get_tree().create_timer(0.25).timeout
	# wait until grounded so the pose isn't in mid-air
	var t := 0.0
	while not p.is_on_floor() and t < 2.5:
		await get_tree().physics_frame
		t += get_physics_process_delta_time()
	p.facing = (camera.global_position - p.global_position) * Vector3(1, 0, 1)
	p.facing = p.facing.normalized() if p.facing.length() > 0.01 else Vector3.BACK
	p.model.play("star_get", 0.1)
	var held := Props.make("star")
	held.scale = Vector3.ONE * 0.55
	var att := p.model.hold(held)
	var spin := held.create_tween().set_loops()
	spin.tween_property(held, "rotation:y", TAU, 1.2).from(0.0)
	Sound.music("")
	Sound.jingle("star_get")
	var c := p.global_position + Vector3.UP * 0.8
	var a0 := atan2(camera.global_position.x - p.global_position.x, camera.global_position.z - p.global_position.z)
	camera.orbit_shot(c, 4.2, 1.2, a0 + 0.6, a0, 1.4)
	get_tree().call_group("hud", "star_banner", id, first)
	Fx.sparkle(c + Vector3.UP * 1.0, Color(1, 0.9, 0.5), 20, 5.0, 0.45, 1.2)
	_refresh_drum()
	await get_tree().create_timer(3.4).timeout
	spin.kill()
	if att:
		att.queue_free()
	else:
		held.queue_free()
	if Game.level_star_count() >= Game.level_star_total() and not Game.finished:
		finale(p)
		return
	camera.release()
	p.lock(false)
	Game.in_cutscene = false
	Sound.music(music, 1.5)
	star_sequence_done.emit()


func finale(p: Player) -> void:
	all_stars_finale(p)


## ALL STARS! Everyone gathers at the bronze drum, which rings out; confetti, dance, credits.
func all_stars_finale(p: Player) -> void:
	Game.finished = true
	Game.finished_levels[Game.level] = true
	Game.in_cutscene = true
	if Game.best_time <= 0.0 or Game.play_time < Game.best_time:
		Game.best_time = Game.play_time
	Game.save()
	get_tree().call_group("hud", "fade", 1.0, 0.6)
	await get_tree().create_timer(0.7).timeout
	p.teleport(Vector3(0, 4.6, -6.5), Vector3.BACK)
	p.lock(true)
	camera.global_position = Vector3(0, 6.2, -1.3)
	camera.look_at(Vector3(0, 5.3, -6.5))
	camera.cutscene = true
	get_tree().call_group("hud", "fade", 0.0, 0.8)
	Sound.music("all_stars", 0.3)
	Sound.play("drum_boom", 2.0)
	Fx.shake(0.5, 0.5)
	for i in 3:
		Fx.ring(Vector3(0, 4.6, -6.5), Color(1, 0.85, 0.4, 1), 10.0 + i * 5.0, 1.0 + i * 0.3)
	var conf := Fx.confetti(Vector3(0, 14, -6.5), 220, 9.0)
	p.model.play("dance", 0.2)
	get_tree().call_group("hud", "all_stars_banner")
	camera.orbit_shot(Vector3(0, 4.9, -6.5), 5.2, 1.3, 0.0, TAU, 14.0)
	await get_tree().create_timer(6.0).timeout
	Sound.play("drum_boom", 0.0, 0.9)
	Fx.star_burst(Vector3(0, 6, -6.5))
	await get_tree().create_timer(8.5).timeout
	get_tree().call_group("hud", "ending_card")
	conf.emitting = false
