shader_type spatial;
// Scrolling white-blue streaks for waterfalls.
render_mode cull_disabled, blend_mix, depth_draw_opaque;

uniform sampler2D noise : repeat_enable, filter_linear_mipmap;
uniform vec4 water : source_color = vec4(0.55, 0.85, 1.0, 1.0);
uniform float speed = 1.4;

void fragment() {
	float n = texture(noise, vec2(UV.x * 1.6, UV.y * 0.5 - TIME * speed)).r;
	float n2 = texture(noise, vec2(UV.x * 3.1 + 0.4, UV.y * 0.9 - TIME * speed * 1.4)).r;
	float streak = smoothstep(0.45, 0.7, n * 0.6 + n2 * 0.4);
	vec3 c = mix(water.rgb, vec3(1.0), streak);
	ALBEDO = c;
	EMISSION = c * 0.25;
	ROUGHNESS = 0.2;
	float edge = smoothstep(0.0, 0.08, UV.x) * smoothstep(1.0, 0.92, UV.x);
	ALPHA = (0.72 + streak * 0.28) * edge;
}
