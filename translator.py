"""
Translation module for Oha-asa Discord Bot
Translates Japanese horoscope text to Korean using deep-translator
"""
import logging
from deep_translator import GoogleTranslator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def translate_to_korean(text: str) -> str:
    """
    Translate Japanese text to Korean using Google Translate

    Args:
        text: Japanese text to translate

    Returns:
        Translated Korean text, or original text with error message if translation fails
    """
    if not text or not text.strip():
        return text

    # Security: Validate input length (Google Translate has ~5000 char limit)
    MAX_TRANSLATION_LENGTH = 4900
    if len(text) > MAX_TRANSLATION_LENGTH:
        logger.warning(f"Text too long for translation ({len(text)} chars), truncating to {MAX_TRANSLATION_LENGTH}")
        text = text[:MAX_TRANSLATION_LENGTH] + "..."

    try:
        translator = GoogleTranslator(source='ja', target='ko')
        translated = translator.translate(text)
        logger.info(f"Successfully translated {len(text)} characters")
        return translated
    except Exception as e:
        logger.error(f"Translation failed: {type(e).__name__}")
        # Return original Japanese text with a note if translation fails
        return f"{text}\n(번역 실패 — 원문)"


async def translate_to_korean_async(text: str) -> str:
    """
    Async wrapper for translate_to_korean
    Uses asyncio.to_thread to run the synchronous translation in a separate thread

    Args:
        text: Japanese text to translate

    Returns:
        Translated Korean text, or original text with error message if translation fails
    """
    import asyncio
    return await asyncio.to_thread(translate_to_korean, text)
