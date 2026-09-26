shader_type spatial;
// Expanding shock ring for jumps, landings and pickups. `age` runs 0 → 1.
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;

uniform vec4 color : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform float age = 0.0;
uniform float thickness = 0.12;

void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float r = length(p);
	float radius = mix(0.25, 0.95, 1.0 - pow(1.0 - age, 3.0));
	float band = 1.0 - smoothstep(0.0, thickness * (1.0 - age * 0.6), abs(r - radius));
	ALBEDO = color.rgb;
	ALPHA = band * (1.0 - age) * color.a;
}
