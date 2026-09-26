class_name TitleScreen
extends CanvasLayer
## The title: the world turning slowly behind a rainbow logo, Little Giant waving on the drum.

signal start_game

var root: Control
var _row: HBoxContainer
var _menu: VBoxContainer
var _items: Array[Label] = []
var _index := 0
var _t := 0.0
var _press: Label


func _ready() -> void:
	layer = 20
	root = Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(root)
	var v := VBoxContainer.new()
	v.anchor_left = 0.5
	v.anchor_right = 0.5
	v.offset_left = -900
	v.offset_right = 900
	v.offset_top = 46
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_theme_constant_override("separation", -26)
	root.add_child(v)
	_row = UiKit.rainbow("LITTLE GIANT 64", 150, v, 0.06, true, 13)
	var sub := UiKit.label(Game.level_name(), 46, Color("#fffbe8"), 10)
	sub.name = "Sub"
	v.add_child(sub)
	_menu = VBoxContainer.new()
	_menu.anchor_left = 0.5
	_menu.anchor_right = 0.5
	_menu.anchor_top = 1.0
	_menu.anchor_bottom = 1.0
	_menu.offset_left = -300
	_menu.offset_right = 300
	_menu.offset_top = -330
	_menu.offset_bottom = -90
	_menu.alignment = BoxContainer.ALIGNMENT_CENTER
	_menu.add_theme_constant_override("separation", 6)
	root.add_child(_menu)
	_build_menu()
	var credit := UiKit.label("VG TEAM · Blender · Godot", 22, Color(1, 1, 1, 0.75), 6, false)
	credit.anchor_top = 1.0
	credit.anchor_bottom = 1.0
	credit.anchor_right = 1.0
	credit.offset_top = -56
	credit.offset_left = 24
	credit.offset_right = -28
	credit.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	root.add_child(credit)
	Game.language_changed.connect(_rebuild)


func _build_menu() -> void:
	for c in _menu.get_children():
		c.queue_free()
	_items.clear()
	var entries := [
		Game.t("Continue", "Chơi tiếp") if Game.star_count() > 0 else Game.t("Start", "Bắt đầu"),
		Game.t("Language: English", "Ngôn ngữ: Tiếng Việt"),
		Game.t("Quit", "Thoát"),
	]
	for e in entries:
		var l := UiKit.label(e, 44, Color.WHITE, 10)
		_menu.add_child(l)
		_items.append(l)
	var hint := UiKit.label(Game.t("WASD move · Space jump ×2 · Shift dash · Ctrl pound · Q/E/mouse camera", "WASD di chuyển · Space nhảy ×2 · Shift lướt · Ctrl dậm · Q/E/chuột xoay"), 22, Color(1, 1, 1, 0.8), 6, false)
	_menu.add_child(hint)
	_highlight()


func _rebuild() -> void:
	(root.find_child("Sub", true, false) as Label).text = Game.level_name()
	_build_menu()


func _highlight() -> void:
	for i in _items.size():
		var sel := i == _index
		_items[i].label_settings = UiKit.style(52 if sel else 40, UiKit.LIME if sel else Color(1, 1, 1, 0.85), 12 if sel else 8)


func _process(delta: float) -> void:
	_t += delta
	UiKit.wave(_row, _t, 8.0)


func _unhandled_input(event: InputEvent) -> void:
	if not visible:
		return
	if event.is_action_pressed("move_forward") or event.is_action_pressed("ui_up"):
		_index = (_index + _items.size() - 1) % _items.size()
		_highlight()
		Sound.play("menu_move", -6.0)
	elif event.is_action_pressed("move_back") or event.is_action_pressed("ui_down"):
		_index = (_index + 1) % _items.size()
		_highlight()
		Sound.play("menu_move", -6.0)
	elif event.is_action_pressed("ui_confirm") or event.is_action_pressed("ui_accept"):
		get_viewport().set_input_as_handled()
		Sound.play("menu_select", -3.0)
		match _index:
			0:
				start_game.emit()
			1:
				Game.toggle_language()
			2:
				get_tree().quit()
	elif event is InputEventMouseButton and event.pressed:
		for i in _items.size():
			if _items[i].get_global_rect().has_point(event.position):
				_index = i
				_highlight()
				Input.action_press("ui_confirm")
				Input.action_release("ui_confirm")
				var ev := InputEventAction.new()
				ev.action = "ui_confirm"
				ev.pressed = true
				_unhandled_input(ev)
