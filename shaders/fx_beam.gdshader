shader_type spatial;
// Soft vertical light shaft over stars and pickups.
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;

uniform vec4 color : source_color = vec4(1.0, 0.92, 0.55, 1.0);
uniform float strength = 1.0;

void fragment() {
	float edge = pow(clamp(1.0 - abs(dot(NORMAL, VIEW)), 0.0, 1.0), 0.6);
	float fade = (1.0 - UV.y) * UV.y * 4.0;
	float sweep = 0.7 + 0.3 * sin(UV.y * 18.0 - TIME * 4.0);
	ALBEDO = color.rgb;
	ALPHA = (1.0 - edge) * smoothstep(0.0, 0.35, UV.y) * (1.0 - smoothstep(0.6, 1.0, UV.y)) * strength * sweep * 0.55;
}
