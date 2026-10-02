uniform vec4 grass_a : source_color = vec4(0.49, 0.83, 0.30, 1.0);
uniform vec4 grass_b : source_color = vec4(0.42, 0.76, 0.26, 1.0);
uniform vec4 soil_a : source_color = vec4(0.87, 0.66, 0.43, 1.0);
uniform vec4 soil_b : source_color = vec4(0.77, 0.55, 0.34, 1.0);
uniform vec4 lip_color : source_color = vec4(0.36, 0.70, 0.24, 1.0);
uniform float checker = 1.8;
uniform float stripe = 0.55;
uniform int kind = 0; // 0 grass, 1 sand, 2 stone, 3 rice paddy, 4 Hạ Long karst, 5 cave, 6 marble, 7 paved street
uniform sampler2D noise : repeat_enable, filter_linear_mipmap;
uniform float self_light = 0.0; // caves glow faintly instead of using lamps
uniform vec4 self_light_color : source_color = vec4(1.0, 0.9, 0.76, 1.0);

#include "res://shaders/toon_light.gdshaderinc"

// colour literals below are written in sRGB, like a colour picker
vec3 srgb(vec3 c) {
	return pow(c, vec3(2.2));
}

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
		top = mix(srgb(vec3(0.78, 0.63, 0.42)), srgb(vec3(0.72, 0.57, 0.37)), chk * 0.7) * (0.94 + n2 * 0.1);
	} else if (kind == 2) {
		top = mix(srgb(vec3(0.40, 0.45, 0.50)), srgb(vec3(0.33, 0.38, 0.45)), n);
		top = mix(top, grass_a.rgb, smoothstep(0.55, 0.7, n2) * 0.8);
	} else if (kind == 4) {
		// dense jungle on every ledge of a Hạ Long karst
		top = mix(srgb(vec3(0.15, 0.38, 0.18)), srgb(vec3(0.26, 0.50, 0.21)), smoothstep(0.35, 0.65, n2)) * (0.9 + n * 0.2);
	} else if (kind == 7) {
		// Hội An's old streets: worn terracotta bricks in a running bond, pale mortar
		vec2 b = wpos.xz * vec2(1.6, 3.2);
		b.x += step(1.0, mod(floor(b.y), 2.0)) * 0.5;
		vec2 f = fract(b);
		float mortar = step(f.x, 0.06) + step(f.y, 0.1);
		float tone = fract(sin(dot(floor(b), vec2(12.9898, 78.233))) * 43758.5453);
		vec3 brick = mix(srgb(vec3(0.80, 0.52, 0.36)), srgb(vec3(0.70, 0.44, 0.30)), tone) * (0.9 + n2 * 0.15);
		brick = mix(brick, srgb(vec3(0.62, 0.62, 0.52)), smoothstep(0.6, 0.75, n) * 0.35); // moss and wear
		top = mix(brick, srgb(vec3(0.86, 0.78, 0.62)), clamp(mortar, 0.0, 1.0));
	} else if (kind == 6) {
		// marble peaks wear a cap of jungle, lighter than Hạ Long's
		top = mix(srgb(vec3(0.33, 0.56, 0.25)), srgb(vec3(0.45, 0.66, 0.30)), smoothstep(0.35, 0.65, n2)) * (0.92 + n * 0.16);
	} else if (kind == 5) {
		top = mix(srgb(vec3(0.72, 0.66, 0.56)), srgb(vec3(0.60, 0.54, 0.46)), n) * (0.92 + n2 * 0.14);
	} else if (kind == 3) {
		// flooded paddy: bright green shoots in rows over mirror water
		float rows = step(0.3, fract(wpos.x * 1.1 + n * 0.6));
		top = mix(srgb(vec3(0.36, 0.62, 0.72)), mix(srgb(vec3(0.52, 0.80, 0.26)), srgb(vec3(0.44, 0.72, 0.22)), chk), rows);
	} else {
		top = mix(grass_a.rgb, grass_b.rgb, chk) * (0.93 + n * 0.14);
	}
	vec3 side;
	if (kind == 4) {
		// project the noise onto the wall itself (blend of the two side planes): weathering
		// runs down the cliff in streaks, jungle grows in clumps, thicker toward the top
		float wx = abs(wnorm.x) / (abs(wnorm.x) + abs(wnorm.z) + 0.001);
		vec2 pa = vec2(wpos.z, wpos.y);
		vec2 pb = vec2(wpos.x, wpos.y);
		float streak = mix(texture(noise, pb * vec2(0.35, 0.025)).r, texture(noise, pa * vec2(0.35, 0.025)).r, wx);
		side = mix(srgb(vec3(0.66, 0.67, 0.64)), srgb(vec3(0.42, 0.45, 0.46)), smoothstep(0.35, 0.65, streak));
		float clump = mix(texture(noise, pb * vec2(0.07, 0.045)).r, texture(noise, pa * vec2(0.07, 0.045)).r, wx) * 0.7
			+ mix(texture(noise, pb * vec2(0.2, 0.13) + 0.3).r, texture(noise, pa * vec2(0.2, 0.13) + 0.3).r, wx) * 0.3;
		float veg = smoothstep(0.5, 0.6, clump + clamp(wpos.y * 0.012, 0.0, 0.14));
		vec3 leaf = mix(srgb(vec3(0.20, 0.42, 0.20)), srgb(vec3(0.33, 0.55, 0.24)), smoothstep(0.3, 0.7, texture(noise, wpos.xz * 0.3 + wpos.y * 0.2).r));
		side = mix(side, leaf, veg);
		// the wave-cut notch at the waterline, dark and wet
		float notch = 1.0 - smoothstep(0.0, 1.4, abs(wpos.y - 0.4));
		side = mix(side, srgb(vec3(0.24, 0.27, 0.27)), notch * 0.75);
	} else if (kind == 6) {
		// Ngũ Hành Sơn marble: creamy white with grey-rose veins and clumps of green
		float wx = abs(wnorm.x) / (abs(wnorm.x) + abs(wnorm.z) + 0.001);
		vec2 pa = vec2(wpos.z, wpos.y);
		vec2 pb = vec2(wpos.x, wpos.y);
		float vein = mix(texture(noise, pb * vec2(0.22, 0.09)).r, texture(noise, pa * vec2(0.22, 0.09)).r, wx);
		float v = 1.0 - smoothstep(0.0, 0.035, abs(vein - 0.5));
		side = mix(srgb(vec3(0.93, 0.91, 0.86)), srgb(vec3(0.80, 0.78, 0.76)), smoothstep(0.3, 0.7, texture(noise, pb * 0.08 + pa * 0.05).r));
		side = mix(side, srgb(vec3(0.66, 0.58, 0.60)), v * 0.7);
		float clump = mix(texture(noise, pb * vec2(0.09, 0.06)).r, texture(noise, pa * vec2(0.09, 0.06)).r, wx);
		side = mix(side, srgb(vec3(0.30, 0.52, 0.24)), smoothstep(0.58, 0.66, clump + clamp(wpos.y * 0.01, 0.0, 0.08)) * 0.9);
		float notch = 1.0 - smoothstep(0.0, 1.2, abs(wpos.y - 0.4));
		side = mix(side, srgb(vec3(0.55, 0.56, 0.52)), notch * 0.5);
	} else if (kind == 5) {
		// warm limestone: pale flowstone with darker drip streaks running down the walls
		float wx = abs(wnorm.x) / (abs(wnorm.x) + abs(wnorm.z) + 0.001);
		float streak = mix(texture(noise, vec2(wpos.x, wpos.y) * vec2(0.5, 0.04)).r, texture(noise, vec2(wpos.z, wpos.y) * vec2(0.5, 0.04)).r, wx);
		float blot = texture(noise, wpos.xz * 0.12 + wpos.y * 0.07).r;
		side = mix(srgb(vec3(0.88, 0.82, 0.70)), srgb(vec3(0.60, 0.55, 0.50)), smoothstep(0.42, 0.66, streak));
		side = mix(side, srgb(vec3(0.97, 0.93, 0.84)), smoothstep(0.62, 0.75, blot) * 0.6);
		side *= 0.94 + 0.06 * sin(wpos.y * 2.0 + streak * 4.0);
	} else if (kind == 2) {
		float streak = texture(noise, vec2(wpos.x * 0.35 + wpos.z * 0.35, wpos.y * 0.03)).r;
		side = mix(srgb(vec3(0.55, 0.58, 0.60)), srgb(vec3(0.34, 0.38, 0.42)), smoothstep(0.4, 0.6, streak));
		// moss clings to the ledges
		side = mix(side, srgb(vec3(0.30, 0.52, 0.24)), smoothstep(0.56, 0.72, texture(noise, wpos.xz * 0.3 + vec2(wpos.y * 0.21)).r) * 0.85);
		side *= 0.9 + 0.12 * sin(wpos.y * 3.0 + streak * 6.0);
	} else if (kind == 7) {
		// a stone embankment along the river: big laterite blocks
		vec2 q = vec2(wpos.x + wpos.z, wpos.y) * vec2(0.9, 1.6);
		q.x += step(1.0, mod(floor(q.y), 2.0)) * 0.5;
		vec2 g = fract(q);
		float joint = step(g.x, 0.04) + step(g.y, 0.07);
		side = mix(srgb(vec3(0.66, 0.58, 0.48)), srgb(vec3(0.52, 0.45, 0.38)), n) * (0.92 + n2 * 0.12);
		side = mix(side, srgb(vec3(0.36, 0.32, 0.28)), clamp(joint, 0.0, 1.0) * 0.8);
		float notch = 1.0 - smoothstep(0.0, 0.8, abs(wpos.y - 0.3));
		side = mix(side, srgb(vec3(0.28, 0.30, 0.26)), notch * 0.6);
	} else if (kind == 1) {
		side = mix(srgb(vec3(0.80, 0.64, 0.42)), srgb(vec3(0.70, 0.54, 0.34)), step(0.5, fract(wpos.y / stripe * 0.5)));
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
	if (kind == 4) c = mix(c, srgb(vec3(0.20, 0.44, 0.22)), lip * 0.8);
	if (kind == 6) c = mix(c, srgb(vec3(0.30, 0.50, 0.24)), lip * 0.7);
	ALBEDO = c;
	if (self_light > 0.0) {
		// lamp-warm near the floor, cooler and darker up in the vault
		float k = self_light * mix(1.0, 0.45, smoothstep(1.0, 11.0, wpos.y));
		EMISSION = c * self_light_color.rgb * k;
	}
	ROUGHNESS = 0.95;
	SPECULAR = 0.1;
}
