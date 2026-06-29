from playwright.sync_api import sync_playwright

def save_text():
    url = "https://www.workana.com/freelancer/47faeeeb9dc264373eac93e0eb1d5eff"
    print(f"Fetching {url}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Use domcontentloaded as established
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_selector("h1", timeout=15000)
        except:
            pass
        
        text = page.evaluate("document.body.innerText")
        html = page.content()
        
        with open("new_profile_text.txt", "w", encoding="utf-8") as f:
            f.write(text)
            
        print("Initial Text captured:")
        print(text[:500])
        
        browser.close()

if __name__ == "__main__":
    save_text()
