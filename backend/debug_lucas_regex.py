import re

# Simulate the innerText of the profile (based on subagent findings)
# I will use a placeholder but I want to see the ACTUAL text.
# I'll first fetch the ACTUAL text using a small script.

import asyncio
from playwright.async_api import async_playwright

async def debug_scrape():
    url = "https://www.workana.com/freelancer/d8b5c583acc0ab18178259cdfb6925fc"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(2000)
        
        body_text = await page.evaluate("document.body.innerText")
        print("--- FULL INNER TEXT START ---")
        print(body_text)
        print("--- FULL INNER TEXT END ---")
        
        # Test existing regexes
        def get_metric(pattern, text):
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            return match.group(0) if match else "MISS"
            
        print(f"Ranking Match: {get_metric(r'(?:Ranking Workana|Ranking).*?#?([\\d.]+)', body_text)}")
        print(f"Projects Match: {get_metric(r'(?:Projetos realizados|Completed projects)[\\s\\n]*(\\d+)', body_text)}")
        print(f"Hours Match: {get_metric(r'(?:Horas trabalhadas|Hours worked)[\\s\\n]*(\\d+)', body_text)}")
        print(f"Reviews Match: {get_metric(r'(?:Classificações dos clientes|Ratings from clients)[\s\n]*\(?(\d+)\)?', body_text)}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_scrape())
