extends Node
## Boots the world, the hero, the camera and the UI; runs the title → play flow, pausing, and
## the command-line QA hooks (screenshots, warps, camera tours).

var world: World
var player: Player
var camera: GameCamera
var hud: Hud
var title: TitleScreen
var pause_menu: PauseMenu
var playing := false
var _title_angle := 0.0


func _ready() -> void:
	add_to_group("main")
	world = World.new()
	world.name = "World"
	add_child(world)
	player = Player.new()
	player.name = "Player"
	add_child(player)
	camera = GameCamera.new()
	camera.name = "Camera"
	add_child(camera)
	world.player = player
	world.camera = camera
	camera.attach(player)
	hud = Hud.new()
	add_child(hud)
	pause_menu = PauseMenu.new()
	add_child(pause_menu)
	if Game.args.has("start") or Game.args.has("warp") or Game.args.has("tour") or Game.args.has("bot"):
		_begin(true)
	else:
		_show_title()
	if Game.args.has("all-stars"):
		# every star but the terraces one, so touching it plays the finale
		for s in Game.STARS.slice(1):
			Game.stars[s["id"]] = true
		world._refresh_drum()
	if Game.args.has("warp"):
		_warp(String(Game.args["warp"]))
	if Game.args.has("shot"):
		_shots(String(Game.args["shot"]))
	if Game.args.has("tour"):
		_tour(String(Game.args["tour"]))
	if Game.args.has("bot"):
		add_child(QaBot.new())


func _show_title() -> void:
	playing = false
	hud.visible = false
	player.teleport(Vector3(0, 4.7, -6.5), Vector3.BACK)
	player.lock(true)
	Game.in_cutscene = true
	camera.cutscene = true
	title = TitleScreen.new()
	add_child(title)
	title.start_game.connect(func(): _begin(false))
	Sound.music("title", 0.5)
	await get_tree().process_frame
	player.model.play("wave", 0.1)


var _fps_t := 0.0


func _process(delta: float) -> void:
	if Game.args.has("fps"):
		_fps_t += delta
		if _fps_t > 2.0:
			_fps_t = 0.0
			print("fps ", Engine.get_frames_per_second(), "  draw calls ", RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME), "  prims ", RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME))
	if not playing and title and title.visible:
		_title_angle += delta * 0.12
		var c := Vector3(0, 4.6, -6.5)
		var a := sin(_title_angle) * 0.7
		camera.global_position = c + Vector3(sin(a) * 6.2, 1.5 + sin(_title_angle * 0.7) * 0.3, cos(a) * 6.2)
		camera.look_at(c + Vector3(0, 1.45, 0))
		if not player.model.is_playing_oneshot():
			player.model.play("idle", 0.3)
			if randf() < delta * 0.25:
				player.model.play("wave", 0.2)


func _begin(instant: bool) -> void:
	if title:
		title.visible = false
		title.queue_free()
		title = null
	hud.visible = true
	if not instant:
		hud.fade(1.0, 0.35)
		await get_tree().create_timer(0.4).timeout
	player.teleport(world.spawn_point, Vector3.FORWARD)
	player.set_checkpoint(world.spawn_point)
	player.lock(false)
	Game.in_cutscene = false
	camera.cutscene = false
	camera.snap_behind()
	playing = true
	Sound.music("world", 1.0)
	if not instant:
		hud.fade(0.0, 0.6)
		hud.toast(Game.t("Find the 8 bronze stars of Hạ Long Skies!", "Tìm 8 ngôi sao đồng của Bầu Trời Hạ Long!"), 4.0)


func _unhandled_input(event: InputEvent) -> void:
	if playing and event.is_action_pressed("pause") and not pause_menu.visible and not Game.in_cutscene:
		pause_menu.open()
		get_viewport().set_input_as_handled()
	if event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func resume_after_ending() -> void:
	camera.release()
	player.lock(false)
	Game.in_cutscene = false
	Sound.music("world", 1.5)


func back_to_title() -> void:
	Game.taken.clear()
	Game.coins = 0
	Game.red_coins = 0
	Game.hp = Game.MAX_HP
	Game.in_cutscene = false
	get_tree().paused = false
	get_tree().reload_current_scene()


# ------------------------------------------------------------------ QA hooks

func _warp(id: String) -> void:
	await get_tree().process_frame
	if world.star_points.has(id):
		var p: Vector3 = world.star_points[id]
		player.teleport(p + Vector3(0, 1.0, 3.5), Vector3.FORWARD)
	elif id.contains(","):
		var v := id.split(",")
		player.teleport(Vector3(float(v[0]), float(v[1]), float(v[2])), Vector3.FORWARD)
	camera.snap_behind()


## --shot=2.5:/tmp/a.png,6:/tmp/b.png  (seconds since start)
func _shots(spec: String) -> void:
	var list := spec.split(",")
	var start := Time.get_ticks_msec()
	for item in list:
		var parts := item.split(":", true, 1)
		var at := float(parts[0])
		while (Time.get_ticks_msec() - start) / 1000.0 < at:
			await get_tree().process_frame
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(parts[1])
		print("shot ", parts[1])
	if Game.args.has("quit-after-shot"):
		get_tree().quit()


## Flies the camera through a list of framings and saves one image each.
func _tour(dir: String) -> void:
	DirAccess.make_dir_recursive_absolute(dir)
	var views := [
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
	await get_tree().create_timer(1.5).timeout
	for v in views:
		if v[0] == "behind_hero":
			camera.cutscene = false
			player.teleport(world.spawn_point, Vector3.FORWARD)
			camera.snap_behind()
			await get_tree().create_timer(1.0).timeout
		else:
			camera.cutscene = true
			camera.global_position = v[1]
			camera.look_at(v[2])
			await get_tree().create_timer(0.6).timeout
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("%s/%s.png" % [dir, v[0]])
		print("tour ", v[0])
	get_tree().quit()
