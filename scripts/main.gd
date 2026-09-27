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
	world = HalongWorld.new() if Game.level == "halong" else World.new()
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
	if Game.touch_mode:
		var touch := TouchControls.new(self)
		touch.name = "TouchControls"
		add_child(touch)
	if TouchQa.wanted():
		add_child(TouchQa.new(self))
	var trailer_title: bool = String(Game.args.get("trailer", "")) == "skies"
	if Game.arriving:
		# sailed in from the other level: straight into play, with the level's greeting
		Game.arriving = false
		_begin(false)
	elif Game.args.has("start") or Game.args.has("warp") or Game.args.has("tour") or Game.args.has("bot") or (Game.args.has("trailer") and not trailer_title):
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
	if Game.args.has("trailer"):
		add_child(Trailer.new())
	player.pounded.connect(func(_w): Game.haptic("heavy"))
	_announce_ready()


## Tells the phone app the game is on screen, once the first frames (and the shaders they
## need) are drawn, so its splash can open onto a finished picture.
func _announce_ready() -> void:
	for i in 3:
		await RenderingServer.frame_post_draw
	Game.rn_set_state("ready")


## The phone app was left (home button, a call): pause rather than play on unseen.
func auto_pause() -> void:
	if playing and not pause_menu.visible and not Game.in_cutscene:
		pause_menu.open()


func _show_title() -> void:
	playing = false
	hud.visible = false
	player.teleport(world.title_focus + Vector3(0, 0.1, 0), Vector3.BACK)
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
		var c := world.title_focus
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
	Sound.music(world.music, 1.0)
	if not instant:
		hud.fade(0.0, 0.6)
		hud.toast(Game.t("Find the %d bronze stars of %s!", "Tìm %d ngôi sao đồng của %s!") % [Game.level_star_total(), Game.level_name()], 4.0)
		if Game.touch_mode and not Game.touch_tips_seen:
			_touch_tips()


## First run on a phone: three short tips that name the on-screen controls.
func _touch_tips() -> void:
	var tips := [
		Game.t("Left thumb moves you · push further to run", "Ngón trái để di chuyển · đẩy xa hơn để chạy"),
		Game.t("Big green button jumps · tap again in the air to double jump", "Nút xanh lớn để nhảy · chạm lần nữa trên không để nhảy đôi"),
		Game.t("Orange dashes · yellow ground-pounds · drag the right side to look", "Nút cam để lướt · nút vàng để dậm · vuốt bên phải để xoay camera"),
	]
	for tip in tips:
		await get_tree().create_timer(4.4).timeout
		hud.toast(tip, 3.6)
	Game.touch_tips_seen = true
	Game.save()


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
	Sound.music(world.music, 1.5)


func back_to_title() -> void:
	if Game.has_host():
		Game.rn_set_state("loading:" + Game.level)
		await get_tree().create_timer(0.6, true).timeout
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
	var views := world.tour_views()
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
