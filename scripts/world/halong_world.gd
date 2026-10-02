class_name HalongWorld
extends World
## Vịnh Hạ Long: an emerald bay crowded with limestone towers. The pier islet is home; the
## floating fishing village lies east, Surprise Cave north-west, the Fighting Cock rocks
## south-west, Ti Tốp's summit north-east, and a dragon circles the whole bay.

var dragon: Dragon
var village_deck := 0.8 ## raft_house deck height (from the Blender prop)
var _pearl_home := Vector3(0, 1.4, -3.5)


func _init() -> void:
	sky_top = Color(0.36, 0.62, 0.86)
	sky_horizon = Color(0.84, 0.92, 0.90)
	fog_color = Color(0.74, 0.86, 0.84)
	fog_begin = 75.0
	fog_end = 380.0
	sea_deep = Color(0.04, 0.36, 0.38)
	sea_mid = Color(0.10, 0.56, 0.50)
	sea_shallow = Color(0.46, 0.86, 0.72)
	sun_rotation = Vector3(-46, 32, 0)
	sun_color = Color(1.0, 0.94, 0.84)
	spawn_point = Vector3(0, 1.6, 4.0)
	title_focus = Vector3(0, 1.0, 0.5)
	music = "underwater_or_night"
	ambient_energy = 0.5
	exposure = 1.0


func build() -> void:
	_bay_backdrop()
	_pier()
	_village()
	_cave()
	_trong_mai()
	_titop()
	_dragon()
	_bay_karsts()
	_junk_ferry()
	_clouds()


func tour_views() -> Array:
	return [
		["pier", Vector3(10, 7, 14), Vector3(0, 1, 0)],
		["village", Vector3(22, 9, 14), Vector3(32, 2, -4)],
		["cave_outside", Vector3(-10, 8, -8), Vector3(-30, 5, -30)],
		["cave_inside", Vector3(-23.5, 3.5, -23.5), Vector3(-31, 4, -33)],
		["trongmai", Vector3(-14, 7, 34), Vector3(-25, 6, 25)],
		["titop", Vector3(14, 14, -20), Vector3(28, 14, -42)],
		["dragon", Vector3(18, 12, 10), Vector3(10, 3, -8)],
		["overview", Vector3(40, 60, 60), Vector3(0, 0, -10)],
		["behind_hero", Vector3.ZERO, Vector3.ZERO],
	]


func ambient_life(l: AmbientLife) -> void:
	l.gulls(Vector3(10, 0, -5), 30.0, 22.0, 8)
	l.gulls(Vector3(32, 0, -2), 10.0, 9.0, 4)
	l.butterflies(Vector3(28, 0, -36), 7.0, 1.0, 4)
	l.butterflies(Vector3(0, 0, 0), 5.0, 1.0, 3)
	l.fish_area(Vector3(5, 0, -5), 90.0)
	l.horizon_sails(120.0, 6)


func ambience() -> void:
	Sound.ambient("ambient_sea", -10.0)
	Sound.ambient("ambient_birds", -20.0)


# ------------------------------------------------------------------ helpers

func karst(pos: Vector3, r: float, top: float, opts := {}) -> Island:
	var o := {"lip": minf(r * 0.35, 1.6), "bulge": 0.12, "taper": -0.1, "dome": minf(r * 0.3, 1.5), "wobble": 0.14, "bottom": -6.0}
	o.merge(opts, true)
	return island(pos, r, top, Island.Kind.KARST, o)


func pearl(pos: Vector3) -> Coin:
	var c := Coin.new(true)
	c.prop_override = "pearl"
	c.position = pos
	add_child(c)
	return c


func raft(pos: Vector3, rot := 0.0) -> Node3D:
	return prop("raft_platform", pos, rot, 1.0, true)


# ------------------------------------------------------------------ areas

func _bay_backdrop() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 2026
	for i in 70:
		var a := rng.randf() * TAU
		var d := rng.randf_range(95.0, 330.0)
		var isl := Island.new()
		isl.collide = false
		isl.segments = 28
		isl.kind = Island.Kind.KARST
		isl.radius = rng.randf_range(5.0, 16.0)
		isl.top = rng.randf_range(12.0, 55.0) * (0.6 + d / 400.0)
		isl.bulge = rng.randf_range(0.05, 0.3)
		isl.taper = rng.randf_range(-0.35, 0.05)
		isl.dome = isl.radius * 0.35
		isl.lip = isl.radius * 0.4
		isl.wobble = 0.18
		isl.bottom = -6.0
		isl.seed = 300 + i
		isl.position = Vector3(cos(a) * d, 0, sin(a) * d)
		add_child(isl)


func _pier() -> void:
	island(Vector3.ZERO, 8.0, 0.9, Island.Kind.SAND, {"dome": 0.25, "seed": 501})
	# a karst wall behind the pier frames the start
	karst(Vector3(-4, 0, -14), 6.0, 24.0, {"seed": 502})
	for p in [Vector3(-4.5, 1.1, 3.5), Vector3(5.5, 1.1, -1.5)]:
		tree(p, 0.9, "tree_palm")
	prop("vietnam_flag", Vector3(2.8, 1.0, -2.5), 0.3, 1.0)
	checkpoint(Vector3(3.5, 1.0, 3.8), -0.6)
	coin_ring(Vector3(0, 1.8, 0.5), 3.2, 8)
	prop("kayak", Vector3(-6.8, 0.1, -2.5), 1.2, 1.0)
	prop("buoy", Vector3(10, 0.0, 9), 0.0, 1.0)
	# the Dragon Pearl shrine: the pearl star appears here
	star("halong_pearls", _pearl_home + Vector3(0, 0.6, 0), "lantern_star")
	_travel_boat(Vector3(-10.5, 0.0, 5.0), 0.9, "skies")
	_travel_boat(Vector3(-2.0, 0.0, 12.5), PI, "danang")
	pearl(Vector3(-4, 25.4, -14)) # 1: on top of the karst behind the pier (via the dragon)


func _village() -> void:
	# floating rafts lead east from the pier to a boardwalk lined with raft houses
	raft(Vector3(12.5, 0, 1.0))
	raft(Vector3(18.0, 0, -0.5))
	coin_line(Vector3(11.5, 1.5, 1.2), Vector3(19, 1.5, -0.6), 5)
	plank_bridge(Vector3(19.6, 0.55, -1.2), Vector3(44.0, village_deck, -1.2))
	coin_line(Vector3(22, 1.6, -1.2), Vector3(42, 1.6, -1.2), 9)
	# porches (+Z) face the boardwalk: north row turned 0, south row turned PI
	for x in [25.0, 31.4, 37.8]:
		raft_house(Vector3(x, 0, -5.05), 0.0)
	for x in [28.2, 34.6]:
		raft_house(Vector3(x, 0, 2.75), PI)
	for p in [Vector3(29, 0, 11), Vector3(41, 0, 8), Vector3(22, 0, -12), Vector3(38, 0, -13)]:
		prop("fish_cage_ring", p, randf() * TAU, 1.0)
	prop("net_rack", Vector3(44.6, village_deck, 1.2), PI * 0.5, 0.9)
	prop("kayak", Vector3(38.5, 0.1, 6.5), -0.4, 1.0)
	raft(Vector3(46.0, 0, -1.2))
	spring(Vector3(45.6, 0.5, -1.2), 17.5)
	# the star floats over the ridge of the last house on the north row; a crate on its
	# porch is the step up to the roof
	block(Vector3(39.2, village_deck, -2.55), false, 1)
	block(Vector3(29.6, village_deck, 0.3), false, 1)
	star("halong_village", Vector3(37.8, 5.35, -5.83))
	pearl(Vector3(28.2, 4.95, 3.53)) # 2: on a south-row roof
	crab(Vector3(34.6, village_deck, 5.0), 1.2)
	karst(Vector3(48, 0, 12), 5.0, 18.0, {"seed": 510})
	karst(Vector3(44, 0, -18), 4.0, 14.0, {"seed": 511})


## A raft house with simple, fair collision: the deck, the house, and two walkable roof
## slopes (the railings are only decoration). Measured from the Blender prop.
func raft_house(pos: Vector3, rot: float) -> void:
	var root := Node3D.new()
	root.position = pos
	root.rotation.y = rot
	add_child(root)
	root.add_child(Props.make("raft_house"))
	var body := StaticBody3D.new()
	body.collision_layer = 1
	body.collision_mask = 0
	root.add_child(body)
	var shapes := [
		[Vector3(6.2, 0.3, 6.2), Transform3D(Basis(), Vector3(0, village_deck - 0.15, 0))],
		[Vector3(4.2, 2.3, 4.15), Transform3D(Basis(), Vector3(0, village_deck + 1.15, -0.78))],
	]
	# roof slopes: eave (±2.45, 3.07) up to the ridge (0, 4.12), running z -3.2 .. 1.65
	var slope := atan2(4.12 - 3.07, 2.45)
	var width := Vector2(2.45, 4.12 - 3.07).length()
	for side in [-1.0, 1.0]:
		var basis := Basis(Vector3.BACK, -slope * side)
		shapes.append([Vector3(width, 0.25, 4.85), Transform3D(basis, Vector3(1.225 * side, (3.07 + 4.12) * 0.5 - 0.12, -0.78))])
	for sh in shapes:
		var cs := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = sh[0]
		cs.shape = box
		cs.transform = sh[1]
		body.add_child(cs)
	coin(pos + Vector3(0, village_deck + 0.9, 2.4).rotated(Vector3.UP, rot))


func _cave() -> void:
	# stepping stones from the pier
	for p in [Vector3(-8.5, 0, -6.5), Vector3(-12.8, 0, -10.8), Vector3(-17.2, 0, -15.6)]:
		island(p, 2.1, 0.9, Island.Kind.STONE, {"dome": 0.15, "seed": int(p.x * 3)})
	coin_line(Vector3(-8.5, 1.9, -6.5), Vector3(-17.2, 1.9, -15.6), 5)
	coin_line(Vector3(-20.5, 1.6, -20.5), Vector3(-24.5, 1.6, -24.5), 4)
	var c := Vector3(-30, 0, -30)
	island(c, 13.2, 0.6, Island.Kind.CAVE, {"dome": 0.1, "lip": 0.4, "bottom": -4.0, "seed": 520})
	var dome := CaveDome.new()
	dome.radius = 13.0
	dome.height = 12.0
	dome.entrance_yaw = atan2(1.0, 1.0) ## toward the pier (south-east)
	dome.position = c
	add_child(dome)
	# limestone towers crowd round the back of the dome, so the cave reads as a mountain
	for k in 5:
		var ang := deg_to_rad(225.0 + [-80.0, -40.0, 0.0, 40.0, 80.0][k])
		var d := 18.5 + (k % 2) * 1.5
		karst(c + Vector3(cos(ang) * d, 0, sin(ang) * d), 4.4 + (k % 3) * 0.5, 17.0 + [3.0, 9.0, 12.0, 7.0, 0.0][k], {"seed": 525 + k})
	var sign := Label3D.new()
	sign.text = Game.t("Surprise Cave", "Hang Sửng Sốt")
	sign.font = UiKit.display_font()
	sign.font_size = 90
	sign.outline_size = 20
	sign.modulate = Color("#fff6d8")
	sign.outline_modulate = Color(0.05, 0.08, 0.2)
	sign.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	sign.pixel_size = 0.01
	sign.position = c + Vector3(1, 0, 1).normalized() * 15.5 + Vector3(0, 7.2, 0)
	sign.visibility_range_begin = 14.0
	sign.visibility_range_begin_margin = 3.0
	sign.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
	add_child(sign)
	# the way up inside: stalagmite pillars to a ledge at the back
	var steps := [[Vector3(-27.5, 0, -27.0), 1.35, 1.9], [Vector3(-30.8, 0, -25.2), 1.3, 3.5], [Vector3(-34.0, 0, -28.0), 1.3, 5.1], [Vector3(-33.2, 0, -32.4), 1.3, 6.7]]
	for s in steps:
		island(s[0], s[1], s[2], Island.Kind.CAVE, {"dome": 0.1, "lip": 0.25, "taper": 0.35, "bottom": 0.0, "seed": int(s[2] * 10)})
		coin((s[0] as Vector3) + Vector3(0, float(s[2]) + 0.9, 0))
	island(Vector3(-29.5, 0, -36.5), 3.0, 8.2, Island.Kind.CAVE, {"dome": 0.1, "lip": 0.4, "bottom": 0.0, "seed": 521})
	star("halong_cave", Vector3(-29.5, 8.9, -36.5))
	pearl(Vector3(-34.0, 6.1, -28.0)) # 3: on a stalagmite
	# formations and crystal light
	var rng := RandomNumberGenerator.new()
	rng.seed = 77
	for i in 16:
		var a := rng.randf() * TAU
		var d := rng.randf_range(2.0, 10.5)
		var p := c + Vector3(cos(a) * d, 0, sin(a) * d)
		var h := cos(asin(clampf(d / 13.0, 0.0, 1.0))) * 12.0 - 0.3
		prop("stalactite", Vector3(p.x, h, p.z), rng.randf() * TAU, rng.randf_range(0.7, 1.4))
	for i in 7:
		var a := rng.randf() * TAU
		var d := rng.randf_range(6.0, 11.0)
		var p := c + Vector3(cos(a) * d, 0.7, sin(a) * d)
		if Vector2(p.x - c.x, p.z - c.z).normalized().dot(Vector2(1, 1).normalized()) > 0.7:
			continue
		prop("crystal_cluster", p, rng.randf() * TAU, rng.randf_range(0.9, 1.6))
	for p in [Vector3(-25, 0.7, -33), Vector3(-36, 0.7, -24), Vector3(-34, 0.7, -35)]:
		prop("stalagmite", p, rng.randf() * TAU, rng.randf_range(0.8, 1.3))
	var shaft := Node3D.new()
	shaft.position = c + Vector3(0, 0.6, 0)
	add_child(shaft)
	Fx.beam(shaft, 13.0, 1.8, Color(1.0, 0.95, 0.8))
	coin_ring(c + Vector3(0, 1.4, 0), 3.0, 8)


func _trong_mai() -> void:
	for p in [Vector3(-8.0, 0, 9.5), Vector3(-12.5, 0, 14.0), Vector3(-17.0, 0, 18.5)]:
		island(p, 2.2, 0.8, Island.Kind.SAND, {"dome": 0.15, "seed": int(p.z * 7)})
	coin_arc(Vector3(-8, 1.8, 9.5), Vector3(-12.5, 1.8, 14), 1.2, 3)
	coin_arc(Vector3(-12.5, 1.8, 14), Vector3(-17, 1.8, 18.5), 1.2, 3)
	island(Vector3(-24.5, 0, 25.0), 6.5, 0.7, Island.Kind.STONE, {"dome": 0.2, "seed": 530})
	# the rooster and the hen: top-heavy rocks balanced on narrow feet
	karst(Vector3(-27.4, 0, 25.0), 2.0, 12.0, {"taper": -0.45, "bulge": 0.08, "lip": 0.6, "dome": 0.4, "wobble": 0.08, "bottom": 0.0, "seed": 531})
	karst(Vector3(-22.2, 0, 25.0), 1.8, 9.5, {"taper": -0.45, "bulge": 0.08, "lip": 0.55, "dome": 0.35, "wobble": 0.08, "bottom": 0.0, "seed": 532})
	star("halong_trongmai", Vector3(-27.4, 13.0, 25.0))
	pearl(Vector3(-22.2, 10.6, 25.0)) # 4: on the hen
	coin_line(Vector3(-24.8, 2.0, 25.0), Vector3(-24.8, 7.0, 25.0), 5)
	coin_ring(Vector3(-24.5, 1.6, 25.0), 4.6, 8)
	checkpoint(Vector3(-21.0, 0.9, 29.5), PI)
	crab(Vector3(-27.0, 0.9, 20.8), 1.6)


func _titop() -> void:
	var c := Vector3(28, 0, -40)
	island(c, 14.0, 0.8, Island.Kind.SAND, {"dome": 0.3, "wobble": 0.12, "seed": 540})
	# the steep green hill: too sheer to climb, the dragon is the way up
	island(c + Vector3(0, 0, -2), 5.0, 19.5, Island.Kind.KARST, {"taper": 0.6, "bulge": 0.0, "lip": 0.7, "dome": 0.2, "wobble": 0.06, "bottom": 0.0, "seed": 541})
	prop("pavilion_titop", c + Vector3(0, 19.7, -2), 0.3, 1.0, true)
	star("halong_titop", c + Vector3(1.3, 21.0, -1.2))
	for p in [Vector3(20, 1.0, -32), Vector3(36, 1.0, -34), Vector3(34, 1.0, -48)]:
		tree(p, 1.0, "tree_palm")
	coin_ring(c + Vector3(0, 1.8, 6.5), 3.0, 8)
	coin_line(c + Vector3(-11, 1.8, 2), c + Vector3(-9, 1.8, -8), 5)
	coin_line(c + Vector3(9, 1.8, 6), c + Vector3(12, 1.8, -3), 4)
	crab(c + Vector3(-6, 1.0, 7), 3.0)
	crab(c + Vector3(7, 1.0, 5), 3.0)
	checkpoint(c + Vector3(-3, 1.0, 10), 0.3)
	pearl(c + Vector3(10.5, 1.8, -6.0)) # 5: behind the hill on the beach
	# stones linking the village to Ti Tốp beach
	for p in [Vector3(30, 0, -17), Vector3(29, 0, -22.5)]:
		island(p, 2.0, 0.9, Island.Kind.STONE, {"dome": 0.1, "seed": int(p.z * 11)})


func _dragon() -> void:
	var curve := Curve3D.new()
	# low past the pier (boarding), a spiral up round Ti Tốp, over the pier karst, and down
	var pts := [
		Vector3(9.5, 0.9, 7.0), Vector3(9.5, 0.9, -3.0), Vector3(12, 2.0, -13), Vector3(17, 4.5, -22),
		Vector3(20, 7.5, -31), Vector3(18.5, 10.5, -40), Vector3(21, 13.0, -50), Vector3(30, 15.5, -53.5),
		Vector3(38, 18.0, -47), Vector3(34.3, 20.8, -39.5), Vector3(22, 19.0, -30), Vector3(6, 24.5, -22),
		Vector3(-3, 27.8, -15.5), Vector3(-8, 27.0, -7), Vector3(-15, 23.0, 1), Vector3(-18, 18.0, 12),
		Vector3(-10, 13.0, 20), Vector3(0, 8.0, 21), Vector3(8, 4.5, 17), Vector3(10.5, 1.6, 12),
	]
	for i in pts.size():
		var p: Vector3 = pts[i]
		var prev: Vector3 = pts[(i - 1 + pts.size()) % pts.size()]
		var next: Vector3 = pts[(i + 1) % pts.size()]
		var tan := (next - prev) * 0.22
		curve.add_point(p, -tan, tan)
	curve.closed = true
	curve.bake_interval = 0.25
	# a boarding jetty right beside the dragon's low pass
	for z in [5.0, 1.0, -3.0]:
		raft(Vector3(6.4, 0, z), 0.0)
	var sign := Label3D.new()
	sign.text = Game.t("🐉 Dragon stop", "🐉 Bến rồng")
	sign.font = UiKit.display_font()
	sign.font_size = 80
	sign.outline_size = 18
	sign.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	sign.pixel_size = 0.01
	sign.position = Vector3(6.4, 3.2, 1.0)
	add_child(sign)
	dragon = Dragon.new()
	dragon.path = curve
	add_child(dragon)
	# the dragon carries a star on its head and a pearl on its back
	var s := Star.new()
	s.id = "halong_dragon"
	s.position = Vector3(0, 1.6, -0.6)
	dragon.head.add_child(s)
	star_points["halong_dragon"] = Vector3(9.5, 2.0, 7.0)
	var p := Coin.new(true)
	p.prop_override = "pearl"
	p.position = Vector3(0, 1.3, 0)
	dragon.get_child(8).add_child(p) # 6: riding on the dragon's back
	# a trail of coins along the spine
	for i in range(2, dragon.segments, 2):
		if i == 8:
			continue
		var c := Coin.new()
		c.position = Vector3(0, 1.2, 0)
		dragon.get_child(i).add_child(c)


func _bay_karsts() -> void:
	# the towers that frame the play area
	var spots := [
		[Vector3(18, 0, 22), 4.5, 16.0], [Vector3(8, 0, -30), 5.0, 22.0],
		[Vector3(-44, 0, 8), 6.0, 26.0], [Vector3(50, 0, -30), 5.5, 24.0], [Vector3(-8, 0, 36), 5.0, 18.0],
		[Vector3(12, 0, 42), 6.0, 21.0], [Vector3(-48, 0, -50), 7.0, 30.0], [Vector3(55, 0, 25), 6.0, 20.0],
	]
	for i in spots.size():
		var s: Array = spots[i]
		karst(s[0], s[1], s[2], {"seed": 560 + i})
	# a tower with a spring ledge and a pearl on top
	karst(Vector3(-20, 0, 2), 4.0, 20.0, {"seed": 561})
	island(Vector3(-15.8, 0, 3.8), 1.8, 1.0, Island.Kind.STONE, {"dome": 0.1, "seed": 570})
	# a lone pearl out over the water: dash to it from the village rafts
	pearl(Vector3(15.2, 2.2, 5.5)) # 8


func _junk_ferry() -> void:
	var b := Sampan.new()
	b.prop_name = "junk_boat"
	b.deck = Vector3(2.8, 0.4, 8.0)
	b.deck_y = 1.35
	b.rock = 0.4
	b.a = Vector3(14.0, 0.0, 14.0)
	b.b = Vector3(36.0, 0.0, 16.0)
	b.trip = 9.0
	b.pause = 2.0
	add_child(b)
	coin_line(Vector3(20, 2.2, 14.6), Vector3(30, 2.2, 15.5), 5)
	var p := Coin.new(true)
	p.prop_override = "pearl"
	p.position = Vector3(0, 1.65, -2.8)
	b.add_child(p) # 7: riding the junk ferry


# ------------------------------------------------------------------ finale

## Every Hạ Long star: the dragon swoops over the pier, confetti, the ending card.
func finale(p: Player) -> void:
	Game.finished = true
	Game.finished_levels[Game.level] = true
	Game.save()
	camera.cutscene = true
	Sound.music("all_stars", 0.3)
	Sound.play("drum_boom", 1.0)
	p.model.play("dance", 0.2)
	get_tree().call_group("hud", "all_stars_banner", Game.t("HẠ LONG CLEAR!", "XONG VỊNH HẠ LONG!"))
	var conf := Fx.confetti(p.global_position + Vector3.UP * 10.0, 200, 8.0)
	camera.orbit_shot(p.global_position + Vector3.UP * 0.6, 5.5, 1.6, 0.0, TAU, 12.0)
	await get_tree().create_timer(12.5).timeout
	conf.emitting = false
	get_tree().call_group("hud", "ending_card")
