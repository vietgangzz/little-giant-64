shader_type spatial;
// Cave stone: the island ground with ambient light switched off, so only the skylight,
// the crystals and the lamps light the inside.
render_mode ambient_light_disabled;

#define NO_SUN
#include "res://shaders/island_body.gdshaderinc"
