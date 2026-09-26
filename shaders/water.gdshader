shader_type spatial;
// The sea: deep-to-shallow colour by real water depth, a white foam ring hugging every shore
// (like the reference's cartoon outlines), rolling waves and glints.
render_mode blend_mix, depth_draw_always, cull_back, specular_schlick_ggx;

uniform vec4 deep : source_color = vec4(0.10, 0.45, 0.82, 1.0);
uniform vec4 mid : source_color = vec4(0.20, 0.66, 0.92, 1.0);
uniform vec4 shallow : source_color = vec4(0.55, 0.90, 0.96, 1.0);
uniform vec4 foam_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform float depth_scale = 6.0;
uniform float foam_width = 0.9;
uniform float wave_height = 0.18;
uniform sampler2D noise : repeat_enable, filter_linear_mipmap;
uniform sampler2D depth_tex : hint_depth_texture, filter_linear_mipmap;

varying vec3 wpos;

float waves(vec2 p, float t) {
	return sin(p.x * 0.18 + t * 0.9) * 0.5 + sin(p.y * 0.23 - t * 1.1) * 0.35 + sin((p.x + p.y) * 0.4 + t * 1.7) * 0.15;
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float h = waves(wpos.xz, TIME) * wave_height;
	VERTEX.y += h;
	float e = 0.5;
	float hx = waves(wpos.xz + vec2(e, 0.0), TIME) * wave_height;
	float hz = waves(wpos.xz + vec2(0.0, e), TIME) * wave_height;
	NORMAL = normalize(vec3(h - hx, e, h - hz));
}

void fragment() {
	float depth = texture(depth_tex, SCREEN_UV).r;
	vec4 upos = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, depth, 1.0);
	vec3 scene = upos.xyz / upos.w;
	float diff = clamp(VERTEX.z - scene.z, 0.0, 100.0);

	vec2 uv1 = wpos.xz * 0.035 + vec2(TIME * 0.012, TIME * 0.008);
	vec2 uv2 = wpos.xz * 0.06 - vec2(TIME * 0.01, -TIME * 0.015);
	float n = texture(noise, uv1).r * 0.6 + texture(noise, uv2).r * 0.4;

	float d = clamp(diff / depth_scale, 0.0, 1.0);
	vec3 c = mix(shallow.rgb, mid.rgb, smoothstep(0.0, 0.35, d));
	c = mix(c, deep.rgb, smoothstep(0.35, 1.0, d));
	// soft caustic-like light patches
	c += vec3(0.06, 0.08, 0.08) * smoothstep(0.55, 0.75, n);

	// shore foam: a solid inner ring and a broken outer ring that pulses outward
	float wob = (n - 0.5) * 0.6;
	float ring = 1.0 - smoothstep(foam_width * 0.35, foam_width * 0.45, diff + wob * 0.3);
	float pulse = fract(diff / foam_width * 0.9 - TIME * 0.35);
	float outer = (1.0 - smoothstep(0.0, 0.18, abs(pulse - 0.5))) * (1.0 - smoothstep(foam_width * 0.6, foam_width * 1.6, diff));
	outer *= step(0.45, n);
	float foam = clamp(ring + outer * 0.85, 0.0, 1.0);
	c = mix(c, foam_color.rgb, foam);

	// far glints
	float glint = smoothstep(0.78, 0.82, n) * smoothstep(20.0, 80.0, -VERTEX.z);
	ALBEDO = c;
	EMISSION = vec3(glint) * 0.25 + c * 0.08;
	ROUGHNESS = mix(0.08, 0.9, foam);
	SPECULAR = 0.55;
	ALPHA = mix(0.72, 0.97, smoothstep(0.0, 0.6, d)) ;
	ALPHA = max(ALPHA, foam);
}
