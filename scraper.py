"""
Web scraper module for Oha-asa horoscope page
Fetches daily horoscope data from JSON API
API: https://www.asahi.co.jp/data/ohaasa2020/horoscope.json
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
import requests

from config import ZODIAC_MAPPING, CACHE_DURATION
from translator import translate_to_korean_async

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JSON API URL (actual data source)
OHAASA_JSON_URL = 'https://www.asahi.co.jp/data/ohaasa2020/horoscope.json'

# Zodiac sign code mapping (from JSON "horoscope_st" field)
ZODIAC_CODE_MAPPING = {
    '01': '牡羊座',
    '02': '牡牛座',
    '03': '双子座',
    '04': '蟹座',
    '05': '獅子座',
    '06': '乙女座',
    '07': '天秤座',
    '08': '蠍座',
    '09': '射手座',
    '10': '山羊座',
    '11': '水瓶座',
    '12': '魚座'
}

# Cache storage
_horoscope_cache: Optional[Dict[str, str]] = None
_cache_timestamp: Optional[datetime] = None

# Circuit breaker for repeated failures
_failure_count: int = 0
_last_failure_time: Optional[datetime] = None
MAX_FAILURES = 3
CIRCUIT_BREAKER_TIMEOUT = 300  # 5 minutes


def scrape_horoscope() -> Dict[str, Dict[str, str]]:
    """
    Fetch horoscope data from the Oha-asa JSON API

    Returns:
        Dictionary mapping Japanese zodiac names to horoscope data
        Format: {
            '牡羊座': {'rank': '1', 'description': '...', 'lucky_item': '...'},
            ...
        }

    Raises:
        Exception: If fetching fails
    """
    try:
        logger.info(f"Fetching horoscope from JSON API: {OHAASA_JSON_URL}")

        # Fetch JSON data
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(OHAASA_JSON_URL, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse JSON
        data = response.json()

        if not data or len(data) == 0:
            raise Exception("Empty JSON response")

        # Get today's horoscope data (first item in array)
        today_data = data[0]
        horoscope_details = today_data.get('detail', [])

        if not horoscope_details:
            raise Exception("No horoscope details found in JSON")

        horoscopes = {}

        # Parse each zodiac entry
        for detail in horoscope_details:
            zodiac_code = detail.get('horoscope_st', '')
            ranking = detail.get('ranking_no', 'N/A')
            horoscope_text = detail.get('horoscope_text', '')

            # Map zodiac code to Japanese name
            jp_sign = ZODIAC_CODE_MAPPING.get(zodiac_code)

            if not jp_sign:
                logger.warning(f"Unknown zodiac code: {zodiac_code}")
                continue

            # Parse horoscope text (tab-separated fields)
            # Format: main_fortune\tadvice1\tadvice2\tlucky_action
            text_parts = horoscope_text.split('\t')

            # Combine all parts into description
            description = '\n'.join([part.strip() for part in text_parts if part.strip()])

            horoscopes[jp_sign] = {
                'rank': str(ranking),
                'description': description,
                'lucky_item': 'N/A'  # Not separately provided in this format
            }

        logger.info(f"Successfully fetched {len(horoscopes)} horoscopes from JSON API")
        return horoscopes

    except requests.RequestException as e:
        logger.error(f"Network error while fetching JSON: {type(e).__name__}")
        # Security: Don't expose internal error details
        raise Exception("ネットワークエラーが発生しました")
    except Exception as e:
        logger.error(f"Error fetching horoscope: {type(e).__name__}: {str(e)[:100]}")
        raise Exception("データ取得エラーが発生しました")


async def scrape_horoscope_async() -> Dict[str, Dict[str, str]]:
    """
    Async wrapper for scrape_horoscope

    Returns:
        Dictionary mapping Japanese zodiac names to horoscope data
    """
    return await asyncio.to_thread(scrape_horoscope)


async def get_horoscope_data(use_cache: bool = True) -> Dict[str, str]:
    """
    Get horoscope data for all zodiac signs (translated to Korean)
    Uses caching to avoid redundant requests

    Args:
        use_cache: Whether to use cached data if available

    Returns:
        Dictionary mapping Korean zodiac names to translated horoscope text
        Format: {'양자리': 'translated horoscope text', ...}

    Raises:
        Exception: If scraping or translation fails
    """
    global _horoscope_cache, _cache_timestamp, _failure_count, _last_failure_time

    # Check cache validity
    if use_cache and _horoscope_cache and _cache_timestamp:
        cache_age = datetime.now() - _cache_timestamp
        if cache_age < timedelta(seconds=CACHE_DURATION):
            logger.info(f"Using cached data (age: {cache_age.seconds}s)")
            return _horoscope_cache

    # Security: Circuit breaker - prevent hammering external service on repeated failures
    if _failure_count >= MAX_FAILURES and _last_failure_time:
        time_since_last_failure = (datetime.now() - _last_failure_time).total_seconds()
        if time_since_last_failure < CIRCUIT_BREAKER_TIMEOUT:
            logger.warning(f"Circuit breaker active. Waiting {CIRCUIT_BREAKER_TIMEOUT - time_since_last_failure:.0f}s")
            raise Exception("サービスが一時的に利用できません。しばらくお待ちください。")
        else:
            # Reset circuit breaker after timeout
            _failure_count = 0
            _last_failure_time = None

    try:
        # Scrape fresh data
        logger.info("Fetching fresh horoscope data...")
        raw_horoscopes = await scrape_horoscope_async()

        # Translate to Korean
        translated_horoscopes = {}

        for jp_sign, data in raw_horoscopes.items():
            kr_sign = ZODIAC_MAPPING.get(jp_sign, jp_sign)

            # Build horoscope text
            horoscope_text = data['description']

            # Add rank if available
            if data.get('rank') and data['rank'] != 'N/A':
                horoscope_text = f"순위: {data['rank']}위\n\n{horoscope_text}"

            # Add lucky item if available
            if data.get('lucky_item') and data['lucky_item'] != 'N/A':
                horoscope_text += f"\n\n행운의 아이템: {data['lucky_item']}"

            # Translate to Korean
            translated_text = await translate_to_korean_async(horoscope_text)
            translated_horoscopes[kr_sign] = translated_text

        # Update cache
        _horoscope_cache = translated_horoscopes
        _cache_timestamp = datetime.now()

        # Reset failure count on success
        _failure_count = 0
        _last_failure_time = None

        logger.info(f"Successfully fetched and translated {len(translated_horoscopes)} horoscopes")
        return translated_horoscopes

    except Exception as e:
        # Track failures for circuit breaker
        _failure_count += 1
        _last_failure_time = datetime.now()
        logger.error(f"Failed to get horoscope data (failure {_failure_count}/{MAX_FAILURES}): {type(e).__name__}")
        raise


async def get_single_horoscope(zodiac_kr: str, use_cache: bool = True) -> str:
    """
    Get horoscope for a single zodiac sign

    Args:
        zodiac_kr: Korean zodiac name (e.g., '양자리')
        use_cache: Whether to use cached data if available

    Returns:
        Translated horoscope text for the specified zodiac sign

    Raises:
        ValueError: If zodiac sign is not found
        Exception: If scraping or translation fails
    """
    all_horoscopes = await get_horoscope_data(use_cache=use_cache)

    if zodiac_kr not in all_horoscopes:
        raise ValueError(f"Zodiac sign '{zodiac_kr}' not found")

    return all_horoscopes[zodiac_kr]
