import os
import json
import time
import re
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver(headless=True):
    opts = Options()
    
    # Basic headless mode
    if headless:
        opts.add_argument("--headless=new")  # Use new headless mode
    
    # Mimic real browser behavior
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)
    opts.add_experimental_option("detach", True)
    
    # Set realistic user agent
    opts.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Window size to mimic real browser
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--start-maximized")
    
    # Additional flags for stability and stealth
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-infobars")
    opts.add_argument("--lang=en-US,en;q=0.9")
    opts.add_argument("--disable-notifications")    
    
    driver = webdriver.Chrome(options=opts)
    
    # Remove webdriver property to further avoid detection
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def extract_link_and_title(html_snippet):
    # simplistic extraction; adjust if structure differs
    m = re.search(r'href="([^"]+)"', html_snippet)
    url = m.group(1) if m else None
    # extract title between <h3>…</h3>
    m2 = re.search(r'<h3[^>]*>([^<]+)</h3>', html_snippet)
    title = m2.group(1).strip() if m2 else None
    return url, title

def google_search_lyrics(driver, query, wait_time=10):
    # Navigate directly to the Google search URL
    search_url = f"https://www.google.com/search?q={quote_plus(query + ' lyrics')}"
    driver.get(search_url)
    wait = WebDriverWait(driver, wait_time)

    # Check if we're on the search results page (not CAPTCHA or redirect)
    # CAPTCHA URLs contain /sorry/ in the path
    while "/sorry/" in driver.current_url or not driver.current_url.startswith("https://www.google.com/search"):
        print("⚠️  CAPTCHA or redirect detected!")
        print(f"Current URL: {driver.current_url}")
        print("Please solve the CAPTCHA manually in the browser window.")
        print("Waiting for you to return to Google search results...")
        time.sleep(5)  # Check every 5 seconds
    
    print("✓ On Google search results page. Continuing...")

    try:            
        # Wait for results to load
        time.sleep(5)

        # get all elements with class JCZQSb
        links = driver.find_elements(By.CSS_SELECTOR, ".JCZQSb")

        lyrics_text = links[0].text

        # for each element, look for the one with inner_text containing "Artist"
        artist = None
        for element in driver.find_elements(By.CSS_SELECTOR, ".rVusze"):
            if "Artist" in element.text:
                artist = element.text
                artist = artist.split("Artist: ")[1]
                break

        return lyrics_text, artist
    except Exception as e:
        
        print("ELEMENTS FOUND: ", driver.find_element(By.CSS_SELECTOR, ".JCZQSb").text)

        # throw error
        raise e

def main():
    # Example list of html snippet(s)

    all_drake_songs = []
    with open("goat/all_songs.txt", "r") as f:
        all_drake_songs = f.readlines()        

    # load into list of strings and remove newlines
    all_drake_songs = [song.strip() for song in all_drake_songs]
    all_drake_songs = [song for song in all_drake_songs if song != ""]    

    html_snippets = all_drake_songs

    # keep driver open for debugging
    driver = setup_driver(headless=False)
    
    try:
        for html in html_snippets:
            url, title = extract_link_and_title(html)
            if not url or not title:
                print("Skipping invalid snippet:", html)
                continue
            
            # Check if already processed (resumability)
            safe_title = title.replace("/", "_").replace("\\", "_").replace(" ", "_")
            categories = ["goat-only", "goat-features", "goat-not-found"]
            already_exists = False
            for cat in categories:
                check_path = os.path.join("output_metadata", cat, f"{safe_title}.json")
                if os.path.exists(check_path):
                    print(f"✓ Skipping (already processed): {title}")
                    already_exists = True
                    break
            
            if already_exists:
                continue
            
            print(f"Processing: {title} -> {url}")

            # Determine if "feat" in title to categorize
            lower = title.lower()
            if "feat." in lower or " ft." in lower or "&" in lower:
                category = "goat-features"
            else:
                category = "goat-only"

            # Search Google and extract lyrics
            try:
                search_query = f"{title} Kendrick Lamar"
                lyrics_text, artist = google_search_lyrics(driver, search_query)
                print("Lyrics:", lyrics_text[:100] + "..." if len(lyrics_text) > 100 else lyrics_text)
                print("Artist:", artist)

                # Validate that lyrics start with "Lyrics\n"
                if not lyrics_text.startswith("Lyrics\n"):
                    raise ValueError(f"Invalid lyrics format - doesn't start with 'Lyrics\\n'. Got: {lyrics_text[:50]}...")

                # Save metadata
                folder = os.path.join("output_metadata_goat", category)
                os.makedirs(folder, exist_ok=True)
                filename = os.path.join(folder, f"{safe_title}.json")
                data = {
                    "title": title,
                    "artist": artist,
                    "lyrics": lyrics_text
                }
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print("✓ Saved metadata:", filename)
                
            except Exception as e:
                # Failed to extract lyrics - save to drake-not-found
                print(f"✗ Failed to extract lyrics: {str(e)}")
                folder = os.path.join("output_metadata_goat", "goat-not-found")
                os.makedirs(folder, exist_ok=True)
                filename = os.path.join(folder, f"{safe_title}.json")
                data = {
                    "title": title,
                    "url": url,
                    "error": str(e),
                    "status": "not_found"
                }
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print("✓ Saved to not-found:", filename)

            time.sleep(1)  # avoid too fast

    finally:
        # leave open for debugging
        pass 

if __name__ == "__main__":
    main()
