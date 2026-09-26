extends Node
## Global state: collectibles, the star catalogue, save data, settings, input map and the
## command-line switches the QA tooling uses.

signal coins_changed(count: int)
signal red_coins_changed(count: int)
signal star_collected(id: String)
signal health_changed(hp: int)
signal all_stars
signal language_changed

const SAVE_PATH := "user://save.json"
const MAX_HP := 3
const RED_COIN_TOTAL := 8
const COIN_STAR_AT := 100

## The eight bronze stars. `hint` is shown on the pause map; `where` is filled in by the world.
const STARS := [
	{"id": "terraces", "level": "skies", "en": "Top of the Rice Terraces", "vi": "Đỉnh Ruộng Bậc Thang",
		"hint_en": "Climb the terraces east of home.", "hint_vi": "Leo ruộng bậc thang phía đông."},
	{"id": "lanterns", "level": "skies", "en": "Eight Red Lanterns", "vi": "Tám Chiếc Đèn Lồng",
		"hint_en": "Find all 8 red lanterns. The star waits by the pagoda pond.", "hint_vi": "Tìm đủ 8 đèn lồng đỏ. Sao chờ ở hồ chùa."},
	{"id": "pagoda", "level": "skies", "en": "Roof of the One Pillar Pagoda", "vi": "Mái Chùa Một Cột",
		"hint_en": "Bamboo steps and a drum lead to the roof.", "hint_vi": "Nhảy ống tre và trống để lên mái."},
	{"id": "karst", "level": "skies", "en": "Karst Summit", "vi": "Đỉnh Núi Đá Vôi",
		"hint_en": "Wall-kick between the limestone towers.", "hint_vi": "Đạp tường giữa các cột đá vôi."},
	{"id": "lagoon", "level": "skies", "en": "Across the Lotus Lagoon", "vi": "Qua Đầm Sen",
		"hint_en": "Ride the sampans; lotus leaves sink!", "hint_vi": "Đi thuyền; lá sen sẽ chìm!"},
	{"id": "waterfall", "level": "skies", "en": "Behind the Waterfall", "vi": "Sau Thác Nước",
		"hint_en": "Something glitters behind the falls.", "hint_vi": "Có gì lấp lánh sau thác."},
	{"id": "crabs", "level": "skies", "en": "King of Crab Beach", "vi": "Vua Bãi Cua",
		"hint_en": "Stomp all the crabs on the beach.", "hint_vi": "Dẫm bẹp hết cua trên bãi biển."},
	{"id": "coins", "level": "skies", "en": "A Hundred Đồng Xu", "vi": "Một Trăm Đồng Xu",
		"hint_en": "Collect 100 coins.", "hint_vi": "Nhặt 100 đồng xu."},
	# ---- Vịnh Hạ Long
	{"id": "halong_village", "level": "halong", "en": "Fishing Village Rooftops", "vi": "Mái Nhà Làng Chài",
		"hint_en": "Hop the raft houses of the floating village.", "hint_vi": "Nhảy qua các nhà bè của làng chài."},
	{"id": "halong_cave", "level": "halong", "en": "Heart of Surprise Cave", "vi": "Lòng Hang Sửng Sốt",
		"hint_en": "Climb the stalagmites deep inside the cave.", "hint_vi": "Leo măng đá sâu trong hang."},
	{"id": "halong_trongmai", "level": "halong", "en": "Fighting Cock Rocks", "vi": "Đỉnh Hòn Trống Mái",
		"hint_en": "Wall-kick up between the two rocks.", "hint_vi": "Đạp tường giữa hai hòn đá."},
	{"id": "halong_titop", "level": "halong", "en": "Ti Tốp Summit", "vi": "Đỉnh Ti Tốp",
		"hint_en": "Only the dragon flies that high.", "hint_vi": "Chỉ có rồng bay cao đến thế."},
	{"id": "halong_dragon", "level": "halong", "en": "Star on the Dragon's Head", "vi": "Sao Trên Đầu Rồng",
		"hint_en": "Board the dragon and run up its back.", "hint_vi": "Lên lưng rồng và chạy tới đầu."},
	{"id": "halong_pearls", "level": "halong", "en": "Eight Dragon Pearls", "vi": "Tám Viên Ngọc Rồng",
		"hint_en": "The dragon scattered 8 pearls. The star waits at the pier.", "hint_vi": "Rồng rải 8 viên ngọc. Sao chờ ở bến."},
]

const LEVELS := {
	"skies": {"en": "Hạ Long Skies", "vi": "Bầu Trời Hạ Long"},
	"halong": {"en": "Hạ Long Bay", "vi": "Vịnh Hạ Long"},
}

var level := "skies"
var coins := 0
var coin_total := 0 ## set by the world once every coin is placed
var red_coins := 0
var stars: Dictionary = {} ## id -> true
var taken: Dictionary = {} ## collectible id -> true, this session only (coins respawn per session like SM64)
var hp := MAX_HP
var lang := "en"
var music_volume := 0.8
var sfx_volume := 0.9
var invert_x := false
var invert_y := false
var cape := true
var mouse_sensitivity := 1.0
var best_time := 0.0
var play_time := 0.0
var finished := false ## the current level's finale has played this session
var finished_levels: Dictionary = {}
var paused := false
var in_cutscene := false

## Command-line switches (after `--`): --start --god --shot=SEC:PATH --warp=ID --tour=DIR
## --all-stars --bot --lang=vi --quit-after-shot
var args: Dictionary = {}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a in OS.get_cmdline_user_args():
		var s := String(a).trim_prefix("--")
		var eq := s.find("=")
		if eq >= 0:
			args[s.substr(0, eq)] = s.substr(eq + 1)
		else:
			args[s] = true
	_setup_input()
	load_save()
	if args.has("lang"):
		lang = String(args["lang"])
	if args.has("level"):
		level = String(args["level"])


func is_test_run() -> bool:
	return args.has("bot") or args.has("god") or args.has("tour") or args.has("shot") or args.has("warp") or args.has("all-stars")


func _process(delta: float) -> void:
	if not paused and not finished and not in_cutscene:
		play_time += delta


# ---------------------------------------------------------------- collectibles

func add_coins(n: int) -> void:
	var before := coins
	coins += n
	coins_changed.emit(coins)
	if before < COIN_STAR_AT and coins >= COIN_STAR_AT:
		get_tree().call_group("coin_star", "reveal")


func add_red_coin() -> void:
	red_coins += 1
	red_coins_changed.emit(red_coins)
	if red_coins >= RED_COIN_TOTAL:
		get_tree().call_group("lantern_star", "reveal")


func has_star(id: String) -> bool:
	return stars.has(id)


func star_count() -> int:
	return stars.size()


func level_stars(lv := "") -> Array:
	var l := level if lv == "" else lv
	return STARS.filter(func(s): return s["level"] == l)


func level_star_total(lv := "") -> int:
	return level_stars(lv).size()


func level_star_count(lv := "") -> int:
	return level_stars(lv).filter(func(s): return stars.has(s["id"])).size()


func level_name(lv := "") -> String:
	return LEVELS[level if lv == "" else lv][lang]


## Leaves for another level: session coins and lanterns start over, stars are kept.
func travel(to: String) -> void:
	level = to
	coins = 0
	red_coins = 0
	taken.clear()
	hp = MAX_HP
	finished = finished_levels.has(to)
	in_cutscene = false
	get_tree().paused = false
	get_tree().reload_current_scene()


func collect_star(id: String) -> void:
	if stars.has(id):
		return
	stars[id] = true
	star_collected.emit(id)
	save()


func star_info(id: String) -> Dictionary:
	for s in STARS:
		if s["id"] == id:
			return s
	return {}


func star_name(id: String) -> String:
	var s := star_info(id)
	return s.get(lang, id)


func hurt(amount := 1) -> void:
	if args.has("god"):
		return
	hp = max(0, hp - amount)
	health_changed.emit(hp)


func heal(amount := 1) -> void:
	hp = min(MAX_HP, hp + amount)
	health_changed.emit(hp)


func t(en: String, vi: String) -> String:
	return vi if lang == "vi" else en


func toggle_language() -> void:
	lang = "vi" if lang == "en" else "en"
	language_changed.emit()
	save()


# ---------------------------------------------------------------- save

func save() -> void:
	if is_test_run():
		return
	var data := {
		"stars": stars.keys(), "lang": lang, "music": music_volume, "sfx": sfx_volume,
		"invert_x": invert_x, "invert_y": invert_y, "cape": cape, "sens": mouse_sensitivity,
		"best_time": best_time, "level": level, "finished_levels": finished_levels.keys(),
	}
	var f := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(data))


func load_save() -> void:
	if not FileAccess.file_exists(SAVE_PATH) or is_test_run():
		return
	var data = JSON.parse_string(FileAccess.get_file_as_string(SAVE_PATH))
	if typeof(data) != TYPE_DICTIONARY:
		return
	for id in data.get("stars", []):
		stars[String(id)] = true
	lang = data.get("lang", lang)
	music_volume = data.get("music", music_volume)
	sfx_volume = data.get("sfx", sfx_volume)
	invert_x = data.get("invert_x", invert_x)
	invert_y = data.get("invert_y", invert_y)
	cape = data.get("cape", cape)
	mouse_sensitivity = data.get("sens", mouse_sensitivity)
	best_time = data.get("best_time", best_time)
	level = data.get("level", level)
	if not LEVELS.has(level):
		level = "skies"
	for l in data.get("finished_levels", []):
		finished_levels[String(l)] = true


func reset_progress() -> void:
	stars.clear()
	taken.clear()
	coins = 0
	red_coins = 0
	hp = MAX_HP
	finished = false
	play_time = 0.0
	save()


# ---------------------------------------------------------------- input

func _setup_input() -> void:
	var keys := {
		"move_forward": [KEY_W, KEY_UP], "move_back": [KEY_S, KEY_DOWN],
		"move_left": [KEY_A, KEY_LEFT], "move_right": [KEY_D, KEY_RIGHT],
		"jump": [KEY_SPACE], "dash": [KEY_SHIFT, KEY_J], "pound": [KEY_CTRL, KEY_C, KEY_K],
		"cam_left": [KEY_Q], "cam_right": [KEY_E], "cam_zoom": [KEY_Z], "cam_center": [KEY_TAB],
		"pause": [KEY_ESCAPE, KEY_P], "ui_confirm": [KEY_ENTER, KEY_SPACE], "walk": [KEY_ALT],
	}
	for action in keys:
		if not InputMap.has_action(action):
			InputMap.add_action(action, 0.2)
		for k in keys[action]:
			var ev := InputEventKey.new()
			ev.physical_keycode = k
			InputMap.action_add_event(action, ev)
	var pad_buttons := {
		"jump": [JOY_BUTTON_A], "dash": [JOY_BUTTON_X, JOY_BUTTON_RIGHT_SHOULDER],
		"pound": [JOY_BUTTON_B, JOY_BUTTON_LEFT_SHOULDER], "pause": [JOY_BUTTON_START],
		"ui_confirm": [JOY_BUTTON_A], "cam_center": [JOY_BUTTON_RIGHT_STICK], "cam_zoom": [JOY_BUTTON_Y],
	}
	for action in pad_buttons:
		for b in pad_buttons[action]:
			var ev := InputEventJoypadButton.new()
			ev.button_index = b
			InputMap.action_add_event(action, ev)
	var pad_axes := {
		"move_left": [JOY_AXIS_LEFT_X, -1.0], "move_right": [JOY_AXIS_LEFT_X, 1.0],
		"move_forward": [JOY_AXIS_LEFT_Y, -1.0], "move_back": [JOY_AXIS_LEFT_Y, 1.0],
		"cam_left": [JOY_AXIS_RIGHT_X, -1.0], "cam_right": [JOY_AXIS_RIGHT_X, 1.0],
		"cam_up": [JOY_AXIS_RIGHT_Y, -1.0], "cam_down": [JOY_AXIS_RIGHT_Y, 1.0],
		"pound_trigger": [JOY_AXIS_TRIGGER_LEFT, 1.0],
	}
	for action in pad_axes:
		if not InputMap.has_action(action):
			InputMap.add_action(action, 0.2)
		var ev := InputEventJoypadMotion.new()
		ev.axis = pad_axes[action][0]
		ev.axis_value = pad_axes[action][1]
		InputMap.action_add_event(action, ev)
	# The pad's left trigger is also a ground pound.
	for ev in InputMap.action_get_events("pound_trigger"):
		InputMap.action_add_event("pound", ev)
