import asyncio
import logging
from app.services.profile_scraper import profile_scraper
import json

# Configure basic logging to see stdout
logging.basicConfig(level=logging.INFO)

async def test_direct_scrape():
    url = "https://www.workana.com/freelancer/47faeeeb9dc264373eac93e0eb1d5eff"
    print(f"Testing direct scrape for {url}...")
    
    metrics = await profile_scraper.fetch_public_profile(url, force_refresh=True)
    
    print("\n--- SCRAPE RESULTS ---")
    print(json.dumps(metrics, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(test_direct_scrape())
