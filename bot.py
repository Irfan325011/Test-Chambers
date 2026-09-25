import os

# ... rest of your script ...
import discord
from discord.ext import tasks, commands
from datetime import datetime, timezone

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Target Channel ID (Replace with your channel's ID)
CHANNEL_ID = 1552651786320613489

# TDS Challenge Trial rotation sequence
MODIFIERS = [
    {"name": "Hidden Enemies", "desc": "Enemies are hidden by default and require detection."},
    {"name": "Glass", "desc": "Towers take increased damage or have lowered health."},
    {"name": "Jailed", "desc": "Random tower slots are locked during play."},
    {"name": "Exploding Enemies", "desc": "Enemies explode upon death, damaging nearby towers."},
    {"name": "Limitation", "desc": "Strict placement limits applied to all towers."},
    {"name": "Committed", "desc": "Towers cannot be sold once placed on the map."},
    {"name": "Healthy Enemies", "desc": "All enemies spawn with significantly boosted health."},
    {"name": "Speedy Enemies", "desc": "Enemies move much faster than standard speed."},
    {"name": "Fog", "desc": "Map visibility is obscured by heavy fog."},
    {"name": "Flying Enemies", "desc": "Flying units spawn continuously throughout waves."},
    {"name": "Broke", "desc": "Starting cash and income generation are severely reduced."},
    {"name": "Quarantine", "desc": "Towers must be spaced far apart from each other."},
    {"name": "Inflation", "desc": "Tower placement and upgrade costs are increased by 50%."}
]

# UTC anchor reference point
ANCHOR_TIME = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

def get_current_modifier():
    """Calculates current and next modifier based on elapsed 3-hour intervals."""
    now = datetime.now(timezone.utc)
    hours_elapsed = int((now - ANCHOR_TIME).total_seconds() // 3600)
    
    current_index = (hours_elapsed // 3) % len(MODIFIERS)
    next_index = (current_index + 1) % len(MODIFIERS)
    
    return MODIFIERS[current_index], MODIFIERS[next_index]

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    if not notify_trial.is_running():
        notify_trial.start()

@tasks.loop(hours=3)
async def notify_trial():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        current_mod, next_mod = get_current_modifier()
        
        embed = discord.Embed(
            title=f"⚔️ Active Trial: {current_mod['name']}",
            description=f"**Modifier Effect:**\n{current_mod['desc']}",
            color=0x3498db
        )
        embed.add_field(
            name="🔮 Up Next (In 3 Hours)", 
            value=f"**{next_mod['name']}**", 
            inline=False
        )
        embed.set_footer(text="Next trial refresh in 3 hours")
        
        await channel.send(embed=embed)

@notify_trial.before_loop
async def before_notify():
    await bot.wait_until_ready()

# Read the token safely from the host environment
TOKEN = os.getenv('BOT_TOKEN')

if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: BOT_TOKEN variable was not found!")
