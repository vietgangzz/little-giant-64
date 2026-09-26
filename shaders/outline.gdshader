shader_type spatial;
// Inverted-hull ink line, used as next_pass. Width is kept roughly constant on screen.
render_mode unshaded, cull_front, depth_draw_opaque, shadows_disabled;

uniform vec4 color : source_color = vec4(0.08, 0.12, 0.1, 1.0);
uniform float width = 0.018;
uniform float max_scale = 3.0;

void vertex() {
	vec4 view_pos = MODELVIEW_MATRIX * vec4(VERTEX, 1.0);
	float grow = width * clamp(-view_pos.z * 0.09, 0.7, max_scale);
	VERTEX += NORMAL * grow;
}

void fragment() {
	ALBEDO = color.rgb;
}
