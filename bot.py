import discord
from discord.ext import commands, tasks
import os
import asyncio
from datetime import timedelta

# Load environment variables
TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = 1329827340850827274
NEW_ROLE_ID = 1379812422264557729  # Role to assign and remove
TIMEOUT_ROLE_ID = 1369889238375596162  # Role for timed-out users
CATEGORY_ID = 1368300793056464998  # Category ID for text channels
TRACKED_CHANNEL_IDS = [
    1368307501564563669,
    1368440679507951757,
    1368441003291181056,
    1368441708211343440,
    1368441771251470497
]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents, application_id=YOUR_APPLICATION_ID)

# For storing votes per message
vote_sessions = {}

# Custom Message for Captain Reset Protocol
CUSTOM_MESSAGE = """
🔁 Captain Reset Protocol

Please use /captainreset to initiate a captain reset.

🗳️ If the vote ends in a 5 Yes / 5 No tie, a coinflip will be triggered.
The user who called the vote will choose Heads or Tails — if guessed correctly, the match will be closed.

🎙️ Important: All players must remain in the voice channel during captain selection.
🚫 Any player who leaves after the process begins will receive an automatic timeout.
"""

async def has_send_permissions(member):
    """Check if the user has send_message permissions in any text channel within CATEGORY_ID."""
    category = discord.utils.get(member.guild.categories, id=CATEGORY_ID)
    for channel in category.text_channels:
        perms = channel.permissions_for(member)
        if perms.send_messages:  # Check if the user has permission to send messages in the text channel
            return True
    return False

@bot.event
async def on_ready():
    print(f"✅ Bot is online: {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="captainreset", description="Start a vote for captain reset", guild=discord.Object(id=GUILD_ID))
async def captainreset(interaction: discord.Interaction):
    """Start a captain reset vote."""
    # Custom logic for captain reset initiation
    await interaction.response.send_message("Captain reset vote has been initiated! Please cast your votes.", ephemeral=False)

@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild

    # Check if the bot moved the user into another voice channel within the nominated category
    if before.channel and after.channel:
        # If the user is moved by the bot (the bot moved the user into another channel)
        if after.channel.id in TRACKED_CHANNEL_IDS and after.channel.category and after.channel.category.id == CATEGORY_ID:
            if before.channel != after.channel:  # User was moved into another voice channel
                # Check if the bot moved the user by comparing the user and bot's voice state channel
                if member.id != bot.user.id:  # This checks if the user moved themselves (if the member is not the bot)
                    return  # No timeout applies if the user was moved by the bot
                print(f"{member.display_name} was moved by the bot into another voice channel under nominated category. No timeout applied.")
                return

    # If the user leaves a tracked voice channel and has permissions in a text channel, apply timeout
    if before.channel and before.channel.id in TRACKED_CHANNEL_IDS and after.channel is None:
        if await has_send_permissions(member):
            # Apply the 30-minute timeout if they have permission in a text channel
            await apply_timeout(member)

    # If the member joins a voice channel in the tracked list, assign role (check send permissions first)
    if after.channel and after.channel.id in TRACKED_CHANNEL_IDS:
        if await has_send_permissions(member):  # Only assign the role if they have send permissions in a text channel
            role_to_add = guild.get_role(NEW_ROLE_ID)  # Role to add on join
            try:
                if role_to_add:
                    await member.add_roles(role_to_add)
                print(f"Assigned role to {member.display_name} on joining channel {after.channel.name}")
            except Exception as e:
                print(f"Failed to assign role for {member.display_name}: {e}")

@bot.event
async def on_guild_channel_delete(channel):
    """Remove the assigned role when the user is no longer in a voice channel under the nominated category."""
    if isinstance(channel, discord.VoiceChannel) and channel.category and channel.category.id == CATEGORY_ID:
        guild = channel.guild
        role_to_remove = guild.get_role(NEW_ROLE_ID)  # Role to remove
        for member in guild.members:
            # Check if the member was in a voice channel in the nominated category and is no longer in it
            if role_to_remove in member.roles and (not member.voice.channel or member.voice.channel.id not in TRACKED_CHANNEL_IDS):
                try:
                    await member.remove_roles(role_to_remove)
                    print(f"Removed role from {member.display_name} because they weren't in any VC in the specified category after deletion.")
                except Exception as e:
                    print(f"Failed to remove role for {member.display_name}: {e}")

async def apply_timeout(member):
    """ Apply a timeout to the user if they leave the queue early. """
    timeout_duration = time_
