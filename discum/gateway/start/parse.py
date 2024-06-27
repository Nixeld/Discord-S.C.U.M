from ..types import Types

#parse (remember to do static methods, unless you're changing the formatting)
class StartParse(object): 
	@staticmethod
	# the old ready method was taking too long to run resulting in session.settings_ready returning an empty dictionary
	# this causes bot.gateway.session.user and bot.gateway.session.guild to return an empty dictionary as well
	# i have no idea what i am doing so i put the old code through chatgpt to optimise it and it seems to be working for...
	# ...what i am using it for so this will require testing to see if there is any problems with it
	def ready(response):
		if not response or 'd' not in response:
			print("Invalid response structure")
			return {}
		
		ready_data = dict(response["d"])
		ready_data.pop("merged_members", None)

		user_pool = {h["id"]: h for h in response["d"].get("users", [])}

		# Parse relationships
		relationships = response["d"].get("relationships", [])
		ready_data["relationships"] = {
			i["id"]: dict(
				dict(i, **{"type": Types.relationshipTypes.get(i["type"], "unknown")}),
				**user_pool.get(i["id"], {})
			) for i in relationships
		}

		# Parse private channels
		private_channels = response["d"].get("private_channels", [])
		ready_data["private_channels"] = {}
		for j in private_channels:
			channel_data = dict(j, **{"type": Types.channelTypes.get(j["type"], "unknown")})
			if "recipient_ids" in channel_data:
				recipient_ids = channel_data.pop("recipient_ids")
				channel_data["recipients"] = {q: user_pool.get(q, {}) for q in recipient_ids}
			ready_data["private_channels"][j["id"]] = channel_data

		# Add activities key to user settings
		user_guild_settings = ready_data.get("user_guild_settings", {})
		user_guild_settings["activities"] = {}
		ready_data["user_guild_settings"] = user_guild_settings

		# Parse guilds
		guilds = response["d"].get("guilds", [])
		ready_data["guilds"] = {k["id"]: k for k in guilds}
		for personal_role, guild in zip(response["d"].get("merged_members", []), guilds):
			guild_id = guild["id"]
			if "unavailable" not in ready_data["guilds"].get(guild_id, {}):
				# Take care of emojis
				emojis = guild.get("emojis", [])
				if isinstance(emojis, list):
					ready_data["guilds"][guild_id]["emojis"] = {l["id"]: l for l in emojis}

				# Take care of roles
				roles = guild.get("roles", [])
				if isinstance(roles, list):
					ready_data["guilds"][guild_id]["roles"] = {m["id"]: m for m in roles}

				# Take care of channels
				channels = guild.get("channels", [])
				if isinstance(channels, list):
					ready_data["guilds"][guild_id]["channels"] = {
						n["id"]: dict(n, **{"type": Types.channelTypes.get(n["type"], "unknown")}) for n in channels
					}

			# Take care of personal role/nick
			my_data = next((i for i in personal_role if i["user_id"] == response["d"]["user"]["id"]), {})
			ready_data["guilds"][guild_id]["my_data"] = my_data

			# Initialize members dictionary
			ready_data["guilds"][guild_id]["members"] = {}

		return ready_data

	@staticmethod
	def ready_supplemental(response):
		ready_supp_data = dict(response["d"])
		ready_supp_data["online_friends"] = {o["user_id"]:o for o in response["d"]["merged_presences"]["friends"]}
		ready_supp_data.pop("guilds")
		ready_supp_data["voice_states"] = {p["id"]:p.get("voice_states",[]) for p in response["d"]["guilds"]} #id is the guild_id
		return ready_supp_data
