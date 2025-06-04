import discord
import os

TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CATEGORY_ID = int(os.getenv("CATEGORY_ID"))
TO_VC_ID = int(os.getenv("TO_VC_ID"))
NEW_ROLE_ID = int(os.getenv("NEW_ROLE_ID"))
ROLES_TO_REMOVE = list(map(int, os.getenv("ROLES_TO_REMOVE").split(",")))

intents = discord.Intents.all()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Bot is ready: {client.user}")

@client.event
async def on_guild_channel_delete(channel):
    if channel.category_id != CATEGORY_ID:
        return

    guild = client.get_guild(GUILD_ID)
    if not guild:
        return

    # Extract user IDs from permission overwrites
    user_ids = [
        int(target_id)
        for target_id, overwrite in channel.overwrites.items()
        if isinstance(target_id, int)
    ]

    for user_id in user_ids:
        member = guild.get_member(user_id)
        if not member:
            continue

        # Move member to new VC
        if member.voice:
            try:
                await member.move_to(guild.get_channel(TO_VC_ID))
            except:
                print(f"Couldn't move {member.display_name}")

        # Remove roles
        roles_to_remove = [guild.get_role(rid) for rid in ROLES_TO_REMOVE]
        await member.remove_roles(*filter(None, roles_to_remove))

        # Add new role
        new_role = guild.get_role(NEW_ROLE_ID)
        if new_role:
            await member.add_roles(new_role)

client.run(TOKEN)

