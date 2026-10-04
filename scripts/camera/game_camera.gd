class_name GameCamera
extends Node3D
## A Super Mario 64 camera: sits behind the hero and swings round lazily as they run, holds its
## height at ground level through jumps, turns in 45° steps (Q/E, like the C-buttons), orbits
## freely with the mouse or right stick, and pulls in when scenery gets in the way.

const DISTANCES := [5.6, 8.4, 4.0]
const MIN_PITCH := deg_to_rad(-12.0)
const MAX_PITCH := deg_to_rad(62.0)

var target: Player
var cam: Camera3D
var yaw := 0.0
var pitch := deg_to_rad(17.0)
var distance := 5.6
var zoom_index := 0
var cutscene := false

var _yaw_goal := 0.0
var _manual_timer := 0.0
var _focus := Vector3.ZERO
var _ground_y := 0.0
var _cur_dist := 5.6
var _shake_time := 0.0
var _shake_strength := 0.0
var _fov_boost := 0.0


func _ready() -> void:
	cam = Camera3D.new()
	cam.fov = 58.0
	cam.near = 0.1
	cam.far = 900.0
	add_child(cam)
	cam.make_current()
	var attrs := CameraAttributesPractical.new()
	attrs.dof_blur_far_enabled = true
	attrs.dof_blur_far_distance = 95.0
	attrs.dof_blur_far_transition = 80.0
	attrs.dof_blur_amount = 0.045
	cam.attributes = attrs
	Fx.shake_requested.connect(_on_shake)
	top_level = true


func attach(p: Player) -> void:
	target = p
	p.camera = self
	_focus = p.global_position + Vector3.UP * 1.1
	_ground_y = p.global_position.y
	snap_behind()


func snap_behind() -> void:
	if target == null:
		return
	yaw = atan2(-target.facing.x, -target.facing.z)
	_yaw_goal = yaw
	_focus = target.global_position + Vector3.UP * 1.1
	_ground_y = target.global_position.y
	_apply(0.0)


func _unhandled_input(event: InputEvent) -> void:
	if cutscene or Game.paused:
		return
	# on a phone, touches also arrive as emulated mouse events; the camera drag has its own path
	if Game.touch_mode and (event is InputEventMouseButton or event is InputEventMouseMotion):
		return
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_LEFT or event.button_index == MOUSE_BUTTON_RIGHT:
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
		elif event.button_index == MOUSE_BUTTON_WHEEL_UP:
			distance = maxf(distance - 0.6, 3.4)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			distance = minf(distance + 0.6, 12.0)
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		var sx := -1.0 if Game.invert_x else 1.0
		var sy := -1.0 if Game.invert_y else 1.0
		yaw -= event.relative.x * 0.0035 * Game.mouse_sensitivity * sx
		pitch = clampf(pitch + event.relative.y * 0.0028 * Game.mouse_sensitivity * sy, MIN_PITCH, MAX_PITCH)
		_yaw_goal = yaw
		_manual_timer = 1.4
	if event.is_action_pressed("cam_left") and event is InputEventKey:
		_yaw_goal += PI / 4.0
		_manual_timer = 2.0
		Sound.play("whoosh_camera", -16.0)
	if event.is_action_pressed("cam_right") and event is InputEventKey:
		_yaw_goal -= PI / 4.0
		_manual_timer = 2.0
		Sound.play("whoosh_camera", -16.0)
	if event.is_action_pressed("cam_zoom"):
		zoom_index = (zoom_index + 1) % DISTANCES.size()
		distance = DISTANCES[zoom_index]
		Sound.play("whoosh_camera", -16.0, 1.2)
	if event.is_action_pressed("cam_center") and target:
		_yaw_goal = atan2(-target.facing.x, -target.facing.z)
		_yaw_goal = yaw + wrapf(_yaw_goal - yaw, -PI, PI)
		_manual_timer = 0.6


## A drag on the right half of a phone screen swings the camera (already scaled to radians).
func touch_orbit(turn: Vector2) -> void:
	if cutscene or Game.paused:
		return
	var sx := -1.0 if Game.invert_x else 1.0
	var sy := -1.0 if Game.invert_y else 1.0
	yaw -= turn.x * Game.mouse_sensitivity * sx
	pitch = clampf(pitch + turn.y * Game.mouse_sensitivity * sy, MIN_PITCH, MAX_PITCH)
	_yaw_goal = yaw
	_manual_timer = 1.4


func _process(delta: float) -> void:
	if cutscene or target == null:
		_update_shake(delta)
		return
	# right stick
	var stick := Vector2(Input.get_axis("cam_left", "cam_right"), Input.get_axis("cam_up", "cam_down"))
	var from_pad := false
	for ev in InputMap.action_get_events("cam_left"):
		if ev is InputEventJoypadMotion:
			from_pad = true
	if from_pad and stick.length() > 0.2 and Input.get_connected_joypads().size() > 0:
		var sx := -1.0 if Game.invert_x else 1.0
		var sy := -1.0 if Game.invert_y else 1.0
		var axis_x := Input.get_joy_axis(0, JOY_AXIS_RIGHT_X)
		var axis_y := Input.get_joy_axis(0, JOY_AXIS_RIGHT_Y)
		if absf(axis_x) > 0.2:
			yaw -= axis_x * 2.6 * delta * sx
			_yaw_goal = yaw
			_manual_timer = 1.2
		if absf(axis_y) > 0.2:
			pitch = clampf(pitch + axis_y * 1.6 * delta * sy, MIN_PITCH, MAX_PITCH)
	_manual_timer = maxf(_manual_timer - delta, 0.0)

	# lazy auto-follow: swing behind the direction of travel, but never while the player runs
	# straight at the camera (so you can run toward it, as in SM64)
	var hv := Vector3(target.velocity.x, 0, target.velocity.z)
	if _manual_timer <= 0.0 and hv.length() > 1.5 and not Game.in_cutscene:
		var behind := atan2(-hv.x, -hv.z)
		var diff := wrapf(behind - yaw, -PI, PI)
		var cam_fwd := Vector3(-sin(yaw), 0, -cos(yaw))
		var toward_cam := hv.normalized().dot(cam_fwd) < -0.55
		if not toward_cam:
			var rate := 1.1 * clampf(hv.length() / Player.RUN_SPEED, 0.0, 1.3)
			_yaw_goal = yaw + diff * clampf(rate * delta, 0.0, 1.0)
	yaw = lerp_angle(yaw, _yaw_goal, clampf(delta * 7.0, 0.0, 1.0))
	if absf(wrapf(_yaw_goal - yaw, -PI, PI)) < 0.001:
		_yaw_goal = yaw

	# height: stay with the ground through jumps, follow falls immediately
	var p := target.global_position
	if target.is_on_floor() or target.state == Player.S.WALL_SLIDE:
		_ground_y = lerpf(_ground_y, p.y, clampf(delta * 6.0, 0.0, 1.0))
	elif p.y < _ground_y:
		_ground_y = p.y
	elif p.y > _ground_y + 3.5:
		_ground_y = lerpf(_ground_y, p.y - 3.5, clampf(delta * 5.0, 0.0, 1.0))
	var focus_goal := Vector3(p.x, lerpf(_ground_y, p.y, 0.35) + 1.35, p.z)
	_focus = _focus.lerp(focus_goal, clampf(delta * 10.0, 0.0, 1.0))
	_focus.y = lerpf(_focus.y, focus_goal.y, clampf(delta * 4.0, 0.0, 1.0))

	var dashing := target.state == Player.S.DASH
	_fov_boost = lerpf(_fov_boost, 8.0 if dashing else 0.0, clampf(delta * 6.0, 0.0, 1.0))
	cam.fov = 58.0 + _fov_boost
	_apply(delta)
	_update_shake(delta)


func _apply(delta: float) -> void:
	var dir := Vector3(sin(yaw) * cos(pitch), sin(pitch), cos(yaw) * cos(pitch))
	var want := distance
	# pull in when scenery blocks the view (sphere cast from the focus out to the camera)
	if is_inside_tree() and target:
		var space := get_world_3d().direct_space_state
		var sphere := SphereShape3D.new()
		sphere.radius = 0.35
		var q := PhysicsShapeQueryParameters3D.new()
		q.shape = sphere
		q.transform = Transform3D(Basis(), _focus)
		q.motion = dir * distance
		q.collision_mask = 1
		q.exclude = [target.get_rid()]
		var r := space.cast_motion(q)
		if r.size() == 2 and r[0] < 1.0:
			want = maxf(distance * r[0] - 0.1, 1.2)
	if delta <= 0.0:
		_cur_dist = want
	elif want < _cur_dist:
		_cur_dist = lerpf(_cur_dist, want, clampf(delta * 18.0, 0.0, 1.0))
	else:
		_cur_dist = lerpf(_cur_dist, want, clampf(delta * 2.5, 0.0, 1.0))
	global_position = _focus + dir * _cur_dist
	look_at(_focus + Vector3.UP * 0.05, Vector3.UP)


func _on_shake(strength: float, duration: float) -> void:
	_shake_strength = maxf(_shake_strength, strength)
	_shake_time = maxf(_shake_time, duration)


func _update_shake(delta: float) -> void:
	if _shake_time > 0.0:
		_shake_time -= delta
		var s := _shake_strength * clampf(_shake_time * 5.0, 0.0, 1.0)
		cam.position = Vector3(randf_range(-s, s), randf_range(-s, s), 0) * 0.5
		cam.rotation.z = randf_range(-s, s) * 0.03
	else:
		_shake_strength = 0.0
		cam.position = Vector3.ZERO
		cam.rotation.z = 0.0


## Moves the camera through a scripted shot; gameplay control resumes with `release()`.
func shot(to: Transform3D, seconds := 1.0) -> Tween:
	cutscene = true
	var from := global_transform
	var tw := create_tween()
	tw.tween_method(func(t: float):
		global_transform = from.interpolate_with(to, t), 0.0, 1.0, seconds).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	return tw


func orbit_shot(center: Vector3, radius: float, height: float, from_angle: float, to_angle: float, seconds: float) -> Tween:
	cutscene = true
	var tw := create_tween()
	tw.tween_method(func(a: float):
		global_position = center + Vector3(sin(a) * radius, height, cos(a) * radius)
		look_at(center + Vector3.UP * 0.6, Vector3.UP), from_angle, to_angle, seconds).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	return tw


func release() -> void:
	cutscene = false
	if target:
		yaw = atan2(global_position.x - target.global_position.x, global_position.z - target.global_position.z)
		_yaw_goal = yaw
		_focus = target.global_position + Vector3.UP * 1.1
		_ground_y = target.global_position.y
