import os
import asyncio
import discord
from discord.ext import tasks, commands
from datetime import datetime, timezone, timedelta

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True  # Required to process ! commands
bot = commands.Bot(command_prefix="!", intents=intents)

# Target channel where automated notifications are posted
CHANNEL_ID = 1552651786320613489  # Replace with your Discord Channel ID

# --- MODIFIER CONFIGURATION ---
# Replace 'role_id': 0 with a Discord Role ID (e.g. 987654321098765432) to ping a specific role when active
MODIFIERS = [
    {
        "name": "Hidden Enemies",
        "emoji": "👁️",
        "desc": "Enemies are hidden by default and require detection.",
        "color": 0x705898,  # Purple
        "role_id": 0
    },
    {
        "name": "Glass",
        "emoji": "⛑️",
        "desc": "Towers take increased damage or have lowered health.",
        "color": 0xE74C3C,  # Bright Red
        "role_id": 0
    },
    {
        "name": "Jailed",
        "emoji": "🔒",
        "desc": "Random tower slots are locked during play.",
        "color": 0x7F8C8D,  # Slate Gray
        "role_id": 0
    },
    {
        "name": "Exploding Enemies",
        "emoji": "💥",
        "desc": "Enemies explode upon death, damaging nearby towers.",
        "color": 0xE67E22,  # Flame Orange
        "role_id": 0
    },
    {
        "name": "Limitation",
        "emoji": "📦",
        "desc": "Strict placement limits applied to all towers.",
        "color": 0x95A5A6,  # Cardboard Silver
        "role_id": 0
    },
    {
        "name": "Committed",
        "emoji": "🗼",
        "desc": "Towers cannot be sold once placed on the map.",
        "color": 0x34495E,  # Steel Navy
        "role_id": 0
    },
    {
        "name": "Healthy Enemies",
        "emoji": "💪",
        "desc": "All enemies spawn with significantly boosted health.",
        "color": 0x2ECC71,  # Hulk Green
        "role_id": 0
    },
    {
        "name": "Speedy Enemies",
        "emoji": "⚡",
        "desc": "Enemies move much faster than standard speed.",
        "color": 0xF1C40F,  # Lightning Yellow
        "role_id": 0
    },
    {
        "name": "Fog",
        "emoji": "🌫️",
        "desc": "Map visibility is obscured by heavy fog.",
        "color": 0xBDC3C7,  # Fog White/Gray
        "role_id": 0
    },
    {
        "name": "Flying Enemies",
        "emoji": "🪽",
        "desc": "Flying units spawn continuously throughout waves.",
        "color": 0x3498DB,  # Sky Blue
        "role_id": 0
    },
    {
        "name": "Broke",
        "emoji": "💸",
        "desc": "Starting cash and income generation are severely reduced.",
        "color": 0x27AE60,  # Cash Green
        "role_id": 0
    },
    {
        "name": "Quarantine",
        "emoji": "☣️",
        "desc": "Towers must be spaced far apart from each other.",
        "color": 0x9B59B6,  # Biohazard Purple
        "role_id": 0
    },
    {
        "name": "Inflation",
        "emoji": "📈",
        "desc": "Tower placement and upgrade costs are increased by 50%.",
        "color": 0x1ABC9C,  # Chart Teal
        "role_id": 0
    }
]

# UTC reference anchor for 3-hour global rotations
ANCHOR_TIME = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

def get_current_modifier():
    """Calculates active trial, next trial, and exact refresh timestamp."""
    now = datetime.now(timezone.utc)
    seconds_elapsed = (now - ANCHOR_TIME).total_seconds()
    hours_elapsed = int(seconds_elapsed // 3600)
    
    current_interval = hours_elapsed // 3
    current_index = current_interval % len(MODIFIERS)
    next_index = (current_index + 1) % len(MODIFIERS)
    
    next_refresh_time = ANCHOR_TIME + timedelta(hours=(current_interval + 1) * 3)
    next_timestamp = int(next_refresh_time.timestamp())
    
    return MODIFIERS[current_index], MODIFIERS[next_index], next_timestamp

# --- BOT EVENTS & AUTOMATED TASK ---
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    if not notify_trial.is_running():
        notify_trial.start()

@tasks.loop(hours=3)
async def notify_trial():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        current_mod, next_mod, next_ts = get_current_modifier()
        
        # Embed uses the active modifier's specific color
        embed = discord.Embed(
            title="🛡️ TDS TRIAL MODIFIER ROTATION",
            color=current_mod["color"]
        )
        embed.add_field(
            name="⚔️ ACTIVE MODIFIER",
            value=f"### {current_mod['emoji']} **{current_mod['name']}**\n> {current_mod['desc']}",
            inline=False
        )
        embed.add_field(
            name="🔮 UP NEXT",
            value=f"{next_mod['emoji']} **{next_mod['name']}**\n*{next_mod['desc']}*\n\n⌛ **Refreshes:** <t:{next_ts}:R> (<t:{next_ts}:t>)",
            inline=False
        )
        embed.set_footer(text="Trial Refresh • Rotates every 3 hours")
        embed.timestamp = datetime.now(timezone.utc)

        # Check for role ping configured for this specific modifier
        role_id = current_mod.get("role_id")
        role_ping = f"<@&{role_id}>" if role_id and role_id != 0 else None
        
        await channel.send(content=role_ping, embed=embed)

@notify_trial.before_loop
async def before_notify():
    """Aligns loop to execute on exact 3-hour clock boundaries (00:00, 03:00, etc UTC)."""
    await bot.wait_until_ready()
    now = datetime.now(timezone.utc)
    next_hour = (now.hour // 3 + 1) * 3
    
    if next_hour >= 24:
        target_time = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        target_time = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)
    
    seconds_to_wait = (target_time - now).total_seconds()
    print(f"Waiting {int(seconds_to_wait)} seconds to sync with exact 3-hour clock schedule...")
    await asyncio.sleep(seconds_to_wait)

# --- USER COMMANDS ---

@bot.command(name="trial", aliases=["current", "mod"])
async def trial_command(ctx):
    """Shows active trial and the next modifier."""
    current_mod, next_mod, next_ts = get_current_modifier()
    
    embed = discord.Embed(
        title="🛡️ TDS TRIAL MODIFIER ROTATION",
        color=current_mod["color"]
    )
    embed.add_field(
        name="⚔️ ACTIVE MODIFIER",
        value=f"### {current_mod['emoji']} **{current_mod['name']}**\n> {current_mod['desc']}",
        inline=False
    )
    embed.add_field(
        name="🔮 UP NEXT",
        value=f"{next_mod['emoji']} **{next_mod['name']}**\n*{next_mod['desc']}*\n\n⌛ **Refreshes:** <t:{next_ts}:R> (<t:{next_ts}:t>)",
        inline=False
    )
    embed.set_footer(text=f"Requested by {ctx.author.display_name}")
    
    await ctx.send(embed=embed)

@bot.command(name="triallist", aliases=["alltrials", "schedule", "list"])
async def triallist_command(ctx):
    """Displays a full list of all 13 trial modifiers and their upcoming timestamps."""
    now = datetime.now(timezone.utc)
    seconds_elapsed = (now - ANCHOR_TIME).total_seconds()
    current_interval = int((seconds_elapsed // 3600) // 3)
    current_index = current_interval % len(MODIFIERS)

    embed = discord.Embed(
        title="🗓️ TDS TRIAL MODIFIER ROTATION SCHEDULE",
        description="Here is the full 13-trial rotation and when each modifier will be active next:",
        color=0x3498DB
    )

    for i, mod in enumerate(MODIFIERS):
        diff = (i - current_index) % len(MODIFIERS)
        interval_for_mod = current_interval + diff
        time_for_mod = ANCHOR_TIME + timedelta(hours=interval_for_mod * 3)
        ts = int(time_for_mod.timestamp())

        if diff == 0:
            end_ts = ts + 10800  # +3 hours
            status_text = f"🟢 **ACTIVE NOW** (Ends <t:{end_ts}:R>)"
        else:
            status_text = f"⌛ Starts <t:{ts}:R> (<t:{ts}:t>)"

        embed.add_field(
            name=f"{mod['emoji']} {mod['name']}",
            value=f"> {status_text}\n> *{mod['desc']}*",
            inline=False
        )

    embed.set_footer(text=f"Requested by {ctx.author.display_name}")
    await ctx.send(embed=embed)

@bot.command(name="help_tds")
async def help_command(ctx):
    """Displays bot command list."""
    help_text = (
        "📋 **TDS Trial Bot Commands:**\n"
        "`!trial` - View current active trial and next modifier.\n"
        "`!triallist` - View the entire 13-modifier rotation schedule with timestamps."
    )
    await ctx.send(help_text)

# --- START BOT ---
TOKEN = os.getenv('BOT_TOKEN')
if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: BOT_TOKEN variable was not found!")
