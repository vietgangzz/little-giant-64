shader_type spatial;
// Waves a cloth mesh along its local +X (the pole sits at x = 0).
render_mode cull_disabled;

uniform vec4 albedo : source_color = vec4(0.84, 0.96, 0.29, 1.0);
uniform float amplitude = 0.12;
uniform float speed = 5.0;
uniform float pole_x = 0.0;
uniform float cloth_length = 1.2;

#include "res://shaders/toon_light.gdshaderinc"

void vertex() {
	float k = clamp((VERTEX.x - pole_x) / cloth_length, 0.0, 1.0);
	VERTEX.z += sin(VERTEX.x * 4.0 - TIME * speed) * amplitude * k;
	VERTEX.y += sin(VERTEX.x * 3.0 - TIME * speed * 0.7) * amplitude * 0.3 * k;
}

void fragment() {
	ALBEDO = albedo.rgb;
}
