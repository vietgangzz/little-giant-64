shader_type spatial;
// The material every imported prop and the mascot are converted to (see Fx.toonify).

uniform vec4 albedo : source_color = vec4(1.0);
uniform vec4 emission_color : source_color = vec4(0.0, 0.0, 0.0, 1.0);
uniform float emission_energy = 0.0;
uniform float metal_sheen : hint_range(0.0, 1.0) = 0.0;
uniform float flash : hint_range(0.0, 1.0) = 0.0;
uniform vec4 flash_color : source_color = vec4(1.0);
uniform float dissolve : hint_range(0.0, 1.0) = 0.0;

#include "res://shaders/toon_light.gdshaderinc"
#include "res://shaders/wind.gdshaderinc"

void vertex() {
	VERTEX += wind_offset(VERTEX, MODEL_MATRIX, MODEL_NORMAL_MATRIX, TIME);
}

void fragment() {
	vec3 c = albedo.rgb;
	// Metals get a fake environment band so gold and bronze read as shiny even in toon light.
	if (metal_sheen > 0.0) {
		vec3 n = (INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz;
		float band = smoothstep(0.15, 0.35, n.y) - smoothstep(0.55, 0.8, n.y) * 0.6;
		c = mix(c, c * 1.55 + vec3(0.08), band * metal_sheen);
	}
	ALBEDO = mix(c, flash_color.rgb, flash);
	ROUGHNESS = 0.9;
	SPECULAR = 0.2;
	EMISSION = emission_color.rgb * emission_energy + flash_color.rgb * flash * 0.6;
	if (dissolve > 0.0) {
		float n = fract(sin(dot(floor(FRAGCOORD.xy / 3.0), vec2(12.9898, 78.233))) * 43758.5453);
		if (n < dissolve) discard;
	}
}
