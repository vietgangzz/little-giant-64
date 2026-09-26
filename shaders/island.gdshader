shader_type spatial;
// Island ground: checkered grass on top (Mario 64 style), layered soil stripes on the sides,
// or sand / limestone variants. Everything is world-space, so any mesh shape works.

uniform vec4 grass_a : source_color = vec4(0.49, 0.83, 0.30, 1.0);
uniform vec4 grass_b : source_color = vec4(0.42, 0.76, 0.26, 1.0);
uniform vec4 soil_a : source_color = vec4(0.87, 0.66, 0.43, 1.0);
uniform vec4 soil_b : source_color = vec4(0.77, 0.55, 0.34, 1.0);
uniform vec4 lip_color : source_color = vec4(0.36, 0.70, 0.24, 1.0);
uniform float checker = 1.8;
uniform float stripe = 0.55;
uniform int kind = 0; // 0 grass, 1 sand, 2 stone, 3 rice paddy
uniform sampler2D noise : repeat_enable, filter_linear_mipmap;

#include "res://shaders/toon_light.gdshaderinc"

varying vec3 wpos;
varying vec3 wnorm;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnorm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	float n = texture(noise, wpos.xz * 0.045).r;
	float n2 = texture(noise, wpos.xz * 0.23 + vec2(0.3, 0.7)).r;
	vec2 cell = floor(wpos.xz / checker);
	float chk = mod(cell.x + cell.y, 2.0);
	vec3 top;
	if (kind == 1) {
		top = mix(vec3(0.78, 0.63, 0.42), vec3(0.72, 0.57, 0.37), chk * 0.7) * (0.94 + n2 * 0.1);
	} else if (kind == 2) {
		top = mix(vec3(0.40, 0.45, 0.50), vec3(0.33, 0.38, 0.45), n);
		top = mix(top, grass_a.rgb, smoothstep(0.55, 0.7, n2) * 0.8);
	} else if (kind == 3) {
		// flooded paddy: bright green shoots in rows over mirror water
		float rows = step(0.3, fract(wpos.x * 1.1 + n * 0.6));
		top = mix(vec3(0.36, 0.62, 0.72), mix(vec3(0.52, 0.80, 0.26), vec3(0.44, 0.72, 0.22), chk), rows);
	} else {
		top = mix(grass_a.rgb, grass_b.rgb, chk) * (0.93 + n * 0.14);
	}
	vec3 side;
	if (kind == 2) {
		float streak = texture(noise, vec2(wpos.x * 0.35 + wpos.z * 0.35, wpos.y * 0.03)).r;
		side = mix(vec3(0.44, 0.48, 0.55), vec3(0.26, 0.30, 0.38), smoothstep(0.4, 0.6, streak));
		// moss clings to the ledges
		side = mix(side, vec3(0.30, 0.52, 0.24), smoothstep(0.56, 0.72, texture(noise, wpos.xz * 0.3 + vec2(wpos.y * 0.21)).r) * 0.85);
		side *= 0.9 + 0.12 * sin(wpos.y * 3.0 + streak * 6.0);
	} else if (kind == 1) {
		side = mix(vec3(0.80, 0.64, 0.42), vec3(0.70, 0.54, 0.34), step(0.5, fract(wpos.y / stripe * 0.5)));
	} else {
		float wob = (n - 0.5) * 0.35;
		float band = step(0.5, fract((wpos.y + wob) / stripe * 0.5));
		side = mix(soil_a.rgb, soil_b.rgb, band);
		side *= 1.0 - clamp(-wpos.y * 0.04, 0.0, 0.3);
	}
	float up = smoothstep(0.42, 0.62, wnorm.y);
	vec3 c = mix(side, top, up);
	// a darker grass lip where the top rolls over the edge
	float lip = smoothstep(0.25, 0.45, wnorm.y) * (1.0 - smoothstep(0.55, 0.75, wnorm.y));
	if (kind == 0 || kind == 3) c = mix(c, lip_color.rgb, lip * 0.9);
	ALBEDO = c;
	ROUGHNESS = 0.95;
	SPECULAR = 0.1;
}
