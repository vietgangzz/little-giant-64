class_name Player
extends CharacterBody3D
## Little Giant's controller, tuned to feel like Super Mario 64: momentum on the ground, a
## variable-height jump, a flipping double jump, an air dash, a ground pound and wall kicks.

signal pounded(where: Vector3)
signal landed(impact: float)

enum S { GROUND, AIR, DASH, POUND_WINDUP, POUND_FALL, POUND_LAND, WALL_SLIDE, HURT, LOCKED, RESPAWN }

const RUN_SPEED := 8.6
const WALK_SPEED := 3.4
const GROUND_ACCEL := 46.0
const GROUND_DECEL := 38.0
const AIR_ACCEL := 17.0
const TURN_SPEED := 14.0
const GRAVITY_UP := 31.0
const GRAVITY_DOWN := 46.0
const MAX_FALL := 32.0
const JUMP_VELOCITY := 12.2
const JUMP2_VELOCITY := 12.8
const JUMP3_VELOCITY := 15.5
const JUMP_CUT := 0.45
const COYOTE := 0.12
const BUFFER := 0.14
const DASH_SPEED := 17.5
const DASH_TIME := 0.2
const DASH_COOLDOWN := 0.45
const POUND_WINDUP := 0.24
const POUND_SPEED := 34.0
const POUND_LAND_TIME := 0.32
const WALL_SLIDE_SPEED := 3.2
const WALL_KICK_OUT := 8.5
const WALL_KICK_UP := 12.8
const SPRING_VELOCITY := 19.0
const SUPER_SPRING_VELOCITY := 26.0
const STOMP_BOUNCE := 11.0
const INVULNERABLE := 1.6
const SEA_LEVEL := -0.55

var state := S.AIR
var facing := Vector3.BACK ## unit vector on XZ the model looks along
var camera: Node3D
var model: PlayerModel
var input_dir := Vector3.ZERO
var input_strength := 0.0

var _coyote := 0.0
var _buffer := 0.0
var _jump_held := false
var _jump_cut_done := false
var _air_jumps := 1
var _dash_available := true
var _dash_cooldown := 0.0
var _state_time := 0.0
var _combo := 0 ## consecutive ground jumps for the SM64 triple jump
var _combo_window := 0.0
var _invulnerable := 0.0
var _safe: Array[Vector3] = []
var _safe_timer := 0.0
var _grounded_time := 0.0
var _fall_peak := 0.0
var _step_dist := 0.0
var _idle_time := 0.0
var _checkpoint := Vector3.ZERO
var _wall_normal := Vector3.ZERO
var _was_on_floor := false
var _knock := Vector3.ZERO
var bot_input := Vector2.ZERO ## used by the QA bot instead of the pad
var bot_jump := false
var bot_dash := false
var bot_pound := false
var bot_jump_hold := false
var bot_world_dir := Vector3.ZERO ## QA bot steering in world space


func _ready() -> void:
	add_to_group("player")
	floor_max_angle = deg_to_rad(50.0)
	floor_snap_length = 0.35
	floor_stop_on_slope = true
	floor_constant_speed = true
	platform_on_leave = CharacterBody3D.PLATFORM_ON_LEAVE_ADD_UPWARD_VELOCITY
	safe_margin = 0.02
	collision_layer = 2
	collision_mask = 1 | 8
	var shape := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.42
	cap.height = 1.1
	shape.shape = cap
	shape.position.y = 0.55
	add_child(shape)
	model = PlayerModel.new()
	model.name = "Model"
	add_child(model)
	_add_blob_shadow()
	_checkpoint = global_position
	set_checkpoint(global_position)


func _add_blob_shadow() -> void:
	var d := Decal.new()
	d.texture_albedo = Fx.soft_tex
	d.size = Vector3(1.1, 30.0, 1.1)
	d.position.y = -14.9
	d.modulate = Color(0.1, 0.16, 0.3, 0.55)
	d.albedo_mix = 1.0
	d.cull_mask = 1
	d.upper_fade = 0.02
	d.lower_fade = 0.3
	add_child(d)


func set_checkpoint(where: Vector3) -> void:
	_checkpoint = where
	_safe.clear()
	_safe.append(where)


# ------------------------------------------------------------------ input

func _read_input() -> void:
	var v := Vector2.ZERO
	if Game.in_cutscene or Game.paused or state == S.LOCKED or state == S.RESPAWN:
		v = Vector2.ZERO
	elif bot_input != Vector2.ZERO:
		v = bot_input
	else:
		v = Input.get_vector("move_left", "move_right", "move_forward", "move_back")
		if Input.is_action_pressed("walk"):
			v *= 0.4
	if bot_world_dir != Vector3.ZERO and not Game.in_cutscene and state != S.LOCKED and state != S.RESPAWN:
		input_dir = Vector3(bot_world_dir.x, 0, bot_world_dir.z).limit_length(1.0)
		input_strength = input_dir.length()
		return
	input_strength = clampf(v.length(), 0.0, 1.0)
	if camera == null or v == Vector2.ZERO:
		input_dir = Vector3.ZERO
		return
	var basis := camera.global_transform.basis
	var fwd := -basis.z
	fwd.y = 0
	fwd = fwd.normalized()
	var right := basis.x
	right.y = 0
	right = right.normalized()
	input_dir = (right * v.x + fwd * -v.y)
	if input_dir.length() > 1.0:
		input_dir = input_dir.normalized()


func _pressed(action: String) -> bool:
	if Game.in_cutscene or Game.paused:
		return false
	match action:
		"jump":
			if bot_jump:
				bot_jump = false
				return true
		"dash":
			if bot_dash:
				bot_dash = false
				return true
		"pound":
			if bot_pound:
				bot_pound = false
				return true
	return Input.is_action_just_pressed(action)


# ------------------------------------------------------------------ main loop

func _physics_process(delta: float) -> void:
	_read_input()
	_state_time += delta
	_dash_cooldown = maxf(_dash_cooldown - delta, 0.0)
	_combo_window = maxf(_combo_window - delta, 0.0)
	if _invulnerable > 0.0:
		_invulnerable -= delta
		model.visible = fmod(_invulnerable, 0.16) > 0.07 or _invulnerable <= 0.0
	_jump_held = Input.is_action_pressed("jump") or bot_jump_hold
	if _pressed("jump"):
		_buffer = BUFFER
	else:
		_buffer = maxf(_buffer - delta, 0.0)
	var want_dash := _pressed("dash")
	var want_pound := _pressed("pound")

	match state:
		S.GROUND: _ground(delta, want_dash)
		S.AIR: _air(delta, want_dash, want_pound)
		S.DASH: _dash(delta)
		S.POUND_WINDUP: _pound_windup(delta)
		S.POUND_FALL: _pound_fall(delta)
		S.POUND_LAND: _pound_land(delta)
		S.WALL_SLIDE: _wall_slide(delta)
		S.HURT: _hurt(delta)
		S.LOCKED, S.RESPAWN:
			velocity.x = move_toward(velocity.x, 0, GROUND_DECEL * delta)
			velocity.z = move_toward(velocity.z, 0, GROUND_DECEL * delta)
			if not is_on_floor():
				velocity.y = maxf(velocity.y - GRAVITY_DOWN * delta, -MAX_FALL)
			else:
				velocity.y = -0.5

	var vy_before := velocity.y
	move_and_slide()
	_after_move(delta, vy_before)
	model.update_visual(self, delta)


func _after_move(delta: float, vy_before: float) -> void:
	var on_floor := is_on_floor()
	if on_floor and not _was_on_floor:
		_on_landed(-vy_before)
	_was_on_floor = on_floor
	if global_position.y > _fall_peak or on_floor:
		_fall_peak = global_position.y
	# stomping enemies and bonking blocks from below
	for i in get_slide_collision_count():
		var col := get_slide_collision(i)
		var other := col.get_collider()
		if other == null:
			continue
		var n := col.get_normal()
		if other.has_method("on_player_head") and n.y < -0.6 and vy_before > 0.0:
			other.on_player_head(self)
			velocity.y = minf(velocity.y, -1.0)
		if other.has_method("on_player_touch"):
			other.on_player_touch(self, n)
	# remember a safe place to put the player back after a fall into the sea
	if on_floor and state == S.GROUND:
		_grounded_time += delta
		var floor := get_last_slide_collision().get_collider() if get_slide_collision_count() > 0 else null
		var stable := floor is StaticBody3D and not (floor as Node).is_in_group("hazard") and not (floor as Node).is_in_group("unsafe")
		_safe_timer -= delta
		if stable and _grounded_time > 0.35 and _safe_timer <= 0.0 and _far_from_edge():
			_safe_timer = 0.3
			_safe.append(global_position)
			if _safe.size() > 6:
				_safe.pop_front()
	else:
		_grounded_time = 0.0
	if global_position.y < SEA_LEVEL and state != S.RESPAWN:
		_fell_in_water()


func _far_from_edge() -> bool:
	var space := get_world_3d().direct_space_state
	for a in 4:
		var off := Vector3(cos(a * PI / 2.0), 0, sin(a * PI / 2.0)) * 0.9
		var q := PhysicsRayQueryParameters3D.create(global_position + off + Vector3.UP * 0.5, global_position + off + Vector3.DOWN * 1.2, 1)
		if space.intersect_ray(q).is_empty():
			return false
	return true


# ------------------------------------------------------------------ states

func _enter(s: S) -> void:
	state = s
	_state_time = 0.0


func _face_input(delta: float, rate := TURN_SPEED) -> void:
	if input_dir.length() > 0.05:
		var target := input_dir.normalized()
		var ang := facing.signed_angle_to(target, Vector3.UP)
		var step := clampf(ang, -rate * delta, rate * delta)
		facing = facing.rotated(Vector3.UP, step).normalized()


func _ground(delta: float, want_dash: bool) -> void:
	_coyote = COYOTE
	_air_jumps = 1
	_dash_available = true
	var target_speed := RUN_SPEED * input_strength
	if input_strength < 0.55 and input_strength > 0.0:
		target_speed = lerpf(WALK_SPEED * 0.5, WALK_SPEED, input_strength / 0.55)
	var hv := Vector3(velocity.x, 0, velocity.z)
	if input_dir.length() > 0.05:
		# turning hard at speed costs momentum, like SM64's skid
		var turn := facing.dot(input_dir.normalized())
		_face_input(delta, TURN_SPEED * (0.6 if hv.length() > 6.0 and turn < -0.3 else 1.0))
		var desired := facing * target_speed
		hv = hv.move_toward(desired, GROUND_ACCEL * delta)
		_idle_time = 0.0
	else:
		hv = hv.move_toward(Vector3.ZERO, GROUND_DECEL * delta)
		_idle_time += delta
	velocity.x = hv.x
	velocity.z = hv.z
	velocity.y = -1.0
	_footsteps(hv.length() * delta)

	if _buffer > 0.0:
		_jump()
		return
	if want_dash and _dash_cooldown <= 0.0:
		_start_dash()
		return
	if not is_on_floor():
		_enter(S.AIR)
		velocity.y = 0.0
		model.play("fall", 0.25)
		return
	var sp := hv.length()
	if sp < 0.3:
		if _idle_time > 22.0:
			model.play("sleep", 0.6)
		elif _idle_time > 7.0 and fmod(_idle_time, 9.0) < 0.05:
			model.play("idle_look", 0.3)
		elif not model.is_playing_oneshot():
			model.play("idle", 0.25)
	elif sp < 5.2:
		model.play("walk", 0.2, clampf(sp / WALK_SPEED, 0.6, 1.7))
	else:
		model.play("run", 0.2, clampf(sp / RUN_SPEED, 0.75, 1.3))


func _footsteps(dist: float) -> void:
	_step_dist += dist
	var sp := Vector2(velocity.x, velocity.z).length()
	var stride := 1.25 if sp > 5.0 else 0.8
	if _step_dist > stride and sp > 1.0:
		_step_dist = 0.0
		Sound.play("footstep_grass_%d" % randi_range(1, 4), -10.0 if sp > 5 else -14.0, 1.0, 0.08)
		if sp > 6.5:
			Fx.dust(global_position - facing * 0.2, 2, 0.25, 0.25, 0.26)


func _jump() -> void:
	_buffer = 0.0
	_coyote = 0.0
	_jump_cut_done = false
	var sp := Vector2(velocity.x, velocity.z).length()
	# SM64 rhythm: jump again right after landing to go higher, a third time for a flip
	if _combo_window > 0.0 and sp > 4.0:
		_combo = mini(_combo + 1, 2)
	else:
		_combo = 0
	var vy := JUMP_VELOCITY
	var anim := "jump"
	var sfx := "jump"
	if _combo == 1:
		vy = JUMP_VELOCITY * 1.12
		sfx = "jump2"
	elif _combo == 2:
		vy = JUMP3_VELOCITY
		anim = "double_jump"
		sfx = "double_jump"
		_combo = -1
	velocity.y = vy
	_enter(S.AIR)
	model.play(anim, 0.06)
	model.squash(Vector3(0.82, 1.25, 0.82))
	Sound.play(sfx, -3.0)
	Fx.dust(global_position, 5, 0.45, 0.3, 0.35)


func _air(delta: float, want_dash: bool, want_pound: bool) -> void:
	_coyote -= delta
	var hv := Vector3(velocity.x, 0, velocity.z)
	if input_dir.length() > 0.05:
		_face_input(delta, TURN_SPEED * 0.55)
		var desired := input_dir * RUN_SPEED
		# keep momentum above run speed (after a dash) instead of clamping it away
		var cap := maxf(hv.length(), RUN_SPEED)
		hv = hv.move_toward(desired, AIR_ACCEL * delta)
		if hv.length() > cap:
			hv = hv.normalized() * cap
	else:
		hv = hv.move_toward(Vector3.ZERO, AIR_ACCEL * 0.25 * delta)
	velocity.x = hv.x
	velocity.z = hv.z
	var g := GRAVITY_UP if velocity.y > 0.0 else GRAVITY_DOWN
	if velocity.y > 0.0 and not _jump_held and not _jump_cut_done:
		velocity.y *= JUMP_CUT
		_jump_cut_done = true
	velocity.y = maxf(velocity.y - g * delta, -MAX_FALL)

	if _buffer > 0.0:
		if _coyote > 0.0:
			_jump()
			return
		if _air_jumps > 0:
			_double_jump()
			return
	if want_dash and _dash_available:
		_start_dash()
		return
	if want_pound and _state_time > 0.08:
		_enter(S.POUND_WINDUP)
		velocity = Vector3.ZERO
		model.play("ground_pound", 0.05)
		Sound.play("ground_pound", -4.0)
		return
	if is_on_wall() and velocity.y < 2.0 and input_dir.length() > 0.3:
		var wn := get_wall_normal()
		if absf(wn.y) < 0.35 and input_dir.normalized().dot(-Vector3(wn.x, 0, wn.z).normalized()) > 0.35:
			_wall_normal = Vector3(wn.x, 0, wn.z).normalized()
			_enter(S.WALL_SLIDE)
			facing = -_wall_normal
			model.play("wall_slide", 0.1)
			return
	if velocity.y < -2.0 and model.current in ["jump", "double_jump"] and model.finished_current():
		model.play("fall", 0.3)
	# is_on_floor() is from the last move; a spring or stomp may have launched us since
	if is_on_floor() and velocity.y <= 0.0:
		_enter(S.GROUND)


func _double_jump() -> void:
	_buffer = 0.0
	_air_jumps -= 1
	_jump_cut_done = false
	velocity.y = JUMP2_VELOCITY
	if input_dir.length() > 0.1:
		var hv := Vector3(velocity.x, 0, velocity.z)
		facing = input_dir.normalized()
		hv = facing * maxf(hv.length(), RUN_SPEED * input_strength * 0.9)
		velocity.x = hv.x
		velocity.z = hv.z
	_enter(S.AIR)
	model.play("double_jump", 0.05)
	model.squash(Vector3(0.8, 1.3, 0.8))
	Sound.play("double_jump", -2.0)
	Fx.ring(global_position + Vector3(0, 0.2, 0), Color(1, 1, 1, 0.9), 2.4, 0.45)
	Fx.sparkle(global_position + Vector3(0, 0.4, 0), Color(1, 0.95, 0.6), 8, 3.0, 0.3, 0.5)
	Fx.dust(global_position, 6, 0.6, -0.2, 0.32)


func _start_dash() -> void:
	_dash_available = false
	_dash_cooldown = DASH_COOLDOWN
	if input_dir.length() > 0.1:
		facing = input_dir.normalized()
	_enter(S.DASH)
	velocity = facing * DASH_SPEED
	velocity.y = 2.2 if not is_on_floor() else 0.0
	model.play("dash", 0.05)
	model.squash(Vector3(0.8, 0.85, 1.35))
	Sound.play("dash", -3.0)
	Fx.dust(global_position + Vector3.UP * 0.3, 5, 0.5, 0.2, 0.3)
	Fx.shake(0.06, 0.1)


func _dash(delta: float) -> void:
	velocity.y = maxf(velocity.y - GRAVITY_UP * 0.35 * delta, -4.0)
	if int(_state_time * 60.0) % 3 == 0:
		Fx.dust(global_position + Vector3.UP * 0.5 - facing * 0.4, 1, 0.1, 0.05, 0.3, Color(1, 1, 1, 0.7))
	if _state_time >= DASH_TIME or is_on_wall():
		var hv := facing * RUN_SPEED * 1.05
		velocity.x = hv.x
		velocity.z = hv.z
		if is_on_floor():
			_enter(S.GROUND)
		else:
			_enter(S.AIR)
			model.play("fall", 0.2)
		return
	if _buffer > 0.0 and is_on_floor():
		_jump()
		# a dash-jump keeps the dash speed: the long jump
		var hv := facing * DASH_SPEED * 0.8
		velocity.x = hv.x
		velocity.z = hv.z


func _pound_windup(_delta: float) -> void:
	velocity = Vector3.ZERO
	if _state_time >= POUND_WINDUP:
		_enter(S.POUND_FALL)
		velocity = Vector3(0, -POUND_SPEED, 0)


func _pound_fall(_delta: float) -> void:
	velocity = Vector3(0, -POUND_SPEED, 0)
	if int(_state_time * 60.0) % 2 == 0:
		Fx.dust(global_position + Vector3.UP * 0.9, 1, 0.05, 0.3, 0.22, Color(1, 1, 1, 0.6))
	if is_on_floor():
		_enter(S.POUND_LAND)
		model.play("ground_pound_land", 0.03)
		model.squash(Vector3(1.4, 0.6, 1.4))
		Sound.play("ground_pound_land", 0.0)
		Fx.dust(global_position, 12, 1.4, 0.3, 0.5)
		Fx.ring(global_position + Vector3.UP * 0.05, Color(1, 1, 1, 1), 5.0, 0.5)
		Fx.shake(0.4, 0.25)
		Fx.hitstop(0.05)
		pounded.emit(global_position)
		get_tree().call_group("poundable", "on_pound", global_position, self)


func _pound_land(_delta: float) -> void:
	velocity = Vector3(0, -1, 0)
	if _state_time >= POUND_LAND_TIME:
		_enter(S.GROUND)
	elif _buffer > 0.0 and _state_time > 0.08:
		_jump()
		velocity.y = JUMP3_VELOCITY
		model.play("double_jump", 0.05)


func _wall_slide(delta: float) -> void:
	velocity.x = -_wall_normal.x * 1.0
	velocity.z = -_wall_normal.z * 1.0
	velocity.y = maxf(velocity.y - GRAVITY_DOWN * delta, -WALL_SLIDE_SPEED)
	if int(_state_time * 30.0) % 4 == 0:
		Fx.dust(global_position + Vector3.UP * 0.8 - _wall_normal * 0.3, 1, 0.1, -0.1, 0.18)
	if _buffer > 0.0:
		_buffer = 0.0
		facing = _wall_normal
		velocity = _wall_normal * WALL_KICK_OUT + Vector3.UP * WALL_KICK_UP
		_air_jumps = 1
		_dash_available = true
		_jump_cut_done = true
		_enter(S.AIR)
		model.play("double_jump", 0.05)
		Sound.play("jump2", -3.0, 1.1)
		Fx.dust(global_position + Vector3.UP * 0.6, 5, 0.5, 0.2, 0.3)
		Fx.ring(global_position + Vector3.UP * 0.6, Color(1, 1, 1, 0.8), 1.8, 0.3, _wall_normal)
		return
	var pushing := input_dir.length() > 0.2 and input_dir.normalized().dot(-_wall_normal) > 0.1
	if is_on_floor():
		_enter(S.GROUND)
	elif not is_on_wall() or not pushing:
		_enter(S.AIR)
		model.play("fall", 0.2)


func _hurt(delta: float) -> void:
	velocity.x = move_toward(velocity.x, 0, 6.0 * delta)
	velocity.z = move_toward(velocity.z, 0, 6.0 * delta)
	velocity.y = maxf(velocity.y - GRAVITY_DOWN * delta, -MAX_FALL)
	if _state_time > 0.45 and is_on_floor() and velocity.y <= 0.0:
		_enter(S.GROUND)
	elif _state_time > 0.9:
		_enter(S.AIR)


func _on_landed(impact: float) -> void:
	landed.emit(impact)
	_combo_window = 0.18 if state == S.AIR else 0.0
	if _combo == -1:
		_combo = 0
		_combo_window = 0.0
	if state == S.POUND_FALL or state == S.POUND_LAND:
		return
	if impact > 6.0:
		var k := clampf((impact - 6.0) / 20.0, 0.0, 1.0)
		model.squash(Vector3(1.0 + 0.35 * k + 0.1, 1.0 - 0.35 * k - 0.1, 1.0 + 0.35 * k + 0.1))
		Fx.dust(global_position, int(4 + 6 * k), 0.5 + k, 0.2, 0.3 + 0.2 * k)
		Sound.play("land", lerpf(-12.0, -3.0, k))
		if Vector2(velocity.x, velocity.z).length() < 2.0:
			model.play("land", 0.05)
	if state == S.AIR or state == S.DASH or state == S.WALL_SLIDE:
		_enter(S.GROUND)


# ------------------------------------------------------------------ interactions

## Called by drum springs. `super` comes from ground-pounding onto the drum.
func spring(power := SPRING_VELOCITY) -> void:
	velocity.y = power
	_coyote = 0.0
	_buffer = 0.0
	_air_jumps = 1
	_dash_available = true
	_jump_cut_done = true
	_enter(S.AIR)
	model.play("double_jump", 0.05)
	model.squash(Vector3(0.75, 1.35, 0.75))


func bounce_off_enemy() -> void:
	velocity.y = STOMP_BOUNCE if not _jump_held else STOMP_BOUNCE * 1.3
	_coyote = 0.0
	_air_jumps = 1
	_dash_available = true
	_jump_cut_done = true
	_enter(S.AIR)
	model.play("jump", 0.05)


func is_pounding() -> bool:
	return state == S.POUND_FALL or state == S.POUND_LAND


func is_stomping_from_above(enemy_top: float) -> bool:
	return velocity.y < 0.5 and global_position.y > enemy_top - 0.35


func damage(from: Vector3, amount := 1) -> void:
	if _invulnerable > 0.0 or state == S.RESPAWN or Game.in_cutscene or Game.args.has("god"):
		return
	Game.hurt(amount)
	_invulnerable = INVULNERABLE
	var away := global_position - from
	away.y = 0
	away = away.normalized() if away.length() > 0.01 else -facing
	velocity = away * 8.0 + Vector3.UP * 7.5
	facing = -away
	_enter(S.HURT)
	model.play("hurt", 0.05)
	Sound.play("hurt", -2.0)
	Fx.shake(0.35, 0.2)
	Fx.sparkle(global_position + Vector3.UP * 0.8, Color(1, 0.6, 0.4), 8, 4.0, 0.35, 0.5)
	if Game.hp <= 0:
		_respawn(true)


func _fell_in_water() -> void:
	Fx.splash(global_position)
	Sound.play("splash", -1.0)
	Game.hurt(1)
	_respawn(Game.hp <= 0)


func _respawn(to_checkpoint: bool) -> void:
	_enter(S.RESPAWN)
	velocity = Vector3.ZERO
	var target := _checkpoint if to_checkpoint or _safe.is_empty() else _safe[0]
	var tw := create_tween()
	tw.tween_interval(0.55)
	tw.tween_callback(func():
		global_position = target + Vector3.UP * 0.3
		velocity = Vector3.ZERO
		if to_checkpoint:
			Game.hp = Game.MAX_HP
			Game.health_changed.emit(Game.hp)
		_invulnerable = 1.2
		if camera and camera.has_method("snap_behind"):
			camera.snap_behind()
		Fx.dust(global_position, 8, 0.8, 0.5, 0.4)
		Fx.sparkle(global_position + Vector3.UP * 0.6, Color(0.85, 1.0, 0.5), 10, 3.0, 0.3, 0.6)
		model.play("idle", 0.0)
		_enter(S.AIR))


func lock(on: bool) -> void:
	if on:
		_enter(S.LOCKED)
	elif state == S.LOCKED:
		_enter(S.GROUND if is_on_floor() else S.AIR)


func teleport(where: Vector3, face := Vector3.ZERO) -> void:
	global_position = where
	velocity = Vector3.ZERO
	if face != Vector3.ZERO:
		facing = Vector3(face.x, 0, face.z).normalized()
	_safe.clear()
	_safe.append(where)
	_enter(S.AIR)


## Somewhere reachable to hang a star: 2.2 m above the ground under the hero, or above the
## last safe spot when the hero is over the sea.
func star_spot() -> Vector3:
	var q := PhysicsRayQueryParameters3D.create(global_position + Vector3.UP * 0.5, global_position + Vector3.DOWN * 30.0, 1)
	var hit := get_world_3d().direct_space_state.intersect_ray(q)
	if not hit.is_empty() and (hit["position"] as Vector3).y > SEA_LEVEL + 0.5:
		return hit["position"] + Vector3.UP * 2.2
	return (_safe[-1] if not _safe.is_empty() else _checkpoint) + Vector3.UP * 2.2


func set_cape(on: bool) -> void:
	model.set_cape(on)
