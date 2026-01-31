import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
import time
import os

# ===== 基本設定 =====
TOKEN = os.getenv("DISCORD_TOKEN")  # ⚠️ 請把 Token 放到環境變數
GUILD_ID = 1392838594741276767

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Bot logged in as {bot.user}")


# ======================
# Giveaway Button View
# ======================
class GiveawayView(discord.ui.View):
    def __init__(self, host, end_timestamp, winners, prize):
        super().__init__(timeout=None)
        self.host = host
        self.end_timestamp = end_timestamp
        self.winners = winners
        self.prize = prize
        self.entries = set()
        self.ended = False

    @discord.ui.button(label="Join Giveaway", emoji="🎁", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ended:
            await interaction.response.send_message("❌ This giveaway has ended.", ephemeral=True)
            return

        if interaction.user in self.entries:
            await interaction.response.send_message("⚠️ You already joined.", ephemeral=True)
            return

        self.entries.add(interaction.user)
        await interaction.response.send_message("✅ You joined the giveaway!", ephemeral=True)

        embed = interaction.message.embeds[0]
        embed.set_field_at(
            5,
            name="➡ Entries",
            value=str(len(self.entries)),
            inline=False
        )
        await interaction.message.edit(embed=embed)

    @discord.ui.button(label="Reroll", emoji="🔁", style=discord.ButtonStyle.red, disabled=True)
    async def reroll(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.host:
            await interaction.response.send_message("❌ Only the host can reroll.", ephemeral=True)
            return

        if not self.entries:
            await interaction.response.send_message("❌ No entries to reroll.", ephemeral=True)
            return

        chosen = random.sample(
            list(self.entries),
            min(self.winners, len(self.entries))
        )
        mentions = ", ".join(u.mention for u in chosen)

        await interaction.channel.send(
            f"🔁 **Reroll Result for `{self.prize}`**\n🏆 Winner(s): {mentions}"
        )
        await interaction.response.send_message("✅ Rerolled!", ephemeral=True)


# ======================
# Slash Command
# ======================
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

    # ===== 解析時間 =====
    unit = duration[-1]
    value = int(duration[:-1])

    if unit == "s":
        seconds = value
    elif unit == "m":
        seconds = value * 60
    elif unit == "h":
        seconds = value * 3600
    else:
        await interaction.response.send_message(
            "❌ Invalid duration format (use s/m/h)",
            ephemeral=True
        )
        return

    end_timestamp = int(time.time()) + seconds

    # ===== Embed =====
    embed = discord.Embed(
        title=f"🎁 {prize} Giveaway",
        color=discord.Color.gold()
    )

    embed.set_author(
        name=f"{interaction.guild.name} || President roleplay 🚔",
        icon_url=interaction.guild.icon.url if interaction.guild.icon else None
    )

    embed.add_field(name="Host:", value=interaction.user.mention, inline=False)
    embed.add_field(name="Prize:", value=prize, inline=False)
    embed.add_field(name="Winners:", value=str(winners), inline=False)
    embed.add_field(
        name="Ends:",
        value=f"<t:{end_timestamp}:F> (<t:{end_timestamp}:R>)",
        inline=False
    )
    embed.add_field(name="➡ Entries", value="0", inline=False)

    view = GiveawayView(
        host=interaction.user,
        end_timestamp=end_timestamp,
        winners=winners,
        prize=prize
    )

    await interaction.response.send_message("🎉 Giveaway started!", ephemeral=True)
    message = await interaction.channel.send(embed=embed, view=view)

    # ===== 等待結束 =====
    await asyncio.sleep(seconds)

    view.ended = True
    view.join.disabled = True
    view.reroll.disabled = False

    # ===== 抽獎 =====
    if not view.entries:
        result = "❌ No valid entries."
    else:
        chosen = random.sample(
            list(view.entries),
            min(winners, len(view.entries))
        )
        result = ", ".join(u.mention for u in chosen)

    ended_embed = embed.copy()
    ended_embed.title += " (ENDED)"
    ended_embed.color = discord.Color.dark_gray()
    ended_embed.set_footer(text="Giveaway Ended")

    await message.edit(embed=ended_embed, view=view)
    await interaction.channel.send(
        f"🏆 **Winner(s) for `{prize}`:** {result}"
    )


bot.run(TOKEN)



