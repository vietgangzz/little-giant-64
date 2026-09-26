class_name HudIcon
extends Control
## Hand-drawn HUD icons: the đồng xu coin, the bronze star, a red lantern and a health pip.

enum Kind { COIN, STAR, LANTERN, HEART, PEARL }

var kind := Kind.COIN
var filled := true
var spin := 0.0


func _init(k := Kind.COIN, s := 64.0) -> void:
	kind = k
	custom_minimum_size = Vector2(s, s)
	size = Vector2(s, s)


func _draw() -> void:
	var s := size
	var c := s * 0.5
	var r := minf(s.x, s.y) * 0.46
	match kind:
		Kind.COIN:
			var squeeze := absf(cos(spin)) * 0.75 + 0.25
			_ellipse(c + Vector2(0, 3), Vector2(r * squeeze, r), Color(0.05, 0.08, 0.2, 0.5))
			_ellipse(c, Vector2(r * squeeze, r), Color("#b07a1c"))
			_ellipse(c, Vector2(r * squeeze * 0.86, r * 0.86), Color("#f2c33d"))
			_ellipse(c - Vector2(r * 0.12 * squeeze, r * 0.12), Vector2(r * squeeze * 0.55, r * 0.55), Color("#ffe07a"))
			var h := r * 0.26
			draw_rect(Rect2(c - Vector2(h * squeeze, h), Vector2(h * 2.0 * squeeze, h * 2.0)), Color("#9c6512"))
		Kind.STAR:
			_star(c + Vector2(0, 3), r, 12, 0.62, Color(0.05, 0.08, 0.2, 0.5))
			_star(c, r, 12, 0.62, Color("#a8661b") if filled else Color(0.3, 0.35, 0.45, 0.6))
			_star(c, r * 0.84, 12, 0.6, Color("#f2b33d") if filled else Color(0.5, 0.55, 0.65, 0.5))
			draw_circle(c, r * 0.34, Color("#ffe07a") if filled else Color(0.6, 0.65, 0.75, 0.4))
			draw_arc(c, r * 0.46, 0, TAU, 32, Color("#a8661b") if filled else Color(0.35, 0.4, 0.5, 0.5), 2.0)
		Kind.LANTERN:
			_ellipse(c + Vector2(0, 3), Vector2(r * 0.72, r * 0.82), Color(0.05, 0.08, 0.2, 0.45))
			_ellipse(c, Vector2(r * 0.72, r * 0.82), Color("#e0452b") if filled else Color(0.4, 0.4, 0.5, 0.5))
			_ellipse(c, Vector2(r * 0.34, r * 0.8), Color("#ff6a4a") if filled else Color(0.5, 0.5, 0.6, 0.5))
			draw_rect(Rect2(c + Vector2(-r * 0.35, -r * 0.95), Vector2(r * 0.7, r * 0.2)), Color("#f2b33d"))
			draw_rect(Rect2(c + Vector2(-r * 0.35, r * 0.75), Vector2(r * 0.7, r * 0.2)), Color("#f2b33d"))
		Kind.PEARL:
			draw_circle(c + Vector2(0, 3), r * 0.8, Color(0.05, 0.08, 0.2, 0.45))
			draw_circle(c, r * 0.8, Color("#e9e4ff") if filled else Color(0.5, 0.5, 0.6, 0.5))
			draw_circle(c - Vector2(r * 0.22, r * 0.22), r * 0.3, Color(1, 1, 1, 0.95))
			draw_arc(c, r * 0.9, PI * 0.1, PI * 1.1, 24, UiKit.GOLD, 4.0)
		Kind.HEART:
			# a tiny Little Giant pebble: lime when full, grey when lost
			var col := UiKit.LIME if filled else Color(0.35, 0.4, 0.5, 0.55)
			_ellipse(c + Vector2(0, 3), Vector2(r, r * 0.86), Color(0.05, 0.08, 0.2, 0.45))
			_ellipse(c, Vector2(r, r * 0.86), col)
			if filled:
				var eye := Color("#234d37")
				draw_colored_polygon(PackedVector2Array([c + Vector2(-r * 0.5, -r * 0.2), c + Vector2(-r * 0.1, r * 0.05), c + Vector2(-r * 0.3, r * 0.3)]), eye)
				draw_colored_polygon(PackedVector2Array([c + Vector2(r * 0.45, -r * 0.1), c + Vector2(r * 0.15, r * 0.1), c + Vector2(r * 0.35, r * 0.3)]), eye)
				draw_colored_polygon(PackedVector2Array([c + Vector2(r * 0.7, -r * 0.95), c + Vector2(r * 0.85, -r * 0.9), c + Vector2(r * 0.65, -r * 0.6)]), UiKit.ORANGE)


func _ellipse(center: Vector2, radii: Vector2, col: Color) -> void:
	var pts := PackedVector2Array()
	for i in 40:
		var a := TAU * i / 40.0
		pts.append(center + Vector2(cos(a) * radii.x, sin(a) * radii.y))
	draw_colored_polygon(pts, col)


func _star(center: Vector2, r: float, points: int, inner: float, col: Color) -> void:
	var pts := PackedVector2Array()
	for i in points * 2:
		var a := -PI / 2.0 + PI * i / points
		var rr := r if i % 2 == 0 else r * inner
		pts.append(center + Vector2(cos(a), sin(a)) * rr)
	draw_colored_polygon(pts, col)
