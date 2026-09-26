class_name Checkpoint
extends Area3D
## A VGANG flag. Touch it to set where you come back after losing all your health.

var _visual: Node3D
var _active := false
var _flag: MeshInstance3D
var _base: Array[Color] = []


func _ready() -> void:
	add_to_group("checkpoint")
	collision_layer = 0
	collision_mask = 2
	monitorable = false
	var cs := CollisionShape3D.new()
	var cyl := CylinderShape3D.new()
	cyl.radius = 1.3
	cyl.height = 3.0
	cs.shape = cyl
	cs.position.y = 1.5
	add_child(cs)
	_visual = Props.make("checkpoint")
	add_child(_visual)
	for mi in Props._meshes(_visual):
		if mi.name.to_lower().contains("flag") and not mi.name.to_lower().contains("pole"):
			_flag = mi
			var m := ShaderMaterial.new()
			m.shader = preload("res://shaders/flag.gdshader")
			var base := mi.get_active_material(0)
			var col := Color("#d5f64b")
			if base is ShaderMaterial:
				col = (base as ShaderMaterial).get_shader_parameter("albedo")
			m.set_shader_parameter("albedo", col.darkened(0.25))
			m.set_shader_parameter("amplitude", 0.06)
			m.set_shader_parameter("pole_x", mi.get_aabb().position.x)
			m.set_shader_parameter("cloth_length", mi.get_aabb().size.x)
			for s in mi.mesh.get_surface_count():
				var orig := mi.get_active_material(s)
				var mm := m.duplicate() as ShaderMaterial
				var c: Color = col
				if orig is ShaderMaterial:
					c = (orig as ShaderMaterial).get_shader_parameter("albedo")
				_base.append(c)
				mi.set_surface_override_material(s, mm)
			_set_lit(false)
	body_entered.connect(_on_body)


func _on_body(b: Node) -> void:
	if not b is Player:
		return
	(b as Player).set_checkpoint(global_position + Vector3(0, 0.3, 1.2).rotated(Vector3.UP, rotation.y))
	Game.heal(3)
	if _active:
		return
	get_tree().call_group("checkpoint", "_deactivate")
	_active = true
	Sound.play("checkpoint", -2.0)
	Fx.sparkle(global_position + Vector3.UP * 2.4, Color(0.85, 1.0, 0.4), 14, 4.0, 0.35, 0.7)
	Fx.ring(global_position + Vector3.UP * 0.1, Color(0.85, 1.0, 0.5, 1), 3.5, 0.5)
	_set_lit(true)


func _deactivate() -> void:
	_active = false
	_set_lit(false)


func _set_lit(on: bool) -> void:
	if _flag == null:
		return
	for s in _flag.mesh.get_surface_count():
		var m := _flag.get_surface_override_material(s) as ShaderMaterial
		if m:
			var c: Color = _base[s] if s < _base.size() else Color("#d5f64b")
			m.set_shader_parameter("albedo", c if on else c.darkened(0.3))
			m.set_shader_parameter("amplitude", 0.14 if on else 0.06)
