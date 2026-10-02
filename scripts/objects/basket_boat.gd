class_name BasketBoat
extends AnimatableBody3D
## A round bamboo basket boat (thúng chai) spinning on the spot, the way the Cẩm Thanh
## boatmen show off. Stand in it and it carries you round; it bobs on the swell and dips a
## little under your weight.

var spin := 1.2 ## radians per second (negative spins the other way)
var phase := 0.0
var floor_y := 0.30 ## where the hero stands (the woven floor of the prop)
var radius := 1.05
var _t := 0.0
var _visual: Node3D
var _base: Vector3
var _sink := 0.0
var _sensor: Area3D
var _riders := 0


func _ready() -> void:
	add_to_group("unsafe")
	sync_to_physics = false
	collision_layer = 8
	collision_mask = 0
	var cs := CollisionShape3D.new()
	var cyl := CylinderShape3D.new()
	cyl.radius = radius
	cyl.height = 0.3
	cs.shape = cyl
	cs.position.y = floor_y - 0.15
	add_child(cs)
	_visual = Props.make("basket_boat")
	add_child(_visual)
	_sensor = Area3D.new()
	_sensor.collision_layer = 0
	_sensor.collision_mask = 2
	var ss := CollisionShape3D.new()
	var sc := CylinderShape3D.new()
	sc.radius = radius
	sc.height = 0.8
	ss.shape = sc
	ss.position.y = floor_y + 0.4
	_sensor.add_child(ss)
	add_child(_sensor)
	_sensor.body_entered.connect(func(_b): _riders += 1)
	_sensor.body_exited.connect(func(_b): _riders = maxi(_riders - 1, 0))
	_base = position
	_t = phase


func _physics_process(delta: float) -> void:
	_t += delta
	_sink = move_toward(_sink, 0.12 if _riders > 0 else 0.0, delta * 0.6)
	position = _base + Vector3(0, sin(_t * 1.5 + phase) * 0.07 - _sink, 0)
	rotation.y += spin * delta
	_visual.rotation.x = sin(_t * 1.2 + phase) * 0.05
	_visual.rotation.z = cos(_t * 1.0 + phase) * 0.05
