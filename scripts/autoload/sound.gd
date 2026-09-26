extends Node
## Sampled audio only: every stream is an Ogg file from assets/audio (see assets/CREDITS.md).
## SFX go through a small voice pool, music crossfades between two players, and ambience loops
## on its own bus. Missing files are skipped quietly, so the game runs while assets are in flux.

const SFX_DIR := "res://assets/audio/sfx/"
const MUSIC_DIR := "res://assets/audio/music/"
const VOICES := 16

var _cache: Dictionary = {}
var _voices: Array[AudioStreamPlayer] = []
var _next := 0
var _music: Array[AudioStreamPlayer] = []
var _music_on := 0
var _music_name := ""
var _ambient: Dictionary = {} ## name -> AudioStreamPlayer
var _lowpass: AudioEffectLowPassFilter
var _last_play: Dictionary = {}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for bus in ["Music", "SFX", "Ambient"]:
		if AudioServer.get_bus_index(bus) == -1:
			AudioServer.add_bus()
			var i := AudioServer.bus_count - 1
			AudioServer.set_bus_name(i, bus)
			AudioServer.set_bus_send(i, "Master")
	_lowpass = AudioEffectLowPassFilter.new()
	_lowpass.cutoff_hz = 20000.0
	AudioServer.add_bus_effect(AudioServer.get_bus_index("Music"), _lowpass)
	for i in VOICES:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_voices.append(p)
	for i in 2:
		var m := AudioStreamPlayer.new()
		m.bus = "Music"
		m.volume_db = -80.0
		add_child(m)
		_music.append(m)
	apply_volumes()


func apply_volumes() -> void:
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("Music"), linear_to_db(maxf(Game.music_volume, 0.0001)))
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("SFX"), linear_to_db(maxf(Game.sfx_volume, 0.0001)))
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("Ambient"), linear_to_db(maxf(Game.sfx_volume * 0.8, 0.0001)))


func stream(path: String) -> AudioStream:
	if _cache.has(path):
		return _cache[path]
	var s: AudioStream = null
	if ResourceLoader.exists(path):
		s = load(path)
	_cache[path] = s
	return s


## Plays a one-shot. `pitch_jitter` randomises pitch a little so repeats don't machine-gun.
func play(name: String, volume_db := 0.0, pitch := 1.0, pitch_jitter := 0.04) -> void:
	var s := stream(SFX_DIR + name + ".ogg")
	if s == null:
		return
	# The same sample twice inside one frame only makes it louder.
	var now := Time.get_ticks_msec()
	if _last_play.get(name, -100) > now - 25:
		return
	_last_play[name] = now
	var p := _voices[_next]
	_next = (_next + 1) % VOICES
	p.stream = s
	p.volume_db = volume_db
	p.pitch_scale = pitch * (1.0 + randf_range(-pitch_jitter, pitch_jitter))
	p.play()


## A positional one-shot that frees itself.
func play_at(name: String, where: Vector3, volume_db := 0.0, pitch := 1.0) -> void:
	var s := stream(SFX_DIR + name + ".ogg")
	if s == null or get_tree().current_scene == null:
		return
	var p := AudioStreamPlayer3D.new()
	p.stream = s
	p.bus = "SFX"
	p.volume_db = volume_db
	p.pitch_scale = pitch * randf_range(0.96, 1.04)
	p.unit_size = 8.0
	p.max_distance = 60.0
	get_tree().current_scene.add_child(p)
	p.global_position = where
	p.finished.connect(p.queue_free)
	p.play()


func music(name: String, fade := 1.2, from := 0.0) -> void:
	if name == _music_name:
		return
	_music_name = name
	var s: AudioStream = stream(MUSIC_DIR + name + ".ogg") if name != "" else null
	var old := _music[_music_on]
	_music_on = 1 - _music_on
	var cur := _music[_music_on]
	var tw := create_tween().set_parallel(true)
	tw.tween_property(old, "volume_db", -80.0, fade)
	tw.chain().tween_callback(old.stop)
	if s == null:
		return
	if s is AudioStreamOggVorbis:
		(s as AudioStreamOggVorbis).loop = not name.begins_with("star_get") and not name.begins_with("all_stars")
	cur.stream = s
	cur.volume_db = -40.0
	cur.play(from)
	create_tween().tween_property(cur, "volume_db", 0.0, fade * 0.6)


## A jingle ducks the music, plays once, then brings the music back.
func jingle(name: String, duck_for := -1.0) -> void:
	var s := stream(MUSIC_DIR + name + ".ogg")
	if s == null:
		return
	if s is AudioStreamOggVorbis:
		(s as AudioStreamOggVorbis).loop = false
	var p := AudioStreamPlayer.new()
	p.stream = s
	p.bus = "SFX"
	p.volume_db = -2.0
	add_child(p)
	p.play()
	p.finished.connect(p.queue_free)
	var length := duck_for if duck_for > 0.0 else s.get_length()
	var cur := _music[_music_on]
	var tw := create_tween()
	tw.tween_property(cur, "volume_db", -30.0, 0.25)
	tw.tween_interval(maxf(length - 0.6, 0.2))
	tw.tween_property(cur, "volume_db", 0.0, 1.2)


func ambient(name: String, volume_db := -8.0) -> void:
	if _ambient.has(name):
		return
	var s := stream(SFX_DIR + name + ".ogg")
	if s == null:
		return
	if s is AudioStreamOggVorbis:
		(s as AudioStreamOggVorbis).loop = true
	var p := AudioStreamPlayer.new()
	p.stream = s
	p.bus = "Ambient"
	p.volume_db = volume_db
	add_child(p)
	p.play()
	_ambient[name] = p


## A looping positional emitter (waterfalls), parented to `parent`.
func loop_at(name: String, parent: Node3D, volume_db := 0.0, unit := 6.0) -> AudioStreamPlayer3D:
	var s := stream(SFX_DIR + name + ".ogg")
	if s == null:
		return null
	if s is AudioStreamOggVorbis:
		s = s.duplicate()
		(s as AudioStreamOggVorbis).loop = true
	var p := AudioStreamPlayer3D.new()
	p.stream = s
	p.bus = "Ambient"
	p.volume_db = volume_db
	p.unit_size = unit
	p.max_distance = 45.0
	p.autoplay = true
	parent.add_child(p)
	return p


func muffle(on: bool) -> void:
	var tw := create_tween()
	tw.tween_property(_lowpass, "cutoff_hz", 700.0 if on else 20000.0, 0.35)
