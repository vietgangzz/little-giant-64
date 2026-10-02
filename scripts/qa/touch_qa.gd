class_name TouchQa
extends Node
## Plays the phone controls with synthetic touches and checks that each one does its job:
## the title's Start tap, the stick, JUMP, DASH, POUND, a camera drag and the pause button.
##
## Touches go in through Input.parse_input_event at window coordinates, so they take the same
## path as a finger: stretch transform, TouchControls, input actions, the player. Turn it on
## with --touch-qa, or on a phone by dropping an empty file named touch_qa.txt into the app's
## Documents folder (user://). Results go to user://touch_qa.log, one PASS/FAIL line each.

var main: Node
var _log: FileAccess
var _fails := 0


static func wanted() -> bool:
	return Game.args.has("touch-qa") or FileAccess.file_exists("user://touch_qa.txt")


func _init(owner_main: Node) -> void:
	main = owner_main


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS # keeps going through the pause menu
	var fresh := not FileAccess.file_exists("user://touch_qa.log") or Game.level == "skies"
	_log = FileAccess.open("user://touch_qa.log", FileAccess.WRITE if fresh else FileAccess.READ_WRITE)
	if not fresh:
		_log.seek_end()
	_run()


func _wants_travel() -> bool:
	if Game.args.has("touch-qa-travel"):
		return true
	var f := FileAccess.open("user://touch_qa.txt", FileAccess.READ)
	return f != null and f.get_as_text().contains("travel")


func _say(line: String) -> void:
	print("[touch-qa] ", line)
	if _log:
		_log.store_line(line)
		_log.flush()


func _check(name: String, ok: bool, detail := "") -> void:
	if not ok:
		_fails += 1
	_say("%s %s %s" % ["PASS" if ok else "FAIL", name, detail])


func _wait(seconds: float) -> void:
	await get_tree().create_timer(seconds, true).timeout


## Canvas (1920×1080 design space) to window pixels, where real touches arrive.
func _to_window(p: Vector2) -> Vector2:
	return get_tree().root.get_final_transform() * p


func _touch(index: int, at: Vector2, pressed: bool) -> void:
	var ev := InputEventScreenTouch.new()
	ev.index = index
	ev.position = _to_window(at)
	ev.pressed = pressed
	Input.parse_input_event(ev)


func _drag(index: int, from: Vector2, to: Vector2, seconds: float, hold_after := 0.0) -> void:
	_touch(index, from, true)
	var steps := maxi(2, int(seconds * 60.0))
	var last := from
	for i in range(1, steps + 1):
		await get_tree().process_frame
		var p := from.lerp(to, float(i) / steps)
		var ev := InputEventScreenDrag.new()
		ev.index = index
		ev.position = _to_window(p)
		ev.relative = _to_window(p) - _to_window(last)
		Input.parse_input_event(ev)
		last = p
	if hold_after > 0.0:
		await _wait(hold_after)
	_touch(index, to, false)


func _tap(at: Vector2, hold := 0.08) -> void:
	_touch(5, at, true)
	await _wait(hold)
	_touch(5, at, false)


func _button(action: String) -> Vector2:
	var tc: TouchControls = main.get_node("TouchControls")
	return tc._pos(tc._button(action))


func _run() -> void:
	_say("start %s  window=%s  canvas=%s" % [Game.level, get_tree().root.size, get_viewport().get_visible_rect().size])
	await _wait(2.5)
	var p: Player = main.player

	# the title: tap Start
	if main.title:
		var start: Label = main.title._items[0]
		await _tap(start.get_global_rect().get_center())
		await _wait(1.6)
	_check("title_start", main.playing)
	await _wait(1.0)

	var hp0 := Game.hp
	# the stick, pushed up: runs away from the camera
	var tc: TouchControls = main.get_node("TouchControls")
	var rest := tc._stick_rest()
	var before := p.global_position
	await _drag(1, rest, rest + Vector2(0, -150), 0.2, 0.6)
	var moved := Vector2(p.global_position.x - before.x, p.global_position.z - before.z).length()
	_check("stick_run", moved > 3.0, "moved %.1f m" % moved)
	await _wait(0.6)

	# JUMP
	var y0 := p.global_position.y
	var peak := y0
	_touch(2, _button("jump"), true)
	for i in 30:
		await get_tree().physics_frame
		peak = maxf(peak, p.global_position.y)
	_touch(2, _button("jump"), false)
	_check("jump", peak - y0 > 1.0, "rose %.2f m" % (peak - y0))
	await _wait(1.2)

	# turn back toward the start (pull the stick down), so the dash stays on dry land
	await _drag(1, rest, rest + Vector2(0, 150), 0.15, 0.3)
	await _wait(0.5)

	# DASH (from the ground)
	var seen_dash := false
	_touch(3, _button("dash"), true)
	for i in 12:
		await get_tree().physics_frame
		seen_dash = seen_dash or p.state == Player.S.DASH
	_touch(3, _button("dash"), false)
	_check("dash", seen_dash)
	await _wait(1.2)

	# POUND: jump, then pound in the air
	var seen_pound := false
	await _tap(_button("jump"), 0.05)
	await _wait(0.3)
	_touch(3, _button("pound"), true)
	for i in 40:
		await get_tree().physics_frame
		seen_pound = seen_pound or p.state in [Player.S.POUND_WINDUP, Player.S.POUND_FALL, Player.S.POUND_LAND]
	_touch(3, _button("pound"), false)
	_check("pound", seen_pound)
	await _wait(1.2)

	# a camera drag on the right half swings the view
	var yaw0: float = main.camera.yaw
	var v := get_viewport().get_visible_rect().size
	await _drag(4, Vector2(v.x * 0.62, v.y * 0.35), Vector2(v.x * 0.62 - 320.0, v.y * 0.35), 0.35)
	var turned := absf(wrapf(main.camera.yaw - yaw0, -PI, PI))
	_check("camera_drag", turned > 0.5, "turned %.0f°" % rad_to_deg(turned))
	await _wait(0.8)

	# pause, then Resume from the menu
	await _tap(_button("pause"))
	await _wait(0.5)
	_check("pause_opens", main.pause_menu.visible)
	var resume: Label = main.pause_menu._items[0][0]
	await _tap(resume.get_global_rect().get_center())
	await _wait(0.5)
	_check("pause_resume", not main.pause_menu.visible and not get_tree().paused)
	_check("kept_health", Game.hp == hp0 and Game.hp == Game.MAX_HP, "hp %d/%d" % [Game.hp, Game.MAX_HP])
	_say("perf  fps %d  draw calls %d  prims %d" % [Engine.get_frames_per_second(), RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME), RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)])

	# optional: sail on to the next map from the pause menu (touch_qa.txt containing "travel").
	# Each level runs these checks again; the last one stops.
	var at := Game.LEVEL_ORDER.find(Game.level)
	if _wants_travel() and at >= 0 and at < Game.LEVEL_ORDER.size() - 1:
		var next: String = Game.LEVEL_ORDER[at + 1]
		await _tap(_button("pause"))
		await _wait(0.5)
		for item in main.pause_menu._items:
			var l: Label = item[0]
			if l.text == Game.t("Sail to ", "Đi ") + Game.level_name(next):
				_say("travel  tapping '%s'" % l.text)
				_say("done  %d failed" % _fails)
				await _tap(l.get_global_rect().get_center())
				return
		_check("travel_item", false)

	_say("done  %d failed" % _fails)
	if Game.args.has("touch-qa") and Game.args.has("quit"):
		get_tree().quit(1 if _fails > 0 else 0)
