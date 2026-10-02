// Shared stylised light model: a soft two-tone band with cool shadows, a toon specular
// dot and a rim that only shows on the lit side. Include after declaring the uniforms below.
uniform float shade_softness : hint_range(0.0, 0.5) = 0.12;
uniform float shade_offset : hint_range(-1.0, 1.0) = 0.0;
uniform vec4 shadow_tint : source_color = vec4(0.62, 0.68, 0.95, 1.0);
uniform float shadow_floor : hint_range(0.0, 1.0) = 0.42;
uniform float spec_strength : hint_range(0.0, 2.0) = 0.25;
uniform float spec_gloss : hint_range(1.0, 256.0) = 40.0;
uniform float rim_strength : hint_range(0.0, 2.0) = 0.28;
uniform float rim_width : hint_range(0.0, 1.0) = 0.38;

void light() {
	float lit = 1.0;
#ifdef NO_SUN
	// cave stone ignores the sun: the dome's shadow map is too coarse to keep it out cleanly
	lit = LIGHT_IS_DIRECTIONAL ? 0.0 : 1.0;
#endif
	float ndl = dot(NORMAL, LIGHT);
	float band = smoothstep(shade_offset - shade_softness, shade_offset + shade_softness, ndl);
	band *= ATTENUATION;
	vec3 dark = shadow_tint.rgb * shadow_floor;
	DIFFUSE_LIGHT += LIGHT_COLOR / PI * mix(dark, vec3(1.0), band) * lit;
	vec3 h = normalize(VIEW + LIGHT);
	float s = pow(max(dot(NORMAL, h), 0.0), spec_gloss);
	s = smoothstep(0.45, 0.55, s) * spec_strength * band;
	float rim = 1.0 - max(dot(NORMAL, VIEW), 0.0);
	rim = smoothstep(1.0 - rim_width, 1.0 - rim_width + 0.08, rim) * rim_strength * clamp(ndl + 0.3, 0.0, 1.0) * ATTENUATION;
	SPECULAR_LIGHT += (s + rim) * LIGHT_COLOR / PI * lit;
}
