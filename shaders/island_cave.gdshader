shader_type spatial;
// Cave stone: the island ground with ambient light and the sun switched off. The stone glows
// faintly by itself (self_light), and the skylight beam and the crystals do the rest.
render_mode ambient_light_disabled;

#define NO_SUN
#include "res://shaders/island_body.gdshaderinc"
