import asyncio
from playwright.async_api import async_playwright
import os

async def save_profile_text():
    url = "https://www.workana.com/freelancer/d8b5c583acc0ab18178259cdfb6925fc"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(5000) # Give more time for dynamic content
        
        # Take a screenshot to see if cookie banner is there
        await page.screenshot(path="lucas_debug_screenshot.png")
        
        body_text = await page.evaluate("document.body.innerText")
        
        with open("lucas_full_text.txt", "w", encoding="utf-8") as f:
            f.write(body_text)
            
        print(f"Saved {len(body_text)} characters to lucas_full_text.txt")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(save_profile_text())
