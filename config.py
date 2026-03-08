"""
Configuration module for Oha-asa Discord Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Discord bot token
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Oha-asa horoscope URL
OHAASA_URL = 'https://www.asahi.co.jp/ohaasa/week/horoscope/index.html'

# Cache duration in seconds (1 hour)
CACHE_DURATION = 3600

# Zodiac sign mappings: Japanese -> Korean
ZODIAC_MAPPING = {
    '牡羊座': '양자리',
    '牡牛座': '황소자리',
    '双子座': '쌍둥이자리',
    '蟹座': '게자리',
    '獅子座': '사자자리',
    '乙女座': '처녀자리',
    '天秤座': '천칭자리',
    '蠍座': '전갈자리',
    '射手座': '사수자리',
    '山羊座': '염소자리',
    '水瓶座': '물병자리',
    '魚座': '물고기자리'
}

# Zodiac emoji mapping
ZODIAC_EMOJI = {
    '양자리': '♈',
    '황소자리': '♉',
    '쌍둥이자리': '♊',
    '게자리': '♋',
    '사자자리': '♌',
    '처녀자리': '♍',
    '천칭자리': '♎',
    '전갈자리': '♏',
    '사수자리': '♐',
    '염소자리': '♑',
    '물병자리': '♒',
    '물고기자리': '♓'
}

# Zodiac color mapping (Discord embed colors)
ZODIAC_COLORS = {
    '양자리': 0xFF4444,      # Red
    '황소자리': 0x44FF44,    # Green
    '쌍둥이자리': 0xFFFF44,  # Yellow
    '게자리': 0xCCCCCC,      # Silver
    '사자자리': 0xFFAA00,    # Orange
    '처녀자리': 0x8844FF,    # Purple
    '천칭자리': 0xFF88FF,    # Pink
    '전갈자리': 0xCC0000,    # Dark Red
    '사수자리': 0x4444FF,    # Blue
    '염소자리': 0x664422,    # Brown
    '물병자리': 0x00FFFF,    # Cyan
    '물고기자리': 0x00AAFF   # Light Blue
}
