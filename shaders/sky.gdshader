shader_type sky;
// A bright summer sky: gradient, a warm sun with halo, and soft painted clouds. No TIME, so the
// radiance map is computed once.

uniform vec4 top_color : source_color = vec4(0.25, 0.56, 0.93, 1.0);
uniform vec4 horizon_color : source_color = vec4(0.78, 0.92, 1.0, 1.0);
uniform vec4 below_color : source_color = vec4(0.55, 0.80, 0.95, 1.0);
uniform vec4 sun_color : source_color = vec4(1.0, 0.95, 0.82, 1.0);
uniform vec4 cloud_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform vec4 cloud_shade : source_color = vec4(0.78, 0.84, 0.95, 1.0);
uniform sampler2D noise : repeat_enable, filter_linear_mipmap;

void sky() {
	vec3 d = EYEDIR;
	float y = d.y;
	vec3 c = mix(horizon_color.rgb, top_color.rgb, smoothstep(0.0, 0.55, y));
	c = mix(c, below_color.rgb, smoothstep(0.0, -0.2, y));
	if (y > 0.0) {
		vec2 p = d.xz / (y + 0.12);
		float n = texture(noise, p * 0.08).r * 0.65 + texture(noise, p * 0.21 + vec2(0.37, 0.11)).r * 0.35;
		float cover = smoothstep(0.52, 0.68, n) * smoothstep(0.0, 0.12, y) * (1.0 - smoothstep(0.55, 0.9, y));
		float shade = smoothstep(0.52, 0.85, n);
		vec3 cc = mix(cloud_shade.rgb, cloud_color.rgb, shade);
		c = mix(c, cc, cover * 0.92);
	}
	float sd = max(dot(d, LIGHT0_DIRECTION), 0.0);
	c += sun_color.rgb * (pow(sd, 900.0) * 3.0 + pow(sd, 18.0) * 0.18);
	COLOR = c;
}
