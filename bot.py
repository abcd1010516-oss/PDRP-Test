import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
import time
import os
from flask import Flask
import threading

# ===== 環境變數讀取 =====
TOKEN = os.environ.get("DISCORD_TOKEN")
if TOKEN is None:
    raise ValueError("DISCORD_TOKEN 環境變數沒有設定！")

GUILD_ID = int(os.environ.get("GUILD_ID", 1392838594741276767))

# ===== Intent 設定 =====
intents = discord.Intents.default()
intents.reactions = True
intents.members = True
intents.message_content = True  # 文字指令需要

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ===== Flask 心跳 Server =====
app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask).start()

# ===== Bot ready =====
@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=1392838594741276767))
    print(f"Bot logged in as {bot.user}")


# ===== Slash Command /giveaway =====
@tree.command(
    name="giveaway",
    description="Start a giveaway",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    duration="Duration (e.g. 10s, 5m, 1h)",
    winners="Number of winners",
    prize="Giveaway prize"
)
async def giveaway(interaction: discord.Interaction, duration: str, winners: int, prize: str):
    emoji = "🎉"

    # ===== 解析時間 =====
    try:
        unit = duration[-1]
        value = int(duration[:-1])
        if unit == "s":
            seconds = value
        elif unit == "m":
            seconds = value * 60
        elif unit == "h":
            seconds = value * 3600
        else:
            raise ValueError
    except:
        await interaction.response.send_message(
            "Invalid duration format. Use s / m / h.",
            ephemeral=True
        )
        return

    end_timestamp = int(time.time()) + seconds

    # ===== Giveaway Embed（開始）=====
    embed = discord.Embed(
        title=prize,
        description=(
            f"React with {emoji} to enter!\n\n"
            f"⏱️ **Time remaining:** <t:{end_timestamp}:R>\n"
            f"🏁 **Ends at:** <t:{end_timestamp}:F>"
        ),
        color=discord.Color.orange()
    )
    embed.set_footer(text=f"{winners} Winner(s)")

    await interaction.response.send_message("🎉 Giveaway started!", ephemeral=True)
    message = await interaction.channel.send(embed=embed)
    await message.add_reaction(emoji)

    # ===== 等待結束 =====
    await asyncio.sleep(seconds)
    message = await interaction.channel.fetch_message(message.id)

    users = []
    for reaction in message.reactions:
        if str(reaction.emoji) == emoji:
            async for user in reaction.users():
                if not user.bot:
                    users.append(user)

    if not users:
        winner_mentions = "❌ No valid entries."
    else:
        winners = min(winners, len(users))
        chosen = random.sample(users, winners)
        winner_mentions = ", ".join(user.mention for user in chosen)

    # ===== Giveaway Embed（結束）=====
    ended_embed = discord.Embed(
        title=f"{prize} (ENDED)",
        description=f"🏆 **Winner(s):** {winner_mentions}",
        color=discord.Color.dark_gray()
    )
    ended_embed.set_footer(text=f"{winners} Winner(s) | Ended at")
    ended_embed.timestamp = discord.utils.utcnow()

    await message.edit(embed=ended_embed)

# ===== 運行 Bot =====
bot.run(TOKEN)

