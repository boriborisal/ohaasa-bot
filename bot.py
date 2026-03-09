"""
Oha-asa Discord Bot
Fetches daily horoscopes from the Japanese TV program "Oha-asa",
translates them to Korean, and posts via Discord slash commands
"""
import logging
import asyncio
from datetime import datetime
from typing import List

import discord
from discord import app_commands
from discord.ext import commands

from config import (
    DISCORD_TOKEN,
    ZODIAC_MAPPING,
    ZODIAC_EMOJI,
    ZODIAC_COLORS
)
from scraper import get_horoscope_data, get_single_horoscope

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Create bot instance
class OhaasaBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        # Message content intent not needed for slash commands only

        super().__init__(
            command_prefix='!',  # Fallback prefix (not used for slash commands)
            intents=intents
        )

    async def setup_hook(self):
        """Setup hook called when bot is starting"""
        # Sync commands globally (works in all servers)
        logger.info("Syncing command tree...")
        await self.tree.sync()
        logger.info("Command tree synced successfully")

    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        print(f"[SUCCESS] {self.user.name} bot is online!")
        print(f"   Servers: {len(self.guilds)}")
        print(f"   Users: {len(set(self.get_all_members()))}")


# Initialize bot
bot = OhaasaBot()


# Global error handler for app_commands
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """
    Global error handler for slash commands
    Security: Prevents exposing internal errors to users
    """
    logger.error(f"Command error: {type(error).__name__} in {interaction.command.name if interaction.command else 'unknown'}")

    # Check if response has already been sent
    if interaction.response.is_done():
        await interaction.followup.send(
            "❌ 명령을 처리하는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "❌ 명령을 처리하는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
            ephemeral=True
        )


# Autocomplete function for zodiac signs
async def zodiac_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> List[app_commands.Choice[str]]:
    """
    Autocomplete function for zodiac sign selection
    Returns matching Korean zodiac names
    """
    korean_zodiacs = list(ZODIAC_MAPPING.values())

    # Filter based on current input
    if current:
        matches = [z for z in korean_zodiacs if current.lower() in z.lower()]
    else:
        matches = korean_zodiacs

    # Return as Choice objects (limit to 25 as per Discord API)
    return [
        app_commands.Choice(name=f"{ZODIAC_EMOJI[z]} {z}", value=z)
        for z in matches[:25]
    ]


@bot.tree.command(name="운세", description="오늘의 별자리 운세를 확인합니다")
@app_commands.describe(별자리="확인할 별자리를 선택하세요")
@app_commands.autocomplete(별자리=zodiac_autocomplete)
@app_commands.checks.cooldown(1, 10.0, key=lambda i: i.user.id)  # Security: 1 use per 10 seconds per user
async def horoscope_command(interaction: discord.Interaction, 별자리: str):
    """
    /운세 <별자리> - Shows horoscope for the specified zodiac sign
    """
    # Defer the response since fetching might take a while
    await interaction.response.defer(thinking=True)

    try:
        # Validate zodiac sign
        if 별자리 not in ZODIAC_MAPPING.values():
            await interaction.followup.send(
                f"❌ 올바르지 않은 별자리입니다: {별자리}\n"
                f"사용 가능한 별자리: {', '.join(ZODIAC_MAPPING.values())}",
                ephemeral=True  # Security: Error messages are ephemeral
            )
            return

        logger.info(f"Fetching horoscope for {별자리}")

        # Fetch horoscope data
        horoscope_text = await get_single_horoscope(별자리)

        # Create embed
        embed = create_horoscope_embed(별자리, horoscope_text)

        # Send response
        await interaction.followup.send(embed=embed)
        logger.info(f"Successfully sent horoscope for {별자리}")

    except Exception as e:
        logger.error(f"Error in /운세 command: {type(e).__name__}")
        await interaction.followup.send(
            "❌ 현재 오하아사 사이트에서 데이터를 불러올 수 없습니다. "
            "잠시 후 다시 시도해 주세요. 🙏",
            ephemeral=True  # Security: Error messages are ephemeral
        )


@bot.tree.command(name="오늘운세", description="오늘의 전체 운세를 확인합니다 (12개 별자리 모두)")
@app_commands.checks.cooldown(1, 30.0, key=lambda i: i.user.id)  # Security: 1 use per 30 seconds per user
async def all_horoscopes_command(interaction: discord.Interaction):
    """
    /오늘운세 - Shows horoscopes for all 12 zodiac signs
    """
    # Defer the response since fetching might take a while
    await interaction.response.defer(thinking=True)

    try:
        logger.info("Fetching all horoscopes")

        # Fetch all horoscope data
        all_horoscopes = await get_horoscope_data()

        # Create summary embed
        today = datetime.now().strftime('%Y년 %m월 %d일')
        summary_embed = discord.Embed(
            title="🌟 오늘의 전체 운세",
            description=f"**{today}** 오하아사 운세입니다!",
            color=0xFFD700,  # Gold color
            timestamp=datetime.now()
        )
        summary_embed.set_footer(text="출처: おはよう朝日です | 오하아사")

        # Create individual embeds for each zodiac
        embeds = [summary_embed]

        for kr_sign in ZODIAC_MAPPING.values():
            if kr_sign in all_horoscopes:
                horoscope_text = all_horoscopes[kr_sign]

                # Truncate if too long (Discord embed field limit is 1024 chars)
                if len(horoscope_text) > 1024:
                    horoscope_text = horoscope_text[:1021] + "..."

                # Create individual embed for each sign
                embed = create_horoscope_embed(kr_sign, horoscope_text, compact=True)
                embeds.append(embed)

        # Discord has a limit of 10 embeds per message, so we send in chunks
        # Send first batch (summary + up to 9 zodiacs)
        await interaction.followup.send(embeds=embeds[:10])

        # Send remaining zodiacs if any
        if len(embeds) > 10:
            for i in range(10, len(embeds), 10):
                await interaction.followup.send(embeds=embeds[i:i+10])

        logger.info("Successfully sent all horoscopes")

    except Exception as e:
        logger.error(f"Error in /오늘운세 command: {type(e).__name__}")
        await interaction.followup.send(
            "❌ 현재 오하아사 사이트에서 데이터를 불러올 수 없습니다. "
            "잠시 후 다시 시도해 주세요. 🙏",
            ephemeral=True  # Security: Error messages are ephemeral
        )


@bot.tree.command(name="도움말", description="봇 사용 방법을 확인합니다")
async def help_command(interaction: discord.Interaction):
    """
    /도움말 - Shows help message with available commands
    """
    help_embed = discord.Embed(
        title="📖 오하아사 운세 봇 도움말",
        description="일본 TV 프로그램 '오하아사'의 오늘의 운세를 한국어로 제공합니다!",
        color=0x00AAFF
    )

    help_embed.add_field(
        name="📌 사용 가능한 명령어",
        value=(
            "`/운세 <별자리>` - 특정 별자리의 오늘 운세를 확인합니다\n"
            "`/오늘운세` - 12개 별자리 전체의 오늘 운세를 확인합니다\n"
            "`/도움말` - 이 도움말 메시지를 표시합니다"
        ),
        inline=False
    )

    help_embed.add_field(
        name="🌟 별자리 목록",
        value=(
            "♈ 양자리, ♉ 황소자리, ♊ 쌍둥이자리, ♋ 게자리\n"
            "♌ 사자자리, ♍ 처녀자리, ♎ 천칭자리, ♏ 전갈자리\n"
            "♐ 사수자리, ♑ 염소자리, ♒ 물병자리, ♓ 물고기자리"
        ),
        inline=False
    )

    help_embed.add_field(
        name="💡 사용 팁",
        value=(
            "• `/운세` 명령어를 입력하면 별자리 자동완성이 나타납니다\n"
            "• 운세는 1시간마다 자동으로 업데이트됩니다\n"
            "• 원본 출처: おはよう朝日です (오하아사)"
        ),
        inline=False
    )

    help_embed.set_footer(text="오하아사 운세 봇 v1.0")
    help_embed.timestamp = datetime.now()

    await interaction.response.send_message(embed=help_embed)


def create_horoscope_embed(zodiac_kr: str, horoscope_text: str, compact: bool = False) -> discord.Embed:
    """
    Create a Discord embed for a horoscope

    Args:
        zodiac_kr: Korean zodiac name
        horoscope_text: Horoscope text (already translated)
        compact: If True, create a more compact embed

    Returns:
        Discord embed object
    """
    emoji = ZODIAC_EMOJI.get(zodiac_kr, '⭐')
    color = ZODIAC_COLORS.get(zodiac_kr, 0xFFFFFF)
    today = datetime.now().strftime('%Y-%m-%d')

    if compact:
        # Compact version for /오늘운세
        embed = discord.Embed(
            title=f"{emoji} {zodiac_kr}",
            description=horoscope_text,
            color=color
        )
    else:
        # Full version for /운세
        embed = discord.Embed(
            title=f"🌟 오늘의 {zodiac_kr} 운세",
            description=horoscope_text,
            color=color,
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"출처: おはよう朝日です | 오하아사 | {today}")

    return embed


async def main():
    """Main entry point"""
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN is not set in .env file")
        print("[ERROR] DISCORD_TOKEN is not set in .env file")
        print("Please create a .env file with your Discord bot token")
        return

    try:
        async with bot:
            await bot.start(DISCORD_TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid Discord token")
        print("[ERROR] Invalid Discord token")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        print(f"[ERROR] Error starting bot: {e}")


if __name__ == "__main__":
    asyncio.run(main())
