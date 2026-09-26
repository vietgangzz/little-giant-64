class_name SpringDrum
extends StaticBody3D
## A small bronze drum that bounces the hero high. Ground-pound onto it for a super bounce.

var power := 19.0
var _visual: Node3D


func _ready() -> void:
	collision_layer = 1
	collision_mask = 0
	var cs := CollisionShape3D.new()
	var cyl := CylinderShape3D.new()
	cyl.radius = 0.72
	cyl.height = 0.5
	cs.shape = cyl
	cs.position.y = 0.25
	add_child(cs)
	_visual = Props.make("drum_spring")
	add_child(_visual)


func on_player_touch(p: Player, n: Vector3) -> void:
	if n.y < 0.7:
		return
	var boosted := p.is_pounding()
	p.spring(Player.SUPER_SPRING_VELOCITY if boosted else power)
	Sound.play_at("spring", global_position, 0.0, 0.9 if boosted else 1.0)
	if boosted:
		Sound.play_at("drum_boom", global_position, -6.0, 1.3)
	Fx.ring(global_position + Vector3.UP * 0.55, Color(1, 0.9, 0.55, 1), 3.2 if boosted else 2.2, 0.4)
	Fx.sparkle(global_position + Vector3.UP * 0.6, Color(1, 0.85, 0.4), 8, 4.0, 0.3, 0.5)
	var tw := create_tween()
	_visual.scale = Vector3(1.25, 0.55, 1.25)
	tw.tween_property(_visual, "scale", Vector3.ONE, 0.45).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
