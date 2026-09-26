class_name Block
extends StaticBody3D
## Drum blocks ("?" blocks) pay out coins when bonked from below; terracotta bricks shatter when
## bonked or ground-pounded from above.

enum Type { DRUM, BRICK }

var type := Type.DRUM
var coins := 1
var _visual: Node3D
var _used := false


func _ready() -> void:
	add_to_group("poundable")
	collision_layer = 1
	collision_mask = 0
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(1, 1, 1)
	cs.shape = box
	cs.position.y = 0.5
	add_child(cs)
	_visual = Props.make("drum_block" if type == Type.DRUM else "brick_block")
	add_child(_visual)


func on_player_head(_p: Node) -> void:
	_bump()


func on_pound(where: Vector3, _p: Node) -> void:
	var top := global_position.y + 1.0
	var d := Vector2(where.x - global_position.x, where.z - global_position.z).length()
	if type == Type.BRICK and d < 0.95 and absf(where.y - top) < 0.35:
		_break()


func _bump() -> void:
	if _used:
		Sound.play_at("block_hit", global_position, -4.0, 0.8)
		return
	var tw := create_tween()
	tw.tween_property(_visual, "position:y", 0.35, 0.07).set_ease(Tween.EASE_OUT)
	tw.tween_property(_visual, "position:y", 0.0, 0.14).set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_BOUNCE)
	Sound.play_at("block_hit", global_position, -1.0)
	get_tree().call_group("crab", "on_block_bump", global_position)
	if type == Type.BRICK:
		_break()
		return
	for i in coins:
		var c := Coin.new()
		get_parent().add_child(c)
		c.global_position = global_position + Vector3(0, 1.1, 0)
		var a := TAU * i / maxf(coins, 1) + randf() * 0.3
		c.launch(Vector3(cos(a) * (1.6 if coins > 1 else 0.0), 9.0, sin(a) * (1.6 if coins > 1 else 0.0)))
	coins = 0
	_used = true
	Fx.sparkle(global_position + Vector3(0, 1.1, 0), Color(1, 0.85, 0.4), 10, 4.0, 0.35, 0.5)
	var old := _visual
	_visual = Props.make("used_block")
	add_child(_visual)
	old.queue_free()


func _break() -> void:
	Sound.play_at("block_break", global_position, 0.0)
	Fx.shake(0.12, 0.12)
	for i in 8:
		var chunk := MeshInstance3D.new()
		var b := BoxMesh.new()
		b.size = Vector3.ONE * randf_range(0.22, 0.34)
		chunk.mesh = b
		chunk.material_override = Fx.toon_material(Color("#c8643c"))
		get_parent().add_child(chunk)
		chunk.global_position = global_position + Vector3(randf_range(-0.3, 0.3), randf_range(0.3, 0.8), randf_range(-0.3, 0.3))
		var dir := Vector3(randf_range(-1, 1), randf_range(0.8, 1.6), randf_range(-1, 1))
		var tw := chunk.create_tween().set_parallel(true)
		var end := chunk.global_position + dir * 2.2 + Vector3.DOWN * 3.0
		tw.tween_property(chunk, "global_position:x", end.x, 0.7)
		tw.tween_property(chunk, "global_position:z", end.z, 0.7)
		tw.tween_property(chunk, "global_position:y", chunk.global_position.y + 1.5, 0.25).set_ease(Tween.EASE_OUT)
		tw.tween_property(chunk, "global_position:y", end.y, 0.45).set_delay(0.25).set_ease(Tween.EASE_IN)
		tw.tween_property(chunk, "rotation", Vector3(randf() * 8, randf() * 8, randf() * 8), 0.7)
		tw.tween_property(chunk, "scale", Vector3.ONE * 0.05, 0.3).set_delay(0.4)
		tw.chain().tween_callback(chunk.queue_free)
	Fx.dust(global_position + Vector3.UP * 0.5, 6, 0.8, 0.4, 0.4, Color(0.95, 0.8, 0.7, 0.9))
	if coins > 0:
		var c := Coin.new()
		get_parent().add_child(c)
		c.global_position = global_position + Vector3(0, 0.6, 0)
		c.launch(Vector3(0, 7, 0))
	queue_free()
