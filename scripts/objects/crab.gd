class_name Crab
extends CharacterBody3D
## Cua: scuttles sideways around its patch of beach, charges when the hero comes close, and is
## flattened by a stomp or a ground pound nearby.

var home := Vector3.ZERO
var wander := 5.0
var group_tag := "" ## e.g. "beach_crab": the world counts these for a star
var _visual: Node3D
var _anim: AnimationPlayer
var _goal := Vector3.ZERO
var _think := 0.0
var _dead := false
var _hurtbox: Area3D
var _heading := 0.0
var _snap_cool := 0.0
var _alert := 0.0 ## >0 while the crab rears up before charging
var _chasing := false


func _ready() -> void:
	add_to_group("crab")
	add_to_group("poundable")
	if group_tag != "":
		add_to_group(group_tag)
	collision_layer = 4
	collision_mask = 1
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(0.9, 0.5, 0.6)
	cs.shape = box
	cs.position.y = 0.25
	add_child(cs)
	_visual = Props.make("crab")
	add_child(_visual)
	_anim = Props.anim_player(_visual)
	if _anim and _anim.has_animation("walk"):
		_anim.get_animation("walk").loop_mode = Animation.LOOP_LINEAR
		_anim.play("walk")
	_hurtbox = Area3D.new()
	_hurtbox.collision_layer = 0
	_hurtbox.collision_mask = 2
	var hs := CollisionShape3D.new()
	var sph := SphereShape3D.new()
	sph.radius = 0.62
	hs.shape = sph
	hs.position.y = 0.35
	_hurtbox.add_child(hs)
	add_child(_hurtbox)
	home = global_position
	_goal = home


func _physics_process(delta: float) -> void:
	if _dead:
		return
	_think -= delta
	_snap_cool -= delta
	var player := get_tree().get_first_node_in_group("player") as Player
	var chasing := false
	var sees := player and player.global_position.distance_to(global_position) < 6.0 and absf(player.global_position.y - global_position.y) < 2.5 and home.distance_to(player.global_position) < wander + 4.0
	if sees and not _chasing:
		_chasing = true
		_alert = 0.7
		_visual.scale = Vector3(1.0, 1.35, 1.0)
		create_tween().tween_property(_visual, "scale", Vector3.ONE, 0.5).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
		Sound.play_at("crab_snap", global_position, -6.0, 1.3)
		if _anim and _anim.has_animation("snap"):
			_anim.play("snap")
			_anim.queue("walk")
	elif not sees:
		_chasing = false
	if _alert > 0.0:
		_alert -= delta
		velocity = Vector3(0, -1.0, 0)
		move_and_slide()
		if player:
			_heading = lerp_angle(_heading, atan2(player.global_position.x - global_position.x, player.global_position.z - global_position.z) + PI / 2.0, delta * 8.0)
			_visual.rotation.y = _heading
		for b in _hurtbox.get_overlapping_bodies():
			if b is Player:
				_touch(b)
		return
	if _chasing:
		_goal = player.global_position
		chasing = true
	elif _think <= 0.0:
		_think = randf_range(1.2, 2.6)
		var a := randf() * TAU
		_goal = home + Vector3(cos(a), 0, sin(a)) * randf() * wander
	var to := _goal - global_position
	to.y = 0
	var speed := 2.7 if chasing else 1.5
	var v := Vector3.ZERO
	if to.length() > 0.3:
		v = to.normalized() * speed
		# crabs walk sideways: face 90° off the direction of travel
		_heading = lerp_angle(_heading, atan2(v.x, v.z) + PI / 2.0, delta * 6.0)
	_visual.rotation.y = _heading
	velocity.x = v.x
	velocity.z = v.z
	velocity.y = -9.0 if not is_on_floor() else -1.0
	# never walk off the edge
	var ahead := global_position + v.normalized() * 0.8 + Vector3.UP * 0.5
	var q := PhysicsRayQueryParameters3D.create(ahead, ahead + Vector3.DOWN * 1.6, 1)
	if v != Vector3.ZERO and get_world_3d().direct_space_state.intersect_ray(q).is_empty():
		velocity.x = 0
		velocity.z = 0
		_goal = home
	move_and_slide()
	if chasing and _snap_cool <= 0.0 and player.global_position.distance_to(global_position) < 2.0:
		_snap_cool = 1.2
		if _anim and _anim.has_animation("snap"):
			_anim.play("snap")
			_anim.queue("walk")
		Sound.play_at("crab_snap", global_position, -4.0)
	for b in _hurtbox.get_overlapping_bodies():
		if b is Player:
			_touch(b)


func _touch(p: Player) -> void:
	if p.is_stomping_from_above(global_position.y + 0.55) or p.is_pounding():
		squash(p)
		p.bounce_off_enemy()
	else:
		p.damage(global_position)


func on_pound(where: Vector3, p: Node) -> void:
	if not _dead and where.distance_to(global_position) < 2.6:
		squash(p)


func on_block_bump(where: Vector3) -> void:
	if not _dead and where.distance_to(global_position) < 1.4:
		squash(null)


func squash(_by: Node) -> void:
	if _dead:
		return
	_dead = true
	Sound.play_at("enemy_stomp", global_position, 0.0)
	Fx.hitstop(0.05)
	Fx.dust(global_position, 6, 0.7, 0.3, 0.35)
	Fx.sparkle(global_position + Vector3.UP * 0.4, Color(1, 0.8, 0.5), 8, 3.5, 0.3, 0.5)
	if _anim and _anim.has_animation("squash"):
		_anim.play("squash")
	var tw := create_tween()
	tw.tween_property(_visual, "scale", Vector3(1.5, 0.2, 1.5), 0.08)
	tw.tween_interval(0.45)
	tw.tween_property(_visual, "scale", Vector3(0.01, 0.01, 0.01), 0.2)
	tw.tween_callback(func():
		var c := Coin.new()
		get_parent().add_child(c)
		c.global_position = global_position + Vector3.UP * 0.4
		c.launch(Vector3(0, 7, 0))
		get_tree().call_group("world", "on_crab_defeated", group_tag)
		queue_free())
