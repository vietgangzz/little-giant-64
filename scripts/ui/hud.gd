class_name Hud
extends CanvasLayer
## In-game overlay: coin and star counters (top-left, as in SM64), health pebbles (top-right),
## red-lantern popups, caption toasts, the STAR GET / ALL STARS banners, fades and the ending card.

var root: Control
var coin_label: Label
var star_label: Label
var hearts: Array[HudIcon] = []
var red_box: HBoxContainer
var red_label: Label
var toast_box: VBoxContainer
var fader: ColorRect
var banner: Control
var _banner_row: HBoxContainer
var _t := 0.0
var _coin_shown := 0.0
var _coin_bump := 0.0
var _star_bump := 0.0
var ending: Control


func _ready() -> void:
	add_to_group("hud")
	layer = 10
	root = Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if Game.touch_mode:
		# keep the counters clear of the rounded corners, the Dynamic Island and the iPhone Duo's
		# front camera, which sits in the top-left corner of the unfolded screen (canvas x 83-187).
		# The right side only has to clear the corner: the pause button sits left of the pips.
		root.offset_left = 190
		root.offset_right = -70
	add_child(root)
	_build_counters()
	_build_hearts()
	_build_red()
	toast_box = VBoxContainer.new()
	toast_box.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	toast_box.anchor_left = 0.5
	toast_box.anchor_right = 0.5
	toast_box.anchor_top = 1.0
	toast_box.anchor_bottom = 1.0
	toast_box.offset_left = -500
	toast_box.offset_right = 500
	toast_box.offset_top = -170
	toast_box.offset_bottom = -60
	toast_box.alignment = BoxContainer.ALIGNMENT_END
	toast_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(toast_box)
	banner = Control.new()
	banner.set_anchors_preset(Control.PRESET_FULL_RECT)
	banner.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(banner)
	fader = ColorRect.new()
	fader.color = Color(0.035, 0.035, 0.043, 0.0)
	fader.set_anchors_preset(Control.PRESET_FULL_RECT)
	fader.mouse_filter = Control.MOUSE_FILTER_IGNORE
	# the fade covers the whole screen, past the phone inset
	fader.offset_left = -root.offset_left
	fader.offset_right = -root.offset_right
	root.add_child(fader)
	Game.coins_changed.connect(func(_c): _coin_bump = 1.0)
	Game.star_collected.connect(func(_id): _star_bump = 1.0)
	Game.health_changed.connect(_on_health)
	_on_health(Game.hp)


func _build_counters() -> void:
	var box := VBoxContainer.new()
	box.position = Vector2(42, 30)
	box.add_theme_constant_override("separation", -6)
	root.add_child(box)
	var row1 := HBoxContainer.new()
	row1.add_theme_constant_override("separation", 10)
	row1.add_child(HudIcon.new(HudIcon.Kind.COIN, 64))
	coin_label = UiKit.label("× 0", 52, Color.WHITE, 10)
	coin_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	row1.add_child(coin_label)
	box.add_child(row1)
	var row2 := HBoxContainer.new()
	row2.add_theme_constant_override("separation", 10)
	row2.add_child(HudIcon.new(HudIcon.Kind.STAR, 64))
	star_label = UiKit.label("× 0", 52, Color.WHITE, 10)
	star_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	row2.add_child(star_label)
	box.add_child(row2)


func _build_hearts() -> void:
	var box := HBoxContainer.new()
	box.anchor_left = 1.0
	box.anchor_right = 1.0
	box.offset_left = -260
	box.offset_right = -36
	box.offset_top = 34
	box.alignment = BoxContainer.ALIGNMENT_END
	box.add_theme_constant_override("separation", 8)
	root.add_child(box)
	for i in Game.MAX_HP:
		var h := HudIcon.new(HudIcon.Kind.HEART, 62)
		box.add_child(h)
		hearts.append(h)


func _build_red() -> void:
	red_box = HBoxContainer.new()
	red_box.anchor_left = 0.5
	red_box.anchor_right = 0.5
	red_box.offset_left = -150
	red_box.offset_right = 150
	red_box.offset_top = 40
	red_box.alignment = BoxContainer.ALIGNMENT_CENTER
	red_box.add_theme_constant_override("separation", 10)
	red_box.modulate.a = 0.0
	root.add_child(red_box)
	red_box.add_child(HudIcon.new({"halong": HudIcon.Kind.PEARL, "danang": HudIcon.Kind.LOTUS}.get(Game.level, HudIcon.Kind.LANTERN), 60))
	red_label = UiKit.label("0 / %d" % Game.RED_COIN_TOTAL, 48, Color("#ffd0c4"), 10)
	red_box.add_child(red_label)


func _process(delta: float) -> void:
	_t += delta
	_coin_shown = move_toward(_coin_shown, Game.coins, maxf(40.0 * delta, 1.0))
	coin_label.text = "× %d  / %d" % [int(_coin_shown), Game.coin_total] if Game.coin_total > 0 else "× %d" % int(_coin_shown)
	star_label.text = "× %d  / %d" % [Game.level_star_count(), Game.level_star_total()]
	_coin_bump = move_toward(_coin_bump, 0.0, delta * 5.0)
	_star_bump = move_toward(_star_bump, 0.0, delta * 2.0)
	coin_label.scale = Vector2.ONE * (1.0 + _coin_bump * 0.12)
	star_label.scale = Vector2.ONE * (1.0 + _star_bump * 0.25)
	if _banner_row:
		UiKit.wave(_banner_row, _t, 7.0)


func _on_health(hp: int) -> void:
	for i in hearts.size():
		hearts[i].filled = i < hp
		hearts[i].queue_redraw()
		if i == hp:
			var tw := hearts[i].create_tween()
			hearts[i].pivot_offset = hearts[i].size * 0.5
			hearts[i].scale = Vector2(1.4, 1.4)
			tw.tween_property(hearts[i], "scale", Vector2.ONE, 0.3)


func show_red(count: int) -> void:
	red_label.text = "%d / %d" % [count, Game.RED_COIN_TOTAL]
	var tw := red_box.create_tween()
	red_box.modulate.a = 1.0
	red_box.pivot_offset = Vector2(150, 30)
	red_box.scale = Vector2(1.3, 1.3)
	tw.tween_property(red_box, "scale", Vector2.ONE, 0.25)
	tw.tween_interval(2.2)
	tw.tween_property(red_box, "modulate:a", 0.0, 0.5)


func toast(text: String, seconds := 3.0) -> void:
	if Game.args.has("trailer"):
		return # the demo video is shown without caption lines
	var p := UiKit.pill(text, 30)
	p.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	toast_box.add_child(p)
	p.modulate.a = 0.0
	var tw := p.create_tween()
	tw.tween_property(p, "modulate:a", 1.0, 0.2)
	tw.tween_interval(seconds)
	tw.tween_property(p, "modulate:a", 0.0, 0.4)
	tw.tween_callback(p.queue_free)


func _clear_banner() -> void:
	for c in banner.get_children():
		c.queue_free()
	_banner_row = null


func star_banner(id: String, first: bool) -> void:
	_clear_banner()
	var v := VBoxContainer.new()
	v.set_anchors_preset(Control.PRESET_CENTER_TOP)
	v.anchor_left = 0.5
	v.anchor_right = 0.5
	v.offset_left = -700
	v.offset_right = 700
	v.offset_top = 120
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	banner.add_child(v)
	_banner_row = UiKit.rainbow(Game.t("STAR GET!", "CÓ SAO RỒI!"), 120, v)
	var name := UiKit.label(Game.star_name(id), 46, Color("#fff6d8"), 10)
	v.add_child(name)
	if not first:
		v.add_child(UiKit.label(Game.t("(already found)", "(đã có rồi)"), 28, Color(0.8, 0.9, 1.0), 6, false))
	name.modulate.a = 0.0
	name.create_tween().tween_property(name, "modulate:a", 1.0, 0.4).set_delay(0.5)
	var tw := v.create_tween()
	tw.tween_interval(3.0)
	tw.tween_property(v, "modulate:a", 0.0, 0.5)
	tw.tween_callback(_clear_banner)


func all_stars_banner(text := "ALL STARS!") -> void:
	_clear_banner()
	var v := VBoxContainer.new()
	v.anchor_left = 0.5
	v.anchor_right = 0.5
	v.offset_left = -800
	v.offset_right = 800
	v.offset_top = 70
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	banner.add_child(v)
	_banner_row = UiKit.rainbow(text, 170 if text.length() <= 11 else 120, v, 0.07)
	var sub := UiKit.label("★ %d %s ★" % [Game.coins, Game.t("coins!", "đồng xu!")], 48, Color("#fff1b8"), 10)
	v.add_child(sub)
	sub.modulate.a = 0.0
	sub.create_tween().tween_property(sub, "modulate:a", 1.0, 0.5).set_delay(1.0)


func fade(alpha: float, seconds := 0.5) -> void:
	create_tween().tween_property(fader, "color:a", alpha, seconds)


## The closing title card, in the studio's ink colour.
func ending_card() -> void:
	fade(0.94, 1.6)
	await get_tree().create_timer(1.4).timeout
	_clear_banner()
	ending = VBoxContainer.new()
	ending.set_anchors_preset(Control.PRESET_FULL_RECT)
	(ending as VBoxContainer).alignment = BoxContainer.ALIGNMENT_CENTER
	(ending as VBoxContainer).add_theme_constant_override("separation", 14)
	root.add_child(ending)
	var title := UiKit.label("LITTLE GIANT: STAR HOP", 104, Color("#f5f1e6"), 0)
	title.label_settings.shadow_size = 0
	ending.add_child(title)
	var sub := UiKit.label(Game.level_name(), 40, UiKit.LIME, 0)
	ending.add_child(sub)
	var line := ColorRect.new()
	line.color = Color(1, 1, 1, 0.35)
	line.custom_minimum_size = Vector2(120, 2)
	line.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	ending.add_child(line)
	var trailer := Game.args.has("trailer")
	if not trailer:
		ending.add_child(UiKit.label(Game.t("Made with ♥ by VG TEAM · Blender · Godot", "Làm bằng ♥ bởi VG TEAM · Blender · Godot"), 34, Color(0.92, 0.92, 0.9), 0, false))
	var mins := int(Game.play_time) / 60
	var secs := int(Game.play_time) % 60
	ending.add_child(UiKit.label("%d ★   ·   %d %s   ·   %d:%02d" % [Game.level_star_count(), Game.coins, Game.t("coins", "đồng xu"), mins, secs], 30, Color(0.75, 0.78, 0.82), 0, false))
	var hint := UiKit.label(Game.t("Press Jump to keep exploring", "Bấm Nhảy để tiếp tục khám phá"), 26, Color(0.6, 0.65, 0.7), 0, false)
	if Game.touch_mode:
		hint.text = Game.t("Tap to keep exploring", "Chạm để tiếp tục khám phá")
	if not trailer:
		ending.add_child(hint)
	ending.modulate.a = 0.0
	ending.create_tween().tween_property(ending, "modulate:a", 1.0, 1.2)
	Sound.music("ending", 2.0)
	set_process_unhandled_input(true)


func _unhandled_input(event: InputEvent) -> void:
	var tap: bool = Game.touch_mode and event is InputEventScreenTouch and event.pressed
	if ending and ending.modulate.a > 0.9 and (event.is_action_pressed("jump") or tap):
		var e := ending
		ending = null
		var tw := e.create_tween()
		tw.tween_property(e, "modulate:a", 0.0, 0.6)
		tw.tween_callback(e.queue_free)
		fade(0.0, 1.0)
		get_tree().call_group("main", "resume_after_ending")
