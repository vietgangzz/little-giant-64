class_name UiKit
extends RefCounted
## Fonts, label styles and the rainbow bouncing headline used across the UI.

const RAINBOW := [Color("#ff5a4e"), Color("#ffb03a"), Color("#ffe14d"), Color("#7ed957"), Color("#4fc3f7"), Color("#8f7cf7"), Color("#ff6fb1")]
const INK := Color("#09090b")
const LIME := Color("#d5f64b")
const ORANGE := Color("#ff7447")
const GOLD := Color("#f2c33d")

static var _display: Font
static var _body: Font


static func display_font() -> Font:
	if _display == null:
		_display = _find_font(["Baloo2-ExtraBold", "Baloo2", "Baloo", "Fredoka"], true)
	return _display


static func body_font() -> Font:
	if _body == null:
		_body = _find_font(["Nunito-ExtraBold", "Nunito-Bold", "BeVietnamPro-Bold", "Nunito", "BeVietnamPro"], false)
	return _body


static func _find_font(prefer: Array, bold: bool) -> Font:
	var files: Array[String] = []
	_collect_fonts("res://assets/fonts", files)
	for p in prefer:
		for f in files:
			if f.get_file().begins_with(p):
				return load(f)
	var sys := SystemFont.new()
	sys.font_names = PackedStringArray(["Avenir Next Rounded", "Arial Rounded MT Bold", "Helvetica Neue"])
	sys.font_weight = 800 if bold else 600
	return sys


static func _collect_fonts(path: String, out: Array[String]) -> void:
	var dir := DirAccess.open(path)
	if dir == null:
		return
	for f in dir.get_files():
		if f.ends_with(".ttf") or f.ends_with(".otf"):
			out.append(path + "/" + f)
	for d in dir.get_directories():
		_collect_fonts(path + "/" + d, out)


static func style(size: int, color := Color.WHITE, outline := 10, display := true, shadow := true) -> LabelSettings:
	var ls := LabelSettings.new()
	ls.font = display_font() if display else body_font()
	ls.font_size = size
	ls.font_color = color
	ls.outline_size = outline
	ls.outline_color = Color(0.05, 0.08, 0.2, 0.9) if outline > 0 else Color.TRANSPARENT
	if shadow:
		ls.shadow_size = 2
		ls.shadow_color = Color(0.0, 0.05, 0.2, 0.45)
		ls.shadow_offset = Vector2(0, size * 0.07)
	return ls


static func label(text: String, size: int, color := Color.WHITE, outline := 10, display := true) -> Label:
	var l := Label.new()
	l.text = text
	l.label_settings = style(size, color, outline, display)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	return l


## A headline where every letter has its own colour and bounces in, like the ALL STARS banner.
static func rainbow(text: String, size: int, parent: Control, stagger := 0.045, white_outline := true) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", int(-size * 0.04))
	parent.add_child(row)
	var i := 0
	for ch in text:
		var l := Label.new()
		l.text = ch
		var ls := style(size, RAINBOW[i % RAINBOW.size()] if ch != " " else Color.WHITE, int(size * 0.16), true)
		if white_outline:
			ls.outline_color = Color.WHITE
			ls.shadow_color = Color(0.05, 0.1, 0.3, 0.55)
			ls.shadow_size = int(size * 0.05)
			ls.shadow_offset = Vector2(0, size * 0.08)
		l.label_settings = ls
		l.pivot_offset = Vector2(size * 0.3, size * 0.6)
		row.add_child(l)
		l.modulate.a = 0.0
		l.scale = Vector2(0.2, 0.2)
		var tw := l.create_tween()
		tw.tween_interval(stagger * i)
		tw.tween_property(l, "modulate:a", 1.0, 0.08)
		tw.parallel().tween_property(l, "scale", Vector2.ONE, 0.5).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
		if ch != " ":
			i += 1
	return row


## Keeps the letters of a rainbow headline bobbing in a wave.
static func wave(row: HBoxContainer, t: float, amp := 6.0) -> void:
	var i := 0
	for l in row.get_children():
		(l as Control).position.y = sin(t * 5.0 - i * 0.55) * amp
		i += 1


static func pill(text: String, size := 30) -> PanelContainer:
	var p := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.03, 0.05, 0.1, 0.62)
	sb.set_corner_radius_all(18)
	sb.content_margin_left = 26
	sb.content_margin_right = 26
	sb.content_margin_top = 10
	sb.content_margin_bottom = 12
	p.add_theme_stylebox_override("panel", sb)
	var l := label(text, size, Color.WHITE, 0, false)
	l.name = "Text"
	p.add_child(l)
	return p
