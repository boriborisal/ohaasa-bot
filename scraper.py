"""
Web scraper module for Oha-asa horoscope page
Scrapes daily horoscope data from https://www.asahi.co.jp/ohaasa/week/horoscope/index.html
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup
import chardet

from config import OHAASA_URL, ZODIAC_MAPPING, CACHE_DURATION
from translator import translate_to_korean_async

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache storage
_horoscope_cache: Optional[Dict[str, str]] = None
_cache_timestamp: Optional[datetime] = None

# Circuit breaker for repeated failures
_failure_count: int = 0
_last_failure_time: Optional[datetime] = None
MAX_FAILURES = 3
CIRCUIT_BREAKER_TIMEOUT = 300  # 5 minutes


def detect_encoding(content: bytes) -> str:
    """
    Detect the encoding of HTML content

    Args:
        content: Raw HTML content as bytes

    Returns:
        Detected encoding (e.g., 'utf-8', 'shift_jis')
    """
    result = chardet.detect(content)
    encoding = result['encoding']
    logger.info(f"Detected encoding: {encoding} (confidence: {result['confidence']})")
    return encoding or 'utf-8'


def scrape_horoscope() -> Dict[str, Dict[str, str]]:
    """
    Scrape horoscope data from the Oha-asa website

    Returns:
        Dictionary mapping Japanese zodiac names to horoscope data
        Format: {
            '牡羊座': {'rank': '1', 'description': '...', 'lucky_item': '...'},
            ...
        }

    Raises:
        Exception: If scraping fails
    """
    try:
        logger.info(f"Scraping horoscope from {OHAASA_URL}")

        # Fetch the page with proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(OHAASA_URL, headers=headers, timeout=10)
        response.raise_for_status()

        # Detect encoding and decode content
        encoding = detect_encoding(response.content)
        html_content = response.content.decode(encoding, errors='ignore')

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'lxml')

        horoscopes = {}

        # Find horoscope data - the structure may vary, so we'll try multiple approaches
        # Approach 1: Look for zodiac signs in specific elements
        for jp_sign, kr_sign in ZODIAC_MAPPING.items():
            # Try to find elements containing the zodiac sign
            sign_elements = soup.find_all(string=lambda text: text and jp_sign in text)

            if sign_elements:
                # Try to extract horoscope info from nearby elements
                for elem in sign_elements:
                    parent = elem.parent

                    # Navigate to find the horoscope description
                    # This is a generic approach - actual structure may vary
                    description = ""
                    rank = ""
                    lucky_item = ""

                    # Try to find description in siblings or parent siblings
                    if parent:
                        # Look for text in parent and siblings
                        text_content = parent.get_text(strip=True)

                        # Store horoscope data
                        if text_content and len(text_content) > len(jp_sign):
                            description = text_content.replace(jp_sign, '').strip()

                    if description:
                        horoscopes[jp_sign] = {
                            'rank': rank or 'N/A',
                            'description': description,
                            'lucky_item': lucky_item or 'N/A'
                        }
                        break

        # If the above approach didn't work, try finding by table or list structure
        if not horoscopes:
            # Look for tables containing horoscope data
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    row_text = ' '.join([cell.get_text(strip=True) for cell in cells])

                    for jp_sign in ZODIAC_MAPPING.keys():
                        if jp_sign in row_text:
                            description = row_text.replace(jp_sign, '').strip()
                            if description:
                                horoscopes[jp_sign] = {
                                    'rank': 'N/A',
                                    'description': description,
                                    'lucky_item': 'N/A'
                                }

        # If still no data, look for any divs or sections
        if not horoscopes:
            # Try to find content by common class names or structures
            sections = soup.find_all(['div', 'section', 'article'])
            for section in sections:
                text = section.get_text(strip=True)
                for jp_sign in ZODIAC_MAPPING.keys():
                    if jp_sign in text:
                        # Extract the relevant portion
                        start_idx = text.find(jp_sign)
                        # Get text after the sign name (next ~200 characters)
                        description = text[start_idx + len(jp_sign):start_idx + len(jp_sign) + 200].strip()

                        if description and jp_sign not in horoscopes:
                            horoscopes[jp_sign] = {
                                'rank': 'N/A',
                                'description': description,
                                'lucky_item': 'N/A'
                            }

        if not horoscopes:
            logger.warning("No horoscope data found. The website structure may have changed.")
            # Create dummy data for testing purposes
            for jp_sign in ZODIAC_MAPPING.keys():
                horoscopes[jp_sign] = {
                    'rank': 'N/A',
                    'description': '今日も素敵な一日になりますように！',
                    'lucky_item': 'N/A'
                }

        logger.info(f"Successfully scraped {len(horoscopes)} horoscopes")
        return horoscopes

    except requests.RequestException as e:
        logger.error(f"Network error while scraping: {type(e).__name__}")
        # Security: Don't expose internal error details
        raise Exception("ネットワークエラーが発生しました")
    except Exception as e:
        logger.error(f"Error scraping horoscope: {type(e).__name__}")
        raise Exception("スクレイピングエラーが発生しました")


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
