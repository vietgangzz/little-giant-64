class_name Coin
extends Area3D
## A spinning bronze coin with a square hole. Red lanterns use the same script with `red = true`.
## Quick successive pickups raise the chime's pitch, like a Mario coin run.

static var _chain := 0
static var _chain_time := 0

var red := false
var prop_override := "" ## e.g. "pearl" for Hạ Long's dragon pearls
var value := 1
var _t := 0.0
var _visual: Node3D
var _taken := false
var _vel := Vector3.ZERO
var _ballistic := false
var _arm := 0.0
var _base_y := 0.0


func _init(is_red := false) -> void:
	red = is_red
	value = 2 if red else 1


func _ready() -> void:
	add_to_group("coin" if not red else "red_coin")
	collision_layer = 0
	collision_mask = 2
	monitorable = false
	var cs := CollisionShape3D.new()
	var s := SphereShape3D.new()
	s.radius = 0.62
	cs.shape = s
	cs.position.y = 0.35
	add_child(cs)
	_visual = Props.make(prop_override if prop_override != "" else ("coin_red" if red else "coin"), true)
	add_child(_visual)
	if red:
		_visual.scale = Vector3.ONE * 1.1
	_t = randf() * TAU
	_base_y = position.y
	body_entered.connect(_on_body)


## Coins that pop out of blocks fly, fall and settle before they can be taken.
func launch(v: Vector3) -> void:
	_vel = v
	_ballistic = true
	_arm = 0.25


func _physics_process(delta: float) -> void:
	_t += delta
	if _taken:
		return
	if _ballistic:
		_arm -= delta
		_vel.y -= 28.0 * delta
		var from := global_position
		var to := from + _vel * delta
		var q := PhysicsRayQueryParameters3D.create(from + Vector3.UP * 0.2, to, 1)
		var hit := get_world_3d().direct_space_state.intersect_ray(q)
		if not hit.is_empty() and _vel.y < 0.0:
			global_position = hit["position"] + Vector3.UP * 0.05
			_vel = Vector3(_vel.x * 0.5, -_vel.y * 0.35, _vel.z * 0.5)
			if _vel.y < 1.2:
				_ballistic = false
				_base_y = position.y
		else:
			global_position = to
		if global_position.y < -1.0:
			queue_free()
		if _arm <= 0.0:
			for b in get_overlapping_bodies():
				_on_body(b)
	_visual.rotation.y = _t * (3.2 if red else 4.2)
	if not _ballistic:
		_visual.position.y = sin(_t * 2.4) * 0.08


func _on_body(b: Node) -> void:
	if _taken or not b.is_in_group("player") or _arm > 0.0:
		return
	_taken = true
	var now := Time.get_ticks_msec()
	_chain = _chain + 1 if now - _chain_time < 900 else 0
	_chain_time = now
	if red:
		Game.add_red_coin()
		Sound.play("coin_red", -2.0, 1.0 + 0.06 * Game.red_coins, 0.0)
		Fx.sparkle(global_position + Vector3.UP * 0.4, Color(1.0, 0.45, 0.35), 14, 4.5, 0.4, 0.8)
		Fx.ring(global_position + Vector3.UP * 0.4, Color(1, 0.5, 0.4, 1), 2.4, 0.4, Vector3.BACK)
		get_tree().call_group("hud", "show_red", Game.red_coins)
	else:
		Sound.play("coin", -5.0, 1.0 + minf(_chain, 12) * 0.035, 0.0)
		Fx.sparkle(global_position + Vector3.UP * 0.4, Color(1.0, 0.86, 0.35), 7, 3.0, 0.3, 0.45)
	Game.add_coins(value)
	if Game.coins % 50 == 0 and value > 0:
		Game.heal(1)
	var tw := create_tween().set_parallel(true)
	tw.tween_property(_visual, "position:y", 1.2, 0.3).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BACK)
	tw.tween_property(_visual, "scale", Vector3.ONE * 0.1, 0.3).set_delay(0.08).set_ease(Tween.EASE_IN)
	tw.chain().tween_callback(queue_free)
