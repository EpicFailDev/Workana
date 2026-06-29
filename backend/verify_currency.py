import asyncio
from app.services.currency import CurrencyService
from app.config import settings

async def main():
    print(f"Configured Workana Rate: {settings.workana_conversion_rate}")
    
    rate = await CurrencyService.get_usd_brl_rate()
    print(f"Service Rate: {rate}")
    
    # Test cases
    test_cases = [
        "USD 50 - 100",
        "USD 100 - 250",
        "USD 500",
        "USD 1.000 - 2.500"
    ]
    
    print("\n--- Testing Conversions ---")
    for tc in test_cases:
        brl = await CurrencyService.convert_to_brl(tc)
        print(f"{tc}  =>  {brl}")

if __name__ == "__main__":
    asyncio.run(main())
