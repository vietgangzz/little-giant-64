class_name QaBot
extends Node
## Plays scripted routes with real inputs (no teleporting mid-route) to prove each star can be
## reached, and prints a trace of the hero's state. Run:
##   godot --path . -- --bot=<route|all> [--trace] [--god]
## Steps: ["goto", Vector3, tol], ["jump", hold_s], ["djump"], ["dash"], ["pound"], ["wait", s],
##        ["hold", Vector3 dir, s], ["star", id], ["warp", Vector3], ["face", Vector3 dir]

var ROUTES := {
	"dash": [["warp", Vector3(0, 2.6, 8)], ["wait", 0.5], ["dash"], ["wait", 0.5], ["jump", 0.3], ["wait", 0.3], ["dash"], ["wait", 0.8]],
	"moves": [
		["warp", Vector3(0, 2.6, 8)], ["wait", 0.5], ["hold", Vector3(0, 0, -1), 1.0], ["jump", 0.3], ["wait", 0.5],
		["djump"], ["wait", 0.8], ["dash"], ["wait", 0.6], ["jump", 0.3], ["wait", 0.35], ["pound"], ["wait", 1.2],
	],
	"terraces": [
		["warp", Vector3(0, 2.6, 8)], ["goto", Vector3(12.8, 0, -1), 0.8], ["leap", Vector3(19.5, 0, -2)], ["goto", Vector3(20.8, 0, -2.4), 0.8],
		["leap", Vector3(24, 0, -3.5)], ["goto", Vector3(25.2, 0, -3.8), 0.7], ["leap", Vector3(31, 0, -4)], ["goto", Vector3(35.8, 0, 4.2), 1.0],
		["leap", Vector3(40.5, 0, 0.9)], ["stop"], ["wait", 0.15], ["leap", Vector3(43.4, 0, -2.8)], ["stop"], ["wait", 0.15],
		["leap", Vector3(46.1, 0, -6.2)], ["stop"], ["wait", 0.15], ["leap", Vector3(48.5, 0, -9.2)], ["stop"], ["wait", 0.15],
		["leap", Vector3(51.3, 0, -12.8)], ["stop"], ["wait", 0.15], ["leap", Vector3(51.4, 0, -12.9)], ["stop"], ["wait", 5.0], ["star", "terraces"],
	],
	"waterfall": [
		["warp", Vector3(28, 2.6, -26)], ["goto", Vector3(28, 0, -35.0), 0.6], ["leap", Vector3(28, 0, -39.5)], ["stop"],
		["wait", 5.0], ["star", "waterfall"],
	],
	"pagoda": [
		["warp", Vector3(-32.5, 3.0, -10)], ["hop", Vector3(-36, 0, -12), 2.4, 0.5], ["stop"], ["wait", 0.3],
		["hop", Vector3(-35.5, 0, -16.5), 3.2, 0.6], ["stop"], ["wait", 0.3],
		["hop", Vector3(-37.5, 0, -20.5), 3.2, 0.6], ["stop"], ["wait", 0.3],
		["hop", Vector3(-41.5, 0, -22), 3.3, 0.6], ["stop"], ["wait", 0.3],
		["hop", Vector3(-42, 0, -16.2), 4.2, 0.75], ["stop"], ["wait", 5.0], ["star", "pagoda"],
	],
	"karst": [
		# each spring hop is tested from standing on the spring (walking onto a 0.5 m drum is trivial)
		["warp", Vector3(-16, 3.2, -46.5)], ["wait_air"], ["glide", Vector3(-20, 0, -50)], ["stop"], ["wait", 0.6], ["on_top", 10.0],
		["warp", Vector3(-20, 11.8, -50)], ["wait_air"], ["glide", Vector3(-12.5, 0, -50.5)], ["glide", Vector3(-16, 0, -56.5)],
		["stop"], ["wait", 5.0], ["star", "karst"],
	],
	"karst_side": [
		["warp", Vector3(-12.5, 2.4, -45)], ["goto", Vector3(-10.5, 0, -48.8), 0.5], ["leap", Vector3(-8.8, 0, -52), 0.35, false], ["stop"], ["wait", 0.3],
		["leap", Vector3(-8, 0, -58), 0.35, true], ["stop"], ["wait", 0.5], ["check_red", 1],
	],
	"lagoon": [
		["warp", Vector3(7, 2.6, 6)], ["goto", Vector3(11.8, 0, 9.6), 0.5], ["leap", Vector3(15.5, 0, 13.0)], ["stop"], ["wait", 0.15],
		["leap", Vector3(19.5, 0, 16.8), 0.35, false, true], ["stop"], ["wait", 0.15], ["leap", Vector3(23.8, 0, 20.2), 0.35, false, true], ["stop"], ["wait", 0.15],
		["leap", Vector3(27.8, 0, 23.4), 0.35, false, true], ["stop"], ["wait_boat", 0], ["leap_boat"], ["stop"], ["ride"],
		["leap", Vector3(43.5, 0, 37.5), 0.35, true], ["stop"], ["wait", 0.2],
		["hop_jelly", Vector3(47.8, 0, 40.0), 2.6, 0.6], ["stop"], ["wait", 0.2], ["hop", Vector3(51.0, 0, 43.6), 3.2, 0.55], ["stop"], ["wait", 0.2],
		["hop", Vector3(55.8, 0, 48.4), 5.0, 0.7], ["goto", Vector3(58, 0, 52), 0.6], ["stop"], ["wait", 5.0], ["star", "lagoon"],
	],
	"crabs": [
		["warp", Vector3(-40, 2.5, 36)], ["hunt"], ["wait", 2.0], ["goto", Vector3(-40, 0, 36), 0.5], ["stop"], ["wait", 5.0], ["star", "crabs"],
	],
	"coins": [
		["collect_coins", 100], ["wait", 1.2], ["reach_star", "coins"], ["stop"], ["wait", 5.0], ["star", "coins"],
	],
	"hl_village": [
		["warp", Vector3(12.5, 1.3, 1.0)], ["hop", Vector3(18.0, 0, -0.5), 3.2, 0.8], ["stop"], ["wait", 0.2],
		["goto", Vector3(20.5, 0, -1.2), 0.5], ["goto", Vector3(40.6, 0, -1.2), 0.5], ["stop"], ["wait", 0.3],
		["hop", Vector3(39.2, 0, -2.05), 1.8, 0.5], ["stop"], ["wait", 0.3],
		["leap", Vector3(38.7, 0, -4.4), 0.35, true], ["goto", Vector3(37.8, 0, -5.83), 0.35], ["stop"], ["wait", 5.0], ["star", "halong_village"],
	],
	"hl_cave": [
		["warp", Vector3(-23.5, 1.4, -23.5)], ["hop", Vector3(-27.5, 0, -27.0), 2.4, 0.5], ["stop"], ["wait", 0.3],
		["hop", Vector3(-30.8, 0, -25.2), 3.0, 0.55], ["stop"], ["wait", 0.3],
		["hop", Vector3(-34.0, 0, -28.0), 3.0, 0.55], ["stop"], ["wait", 0.3],
		["hop", Vector3(-33.2, 0, -32.4), 3.3, 0.55], ["stop"], ["wait", 0.3],
		["hop", Vector3(-29.5, 0, -36.5), 4.4, 0.7], ["stop"], ["wait", 5.0], ["star", "halong_cave"],
	],
	"hl_trongmai": [
		["warp", Vector3(-24.8, 1.2, 28.5)], ["goto", Vector3(-24.8, 0, 25.0), 0.4], ["stop"], ["wait", 0.3],
		["wallclimb", Vector3(-1, 0, 0), 9.6, Vector3(-22.2, 0, 25.0)], ["stop"], ["wait", 0.5],
		["goto", Vector3(-22.2, 0, 25.0), 0.3], ["stop"], ["wait", 0.3],
		["leap", Vector3(-27.4, 0, 25.0), 0.35, true], ["goto", Vector3(-27.4, 0, 25.0), 0.3], ["stop"], ["wait", 5.0], ["star", "halong_trongmai"],
	],
	"hl_dragon": [
		["warp", Vector3(7.2, 1.4, 1.0)], ["board_dragon"], ["run_to_head", 40.0], ["wait", 5.0], ["star", "halong_dragon"],
	],
	"hl_titop": [
		["warp", Vector3(7.2, 1.4, 1.0)], ["board_dragon"], ["ride_near", Vector3(28, 0, -42), 7.5, 18.5],
		["hop", Vector3(29.3, 0, -41.2), 20.0, 0.7], ["goto", Vector3(29.3, 0, -41.2), 0.4], ["stop"], ["wait", 5.0], ["star", "halong_titop"],
	],
	"hl_pearls": [
		["collect_red"], ["wait", 1.5], ["warp", Vector3(0, 1.4, 1.5)], ["goto", Vector3(0, 0, -3.5), 0.5], ["stop"], ["wait", 5.0], ["star", "halong_pearls"],
	],
	"bridges": [
		["warp", Vector3(-11.5, 2.6, -4.2)], ["goto", Vector3(-18.6, 0, -5.7), 0.4], ["leap", Vector3(-22.6, 0, -6.4)], ["goto", Vector3(-28.5, 0, -7.6), 0.6],
		["stop"], ["check_y", 1.8],
		["warp", Vector3(-4.4, 2.6, -12.0)], ["goto", Vector3(-6.0, 0, -17.0), 0.4], ["goto", Vector3(-11.2, 0, -35.0), 0.6], ["stop"], ["check_y", 1.2],
	],
	"lanterns": [
		["collect_red"], ["wait", 1.5], ["warp", Vector3(-38.5, 3.0, -7.5)], ["goto", Vector3(-38.5, 0, -10.5), 0.5], ["stop"], ["wait", 5.0], ["star", "lanterns"],
	],
	# ---- Đà Nẵng – Hội An (--level=danang)
	"dn_dragon": [["dn_dragon_back"], ["stop"], ["wait", 5.0], ["star", "danang_dragon"]],
	"dn_goldenbridge": [["dn_cable"], ["dn_bridge_walk"], ["stop"], ["wait", 5.0], ["star", "danang_goldenbridge"]],
	"dn_marble": [["dn_marble_climb"], ["stop"], ["wait", 5.0], ["star", "danang_marble"]],
	"dn_chuacau": [
		["warp", Vector3(31.0, 2.2, 25.6)], ["hop", Vector3(31.0, 0, 27.9), 1.9, 0.45], ["stop"], ["wait", 0.3],
		["hop", Vector3(31.0, 0, 29.4), 1.3, 0.5], ["stop"], ["wait", 0.3],
		["goto", Vector3(32.6, 0, 32.6), 0.4], ["stop"], ["wait", 0.2],
		["leap", Vector3(35.9, 0, 33.8), 0.35, false], ["stop"], ["wait", 0.2],
		["goto", Vector3(37.0, 0, 38.8), 0.35], ["stop"], ["wait", 5.0], ["star", "hoian_bridge"],
	],
	"dn_basket": [["warp", Vector3(51.5, 2.0, 18.6)], ["dn_baskets"], ["stop"], ["wait", 5.0], ["star", "hoian_basket"]],
	"dn_lanterns": [
		["collect_red"], ["wait", 1.5], ["warp", Vector3(30.0, 2.4, 44.0)], ["goto", Vector3(30.0, 0, 46.5), 0.5], ["stop"], ["wait", 5.0], ["star", "hoian_lanterns"],
	],
	"dn_coins": [
		["collect_coins", 100], ["wait", 1.2], ["reach_star", "danang_coins"], ["stop"], ["wait", 5.0], ["star", "danang_coins"],
	],
}

var player: Player
var route: Array = []
var name_list: Array = []
var _results: Dictionary = {}
var trace := false


func _ready() -> void:
	trace = Game.args.has("trace")
	if not Game.args.has("bot"):
		return # used as a move library by the trailer director
	var which := String(Game.args.get("bot", "moves"))
	name_list = ROUTES.keys() if which == "all" else which.split(",")
	await get_tree().create_timer(0.6).timeout
	player = get_tree().get_first_node_in_group("player")
	for n in name_list:
		await _run(n)
	print("BOT RESULTS: ", _results)
	get_tree().quit()


func _log(msg: String) -> void:
	print("[bot %.2f] %s" % [Time.get_ticks_msec() / 1000.0, msg])


func _run(n: String) -> void:
	while player.state == Player.S.RESPAWN or Game.in_cutscene:
		await get_tree().physics_frame
	await get_tree().create_timer(0.3).timeout
	_log("route " + n)
	Game.hp = Game.MAX_HP
	var ok := true
	for step in ROUTES[n]:
		var r = await _step(step)
		if r == false:
			ok = false
			_log("  FAILED at %s  pos=%s state=%s" % [str(step), str(player.global_position), Player.S.keys()[player.state]])
			break
	_results[n] = ok
	player.bot_world_dir = Vector3.ZERO
	# let any star cutscene finish
	while Game.in_cutscene:
		await get_tree().process_frame
	await get_tree().create_timer(0.5).timeout


func _step(step: Array):
	if trace: _log("  step %s  at (%.1f,%.1f,%.1f) %s" % [str(step), player.global_position.x, player.global_position.y, player.global_position.z, Player.S.keys()[player.state]])
	var op: String = step[0]
	match op:
		"warp":
			player.teleport(step[1], Vector3.FORWARD)
			player.camera.snap_behind()
			await get_tree().create_timer(0.4).timeout
		"wait":
			await _wait(step[1])
		"hold":
			player.bot_world_dir = step[1]
			await _wait(step[2])
			player.bot_world_dir = Vector3.ZERO
		"goto":
			return await _goto(step[1], step[2])
		"jump":
			player.bot_jump = true
			player.bot_jump_hold = true
			await _wait(step[1])
			player.bot_jump_hold = false
		"djump":
			player.bot_jump = true
			player.bot_jump_hold = true
			await _wait(0.3)
			player.bot_jump_hold = false
		"dash":
			player.bot_dash = true
			await get_tree().physics_frame
		"pound":
			player.bot_pound = true
			await get_tree().physics_frame
		"hop":
			return await _hop(step[1], step[2], step[3] if step.size() > 3 else 1.0)
		"hop_jelly":
			var best: Node3D
			for n in get_tree().get_nodes_in_group("unsafe"):
				if n is JellyBlock and (best == null or (n as Node3D).global_position.distance_to(step[1]) < best.global_position.distance_to(step[1])):
					best = n
			return await _hop(step[1], step[2], step[3], best)
		"collect_coins":
			# far coins first, so a few stay on home island to walk into at the end
			var all := get_tree().get_nodes_in_group("coin")
			all.sort_custom(func(a, b): return (a as Node3D).global_position.length() > (b as Node3D).global_position.length())
			for c in all:
				if Game.coins >= int(step[1]) - 1:
					break
				while Game.in_cutscene:
					await get_tree().physics_frame
				if not is_instance_valid(c):
					continue
				player.teleport((c as Node3D).global_position + Vector3(0, -0.2, 0), Vector3.FORWARD)
				await _wait(0.15)
			# walk into the last one on home island like a player would
			player.teleport(Vector3(0, 2.6, 12), Vector3.FORWARD)
			await _wait(0.6)
			var last: Node3D
			for c in get_tree().get_nodes_in_group("coin"):
				if is_instance_valid(c) and absf((c as Node3D).global_position.y - player.global_position.y) < 1.2 and (last == null or (c as Node3D).global_position.distance_to(player.global_position) < last.global_position.distance_to(player.global_position)):
					last = c
			await _goto(last.global_position, 0.3)
			player.bot_world_dir = Vector3.ZERO
			await _wait(0.6)
			_log("  coins: %d" % Game.coins)
			return Game.coins >= int(step[1])
		"reach_star":
			for n in get_tree().get_nodes_in_group("star"):
				if (n as Star).id == step[1] and n.visible:
					return await _hop((n as Node3D).global_position, 1.2, 0.5)
			return false
		"wallclimb":
			return await _wallclimb(step[1], step[2], step[3] if step.size() > 3 else Vector3.INF)
		"board_dragon":
			return await _board_dragon()
		"run_to_head":
			var dr := get_tree().get_first_node_in_group("dragon") as Dragon
			var t := 0.0
			while t < float(step[1]):
				await get_tree().physics_frame
				t += get_physics_process_delta_time()
				_trace()
				if Game.in_cutscene:
					player.bot_world_dir = Vector3.ZERO
					return true
				# follow the spine: aim at the segment just ahead of the one underfoot
				var near := 0
				for i in dr.get_child_count():
					if (dr.get_child(i) as Node3D).global_position.distance_to(player.global_position) < (dr.get_child(near) as Node3D).global_position.distance_to(player.global_position):
						near = i
				var aim := (dr.get_child(maxi(near - 1, 0)) as Node3D).global_position
				if near <= 1:
					aim = dr.head.global_transform * Vector3(0, 0, -0.9)
				if trace and Engine.get_physics_frames() % 6 == 0:
					var sg := dr.get_child(near) as Node3D
					print("   seg %d at %s  local player %s" % [near, sg.global_position, sg.global_transform.affine_inverse() * player.global_position])
				var d := (aim - player.global_position) * Vector3(1, 0, 1)
				player.bot_world_dir = d.normalized() * clampf(d.length() / 1.5, 0.3, 0.6)
				if player.state == Player.S.RESPAWN:
					return false
			return false
		"ride_near":
			var t := 0.0
			var target: Vector3 = step[1]
			player.bot_world_dir = Vector3.ZERO
			while t < 60.0:
				await get_tree().physics_frame
				t += get_physics_process_delta_time()
				_trace()
				var d := Vector2(target.x - player.global_position.x, target.z - player.global_position.z).length()
				if d < float(step[2]) and player.global_position.y > float(step[3]):
					return true
				if player.state == Player.S.RESPAWN:
					return false
			return false
		"dn_dragon_back":
			# onto the tail, then run the golden back hump by hump to the head
			var w := get_tree().get_first_node_in_group("world") as DanangWorld
			var parts := w.gold_dragon
			player.teleport(parts[parts.size() - 1].global_position + Vector3.UP * 1.8, Vector3.FORWARD)
			await _wait(0.5)
			for i in range(parts.size() - 2, -1, -1):
				if not await _goto(parts[i].global_position, 0.7, 6.0):
					return Game.in_cutscene
				if Game.in_cutscene:
					return true
			return await _goto(parts[0].global_transform * Vector3(0, 0, -0.6), 0.3) or Game.in_cutscene
		"dn_cable":
			# wait on the boarding deck for a cabin, hop on its roof and ride to the summit
			var w := get_tree().get_first_node_in_group("world") as DanangWorld
			player.teleport(w.cable_deck + Vector3.UP * 0.6, Vector3.FORWARD)
			await _wait(0.4)
			var car: Sampan
			var t := 0.0
			while car == null and t < 45.0:
				for c in w.cable_cars:
					if c.global_position.distance_to(c.a) < 0.3:
						car = c
				await get_tree().physics_frame
				t += get_physics_process_delta_time()
			if car == null:
				return false
			await _wait(0.4)
			if not await _leap(car.global_position, 0.3, false, true):
				return false
			player.bot_world_dir = Vector3.ZERO
			t = 0.0
			while t < 25.0 and car.global_position.distance_to(car.b) > 0.3:
				var d := (car.global_position - player.global_position) * Vector3(1, 0, 1)
				player.bot_world_dir = d.normalized() * 0.3 if d.length() > 0.5 else Vector3.ZERO
				await get_tree().physics_frame
				t += get_physics_process_delta_time()
			player.bot_world_dir = Vector3.ZERO
			_log("  rode to y=%.1f" % player.global_position.y)
			return player.global_position.y > DanangWorld.UPPER_TOP
		"dn_bridge_walk":
			var w := get_tree().get_first_node_in_group("world") as DanangWorld
			var p0: Vector3 = w.bridge_path[w.bridge_path.size() - 1]
			var p1: Vector3 = w.bridge_path[w.bridge_path.size() - 2]
			if not await _goto(p0 + (p0 - p1).normalized() * 2.5, 0.6, 10.0):
				return false
			for i in range(w.bridge_path.size() - 1, -1, -1):
				if Game.in_cutscene:
					return true
				if not await _goto(w.bridge_path[i], 0.5, 6.0):
					return Game.in_cutscene
			return true
		"dn_marble_climb":
			var w := get_tree().get_first_node_in_group("world") as DanangWorld
			var first: Vector3 = w.marble_ledges[0]
			var out := (first - w.thuy_son) * Vector3(1, 0, 1)
			player.teleport(Vector3(first.x, 0, first.z) + out.normalized() * 3.5 + Vector3.UP * 2.2, Vector3.FORWARD)
			await _wait(0.5)
			for l in w.marble_ledges:
				if not await _hop(l, 2.4, 0.55):
					return false
				player.bot_world_dir = Vector3.ZERO
				await _wait(0.3)
			var last: Vector3 = w.marble_ledges[w.marble_ledges.size() - 1]
			var edge := w.thuy_son + ((last - w.thuy_son) * Vector3(1, 0, 1)).normalized() * 2.6
			if not await _hop(edge, 3.5, 0.6):
				return false
			return await _goto(w.thuy_son + Vector3(0, 0, 2.6), 0.4)
		"dn_baskets":
			var w := get_tree().get_first_node_in_group("world") as DanangWorld
			for b in w.basket_boats:
				if not await _leap(b.global_position, 0.35, false):
					return false
				player.bot_world_dir = Vector3.ZERO
				await _wait(0.25)
			if not await _leap(Vector3(60.5, 0, -9.0), 0.35, false):
				return false
			return await _goto(Vector3(60.5, 0, -12.0), 0.35)
		"back":
			# step back from the edge of a pillar, away from the next target, to get a run-up
			var away: Vector3 = (player.global_position - (step[1] as Vector3)) * Vector3(1, 0, 1)
			player.bot_world_dir = away.normalized() * 0.5
			await _wait(step[2] * 0.4)
			player.bot_world_dir = Vector3.ZERO
			await _wait(0.1)
		"stop":
			player.bot_world_dir = Vector3.ZERO
		"leap":
			return await _leap(step[1], step[2] if step.size() > 2 else 0.35, step[3] if step.size() > 3 else false, step[4] if step.size() > 4 else false)
		"glide":
			return await _glide(step[1])
		"wait_air":
			var t := 0.0
			while player.is_on_floor() and t < 1.0:
				await get_tree().physics_frame
				t += get_physics_process_delta_time()
		"leap_boat":
			var boat := _nearest_boat()
			return await _leap(boat.global_position, 0.3, false, true)
		"on_top":
			var ok := player.is_on_floor() and player.global_position.y > float(step[1])
			_log("  on top (y > %s): %s  y=%.2f" % [step[1], ok, player.global_position.y])
			return ok
		"check_y":
			await _wait(0.4)
			_log("  y=%.2f (need > %s)" % [player.global_position.y, step[1]])
			return player.global_position.y > float(step[1])
		"check_red":
			return Game.red_coins >= int(step[1])
		"star":
			var got := Game.has_star(step[1])
			_log("  star %s: %s" % [step[1], "YES" if got else "no"])
			return got
		"hunt":
			return await _hunt()
		"collect_red":
			return await _collect_red()
		"wait_boat":
			var boat := _nearest_boat()
			var t := 0.0
			while boat.global_position.distance_to(boat.a) > 0.4 and t < 20.0:
				await get_tree().physics_frame
				t += get_physics_process_delta_time()
			if t >= 20.0:
				return false
		"goto_boat":
			var boat := _nearest_boat()
			return await _goto(boat.global_position, step[1])
		"ride":
			var boat := _nearest_boat()
			var t := 0.0
			while t < 20.0 and boat.global_position.distance_to(boat.b) > 0.4:
				# stay near the middle of the deck
				var d := (boat.global_position - player.global_position) * Vector3(1, 0, 1)
				player.bot_world_dir = d.normalized() * 0.3 if d.length() > 0.5 else Vector3.ZERO
				await get_tree().physics_frame
				t += get_physics_process_delta_time()
			player.bot_world_dir = Vector3.ZERO
			if player.global_position.y < 0.2:
				return false
	return true


func _nearest_boat() -> Sampan:
	var best: Sampan
	for n in get_tree().get_nodes_in_group("unsafe"):
		if n is Sampan and (best == null or (n as Node3D).global_position.distance_to(player.global_position) < best.global_position.distance_to(player.global_position)):
			best = n
	return best


func _wait(s: float) -> void:
	var t := 0.0
	while t < s:
		await get_tree().physics_frame
		t += get_physics_process_delta_time()
		_trace()


func _goto(target: Vector3, tol: float, timeout := 8.0) -> bool:
	var t := 0.0
	while t < timeout:
		var d := Vector3(target.x - player.global_position.x, 0, target.z - player.global_position.z)
		if d.length() < tol:
			return true
		player.bot_world_dir = d.normalized() * clampf(d.length() / 1.5, 0.35, 1.0)
		await get_tree().physics_frame
		t += get_physics_process_delta_time()
		_trace()
		if player.state == Player.S.RESPAWN:
			player.bot_world_dir = Vector3.ZERO
			return false
	player.bot_world_dir = Vector3.ZERO
	return false


## A running jump toward `target`, steering all the way; optional double jump at the apex.
## `short` jumps from a standstill toward a close target (lotus hopping).
func _leap(target: Vector3, hold: float, double: bool, short := false) -> bool:
	var dir := (target - player.global_position) * Vector3(1, 0, 1)
	player.bot_world_dir = dir.normalized()
	if short:
		await _wait(0.12)
	player.bot_jump = true
	player.bot_jump_hold = true
	var t := 0.0
	var did_double := false
	var left := false
	while t < 4.0:
		await get_tree().physics_frame
		t += get_physics_process_delta_time()
		_trace()
		left = left or not player.is_on_floor()
		if not left and t > 0.25:
			player.bot_jump = true
			player.bot_jump_hold = true
			t = 0.0
		if t > hold:
			player.bot_jump_hold = false
		var d := (target - player.global_position) * Vector3(1, 0, 1)
		player.bot_world_dir = d.normalized() * clampf(d.length() / 1.2, 0.2, 1.0) if d.length() > 0.25 else Vector3.ZERO
		if double and not did_double and player.velocity.y < 1.5 and t > 0.15:
			did_double = true
			player.bot_jump = true
			player.bot_jump_hold = true
			await _wait(0.3)
			player.bot_jump_hold = false
		if left and t > 0.2 and player.is_on_floor():
			return true
		if player.state == Player.S.RESPAWN:
			return false
	return false


## Runs at `target` and jumps once within `jump_dist`, steering (and braking) until landed.
func _hop(target: Vector3, jump_dist: float, speed := 1.0, follow: Node3D = null) -> bool:
	var t := 0.0
	var jumped := false
	var jt := 0.0
	while t < 6.0:
		await get_tree().physics_frame
		t += get_physics_process_delta_time()
		_trace()
		if follow:
			target = follow.global_position
		var d := (target - player.global_position) * Vector3(1, 0, 1)
		if not jumped:
			player.bot_world_dir = d.normalized() * speed
			if d.length() < jump_dist:
				jumped = true
				player.bot_jump = true
				player.bot_jump_hold = true
		else:
			jt += get_physics_process_delta_time()
			if jt > 0.35:
				player.bot_jump_hold = false
			player.bot_world_dir = d.normalized() * clampf(d.length() / 1.0, 0.0, 1.0) if d.length() > 0.2 else Vector3.ZERO
			if jt > 0.2 and player.is_on_floor():
				return true
		if player.state == Player.S.RESPAWN:
			return false
	return false


## Wall-kicks up between two walls: jump toward `dir`, then kick every time we slide.
func _wallclimb(dir: Vector3, height: float, land := Vector3.INF) -> bool:
	player.bot_world_dir = dir
	player.bot_jump = true
	player.bot_jump_hold = true
	var t := 0.0
	var push := dir
	while t < 12.0:
		await get_tree().physics_frame
		t += get_physics_process_delta_time()
		_trace()
		if player.state == Player.S.WALL_SLIDE:
			player.bot_jump = true
			player.bot_jump_hold = true
			# the kick sends us back across the gap
			push = -push
		player.bot_world_dir = push
		if land != Vector3.INF and player.global_position.y > height and player.state == Player.S.AIR:
			var d := (land - player.global_position) * Vector3(1, 0, 1)
			player.bot_world_dir = d.normalized() * clampf(d.length(), 0.0, 1.0)
		if player.is_on_floor() and player.global_position.y > height:
			player.bot_world_dir = Vector3.ZERO
			return true
		if player.is_on_floor() and t > 0.5:
			push = dir
			player.bot_world_dir = dir
			player.bot_jump = true
			player.bot_jump_hold = true
		if player.state == Player.S.RESPAWN:
			return false
	return false


## Waits at the shore for the dragon's back to pass, then hops onto the nearest segment.
func _board_dragon() -> bool:
	var dr := get_tree().get_first_node_in_group("dragon") as Dragon
	var t := 0.0
	while t < 90.0:
		await get_tree().physics_frame
		t += get_physics_process_delta_time()
		for i in range(4, dr.get_child_count() - 2):
			var seg := dr.get_child(i) as Node3D
			var d := Vector2(seg.global_position.x - player.global_position.x, seg.global_position.z - player.global_position.z).length()
			if d < 4.6 and seg.global_position.y < 1.6:
				var ok := await _hop(seg.global_position, 4.0, 0.8, seg)
				player.bot_world_dir = Vector3.ZERO
				await _wait(0.3)
				return ok and player.global_position.y > 0.5
	return false


## Already airborne (after a spring): steer to `target` and double-jump at the apex.
func _glide(target: Vector3) -> bool:
	var t := 0.0
	var did_double := false
	var rose := false
	while t < 4.0:
		await get_tree().physics_frame
		t += get_physics_process_delta_time()
		_trace()
		rose = rose or player.velocity.y > 8.0
		var d := (target - player.global_position) * Vector3(1, 0, 1)
		player.bot_world_dir = d.normalized() * clampf(d.length() / 1.2, 0.2, 1.0) if d.length() > 0.25 and rose else Vector3.ZERO
		if rose and not did_double and player.velocity.y < 1.0:
			did_double = true
			player.bot_jump = true
			player.bot_jump_hold = true
			await _wait(0.3)
			player.bot_jump_hold = false
		if t > 0.3 and player.is_on_floor():
			return true
		if player.state == Player.S.RESPAWN:
			return false
	return false


func _hunt() -> bool:
	var t := 0.0
	while t < 60.0:
		var crabs := get_tree().get_nodes_in_group("beach_crab")
		if crabs.is_empty():
			return true
		var c := crabs[0] as Node3D
		await _goto(c.global_position, 4.0, 6.0)
		player.bot_jump = true
		player.bot_jump_hold = true
		await _wait(0.2)
		player.bot_jump_hold = false
		var land := 0.0
		while land < 1.2:
			if is_instance_valid(c):
				player.bot_world_dir = ((c.global_position - player.global_position) * Vector3(1, 0, 1)).normalized()
			await get_tree().physics_frame
			land += get_physics_process_delta_time()
		player.bot_world_dir = Vector3.ZERO
		t += 3.0
	return false


## Warps next to each lantern (the routes to them are tested separately) and grabs it.
func _collect_red() -> bool:
	for c in get_tree().get_nodes_in_group("red_coin"):
		var p := (c as Node3D).global_position
		player.teleport(p + Vector3(0, -0.2, 0), Vector3.FORWARD)
		await _wait(0.4)
	return Game.red_coins >= 8


func _trace() -> void:
	var every := 2 if Game.args.has("trace-fine") else 15
	if trace and Engine.get_physics_frames() % every == 0:
		print("  t pos=(%.1f,%.1f,%.1f) v=(%.1f,%.1f,%.1f) %s floor=%s" % [player.global_position.x, player.global_position.y, player.global_position.z, player.velocity.x, player.velocity.y, player.velocity.z, Player.S.keys()[player.state], player.is_on_floor()])
