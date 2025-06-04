import discord
import os

# Load environment variables
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1329827340850827274
CATEGORY_ID = 1368300793056464998  # ✅ Updated category ID
TO_VC_ID = 1379816672851923085
NEW_ROLE_ID = 1368336669861875845
ROLES_TO_REMOVE = 1379814953619558530,1379815000306090034,1379815009470775358,1379815013845438554,1379815016970195146,1379815020015386757,1379812422264557729

intents = discord.Intents.all()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Bot is online: {client.user}")

@client.event
async def on_guild_channel_delete(channel):
    # Check if the deleted channel was inside the target category
    if channel.category_id != CATEGORY_ID:
        return

    guild = client.get_guild(GUILD_ID)
    if not guild:
        return

    # Extract user IDs from permission overwrites
    user_ids = [
        target.id for target in channel.overwrites
        if isinstance(target, discord.Member)
    ]

    for user_id in user_ids:
        member = guild.get_member(user_id)
        if not member:
            continue

        # Move member to the specified voice channel if they're in VC
        if member.voice:
            try:
                await member.move_to(guild.get_channel(TO_VC_ID))
                print(f"Moved {member.display_name} to voice channel.")
            except Exception as e:
                print(f"Could not move {member.display_name}: {e}")

        # Remove specific roles
        roles_to_remove = [guild.get_role(rid) for rid in ROLES_TO_REMOVE]
        await member.remove_roles(*filter(None, roles_to_remove))

        # Add the new role
        new_role = guild.get_role(NEW_ROLE_ID)
        if new_role:
            await member.add_roles(new_role)

client.run(TOKEN)

