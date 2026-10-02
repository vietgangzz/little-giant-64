class_name PauseMenu
extends CanvasLayer
## Pause: the star list with hints, settings, and a way back to the title.

var root: Control
var _list: VBoxContainer
var _items: Array = [] ## [Label, Callable]
var _index := 0


func _ready() -> void:
	layer = 30
	process_mode = Node.PROCESS_MODE_ALWAYS
	visible = false
	root = Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(root)
	var dim := ColorRect.new()
	dim.color = Color(0.02, 0.03, 0.08, 0.62)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(dim)
	var h := HBoxContainer.new()
	h.set_anchors_preset(Control.PRESET_FULL_RECT)
	h.offset_left = 120
	h.offset_right = -120
	h.offset_top = 70
	h.offset_bottom = -70
	h.add_theme_constant_override("separation", 80)
	root.add_child(h)
	_list = VBoxContainer.new()
	_list.custom_minimum_size = Vector2(620, 0)
	_list.add_theme_constant_override("separation", 2)
	h.add_child(_list)
	var stars := VBoxContainer.new()
	stars.name = "Stars"
	stars.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	stars.add_theme_constant_override("separation", 10)
	h.add_child(stars)


func open() -> void:
	visible = true
	Game.paused = true
	get_tree().paused = true
	Sound.muffle(true)
	Sound.play("pause", -4.0)
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	_show_hud(false) # the menu has its own counts; the HUD would sit under PAUSED
	_index = 0
	_rebuild()


func close() -> void:
	visible = false
	Game.paused = false
	get_tree().paused = false
	Sound.muffle(false)
	_show_hud(true)
	Game.save()


func _show_hud(on: bool) -> void:
	for h in get_tree().get_nodes_in_group("hud"):
		h.visible = on


func _rebuild() -> void:
	for c in _list.get_children():
		c.queue_free()
	_items.clear()
	_list.add_child(UiKit.label(Game.t("PAUSED", "TẠM DỪNG"), 84, UiKit.LIME, 12))
	var onoff := func(b: bool) -> String: return Game.t("On", "Bật") if b else Game.t("Off", "Tắt")
	_add(Game.t("Resume", "Chơi tiếp"), close)
	_add(Game.t("Cape: ", "Áo choàng: ") + onoff.call(Game.cape), func():
		Game.cape = not Game.cape
		get_tree().call_group("player", "set_cape", Game.cape))
	_add(Game.t("Music: ", "Nhạc: ") + "%d%%" % int(Game.music_volume * 100), func():
		Game.music_volume = fmod(Game.music_volume + 0.2, 1.2) if Game.music_volume < 0.99 else 0.0
		Game.music_volume = snappedf(Game.music_volume, 0.2)
		Sound.apply_volumes())
	_add(Game.t("Sound: ", "Âm thanh: ") + "%d%%" % int(Game.sfx_volume * 100), func():
		Game.sfx_volume = fmod(Game.sfx_volume + 0.2, 1.2) if Game.sfx_volume < 0.99 else 0.0
		Game.sfx_volume = snappedf(Game.sfx_volume, 0.2)
		Sound.apply_volumes())
	_add(Game.t("Camera speed: ", "Tốc độ camera: ") + "%.1f×" % Game.mouse_sensitivity, func():
		var speeds := [0.6, 0.8, 1.0, 1.3, 1.6]
		var i := speeds.find(snappedf(Game.mouse_sensitivity, 0.1))
		Game.mouse_sensitivity = speeds[(i + 1) % speeds.size()])
	_add(Game.t("Invert camera X: ", "Đảo camera X: ") + onoff.call(Game.invert_x), func(): Game.invert_x = not Game.invert_x)
	_add(Game.t("Invert camera Y: ", "Đảo camera Y: ") + onoff.call(Game.invert_y), func(): Game.invert_y = not Game.invert_y)
	_add(Game.t("Language: English", "Ngôn ngữ: Tiếng Việt"), Game.toggle_language)
	for other in Game.LEVEL_ORDER:
		if other == Game.level:
			continue
		_add(Game.t("Sail to ", "Đi ") + Game.level_name(other), func():
			close()
			Game.travel(other))
	_add(Game.t("Quit to title", "Về màn hình chính"), func():
		close()
		get_tree().call_group("main", "back_to_title"))
	_highlight()
	var stars := root.find_child("Stars", true, false) as VBoxContainer
	for c in stars.get_children():
		c.queue_free()
	stars.add_child(UiKit.label("%s   %d / %d" % [Game.level_name(), Game.level_star_count(), Game.level_star_total()], 52, UiKit.GOLD, 10))
	for s in Game.level_stars():
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 14)
		var icon := HudIcon.new(HudIcon.Kind.STAR, 44)
		icon.filled = Game.has_star(s["id"])
		row.add_child(icon)
		var col := VBoxContainer.new()
		col.add_theme_constant_override("separation", -4)
		var name := UiKit.label(s[Game.lang], 32, Color.WHITE if icon.filled else Color(0.85, 0.88, 0.95), 8)
		name.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
		col.add_child(name)
		var hint := UiKit.label(s["hint_" + Game.lang], 22, Color(0.75, 0.82, 0.92), 0, false)
		hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
		col.add_child(hint)
		row.add_child(col)
		stars.add_child(row)
	var what := Game.red_name()
	var red := UiKit.label("%s  %d / 8    ·    %s  %d    ·    %s  %d / %d" % [what, Game.red_coins, Game.t("Coins", "Đồng xu"), Game.coins, Game.t("All stars", "Tổng sao"), Game.star_count(), Game.STARS.size()], 26, Color("#ffc9b8"), 6, false)
	red.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	stars.add_child(red)


func _add(text: String, action: Callable) -> void:
	var l := UiKit.label(text, 38, Color.WHITE, 8)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	l.mouse_filter = Control.MOUSE_FILTER_STOP
	_list.add_child(l)
	_items.append([l, action])


func _highlight() -> void:
	# finger-sized on phones, but the whole list must clear the home-indicator edge
	var k := (1.2 if _items.size() <= 9 else 1.07) if Game.touch_mode else 1.0
	for i in _items.size():
		var sel := i == _index
		(_items[i][0] as Label).label_settings = UiKit.style(int((44 if sel else 36) * k), UiKit.LIME if sel else Color(1, 1, 1, 0.85), 10 if sel else 6)


func _activate() -> void:
	Sound.play("menu_select", -4.0)
	var keep := _index
	(_items[_index][1] as Callable).call()
	if visible:
		_rebuild()
		_index = keep
		_highlight()


func _unhandled_input(event: InputEvent) -> void:
	if not visible:
		return
	if event.is_action_pressed("pause"):
		close()
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("move_forward") or event.is_action_pressed("ui_up"):
		_index = (_index + _items.size() - 1) % _items.size()
		_highlight()
		Sound.play("menu_move", -8.0)
	elif event.is_action_pressed("move_back") or event.is_action_pressed("ui_down"):
		_index = (_index + 1) % _items.size()
		_highlight()
		Sound.play("menu_move", -8.0)
	elif event.is_action_pressed("ui_confirm") or event.is_action_pressed("ui_accept"):
		get_viewport().set_input_as_handled()
		_activate()


## Clicks and taps are read before the GUI (the dimmer would swallow them). A phone tap
## arrives both as a touch and as an emulated click, so touch mode only listens to the touch.
func _input(event: InputEvent) -> void:
	if not visible:
		return
	var tap := false
	if Game.touch_mode:
		tap = event is InputEventScreenTouch and event.pressed
	else:
		tap = event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT
	if not tap:
		return
	for i in _items.size():
		if (_items[i][0] as Label).get_global_rect().grow(10).has_point(event.position):
			get_viewport().set_input_as_handled()
			_index = i
			_activate()
			return
