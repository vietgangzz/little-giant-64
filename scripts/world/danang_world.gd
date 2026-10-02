class_name DanangWorld
extends World
## Đà Nẵng – Hội An at golden hour. Mỹ Khê beach is home. Dragon Bridge strides north over the
## Hàn river to the Bà Nà cable car, which climbs to the Golden Bridge held up by two stone
## hands. The Marble Mountains rise to the west, Hội An's lantern-lit old town and the Japanese
## Bridge lie south-east, and basket boats spin in the Bảy Mẫu coconut forest to the east.

const BRIDGE_Y := 3.2 ## Dragon Bridge road surface
const MOUNTAIN := Vector3(-48, 0, -122) ## Bà Nà: centre of the two-tier mountain
const LOWER_TOP := 19.0 ## the wide lower terrace the stone hands stand on
const UPPER_TOP := 28.0 ## the summit plateau
const TOWN_Y := 1.0 ## Hội An's streets (and both ends of Chùa Cầu)

var gold_dragon: Array[Node3D] = [] ## head first
var fire: DragonFire
var cable_cars: Array[Sampan] = []
var basket_boats: Array[BasketBoat] = []
var golden_bridge_mid := Vector3.ZERO
## Waypoints the QA bot follows (filled in by the builders).
var cable_deck := Vector3.ZERO
var bridge_path: Array[Vector3] = []
var marble_ledges: Array[Vector3] = []
var thuy_son := Vector3(-46, 0, -15)


func _init() -> void:
	sky_top = Color(0.30, 0.44, 0.80)
	sky_horizon = Color(1.0, 0.80, 0.62)
	fog_color = Color(0.98, 0.83, 0.72)
	fog_begin = 95.0
	fog_end = 430.0
	sea_deep = Color(0.06, 0.34, 0.60)
	sea_mid = Color(0.13, 0.53, 0.74)
	sea_shallow = Color(0.50, 0.87, 0.84)
	sun_rotation = Vector3(-27, -55, 0) # low in the south-west: long golden-hour shadows
	sun_color = Color(1.0, 0.82, 0.60)
	spawn_point = Vector3(0, 2.0, 6.0)
	title_focus = Vector3(0, 1.3, 2.5)
	music = "world"
	ambient_energy = 0.78
	exposure = 1.04


func build() -> void:
	_coast_backdrop()
	_my_khe()
	_dragon_bridge()
	_ba_na()
	_marble_mountains()
	_hoi_an()
	_coconut_forest()
	_clouds()
	_travel_boat(Vector3(-4.0, 0.0, 18.5), PI, "halong")


func tour_views() -> Array:
	return [
		["home", Vector3(12, 8, 16), Vector3(0, 2, 0)],
		["dragon_bridge", Vector3(16, 12, -30), Vector3(0, 6, -42)],
		["dragon_head", Vector3(7, 10, -62), Vector3(0, 7, -68)],
		["cable_car", Vector3(-6, 14, -86), Vector3(-30, 16, -108)],
		["golden_bridge", Vector3(-62, 34, -92), Vector3(-56, 26, -110)],
		["marble", Vector3(-28, 12, 4), Vector3(-46, 9, -15)],
		["hoi_an", Vector3(30, 9, 8), Vector3(36, 3, 25)],
		["chua_cau", Vector3(48, 6, 33), Vector3(37, 3, 39)],
		["coconut", Vector3(46, 9, 18), Vector3(58, 1, 0)],
		["overview", Vector3(70, 90, 70), Vector3(-5, 0, -25)],
		["behind_hero", Vector3.ZERO, Vector3.ZERO],
	]


func ambience() -> void:
	Sound.ambient("ambient_sea", -9.0)
	Sound.ambient("ambient_birds", -19.0)


func ambient_life(l: AmbientLife) -> void:
	l.gulls(Vector3(0, 0, -30), 32.0, 20.0, 7)
	l.gulls(MOUNTAIN, 26.0, 36.0, 4)
	l.butterflies(Vector3(36, 0, 25), 10.0, TOWN_Y, 5)
	l.butterflies(MOUNTAIN + Vector3(0, 0, -4), 7.0, UPPER_TOP, 4)
	l.butterflies(Vector3(-44, 0, -10), 7.0, 1.2, 3)
	l.fish_area(Vector3(10, 0, -20), 120.0)
	# kites over Mỹ Khê beach
	l.kite(Vector3(6.5, 1.2, 3.0), 16.0, Color("#e0452b"))
	l.kite(Vector3(-7.0, 1.2, 5.0), 13.0, Color("#3d84c6"), Color("#ffffff"))
	l.kite(Vector3(2.0, 1.2, 10.0), 11.0, Color("#ffd23f"), Color("#e0452b"))
	l.horizon_sails(140.0, 6)


# ------------------------------------------------------------------ helpers

func flower_lantern(pos: Vector3, parent: Node3D = null) -> Coin:
	var c := Coin.new(true)
	c.prop_override = "hoa_dang"
	c.position = pos
	(parent if parent else self).add_child(c)
	return c


## A static collision box, optionally rotated (basis) — for hand-fitted colliders.
func box(size: Vector3, at: Vector3, basis := Basis(), parent: Node3D = null) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.collision_layer = 1
	body.collision_mask = 0
	var cs := CollisionShape3D.new()
	var b := BoxShape3D.new()
	b.size = size
	cs.shape = b
	body.add_child(cs)
	(parent if parent else self).add_child(body)
	body.transform = Transform3D(basis, at)
	return body


func karst_like(pos: Vector3, r: float, top: float, kind: Island.Kind, opts := {}) -> Island:
	var o := {"lip": minf(r * 0.3, 1.4), "bulge": 0.06, "taper": 0.25, "dome": minf(r * 0.12, 0.8), "wobble": 0.06, "bottom": -6.0}
	o.merge(opts, true)
	return island(pos, r, top, kind, o)


func _lit(node: Node3D, energy := 0.9) -> Node3D:
	Props.glow(node, energy)
	return node


# ------------------------------------------------------------------ backdrop

## The coast at dusk: the Sơn Trà peninsula, low green hills and a few far karsts.
func _coast_backdrop() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 3005
	for i in 30:
		var a := rng.randf() * TAU
		var d := rng.randf_range(170.0, 320.0)
		var isl := Island.new()
		isl.collide = false
		isl.segments = 28
		if rng.randf() < 0.35:
			isl.kind = Island.Kind.MARBLE
			isl.radius = rng.randf_range(5.0, 11.0)
			isl.top = rng.randf_range(14.0, 34.0)
			isl.taper = 0.3
			isl.dome = isl.radius * 0.2
			isl.lip = isl.radius * 0.3
		else:
			isl.kind = Island.Kind.KARST
			isl.radius = rng.randf_range(22.0, 48.0)
			isl.top = rng.randf_range(10.0, 30.0)
			isl.taper = 0.6
			isl.dome = isl.radius * 0.25
			isl.lip = isl.radius * 0.3
		isl.wobble = 0.16
		isl.bottom = -6.0
		isl.seed = 900 + i
		isl.position = Vector3(cos(a) * d, 0, sin(a) * d)
		add_child(isl)


# ------------------------------------------------------------------ Mỹ Khê (home)

func _my_khe() -> void:
	island(Vector3.ZERO, 14.0, 1.0, Island.Kind.SAND, {"dome": 0.35, "wobble": 0.06, "seed": 701})
	for p in [Vector3(-10, 1.2, 2), Vector3(-8.5, 1.2, 8.5), Vector3(9.5, 1.2, 6.0), Vector3(11, 1.2, -3), Vector3(-11.5, 1.2, -5), Vector3(4.5, 1.2, 11.5)]:
		tree(p, randf_range(0.9, 1.15), "tree_palm")
	# straw umbrellas and loungers along the sand
	var umbrellas := [Vector3(5.5, 1.25, 7.5), Vector3(-3.5, 1.25, 9.5), Vector3(8.5, 1.2, 0.5)]
	for i in umbrellas.size():
		var u: Vector3 = umbrellas[i]
		prop("beach_umbrella", u, randf() * TAU)
		Props.add_cylinder(self, 0.12, 2.6, u + Vector3(0, 1.3, 0))
		prop("beach_chair", u + Vector3(1.3, 0.0, 0.4), 0.3 + i, 1.0)
		prop("beach_chair", u + Vector3(-1.2, 0.0, 0.6), -0.2 + i, 1.0)
	prop("banh_mi_cart", Vector3(-6.0, 1.3, -1.0), 0.6, 1.0, true)
	checkpoint(Vector3(4.0, 1.2, 4.0), -0.5)
	coin_ring(Vector3(0, 1.9, 1.5), 3.6, 8)
	coin_line(Vector3(-9, 1.9, -1), Vector3(-9, 1.9, 6), 4)
	coin_arc(Vector3(7, 1.9, -6), Vector3(10.5, 1.9, -9.5), 1.2, 3)
	spring(Vector3(-2.0, 1.25, -6.5), 19.0)
	block(Vector3(-2.0, 6.0, -6.5), true, 5)
	# 1: on top of the tallest straw umbrella
	flower_lantern(umbrellas[0] + Vector3(0, 2.75, 0))
	sign_board("Mỹ Khê Beach", "Biển Mỹ Khê", Vector3(-6.5, 5.2, 11.0), 70)
	coin_line(Vector3(-6, 1.8, 12.5), Vector3(6, 1.8, 12.5), 5)
	# the hundred-coin star appears over the hero's head
	var cs := star("danang_coins", spawn_point + Vector3(0, 3.0, -2.0), "coin_star")
	cs.name = "CoinStar"


# ------------------------------------------------------------------ Dragon Bridge

func _dragon_bridge() -> void:
	# the road deck: six 10 m tiles over the Hàn river, a ramp down to each shore
	for i in 6:
		var z := -17.0 - i * 10.0
		prop("dragon_bridge_deck", Vector3(0, BRIDGE_Y, z))
		if i > 0:
			prop("dragon_bridge_pier", Vector3(0, BRIDGE_Y, z + 5.0))
	box(Vector3(9.0, 0.4, 60.0), Vector3(0, BRIDGE_Y - 0.2, -42.0))
	for side in [-1.0, 1.0]:
		box(Vector3(0.2, 1.2, 60.0), Vector3(4.45 * side, BRIDGE_Y + 0.5, -42.0))
	_ramp(Vector3(0, 1.3, -2.0), Vector3(0, BRIDGE_Y, -12.0))
	_ramp(Vector3(0, BRIDGE_Y, -72.0), Vector3(0, 1.4, -82.0))
	coin_line(Vector3(-2.2, BRIDGE_Y + 0.7, -14), Vector3(-2.2, BRIDGE_Y + 0.7, -30), 5)
	coin_line(Vector3(2.2, BRIDGE_Y + 0.7, -54), Vector3(2.2, BRIDGE_Y + 0.7, -70), 5)
	coin_line(Vector3(-2.2, BRIDGE_Y + 0.7, -36), Vector3(-2.2, BRIDGE_Y + 0.7, -50), 4)
	_gold_dragon()
	sign_board("Dragon Bridge", "Cầu Rồng", Vector3(-6.0, BRIDGE_Y + 8.5, -14.0))
	checkpoint(Vector3(3.2, BRIDGE_Y, -44.0), -PI * 0.5)


## A tilted deck tile from `low` to `high` (or high to low), with a matching collider.
func _ramp(from: Vector3, to: Vector3) -> void:
	var mid := (from + to) * 0.5
	var d := to - from
	var pitch := atan2(d.y, -d.z) # +pitch lifts the −Z end
	var t := prop("dragon_bridge_deck", mid)
	t.rotation.x = pitch
	t.scale.z = Vector2(d.z, d.y).length() / 10.0
	var b := Basis(Vector3.RIGHT, pitch)
	box(Vector3(9.0, 0.4, Vector2(d.z, d.y).length() + 0.6), mid + b * Vector3(0, -0.2, 0), b)


## Đà Nẵng's golden dragon arches three times over the road and raises its head at the north
## end; every few seconds it breathes fire, then water, over the far end of the deck.
func _gold_dragon() -> void:
	var pts := [
		Vector3(0, 4.3, -13.5), Vector3(0, 4.4, -16), Vector3(0, 6.0, -19), Vector3(0, 7.6, -22.5),
		Vector3(0, 6.0, -26), Vector3(0, 4.4, -29.5), Vector3(0, 6.4, -33), Vector3(0, 8.4, -37),
		Vector3(0, 6.4, -41), Vector3(0, 4.4, -44.5), Vector3(0, 6.1, -48), Vector3(0, 7.9, -51.5),
		Vector3(0, 6.2, -55), Vector3(0, 4.6, -58), Vector3(0, 5.6, -61), Vector3(0, 7.2, -64),
		Vector3(0, 8.2, -66.5),
	]
	var curve := Curve3D.new()
	for i in pts.size():
		var p: Vector3 = pts[i]
		var prev: Vector3 = pts[maxi(i - 1, 0)]
		var next: Vector3 = pts[mini(i + 1, pts.size() - 1)]
		var handle := (next - prev) * 0.25
		curve.add_point(p, -handle, handle)
	curve.bake_interval = 0.2
	var length := curve.get_baked_length()
	var sc := 1.5
	var spacing := 1.6 * sc
	var saddle := 0.56 * sc
	var n := int((length - 3.0 * sc) / spacing)
	var names := ["dragon_head"]
	for i in n:
		names.append("dragon_body")
	names.append("dragon_tail")
	var gold := func(c: Color) -> Color:
		# the bay dragon's jade becomes Đà Nẵng gold (belly gold, eyes and teeth stay)
		if c.g > c.r * 1.1 and c.g > c.b:
			return Color.from_hsv(0.115, clampf(c.s * 1.05, 0.45, 0.85), clampf(c.v * 1.3, 0.5, 1.0))
		return c
	for i in names.size():
		var off := 0.0
		if i > 0:
			off = spacing * 0.5 + (i - 1) * spacing if i < names.size() - 1 else spacing * 0.5 + (n - 1) * spacing + spacing * 0.5
		var s := clampf(length - off, 0.0, length)
		var p := curve.sample_baked(s, true)
		var behind := curve.sample_baked(maxf(s - 0.8, 0.0), true)
		var dir := (p - behind).normalized() if i < names.size() - 1 else (curve.sample_baked(minf(s + 0.8, length), true) - p).normalized()
		var body := StaticBody3D.new()
		body.collision_layer = 1
		body.collision_mask = 0
		add_child(body)
		body.global_transform = Transform3D(Basis.looking_at(dir, Vector3.UP), p)
		var visual := Props.make(names[i])
		visual.rotation.y = PI
		visual.scale = Vector3.ONE * sc
		Props.tint(visual, gold, 0.8)
		body.add_child(visual)
		if i == 0:
			# the head: a flat top over the brow, where the star sits
			var cs := CollisionShape3D.new()
			var b := BoxShape3D.new()
			b.size = Vector3(1.7, 0.5, 2.4)
			cs.shape = b
			cs.position = Vector3(0, saddle - 0.25, -1.0)
			body.add_child(cs)
		gold_dragon.append(body)
		if i > 1 and i < names.size() - 1 and i % 3 == 0:
			var c := Coin.new()
			c.position = Vector3(0, saddle + 0.5, 0)
			body.add_child(c)
	# one smooth ribbon along the whole back to walk on: per-segment boxes left little lips at
	# every joint on the bends, which stopped the hero halfway up a hump
	var ribbon := PackedVector3Array()
	var step := 0.5
	var s0 := 1.2
	var prev_l := Vector3.ZERO
	var prev_r := Vector3.ZERO
	var s := s0
	while s <= length + 0.01:
		var p := curve.sample_baked(s, true)
		var ahead := curve.sample_baked(minf(s + 0.4, length), true)
		var back := curve.sample_baked(maxf(s - 0.4, 0.0), true)
		var basis := Basis.looking_at((ahead - back).normalized(), Vector3.UP)
		var top := p + basis.y * saddle
		var l := top - basis.x * 0.85
		var r := top + basis.x * 0.85
		if s > s0:
			ribbon.append_array([prev_l, l, prev_r, prev_r, l, r])
		prev_l = l
		prev_r = r
		s += step
	var back_body := StaticBody3D.new()
	back_body.collision_layer = 1
	back_body.collision_mask = 0
	var shape := ConcavePolygonShape3D.new()
	shape.set_faces(ribbon)
	shape.backface_collision = true
	var rcs := CollisionShape3D.new()
	rcs.shape = shape
	back_body.add_child(rcs)
	add_child(back_body)
	# the star rides on the head; a flower lantern on the middle hump (2)
	var head := gold_dragon[0]
	var st := Star.new()
	st.id = "danang_dragon"
	st.position = Vector3(0, saddle + 0.9, -0.4 * sc)
	head.add_child(st)
	star_points["danang_dragon"] = head.global_position
	var top := gold_dragon[1]
	for part in gold_dragon:
		if part.global_position.y > top.global_position.y and absf(part.global_position.z + 37.0) < 6.0:
			top = part
	flower_lantern(Vector3(0, saddle + 0.3, 0), top)
	# fire and water from the mouth, aimed down at the end of the road
	fire = DragonFire.new()
	fire.position = Vector3(0, 0.55 * sc, -2.2 * sc)
	fire.rotation.x = -1.05
	head.add_child(fire)


# ------------------------------------------------------------------ Bà Nà

func _ba_na() -> void:
	# the station island at the north end of the bridge
	island(Vector3(0, 0, -88), 11.0, 1.4, Island.Kind.GRASS, {"dome": 0.25, "wobble": 0.05, "seed": 720})
	for p in [Vector3(6, 1.5, -92), Vector3(-4, 1.5, -82.5), Vector3(5.5, 1.5, -83)]:
		tree(p, randf_range(0.9, 1.1))
	checkpoint(Vector3(2.5, 1.5, -86.0), PI)
	coin_ring(Vector3(0, 2.3, -90), 3.0, 6)
	coin_line(Vector3(-4, 2.3, -84), Vector3(4, 2.3, -84), 3)
	# the mountain: a wide lower terrace and the summit plateau above it
	island(MOUNTAIN, 20.0, LOWER_TOP, Island.Kind.KARST, {"taper": 0.3, "bulge": 0.04, "dome": 0.2, "lip": 1.4, "wobble": 0.05, "bottom": -6.0, "seed": 730})
	island(MOUNTAIN + Vector3(0, LOWER_TOP - 1.0, 0), 13.0, UPPER_TOP - LOWER_TOP + 1.0, Island.Kind.KARST, {"taper": 0.15, "dome": 0.15, "lip": 0.9, "wobble": 0.04, "bottom": -1.0, "seed": 731})
	for p in [Vector3(-5, 0, -4), Vector3(4, 0, -7), Vector3(-7, 0, 3), Vector3(6, 0, 1)]:
		tree(MOUNTAIN + p + Vector3(0, UPPER_TOP + 0.1, 0), randf_range(0.9, 1.2))
	scatter(MOUNTAIN, 9.0, 18, UPPER_TOP + 0.15, ["flower_pink", "flower_yellow", "grass_tuft"], 731)
	coin_ring(MOUNTAIN + Vector3(0, UPPER_TOP + 0.9, -3), 3.0, 8)
	checkpoint(MOUNTAIN + Vector3(3.0, UPPER_TOP + 0.1, -6.0), 0.4)
	# a spring on the lower terrace bounces fallers back up to the summit
	spring(MOUNTAIN + Vector3(0, LOWER_TOP + 0.2, -16.0), Player.SUPER_SPRING_VELOCITY)
	sign_board("Bà Nà Hills", "Bà Nà Hills", MOUNTAIN + Vector3(9, UPPER_TOP + 5.0, 6), 80)
	_cable_car()
	_golden_bridge()
	# Bà Nà sits in the clouds
	var rng := RandomNumberGenerator.new()
	rng.seed = 731
	for i in 9:
		var a := rng.randf() * TAU
		var d := rng.randf_range(22.0, 34.0)
		var c := prop("cloud", MOUNTAIN + Vector3(cos(a) * d, rng.randf_range(14.0, 26.0), sin(a) * d), rng.randf() * TAU, rng.randf_range(2.2, 3.6))
		_no_shadow(c)


func _cable_car() -> void:
	# two cabins on parallel lines 4 m apart; one goes up while the other comes down
	var dir := (Vector3(MOUNTAIN.x, 0, MOUNTAIN.z) - Vector3(0, 0, -88)).normalized()
	var perp := Vector3(dir.z, 0, -dir.x)
	var low := Vector3(0, 0.3, -88) + dir * 13.4
	var high := Vector3(MOUNTAIN.x, UPPER_TOP - 2.2, MOUNTAIN.z) - dir * 14.6
	var trip := 12.0
	var pause := 3.0
	for k in 2:
		var side := 2.0 if k == 0 else -2.0
		var car := Sampan.new()
		car.prop_name = "cable_car"
		car.deck = Vector3(2.3, 0.3, 2.3)
		car.deck_y = 2.35
		car.rock = 0.35
		car.a = low + perp * side
		car.b = high + perp * side
		car.trip = trip
		car.pause = pause
		car.phase = 0.0 if k == 0 else trip + pause
		add_child(car)
		cable_cars.append(car)
		# the cable itself
		var a := car.a + Vector3(0, 4.4, 0) - dir * 3.0
		var b := car.b + Vector3(0, 4.4, 0) + dir * 2.0
		var line := MeshInstance3D.new()
		var cyl := CylinderMesh.new()
		cyl.top_radius = 0.035
		cyl.bottom_radius = 0.035
		cyl.height = a.distance_to(b)
		cyl.radial_segments = 5
		cyl.rings = 1
		line.mesh = cyl
		line.material_override = Fx.toon_material(Color("#3b3f46"))
		line.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(line)
		line.global_position = (a + b) * 0.5
		line.look_at(b, Vector3.UP)
		line.rotate_object_local(Vector3.RIGHT, PI / 2)
	# 3: riding the first cabin's roof
	flower_lantern(Vector3(0.5, 2.55, 0.6), cable_cars[0])
	var c := Coin.new()
	c.position = Vector3(-0.5, 2.9, 0.6)
	cable_cars[1].add_child(c)
	# station decks at both ends, so you step straight off the cabin roof onto boards
	var deck_at := low - dir * 2.65
	cable_deck = Vector3(deck_at.x, 2.45, deck_at.z)
	_station_deck(Vector3(deck_at.x, 2.425, deck_at.z), atan2(dir.x, dir.z), 2.7, 1.4)
	var top_at := high + dir * 2.4
	_station_deck(Vector3(top_at.x, UPPER_TOP + 0.02, top_at.z), atan2(dir.x, dir.z), 2.0, LOWER_TOP)
	sign_board("Cable car", "Cáp treo", Vector3(deck_at.x, 6.5, deck_at.z), 70)
	var tower_at := low.lerp(high, 0.86)
	var tw := prop("cable_tower", Vector3(tower_at.x, LOWER_TOP, tower_at.z), atan2(dir.x, dir.z) + PI / 2)
	tw.scale.y = (tower_at.y + 4.4 - LOWER_TOP) / 14.2
	coin_line(low + Vector3(0, 3.2, 0) + perp * 2.0 - dir * 3.0, low + Vector3(0, 3.2, 0) - perp * 2.0 - dir * 3.0, 3)


## A plank deck on posts, `top` its walking surface, `depth` along the cable.
func _station_deck(top: Vector3, yaw: float, depth: float, ground_y: float) -> void:
	var plat := Node3D.new()
	add_child(plat)
	plat.global_position = Vector3(top.x, 0, top.z)
	plat.rotation.y = yaw
	var boards := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(7.0, 0.35, depth)
	boards.mesh = bm
	boards.material_override = Fx.toon_material(Color("#a0612f"))
	boards.position.y = top.y - 0.175
	plat.add_child(boards)
	box(Vector3(7.0, 0.35, depth), Vector3(0, top.y - 0.175, 0), Basis(), plat)
	var h := top.y - 0.35 - ground_y
	for x in [-3.2, 3.2]:
		for z in [-depth * 0.4, depth * 0.4]:
			var post := MeshInstance3D.new()
			var pc := CylinderMesh.new()
			pc.top_radius = 0.12
			pc.bottom_radius = 0.12
			pc.height = h
			post.mesh = pc
			post.material_override = Fx.toon_material(Color("#62381d"))
			post.position = Vector3(x, ground_y + h * 0.5, z)
			plat.add_child(post)


## Cầu Vàng: a golden walkway looping out from the summit, held up by two giant stone hands.
func _golden_bridge() -> void:
	var out := Vector3(-0.6, 0, 0.8) # the loop bulges south-south-west
	var across := Vector3(0.8, 0, 0.6)
	var r := 9.0
	var centre := MOUNTAIN + out * 9.0
	var deck_y := UPPER_TOP - 0.28 # segment origin; its deck top (0.30 above) meets the plateau flush
	var steps := 15
	for i in steps:
		var phi := PI * (1.0 - (i + 0.5) / steps)
		var p := centre + (across * cos(phi) + out * sin(phi)) * r
		var tangent := (across * sin(phi) - out * cos(phi)).normalized()
		bridge_path.append(Vector3(p.x, deck_y + 0.3, p.z))
		var seg := prop("golden_bridge_seg", Vector3(p.x, deck_y, p.z))
		seg.rotation.y = atan2(tangent.x, tangent.z)
		seg.scale.z = 1.0 * (PI * r / steps) / 2.0 + 0.04
		var bs := Basis(Vector3.UP, seg.rotation.y)
		box(Vector3(2.4, 0.3, PI * r / steps + 0.3), Vector3(p.x, deck_y + 0.15, p.z), bs)
		for side in [-1.0, 1.0]:
			if i == 0 or i == steps - 1:
				continue # the ends stay open so you can walk on from the plateau at any angle
			box(Vector3(0.16, 1.3, PI * r / steps + 0.3), Vector3(p.x, deck_y + 0.95, p.z) + bs * Vector3(1.15 * side, 0, 0), bs)
		if i % 2 == 1 and i != 7:
			coin(Vector3(p.x, deck_y + 1.1, p.z))
	# the hands: fingers along the walkway, the cradle 0.2 under the girders
	for phi in [deg_to_rad(52.0), deg_to_rad(128.0)]:
		var p: Vector3 = centre + (across * cos(phi) + out * sin(phi)) * r
		var tangent := (across * sin(phi) - out * cos(phi)).normalized()
		var hand := prop("golden_hand", Vector3(p.x, LOWER_TOP - 0.05, p.z), atan2(-tangent.z, tangent.x), (deck_y - 0.2 - LOWER_TOP + 0.05) / 8.6)
		hand.name = "GoldenHand"
	var mid := centre + out * r
	golden_bridge_mid = Vector3(mid.x, deck_y + 0.3, mid.z)
	star("danang_goldenbridge", golden_bridge_mid + Vector3(0, 0.7, 0))
	sign_board("Golden Bridge", "Cầu Vàng", golden_bridge_mid + out * 3.0 + Vector3(0, 6.0, 0), 80)


# ------------------------------------------------------------------ Ngũ Hành Sơn

func _marble_mountains() -> void:
	# sandbars from Mỹ Khê
	for p in [Vector3(-17.5, 0, -4.0), Vector3(-21.6, 0, -5.6), Vector3(-25.6, 0, -7.4)]:
		island(p, 2.2, 0.9, Island.Kind.SAND, {"dome": 0.15, "wobble": 0.05, "seed": int(p.x * 5)})
	coin_arc(Vector3(-15, 1.9, -3.2), Vector3(-21.6, 1.9, -5.6), 1.4, 4)
	island(Vector3(-44, 0, -12), 13.0, 1.2, Island.Kind.SAND, {"dome": 0.3, "wobble": 0.05, "stretch": Vector2(1.25, 1.0), "seed": 740})
	var thuy := thuy_son
	karst_like(thuy, 4.6, 15.5, Island.Kind.MARBLE, {"taper": 0.3, "lip": 0.9, "dome": 0.5, "seed": 741})
	var peaks := [[Vector3(-33.5, 0, -7.0), 2.4, 7.2], [Vector3(-56.0, 0, -5.5), 2.8, 9.0], [Vector3(-37.5, 0, -21.5), 3.0, 10.5], [Vector3(-55.5, 0, -20.0), 2.6, 7.5]]
	for i in peaks.size():
		var pk: Array = peaks[i]
		karst_like(pk[0], pk[1], pk[2], Island.Kind.MARBLE, {"seed": 742 + i})
	# marble ledges spiral up Thủy Sơn, one easy hop apart
	for k in 7:
		var a := deg_to_rad(20.0 + k * 34.0)
		var h := 2.9 + k * 1.85
		var p := thuy + Vector3(cos(a) * 6.4, 0, sin(a) * 6.4)
		marble_ledges.append(p + Vector3(0, h, 0))
		island(p + Vector3(0, h - 0.8, 0), 1.5, 0.8, Island.Kind.MARBLE, {"floating": true, "bottom": -2.0, "dome": 0.1, "lip": 0.35, "wobble": 0.05, "seed": 750 + k})
		if k % 2 == 0:
			coin(p + Vector3(0, h + 0.9, 0))
	prop("stupa_tower", thuy + Vector3(0, 15.5 + 0.45, 0), 0.3, 1.0, true)
	star("danang_marble", thuy + Vector3(0, 16.9, 2.6))
	coin_ring(thuy + Vector3(0, 16.7, 0), 2.6, 6)
	# 4: on top of Kim Sơn, with a spring at its foot
	spring(Vector3(-31.0, 1.25, -9.5), 21.0)
	flower_lantern(Vector3(-33.5, 7.9, -7.0))
	checkpoint(Vector3(-34.5, 1.3, -13.0), PI * 0.5)
	coin_ring(Vector3(-44, 2.0, -6.0), 3.0, 8)
	for p in [Vector3(-50, 1.5, -3), Vector3(-40, 1.5, -2.5), Vector3(-52, 1.5, -13)]:
		tree(p, randf_range(0.8, 1.0))
	sign_board("Marble Mountains", "Ngũ Hành Sơn", thuy + Vector3(5, 20.5, 4), 80)


# ------------------------------------------------------------------ Hội An

func _hoi_an() -> void:
	# stepping islets from the beach
	for p in [Vector3(15.0, 0, 11.2), Vector3(18.5, 0, 15.2)]:
		island(p, 2.0, 0.9, Island.Kind.SAND, {"dome": 0.15, "wobble": 0.05, "seed": int(p.z * 9)})
	coin_arc(Vector3(12, 1.8, 8.5), Vector3(18.5, 1.8, 15.2), 1.4, 4)
	island(Vector3(36, 0, 25), 14.0, TOWN_Y, Island.Kind.PAVED, {"dome": 0.12, "lip": 0.5, "wobble": 0.03, "stretch": Vector2(1.6, 0.8), "seed": 760})
	island(Vector3(37, 0, 47), 7.5, TOWN_Y, Island.Kind.PAVED, {"dome": 0.1, "lip": 0.5, "wobble": 0.03, "stretch": Vector2(1.7, 0.75), "seed": 761})
	# the old street: shophouses facing each other, lanterns strung between them
	var north := [[24.0, false], [30.0, true], [36.0, true], [42.0, false], [48.0, true]]
	for h in north:
		hoian_house(Vector3(h[0], TOWN_Y, 19.0), 0.0, h[1])
	var south := [[25.0, true], [31.0, false], [44.0, false], [49.5, false]]
	for h in south:
		hoian_house(Vector3(h[0], TOWN_Y, 31.0), PI, h[1])
	for x in [27.0, 33.0, 39.0, 45.0]:
		var s := prop("silk_lantern_string", Vector3(x, TOWN_Y + 4.3, 25.0), PI / 2)
		_no_shadow(s)
	prop("banh_mi_cart", Vector3(40.0, TOWN_Y, 25.5), -0.4, 1.0, true)
	for p in [Vector3(21, TOWN_Y, 25), Vector3(53, TOWN_Y, 24)]:
		tree(p, 1.0)
	coin_line(Vector3(23, 1.8, 25.5), Vector3(51, 1.8, 25.5), 9)
	coin_line(Vector3(29.4, TOWN_Y + 4.3, 31), Vector3(32.6, TOWN_Y + 4.3, 31), 3) # along a ridge
	coin_ring(Vector3(34, TOWN_Y + 0.8, 47.5), 2.4, 6)
	checkpoint(Vector3(21.0, TOWN_Y, 27.5), -PI * 0.5)
	# crates to climb the roofs
	block(Vector3(31.0, TOWN_Y + 0.08, 27.4), true, 1)
	block(Vector3(36.0, TOWN_Y + 0.08, 23.9), true, 1)
	# 5: on a north-row ridge
	flower_lantern(Vector3(36.0, TOWN_Y + 5.75, 19.0))
	_chua_cau(Vector3(37.0, 0, 38.8))
	# the flower-lantern star waits on An Hội's riverside
	star("hoian_lanterns", Vector3(30.0, TOWN_Y + 1.0, 46.5), "lantern_star")
	hoian_house(Vector3(44.0, TOWN_Y, 48.0), PI, false)
	spring(Vector3(40.5, TOWN_Y + 0.25, 46.0), 19.0)
	# 8: on the An Hội house's ridge
	flower_lantern(Vector3(44.0, TOWN_Y + 3.95, 48.0))
	# lantern boats on the Thu Bồn
	var b1 := Sampan.new()
	b1.prop_name = "lantern_boat"
	b1.deck = Vector3(1.3, 0.3, 3.4)
	b1.deck_y = 0.4
	b1.a = Vector3(45.5, 0, 38.9)
	b1.b = Vector3(64.0, 0, 38.9)
	b1.trip = 8.0
	b1.pause = 2.0
	add_child(b1)
	flower_lantern(Vector3(0, 0.6, 0.9), b1) # 6: on a lantern boat
	var b2 := Sampan.new()
	b2.prop_name = "lantern_boat"
	b2.deck = Vector3(1.3, 0.3, 3.4)
	b2.deck_y = 0.4
	b2.a = Vector3(18.0, 0, 57.0)
	b2.b = Vector3(54.0, 0, 57.0)
	b2.trip = 12.0
	b2.phase = 5.0
	add_child(b2)
	for k in 3:
		var c := Coin.new()
		c.position = Vector3(0, 1.0, -1.2 + k * 1.2)
		b2.add_child(c)
	# floating flower lanterns drifting on the river (scenery)
	var rng := RandomNumberGenerator.new()
	rng.seed = 762
	for i in 12:
		var f := prop("hoa_dang", Vector3(rng.randf_range(24, 60), 0.05, rng.randf_range(37.5, 40.5) if i % 2 else rng.randf_range(54, 60)), rng.randf() * TAU, 1.1)
		_no_shadow(f)
	sign_board("Hội An Ancient Town", "Phố cổ Hội An", Vector3(36, TOWN_Y + 8.5, 13.0), 80)


## A Hội An shophouse with fitted colliders: the walls, the awning (big house) and the two roof
## slopes, ridge along X. Front (+Z local) faces the street.
func hoian_house(pos: Vector3, rot: float, big: bool) -> void:
	var root := Node3D.new()
	root.position = pos
	root.rotation.y = rot
	add_child(root)
	var visual := Props.make("hoian_house" if big else "hoian_house_small")
	root.add_child(visual)
	var half := Vector2(2.5, 3.0) if big else Vector2(2.0, 2.5)
	var eave := 4.2 if big else 2.6
	var ridge := 5.6 if big else 3.8
	var eave_z := 3.4 if big else 2.85
	var roof_x := 2.75 if big else 2.25
	box(Vector3(half.x * 2.0, eave, half.y * 2.0), Vector3(0, eave * 0.5, 0), Basis(), root)
	var slope := atan2(ridge - eave, eave_z)
	var width := Vector2(eave_z, ridge - eave).length()
	for side in [-1.0, 1.0]:
		var b := Basis(Vector3.RIGHT, slope * side)
		box(Vector3(roof_x * 2.0, 0.25, width), Vector3(0, (eave + ridge) * 0.5 - 0.12, eave_z * 0.5 * side), b, root)
	if big:
		var aw := atan2(3.0 - 2.55, 0.95)
		box(Vector3(5.3, 0.2, 1.1), Vector3(0, 2.72, 3.47), Basis(Vector3.RIGHT, aw), root)
	# a silk lantern by the door
	var l := Props.make("lantern")
	l.position = Vector3(half.x - 0.6, (2.5 if big else 2.1) - 0.6, half.y + 0.35)
	root.add_child(l)
	_lit(l, 1.1)


## Chùa Cầu, the Japanese Covered Bridge, over the channel to An Hội: a gently arched deck,
## a tiled roof whose ridge runs along the bridge, and the little temple on its east side.
func _chua_cau(at: Vector3) -> void:
	var root := Node3D.new()
	root.position = at
	add_child(root)
	root.add_child(Props.make("chua_cau"))
	# deck: flat ends at street level, then the arch y = 1.6 − 0.6·(z/4.5)²
	var zs := [-6.3, -4.5, -2.25, 0.0, 2.25, 4.5, 6.3]
	var ys := [1.0, 1.0, 1.45, 1.6, 1.45, 1.0, 1.0]
	for i in zs.size() - 1:
		var p0 := Vector3(0, ys[i], zs[i])
		var p1 := Vector3(0, ys[i + 1], zs[i + 1])
		var d := p1 - p0
		var b := Basis(Vector3.RIGHT, -atan2(d.y, d.z))
		box(Vector3(2.9, 0.3, d.length() + 0.05), (p0 + p1) * 0.5 + b * Vector3(0, -0.15, 0), b, root)
	# balustrades keep you on the deck over the water
	for side in [-1.0, 1.0]:
		box(Vector3(0.15, 1.0, 9.0), Vector3(1.55 * side, 2.0, 0), Basis(), root)
	# the main roof: eaves 3.8 at x ±2.35, ridge 5.6, z ±6.35
	var slope := atan2(5.6 - 3.8, 2.35)
	var width := Vector2(2.35, 5.6 - 3.8).length()
	for side in [-1.0, 1.0]:
		box(Vector3(width, 0.25, 12.7), Vector3(1.175 * side, (3.8 + 5.6) * 0.5 - 0.12, 0), Basis(Vector3.BACK, -slope * side), root)
	# the temple room and its small roof (ridge along X at 4.25, eaves 3.10 at z ±1.75)
	box(Vector3(2.05, 3.25, 2.8), Vector3(2.72, 1.62, 0), Basis(), root)
	var ts := atan2(4.25 - 3.1, 1.75)
	var tw := Vector2(1.75, 4.25 - 3.1).length()
	for side in [-1.0, 1.0]:
		box(Vector3(2.2, 0.2, tw), Vector3(2.72, (3.1 + 4.25) * 0.5 - 0.1, 0.875 * side), Basis(Vector3.RIGHT, ts * side), root)
	star("hoian_bridge", at + Vector3(0, 6.35, 0))
	coin_line(at + Vector3(0, 2.1, -4.0), at + Vector3(0, 2.4, 4.0), 5)
	# lanterns along the bridge glow at dusk
	for z in [-5.6, 5.6]:
		for x in [-1.9, 1.9]:
			var l := prop("lantern", at + Vector3(x, 3.0, z), 0.0, 0.9)
			_lit(l, 1.2)


# ------------------------------------------------------------------ the Bảy Mẫu coconut forest

func _coconut_forest() -> void:
	var spots := [Vector3(54.5, 0, 13.5), Vector3(57.5, 0, 9.8), Vector3(55.0, 0, 6.0), Vector3(58.2, 0, 2.3), Vector3(55.6, 0, -1.6), Vector3(58.6, 0, -5.4)]
	for i in spots.size():
		var b := BasketBoat.new()
		b.position = spots[i]
		b.spin = [1.0, -1.3, 1.5, -1.1, 1.6, -1.4][i]
		b.phase = i * 0.9
		add_child(b)
		basket_boats.append(b)
		if i == 3:
			flower_lantern(Vector3(0, 0.45, 0), b) # 7: in a spinning basket
		else:
			var c := Coin.new()
			c.position = Vector3(0, 0.8, 0)
			b.add_child(c)
	island(Vector3(60.5, 0, -11.5), 4.5, 1.0, Island.Kind.SAND, {"dome": 0.2, "wobble": 0.05, "seed": 770})
	star("hoian_basket", Vector3(60.5, 2.0, -12.0))
	coin_ring(Vector3(60.5, 1.9, -11.5), 2.6, 6)
	for p in [Vector3(58.0, 1.1, -14.0), Vector3(63.0, 1.1, -10.0)]:
		tree(p, 0.95, "tree_palm")
	# the water coconut forest itself, leaving the boats' lane clear
	var rng := RandomNumberGenerator.new()
	rng.seed = 771
	var placed := 0
	var tries := 0
	while placed < (10 if Game.is_phone() else 20) and tries < 400:
		tries += 1
		var p := Vector3(rng.randf_range(46.0, 74.0), 0.0, rng.randf_range(-24.0, 16.0))
		var clear := true
		for s in spots:
			clear = clear and Vector2(p.x - s.x, p.z - s.z).length() > 3.6
		clear = clear and Vector2(p.x - 60.5, p.z + 11.5).length() > 6.0 and p.z < 12.0
		# keep off Hội An's island (an ellipse 22.4 x 11.2) with a few metres to spare
		clear = clear and Vector2((p.x - 36.0) / 22.4, (p.z - 25.0) / 11.2).length() > 1.2
		if clear:
			prop("nipa_palm", p, rng.randf() * TAU, rng.randf_range(0.8, 1.2))
			placed += 1
	sign_board("Bảy Mẫu Coconut Forest", "Rừng dừa Bảy Mẫu", Vector3(62, 7.5, 6), 70)


# ------------------------------------------------------------------ finale

## Every star of the coast: fireworks over the Hàn river (the Đà Nẵng fireworks festival),
## the dragon roars, confetti, the ending card.
func finale(p: Player) -> void:
	Game.finished = true
	Game.finished_levels[Game.level] = true
	Game.save()
	camera.cutscene = true
	Sound.music("all_stars", 0.3)
	Sound.play("drum_boom", 1.0)
	p.model.play("dance", 0.2)
	get_tree().call_group("hud", "all_stars_banner", Game.t("ĐÀ NẴNG CLEAR!", "XONG ĐÀ NẴNG!"))
	var conf := Fx.confetti(p.global_position + Vector3.UP * 10.0, 200, 8.0)
	camera.orbit_shot(p.global_position + Vector3.UP * 0.6, 5.5, 1.6, 0.0, TAU, 12.0)
	var colors := [Color("#ff5c8a"), Color("#ffd23f"), Color("#4fc3f7"), Color("#d5f64b"), Color("#ff7447"), Color("#ffffff")]
	for i in 16:
		await get_tree().create_timer(0.7).timeout
		# bursts low over the water all round, so the orbiting camera always catches some
		var a := randf() * TAU
		var at := p.global_position + Vector3(cos(a) * randf_range(9, 15), randf_range(5, 11), sin(a) * randf_range(9, 15))
		var c: Color = colors[i % colors.size()]
		Fx.sparkle(at, c, 56, 13.0, 1.5, 1.7)
		Fx.sparkle(at, Color.WHITE, 20, 6.0, 0.9, 1.0)
		Fx.ring(at, Color(c.r, c.g, c.b, 0.9), 9.0, 0.7, Vector3.BACK)
		Sound.play("drum_boom", -10.0, randf_range(1.3, 1.7))
	await get_tree().create_timer(1.5).timeout
	conf.emitting = false
	get_tree().call_group("hud", "ending_card")
