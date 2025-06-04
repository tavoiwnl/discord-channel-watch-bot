import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio

# Load environment variables
TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = 1329827340850827274
CATEGORY_ID = 1368300793056464998  # The category for the text channels for captainreset command
TO_VC_ID = 1379816672851923085
NEW_ROLE_ID = 1368336669861875845  # Role to remove on channel join

CHANNEL_ROLE_MAP = {
    1378100842598629518: (1379814953619558530, 1379812422264557729),
    1378100860562702358: (1379815000306090034, 1379812422264557729),
    1379797554367037581: (1379815009470775358, 1379812422264557729),
    1379797571010301963: (1379815013845438554, 1379812422264557729),
    1379797582255231138: (1379815016970195146, 1379812422264557729),
    1379797629533290537: (1379815020015386757, 1379812422264557729),
}

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# For storing votes per message
vote_sessions = {}

class VoteView(discord.ui.View):
    def __init__(self, initiator: discord.Member):
        super().__init__(timeout=60)  # 60 seconds timeout
        self.initiator = initiator
        self.yes_votes = set()
        self.no_votes = set()
        self.total_votes = 0
        self.message = None  # Will hold the message object after sending

    async def update_message(self):
        # Update the button labels with vote counts
        yes_count = len(self.yes_votes)
        no_count = len(self.no_votes)
        content = f"Vote for captain reset by {self.initiator.display_name}\n" \
                  f"Yes: {yes_count} | No: {no_count}\n" \
                  f"Need 6/10 YES votes to pass."
        await self.message.edit(content=content, view=self)

        # Check if threshold reached
        if yes_count >= 6:
            await self.success_action()

    async def success_action(self):
        # Disable buttons
        for child in self.children:
            child.disabled = True
        await self.update_message()

        # Move initiator out and back in VC
        guild = self.initiator.guild
        voice_state = self.initiator.voice
        if voice_state and voice_state.channel:
            channel = voice_state.channel
            try:
                await self.initiator.move_to(None)  # Disconnect
                await asyncio.sleep(1)
                await self.initiator.move_to(channel)  # Reconnect
                await self.message.channel.send(f"{self.initiator.mention} has been reset in their voice channel.")
            except Exception as e:
                await self.message.channel.send(f"Failed to reset {self.initiator.mention}: {e}")
        else:
            await self.message.channel.send(f"{self.initiator.mention} is not in a voice channel.")

        self.stop()  # End the view

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(content="Vote timed out. Captain reset failed.", view=self)

    def is_voter_eligible(self, interaction: discord.Interaction):
        # Check user is not already voted and is in guild
        if interaction.user.id in self.yes_votes or interaction.user.id in self.no_votes:
            return False
        return True

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_voter_eligible(interaction):
            await interaction.response.send_message("You already voted!", ephemeral=True)
            return
        self.yes_votes.add(interaction.user.id)
        self.total_votes += 1
        await interaction.response.defer()
        await self.update_message()

    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_voter_eligible(interaction):
            await interaction.response.send_message("You already voted!", ephemeral=True)
            return
        self.no_votes.add(interaction.user.id)
        self.total_votes += 1
        await interaction.response.defer()
        await self.update_message()

@bot.event
async def on_ready():
    print(f"✅ Bot is online: {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="captainreset", description="Start a vote to reset your captain status", guild=discord.Object(id=GUILD_ID))
async def captainreset(interaction: discord.Interaction):
    # Only allow command in text channels under CATEGORY_ID with send_message perms

    # Check channel category
    if not interaction.channel or getattr(interaction.channel.category, "id", None) != CATEGORY_ID:
        await interaction.response.send_message("You can only use this command in the designated category channels.", ephemeral=True)
        return

    # Check permissions for user in this channel (send_messages)
    perms = interaction.channel.permissions_for(interaction.user)
    if not perms.send_messages:
        await interaction.response.send_message("You don't have permission to use this command in this channel.", ephemeral=True)
        return

    # Create and send vote view
    view = VoteView(interaction.user)
    content = f"Vote for captain reset by {interaction.user.display_name}\n" \
              f"Yes: 0 | No: 0\n" \
              f"Need 6/10 YES votes to pass."
    message = await interaction.response.send_message(content, view=view, ephemeral=False)
    view.message = await interaction.original_response()

@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild

    # If member joins a voice channel or moves to a new one
    if after.channel and (before.channel != after.channel):

        # Check if the joined channel ID is in our map
        roles_to_add_ids = CHANNEL_ROLE_MAP.get(after.channel.id)
        if roles_to_add_ids:
            roles_to_add = [guild.get_role(rid) for rid in roles_to_add_ids if guild.get_role(rid)]
            role_to_remove = guild.get_role(NEW_ROLE_ID)  # Role to remove

            try:
                # Add roles
                await member.add_roles(*roles_to_add)
                # Remove role
                if role_to_remove:
                    await member.remove_roles(role_to_remove)

                print(f"Updated roles for {member.display_name} on joining channel {after.channel.name}")

            except Exception as e:
                print(f"Failed to update roles for {member.display_name}: {e}")

# (Optional) Your existing on_guild_channel_delete or other event handlers go here...

bot.run(TOKEN)
