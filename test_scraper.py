import asyncio
from scraper import get_horoscope_data, get_single_horoscope

async def test():
    print("Testing scraper with real JSON API...")
    print("=" * 60)

    # Test fetching all horoscopes
    print("\n1. Fetching all horoscopes...")
    all_horoscopes = await get_horoscope_data(use_cache=False)

    print(f"\nTotal horoscopes fetched: {len(all_horoscopes)}")

    # Print first 3 horoscopes
    count = 0
    for sign, text in all_horoscopes.items():
        count += 1
        print(f"\n{count}. {sign}:")
        print(f"   {text[:200]}..." if len(text) > 200 else f"   {text}")
        if count >= 3:
            break

    print("\n" + "=" * 60)
    print("\n2. Testing single horoscope (양자리)...")
    aries = await get_single_horoscope('양자리', use_cache=True)
    print(f"\n양자리 운세:\n{aries}")

    print("\n" + "=" * 60)
    print("✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(test())
