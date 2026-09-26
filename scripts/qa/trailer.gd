class_name Trailer
extends Node
## The demo-video director (docs/TRAILER.md). Run under Movie Maker:
##   godot --path . --write-movie clip.avi -- --trailer=skies|halong|finale
## It plays each shot for real (the QA bot presses the buttons), moves the camera, shows
## captions, and prints "SHOT name start_frame end_frame" so tools/record_trailer.sh can cut
## every shot to length.

var main: Node
var world: World
var player: Player
var camera: GameCamera
var hud: Hud
var bot: QaBot
var layer: CanvasLayer
var _caption: PanelContainer
var _t0 := 0


func _ready() -> void:
	main = get_parent()
	await get_tree().process_frame
	world = main.world
	player = main.player
	camera = main.camera
	hud = main.hud
	bot = QaBot.new()
	add_child(bot)
	bot.player = player
	_build_overlay()
	_t0 = Engine.get_process_frames()
	match String(Game.args["trailer"]):
		"skies": await _skies()
		"halong": await _halong()
		"finale": await _finale()
	await _hold(0.3)
	print("TRAILER DONE ", _frame())
	get_tree().quit()


# ------------------------------------------------------------------ plumbing

func _frame() -> int:
	return Engine.get_process_frames() - _t0


func _hold(seconds: float) -> void:
	await get_tree().create_timer(seconds, false).timeout


## Runs a shot: prints its frame range for the editor.
func shot(name: String, action: Callable) -> void:
	var start := _frame()
	await action.call()
	print("SHOT %s %d %d" % [name, start, _frame()])


func _build_overlay() -> void:
	layer = CanvasLayer.new()
	layer.layer = 40
	add_child(layer)
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(root)
	_caption = PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.03, 0.05, 0.1, 0.66)
	sb.set_corner_radius_all(22)
	sb.content_margin_left = 34
	sb.content_margin_right = 34
	sb.content_margin_top = 12
	sb.content_margin_bottom = 16
	_caption.add_theme_stylebox_override("panel", sb)
	var l := UiKit.label("", 44, Color.WHITE, 0, false)
	l.name = "Text"
	_caption.add_child(l)
	_caption.anchor_left = 0.5
	_caption.anchor_right = 0.5
	_caption.anchor_top = 1.0
	_caption.anchor_bottom = 1.0
	_caption.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_caption.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_caption.offset_bottom = -70
	_caption.modulate.a = 0.0
	root.add_child(_caption)


func caption(text: String, seconds := 3.0) -> void:
	(_caption.get_node("Text") as Label).text = text
	_caption.reset_size()
	_caption.offset_left = -_caption.size.x * 0.5
	_caption.offset_right = _caption.size.x * 0.5
	var tw := _caption.create_tween()
	tw.tween_property(_caption, "modulate:a", 1.0, 0.25)
	tw.tween_interval(seconds)
	tw.tween_property(_caption, "modulate:a", 0.0, 0.3)


## A big rainbow chapter title in the middle of the screen.
func chapter(title: String, sub: String, seconds := 3.0) -> void:
	var v := VBoxContainer.new()
	v.set_anchors_preset(Control.PRESET_FULL_RECT)
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_theme_constant_override("separation", -8)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.get_child(0).add_child(v)
	var tag := UiKit.label(title, 48, UiKit.GOLD, 10)
	v.add_child(tag)
	UiKit.rainbow(sub, 140, v, 0.05)
	var tw := v.create_tween()
	tw.tween_interval(seconds)
	tw.tween_property(v, "modulate:a", 0.0, 0.4)
	tw.tween_callback(v.queue_free)


func follow_cam() -> void:
	camera.cutscene = false
	camera.snap_behind()


## Moves the camera from one framing to another over `seconds`.
func dolly(eye_a: Vector3, eye_b: Vector3, look_a: Vector3, look_b: Vector3, seconds: float) -> void:
	camera.cutscene = true
	var tw := create_tween()
	tw.tween_method(func(t: float):
		camera.global_position = eye_a.lerp(eye_b, t)
		camera.look_at(look_a.lerp(look_b, t), Vector3.UP), 0.0, 1.0, seconds).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	await tw.finished


## A camera that stays at `eye` and keeps the hero in frame.
func track_from(eye: Vector3, seconds: float, look_up := 0.6) -> void:
	camera.cutscene = true
	var t := 0.0
	while t < seconds:
		camera.global_position = eye
		camera.look_at(player.global_position + Vector3.UP * look_up, Vector3.UP)
		await get_tree().process_frame
		t += get_process_delta_time()


func place(pos: Vector3, face: Vector3) -> void:
	# never teleport while a respawn is pending: its tween would move the hero back
	while player.state == Player.S.RESPAWN:
		await get_tree().physics_frame
	player.lock(false)
	player.teleport(pos, face)
	player.bot_world_dir = Vector3.ZERO


func wait_cutscene() -> void:
	await _hold(0.2)
	while Game.in_cutscene:
		await get_tree().process_frame


## Jump on landing three times: jump, higher jump, flip (the SM64 rhythm).
func triple(dir: Vector3) -> void:
	player.bot_world_dir = dir
	for i in 3:
		while not player.is_on_floor():
			await get_tree().physics_frame
		player.bot_jump = true
		player.bot_jump_hold = true
		await bot._wait(0.25)
		player.bot_jump_hold = i == 2
		await bot._wait(0.2)
		while player.velocity.y > -1.0 and not player.is_on_floor():
			await get_tree().physics_frame
	player.bot_jump_hold = false


# ------------------------------------------------------------------ part 1

func _skies() -> void:
	# 1. title
	await shot("title", func(): await _hold(3.8))
	if main.title:
		main.title.queue_free()
		main.title = null
	main.playing = true
	Game.in_cutscene = false
	Sound.music("world", 0.6)

	# 2. mascot close-up: front round to the flag cape on its back
	await shot("mascot", func():
		hud.visible = false
		await place(Vector3(0.0, 2.4, 11.2), Vector3.BACK)
		await _hold(0.4)
		player.lock(true)
		player.facing = Vector3.BACK
		player.model.play("wave", 0.1)
		caption("Mascot VGANG  ·  dựng, rig & animate bằng Blender", 4.2)
		var c := player.global_position + Vector3.UP * 0.55
		camera.orbit_shot(c, 2.6, 0.35, 0.15, PI * 1.12, 4.8)
		await _hold(1.7)
		player.model.play("dance", 0.25)
		await _hold(3.1))

	# 3. moves
	await shot("moves", func():
		hud.visible = true
		await place(Vector3(-11.0, 2.6, 1.0), Vector3.RIGHT)
		follow_cam()
		caption("Nhảy 3 bậc  ·  lộn nhào  ·  lướt  ·  dậm đất", 4.6)
		var dir := Vector3.RIGHT
		player.bot_world_dir = dir
		await bot._wait(0.45)
		player.bot_dash = true
		await bot._wait(0.35)
		await triple(dir)
		await bot._wait(0.15)
		player.bot_pound = true
		player.bot_world_dir = Vector3.ZERO
		await bot._wait(1.0))

	# 4. "?" block and the spring drum
	await shot("block_spring", func():
		await place(Vector3(-5.0, 2.6, 5.6), Vector3.FORWARD)
		follow_cam()
		caption("Khối ? tung xu  ·  trống đồng lò xo", 4.0)
		await bot._wait(0.35)
		await bot._goto(Vector3(-5.0, 0, 4.0), 0.25)
		player.bot_world_dir = Vector3.ZERO
		player.bot_jump = true
		player.bot_jump_hold = true
		await bot._wait(0.35)
		player.bot_jump_hold = false
		await bot._wait(0.9)
		await place(Vector3(-8.5, 3.6, 10.8), Vector3.BACK)
		follow_cam()
		await bot._glide(Vector3(-10.0, 0, 16.0))
		player.bot_world_dir = Vector3.ZERO
		await bot._wait(0.4))

	# 5. top of the rice terraces: STAR GET
	await shot("terraces_star", func():
		await place(Vector3(48.5, 9.4, -9.2), Vector3(0.6, 0, -0.8))
		follow_cam()
		caption("8 ngôi sao đồng Đông Sơn", 2.2)
		await bot._wait(0.4)
		await bot._leap(Vector3(51.3, 0, -12.8), 0.35, false)
		player.bot_world_dir = Vector3.ZERO
		await bot._wait(0.15)
		if not Game.in_cutscene:
			await bot._leap(Vector3(51.4, 0, -12.9), 0.35, false)
		player.bot_world_dir = Vector3.ZERO
		await wait_cutscene())

	# 6. a fly-through of the landmarks
	await shot("montage", func():
		hud.visible = false
		caption("Hạ Long Skies  ·  146 đồng xu  ·  8 sao", 5.0)
		await dolly(Vector3(-28, 6, -5), Vector3(-31, 9.5, -25), Vector3(-42, 5, -15), Vector3(-41, 6, -17), 1.9)
		await dolly(Vector3(25, 5.5, -20), Vector3(29.5, 7.5, -27), Vector3(28, 5, -38), Vector3(28, 7, -40), 1.8)
		await dolly(Vector3(-1, 5.5, -15), Vector3(-3.5, 7, -27), Vector3(-7.5, 3, -21), Vector3(-9, 4, -29), 1.8))

	# 7. board the junk for Hạ Long Bay
	await shot("boat", func():
		hud.visible = true
		await place(Vector3(5.2, 2.6, 13.2), Vector3(0.3, 0, 1))
		follow_cam()
		caption("Lên thuyền buồm  →  Vịnh Hạ Long", 2.6)
		await bot._goto(Vector3(6.5, 0, 18.3), 0.4, 2.5)
		player.bot_world_dir = Vector3.ZERO
		await _hold(2.6))


# ------------------------------------------------------------------ part 2

func _halong() -> void:
	var hw := world as HalongWorld
	var dragon := hw.dragon
	# 8. the bay from above
	await shot("bay", func():
		hud.visible = false
		await place(Vector3(0, 1.6, 4.0), Vector3.FORWARD)
		player.lock(true)
		dragon.set_head(dragon.offset_of(Vector3(17, 4.5, -22)))
		chapter("MAP 2", "VỊNH HẠ LONG", 3.2)
		await dolly(Vector3(62, 42, 70), Vector3(10, 10, 17), Vector3(0, 0, -12), Vector3(3, 2, -4), 4.6))

	# 9. the floating village
	await shot("village", func():
		hud.visible = true
		await place(Vector3(21.5, 1.4, -1.2), Vector3.RIGHT)
		follow_cam()
		caption("Làng chài nổi trên vịnh", 3.0)
		await bot._wait(0.2)
		await bot._goto(Vector3(40.5, 0, -1.2), 0.5, 3.6)
		player.bot_world_dir = Vector3.ZERO
		await bot._wait(0.8))

	# 10. Surprise Cave
	await shot("cave", func():
		await place(Vector3(-24.6, 1.4, -24.6), Vector3(-0.7, 0, -0.7))
		camera.cutscene = true
		caption("Hang Sửng Sốt", 3.2)
		var watch := func(): await track_from(Vector3(-26.0, 5.2, -20.0), 4.0, 0.8)
		watch.call()
		await bot._wait(0.3)
		await bot._hop(Vector3(-27.5, 0, -27.0), 2.4, 0.5)
		player.bot_world_dir = Vector3.ZERO
		await bot._wait(0.2)
		await bot._hop(Vector3(-30.8, 0, -25.2), 3.0, 0.55)
		player.bot_world_dir = Vector3.ZERO
		await bot._wait(0.2)
		await bot._hop(Vector3(-34.0, 0, -28.0), 3.0, 0.55)
		player.bot_world_dir = Vector3.ZERO
		await bot._wait(0.3))

	# 11. wall-kicks up the Fighting Cock rocks
	await shot("trongmai", func():
		await place(Vector3(-24.8, 1.2, 25.0), Vector3.LEFT)
		caption("Đạp tường  ·  Hòn Trống Mái", 3.4)
		var watch := func(): await track_from(Vector3(-24.8, 5.5, 35.5), 4.2, 0.5)
		watch.call()
		await bot._wait(0.25)
		await bot._wallclimb(Vector3(-1, 0, 0), 9.6, Vector3(-22.2, 0, 25.0))
		player.bot_world_dir = Vector3.ZERO
		await bot._wait(1.2))

	# 12. board the dragon
	await shot("board_dragon", func():
		await place(Vector3(7.2, 1.4, 1.0), Vector3.RIGHT)
		# a body segment reaches the jetty about a second from now
		dragon.set_head(dragon.offset_of(Vector3(9.5, 0.9, 1.0)) + dragon.part_offset(6) - 3.0)
		caption("Cưỡi rồng bay quanh vịnh!", 3.0)
		var watch := func(): await track_from(Vector3(3.0, 4.5, 8.0), 3.4, 0.4)
		watch.call()
		await bot._board_dragon()
		await bot._wait(2.0)
		follow_cam())

	# 13. ride on up to Ti Tốp's summit: STAR GET (the edit keeps the last few seconds)
	await shot("titop_star", func():
		await bot._step(["ride_near", Vector3(28, 0, -42), 7.5, 18.5])
		await bot._hop(Vector3(29.3, 0, -41.2), 20.0, 0.7)
		await bot._goto(Vector3(29.3, 0, -41.2), 0.4, 1.5)
		player.bot_world_dir = Vector3.ZERO
		await wait_cutscene())


# ------------------------------------------------------------------ part 3

func _finale() -> void:
	for s in Game.level_stars("skies"):
		Game.stars[s["id"]] = true
	Game.coins = 118
	Game.play_time = 1432.0
	world._refresh_drum()
	await shot("all_stars", func():
		player.lock(true)
		await world.all_stars_finale(player)
		await _hold(6.0))
