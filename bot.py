import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta
import os

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

TRIALS = [
    "Speedy Enemies",
    "Glass",
    "Quarantine",
    "Fog",
    "Limitation Makes Creativity",
    "Flying Enemies",
    "Jailed Towers",
    "Exploding Enemies",
    "Inflation",
    "Committed",
    "Hidden Enemies",
    "Broke",
    "Healthy Enemies",
]

ANCHOR = datetime(2026, 2, 20, 12, 0, 0, tzinfo=timezone.utc)
ANCHOR_INDEX = TRIALS.index("Exploding Enemies")
INTERVAL = timedelta(hours=3)

def get_current_and_next():
    now = datetime.now(timezone.utc)
    elapsed = now - ANCHOR
    slots = int(elapsed.total_seconds() // INTERVAL.total_seconds())
    current_idx = (ANCHOR_INDEX + slots) % len(TRIALS)
    next_idx = (current_idx + 1) % len(TRIALS)
    current_start = ANCHOR + slots * INTERVAL
    next_start = current_start + INTERVAL
    return {
        "current": TRIALS[current_idx],
        "next": TRIALS[next_idx],
        "next_start": next_start,
        "time_left": next_start - now
    }

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    post_trial.start()

@tasks.loop(hours=3)
async def post_trial():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("Channel not found!")
        return
    data = get_current_and_next()
    starts_in = str(data["time_left"]).split(".")[0]
    embed = discord.Embed(
        title="⚔️ TDS Challenge Trial",
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="Current Trial", value=f"**{data['current']}**", inline=False)
    embed.add_field(name="Next Trial", value=f"**{data['next']}**", inline=False)
    embed.add_field(name="Next starts in", value=f"`{starts_in}` (at {data['next_start'].strftime('%H:%M UTC')})", inline=False)
    embed.set_footer(text="Rotates every 3 hours • Global UTC")
    await channel.send(embed=embed)

@post_trial.before_loop
async def before_post():
    await bot.wait_until_ready()
    data = get_current_and_next()
    await discord.utils.sleep_until(data["next_start"])

@bot.command(name="trial")
async def trial_cmd(ctx):
    data = get_current_and_next()
    starts_in = str(data["time_left"]).split(".")[0]
    embed = discord.Embed(title="⚔️ Current TDS Trial", color=discord.Color.green())
    embed.add_field(name="Live Now", value=f"**{data['current']}**", inline=False)
    embed.add_field(name="Next Up", value=f"**{data['next']}**", inline=False)
    embed.add_field(name="Changes in", value=f"`{starts_in}`", inline=False)
    await ctx.send(embed=embed)

bot.run(TOKEN)