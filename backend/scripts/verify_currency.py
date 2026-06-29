
import httpx
from bs4 import BeautifulSoup
import asyncio

async def verify():
    url = "https://www.workana.com/pt/jobs"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    print(f"Checking URL: {url}")
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        response = await client.get(url)
        print(f"Status: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Use exact selector from fast_scraper
        project_cards = soup.select('.project-item, .job-item, [data-testid="project-card"]')
        print(f"Found {len(project_cards)} cards.")
        
        for i, card in enumerate(project_cards[:5]):
            title_el = card.select_one('h2 a, .project-title a')
            title = title_el.get_text(strip=True) if title_el else "No Title"
            
            budget_el = card.select_one('.budget, .price')
            budget = budget_el.get_text(strip=True) if budget_el else "No Budget"
            
            print(f"[{i+1}] {title} | Price: {budget}")

if __name__ == "__main__":
    asyncio.run(verify())
