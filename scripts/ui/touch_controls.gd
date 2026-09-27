class_name TouchControls
extends CanvasLayer
## Phone controls laid out the way 3D mobile platformers do it:
##
##  left thumb   a floating analog stick. Touch anywhere on the left side and the stick appears
##               under the thumb; how far it is pushed sets the run speed, as a pad stick does.
##  right thumb  a big lime JUMP button lifted off the corner, with DASH and POUND on an arc
##               around it and the two camera buttons (recenter, zoom) above.
##  right side   dragging anywhere else on the right half swings the camera.
##  top          pause.
##
## Every button presses the same input actions the keyboard does, so the game reads touch
## exactly like keys. Layout is measured from the live view's corners, so it holds on any
## screen shape. Sizes are in the 1920×1080 design canvas.

const STICK_R := 150.0
const KNOB_R := 62.0
const STICK_ZONE := 0.45 ## the left share of the screen that grabs the stick
const DEADZONE := 0.12
const INSET := 96.0 ## clear of rounded corners and the Dynamic Island in landscape
const MAIN_FROM_CORNER := Vector2(250, 215)
const ARC_R := 250.0
const CAM_SPEED := Vector2(0.0042, 0.0034) ## radians per canvas pixel dragged

const FOREST := Color("#234d37")
const INK := Color("#09090b")

## action: the input action pressed; angle: where it sits on the arc round JUMP (180 = left,
## 270 = straight up); event: also sent as an input event (for handlers that read events).
const BUTTONS := [
	{"action": "jump", "main": true, "r": 118.0, "color": Color("#d5f64b")},
	{"action": "dash", "angle": 180.0, "r": 78.0, "color": Color("#ff7447")},
	{"action": "pound", "angle": 228.0, "r": 78.0, "color": Color("#f2c33d")},
	{"action": "cam_center", "angle": 276.0, "r": 56.0, "color": Color(1, 1, 1, 0.9), "event": true},
	{"action": "cam_zoom", "angle": 318.0, "r": 56.0, "color": Color(1, 1, 1, 0.9), "event": true},
	{"action": "pause", "pause": true, "r": 50.0, "color": Color(1, 1, 1, 0.9), "event": true},
]

var main: Node
var root: Control
var fingers := {} ## touch index -> action ("" = none)
var cam_finger := -1
var stick_finger := -1
var stick_center := Vector2.ZERO
var stick_knob := Vector2.ZERO ## offset from the centre, clamped to STICK_R
var _was_active := false


func _init(owner_main: Node) -> void:
	main = owner_main


func _ready() -> void:
	layer = 11
	process_mode = Node.PROCESS_MODE_ALWAYS
	root = Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.draw.connect(_draw_controls)
	add_child(root)


func view() -> Vector2:
	return get_viewport().get_visible_rect().size


## Controls show while you play; they hide on the title, in the pause menu and in cutscenes.
func _active() -> bool:
	return main.playing and not Game.paused and not Game.in_cutscene and not get_tree().paused


func _process(_delta: float) -> void:
	var active := _active()
	if not active and _was_active:
		_release_all()
	_was_active = active
	root.visible = active
	root.queue_redraw()


func _input(event: InputEvent) -> void:
	if not _active():
		return
	if event is InputEventScreenTouch:
		if event.pressed:
			var b := _button_at(event.position)
			if b != "":
				_assign(event.index, b)
			elif event.position.x < view().x * STICK_ZONE and stick_finger == -1:
				_stick_begin(event.index, event.position)
			elif cam_finger == -1:
				cam_finger = event.index
		else:
			if event.index == stick_finger:
				_stick_end()
			elif event.index == cam_finger:
				cam_finger = -1
			else:
				_assign(event.index, "")
				fingers.erase(event.index)
		get_viewport().set_input_as_handled()
	elif event is InputEventScreenDrag:
		if event.index == stick_finger:
			_stick_move(event.position)
		elif event.index == cam_finger:
			if main.camera:
				main.camera.touch_orbit(event.relative * Vector2(CAM_SPEED.x, CAM_SPEED.y))
		elif fingers.has(event.index):
			# sliding across the fan switches to the button under the thumb (jump → dash)
			var now := _button_at(event.position)
			if now in ["jump", "dash", "pound"]:
				_assign(event.index, now)
		get_viewport().set_input_as_handled()


# ------------------------------------------------------------------ stick

func _stick_rest() -> Vector2:
	return Vector2(INSET + STICK_R + 70.0, view().y - STICK_R - 90.0)


func _stick_begin(index: int, p: Vector2) -> void:
	stick_finger = index
	var v := view()
	stick_center = Vector2(clampf(p.x, INSET + STICK_R * 0.6, v.x * STICK_ZONE), clampf(p.y, STICK_R + 60.0, v.y - STICK_R * 0.6))
	_stick_move(p)


func _stick_move(p: Vector2) -> void:
	var d := p - stick_center
	# dragging past the rim pulls the base along, so the thumb never loses the stick
	if d.length() > STICK_R * 1.35:
		stick_center = p - d.normalized() * STICK_R * 1.35
		d = p - stick_center
	stick_knob = d.limit_length(STICK_R)
	var k := stick_knob / STICK_R
	var m := k.length()
	var s := 0.0 if m < DEADZONE else inverse_lerp(DEADZONE, 1.0, m)
	var dir := k.normalized() * s if m > 0.0 else Vector2.ZERO
	_axis("move_left", "move_right", dir.x)
	_axis("move_forward", "move_back", dir.y)


func _axis(neg: String, pos: String, x: float) -> void:
	if x < 0.0:
		Input.action_release(pos)
		Input.action_press(neg, -x)
	elif x > 0.0:
		Input.action_release(neg)
		Input.action_press(pos, x)
	else:
		Input.action_release(neg)
		Input.action_release(pos)


func _stick_end() -> void:
	stick_finger = -1
	stick_knob = Vector2.ZERO
	for a in ["move_left", "move_right", "move_forward", "move_back"]:
		Input.action_release(a)


# ------------------------------------------------------------------ buttons

func _main_pos() -> Vector2:
	return view() - MAIN_FROM_CORNER - Vector2(INSET - 40.0, 0)


func _pos(b: Dictionary) -> Vector2:
	if b.get("pause", false):
		# left of the health pebbles
		return Vector2(view().x - INSET - 330.0, 78.0)
	if b.get("main", false):
		return _main_pos()
	var a := deg_to_rad(float(b.angle))
	return _main_pos() + Vector2(cos(a), sin(a)) * ARC_R


func _button_at(p: Vector2) -> String:
	var best := ""
	var best_d := INF
	for b in BUTTONS:
		var d: float = p.distance_to(_pos(b))
		# thumbs are bigger than the drawn buttons
		if d < float(b.r) * 1.3 and d < best_d:
			best = b.action
			best_d = d
	return best


func _button(action: String) -> Dictionary:
	for b in BUTTONS:
		if b.action == action:
			return b
	return {}


func _assign(index: int, action: String) -> void:
	var old: String = fingers.get(index, "")
	if old == action:
		return
	if old != "":
		Input.action_release(old)
	fingers[index] = action
	if action == "":
		return
	Input.action_press(action)
	if _button(action).get("event", false):
		# the camera and pause handlers read input events, not action state
		var ev := InputEventAction.new()
		ev.action = action
		ev.pressed = true
		Input.parse_input_event(ev)
		Input.action_release(action)
	Game.haptic("light")


func _release_all() -> void:
	_stick_end()
	cam_finger = -1
	for i in fingers:
		var a: String = fingers[i]
		if a != "":
			Input.action_release(a)
	fingers.clear()


# ------------------------------------------------------------------ drawing

func _draw_controls() -> void:
	_draw_stick()
	var held := {}
	for i in fingers:
		held[fingers[i]] = true
	for b in BUTTONS:
		_draw_button(b, held.has(b.action))


func _draw_stick() -> void:
	var held := stick_finger != -1
	var c := stick_center if held else _stick_rest()
	var a := 1.0 if held else 0.6
	root.draw_circle(c + Vector2(0, 8), STICK_R, Color(0, 0, 0, 0.10 * a))
	root.draw_circle(c, STICK_R, Color(1, 1, 1, 0.10 * a))
	root.draw_arc(c, STICK_R, 0, TAU, 96, Color(1, 1, 1, 0.55 * a), 6.0, true)
	# four direction ticks, the one we push toward lit lime
	for i in 4:
		var ang := i * PI / 2.0
		var dir := Vector2(cos(ang), sin(ang))
		var lit := held and stick_knob.length() > STICK_R * 0.3 and stick_knob.normalized().dot(dir) > 0.7
		var tip := c + dir * (STICK_R - 22.0)
		var side := dir.orthogonal() * 14.0
		root.draw_colored_polygon(PackedVector2Array([tip + dir * 12.0, tip - dir * 6.0 + side, tip - dir * 6.0 - side]), Color(UiKit.LIME, 0.95) if lit else Color(1, 1, 1, 0.35 * a))
	var k := c + stick_knob
	root.draw_circle(k + Vector2(0, 6), KNOB_R, Color(0, 0, 0, 0.18 * a))
	root.draw_circle(k, KNOB_R, Color(1, 1, 1, 0.78 if held else 0.45))
	root.draw_arc(k, KNOB_R, 0, TAU, 64, Color(1, 1, 1, 0.95 * a), 5.0, true)
	root.draw_circle(k, KNOB_R * 0.45, Color(UiKit.LIME, 0.9 * a))


func _draw_button(b: Dictionary, down: bool) -> void:
	var c := _pos(b)
	var r: float = b.r * (0.92 if down else 1.0)
	var col: Color = b.color
	# a skill that can't fire right now (dash cooling down, pound on the ground) greys out
	var p: Player = main.player
	if p and ((b.action == "dash" and not p.dash_ready()) or (b.action == "pound" and not p.pound_ready())):
		col = col.lerp(Color(0.55, 0.58, 0.62), 0.7)
	var small: bool = b.r < 60.0
	var fill := Color(col, 0.95 if down else 0.8) if not small else Color(0.05, 0.06, 0.1, 0.5 if down else 0.32)
	root.draw_circle(c + Vector2(0, 7), r, Color(0, 0, 0, 0.22))
	root.draw_circle(c, r, fill)
	root.draw_arc(c, r, 0, TAU, 72, Color(1, 1, 1, 0.95) if down else Color(1, 1, 1, 0.7), 5.0, true)
	var g := FOREST if not small else Color.WHITE
	var s := r * 0.42
	match b.action:
		"jump":
			_chevron(c + Vector2(0, s * 0.35), s, -1.0, g, 13.0)
			_chevron(c + Vector2(0, -s * 0.45), s * 0.8, -1.0, Color(g, 0.6), 11.0)
		"dash":
			for dx in [-0.45, 0.35]:
				root.draw_polyline(PackedVector2Array([c + Vector2(dx * s - s * 0.35, -s * 0.6), c + Vector2(dx * s + s * 0.35, 0), c + Vector2(dx * s - s * 0.35, s * 0.6)]), INK, 11.0, true)
		"pound":
			root.draw_line(c + Vector2(0, -s * 0.8), c + Vector2(0, s * 0.25), INK, 11.0, true)
			_chevron(c + Vector2(0, s * 0.1), s * 0.7, 1.0, INK, 11.0)
			root.draw_line(c + Vector2(-s * 0.8, s * 0.85), c + Vector2(s * 0.8, s * 0.85), INK, 11.0, true)
		"cam_center":
			root.draw_arc(c, s * 0.95, deg_to_rad(-60), deg_to_rad(220), 32, g, 7.0, true)
			var tip := c + Vector2(cos(deg_to_rad(-60)), sin(deg_to_rad(-60))) * s * 0.95
			root.draw_colored_polygon(PackedVector2Array([tip + Vector2(10, -2), tip + Vector2(-12, -10), tip + Vector2(-4, 12)]), g)
		"cam_zoom":
			root.draw_arc(c + Vector2(-s * 0.2, -s * 0.2), s * 0.62, 0, TAU, 32, g, 7.0, true)
			root.draw_line(c + Vector2(s * 0.25, s * 0.25), c + Vector2(s * 0.85, s * 0.85), g, 9.0, true)
		"pause":
			for dx in [-0.35, 0.35]:
				root.draw_rect(Rect2(c + Vector2(dx * s - 6.0, -s * 0.65), Vector2(12, s * 1.3)), g)


## An arrowhead: up when dir = -1, down when dir = 1.
func _chevron(c: Vector2, s: float, dir: float, col: Color, w: float) -> void:
	root.draw_polyline(PackedVector2Array([c + Vector2(-s * 0.7, -dir * s * 0.35), c + Vector2(0, dir * s * 0.35), c + Vector2(s * 0.7, -dir * s * 0.35)]), col, w, true)
