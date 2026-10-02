// Wind: leaves, grass and fronds lean with the breeze. The push grows with the square of the
// height above the prop's origin, so trunks stay planted, and each prop gets its own phase
// from where it stands. `sway` is set per prop by Fx.toonify (0 = still).
uniform float sway = 0.0;

vec3 wind_offset(vec3 v, mat4 model, mat3 normal_matrix, float t) {
	if (sway <= 0.0) return vec3(0.0);
	vec3 o = model[3].xyz;
	float phase = o.x * 0.37 + o.z * 0.23;
	float gust = sin(t * 1.3 + phase) * 0.65 + sin(t * 2.7 + phase * 1.7) * 0.35;
	float h = max(v.y, 0.0);
	vec3 w = vec3(1.0, 0.0, 0.45) * gust * h * h * 0.03 * sway;
	// world → local (props are rotated and uniformly scaled)
	return transpose(normal_matrix) * w;
}
