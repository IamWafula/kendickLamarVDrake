import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver(headless=False):
    opts = Options()
    
    # Basic headless mode
    if headless:
        opts.add_argument("--headless=new")
    
    # Mimic real browser behavior
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)
    opts.add_experimental_option("detach", True)
    
    # Set realistic user agent
    opts.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Window size
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--start-maximized")
    
    # Additional flags
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-infobars")
    opts.add_argument("--lang=en-US,en;q=0.9")
    opts.add_argument("--disable-notifications")    
    
    driver = webdriver.Chrome(options=opts)
    
    # Set page load timeout to 5 seconds
    driver.set_page_load_timeout(5)
    
    # Remove webdriver property
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def extract_genius_lyrics(driver, url, wait_time=30):
    """
    Navigate to Genius URL and extract lyrics.
    Waits for captcha to be resolved if needed.
    """
    print(f"  → Navigating to: {url}")
    
    # Try to load the page with timeout
    try:
        driver.get(url)
    except Exception as e:
        # Page load timeout - that's okay, we'll work with what loaded
        print(f"  ⚠️  Page load timed out after 5 seconds (continuing anyway)")

    
    try:
        # Try to find lyrics container on Genius
        # Genius uses different selectors - we'll try multiple approaches
        
        # Method 1: Look for lyrics containers with data-lyrics-container attribute
        lyrics_containers = driver.find_elements(By.CSS_SELECTOR, '.dfzvqs')

        if lyrics_containers:
            lyrics_text = "\n\n".join([container.get_attribute('innerText').strip() 
                                       for container in lyrics_containers])
            print(f"  ✓ Extracted lyrics (Method 1): {len(lyrics_text)} characters")
            
            # Also get artist and title from page
            try:
                title_elem = driver.find_element(By.CSS_SELECTOR, '.ccUdQo')
                title = title_elem.text.strip() if title_elem else None
            except:
                title = None
            
            return lyrics_text, title
        
        raise Exception("Could not find lyrics container on page")
        
    except Exception as e:
        print(f"  ✗ Error extracting lyrics: {str(e)}")
        raise

def process_not_found_files(artist_name="drake"):
    """
    Process all files in the not-found directory for a given artist.
    """
    not_found_dir = f"output_metadata/{artist_name}-not-found"
    success_dir = f"output_metadata/{artist_name}-only"
    features_dir = f"output_metadata/{artist_name}-features"
    
    if not os.path.exists(not_found_dir):
        print(f"Directory not found: {not_found_dir}")
        return
    
    # Get all JSON files
    json_files = [f for f in os.listdir(not_found_dir) if f.endswith('.json')]
    total = len(json_files)
    
    print(f"\n{'='*60}")
    print(f"Processing {total} files from {not_found_dir}")
    print(f"{'='*60}\n")
    
    driver = setup_driver(headless=False)
    
    try:
        processed = 0
        successful = 0
        failed = 0
        
        for idx, filename in enumerate(json_files, 1):
            filepath = os.path.join(not_found_dir, filename)
            
            print(f"\n[{idx}/{total}] Processing: {filename}")
            
            # Load the JSON file
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if it has a URL
            if 'url' not in data:
                print("  ⚠️  No URL found in JSON, skipping...")
                failed += 1
                continue
            
            url = data['url']
            title = data.get('title', 'Unknown')
            
            try:
                # Extract lyrics from Genius
                lyrics_text, page_title = extract_genius_lyrics(driver, url)
                
                # Determine category (use page_title if available, otherwise fall back to title)
                check_title = page_title if page_title else title
                title_lower = check_title.lower()
                if "feat." in title_lower or " ft." in title_lower or "&" in title_lower:
                    category_dir = features_dir
                    category_name = f"{artist_name}-features"
                else:
                    category_dir = success_dir
                    category_name = f"{artist_name}-only"
                
                # Create success directory if needed
                os.makedirs(category_dir, exist_ok=True)
                
                # Update data
                data['lyrics'] = lyrics_text
                data['status'] = 'success'
                if 'error' in data:
                    del data['error']
                
                # Save to appropriate category directory
                new_filepath = os.path.join(category_dir, filename)
                with open(new_filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"  ✓ SUCCESS - Saved to {category_name}/{filename}")
                
                # Remove from not-found directory
                os.remove(filepath)
                print(f"  ✓ Removed from not-found directory")
                
                successful += 1
                
                # Polite delay between requests
                time.sleep(5)
                
            except Exception as e:
                print(f"  ✗ FAILED: {str(e)}")
                failed += 1
                
                # Update error in the file
                data['error'] = str(e)
                data['last_attempt'] = time.strftime('%Y-%m-%d %H:%M:%S')
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # Continue to next file
                time.sleep(1)
            
            processed += 1
            
            # Progress update
            if processed % 10 == 0:
                print(f"\n{'='*60}")
                print(f"Progress: {processed}/{total} processed")
                print(f"Success: {successful} | Failed: {failed}")
                print(f"{'='*60}\n")
    
    finally:
        print("\n" + "="*60)
        print("FINAL SUMMARY")
        print("="*60)
        print(f"Total processed: {processed}/{total}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Remaining: {total - processed}")
        print("="*60)
        
        # Keep browser open for inspection
        input("\nPress Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    # Process Drake songs first
    print("Starting to process Drake songs...")
    process_not_found_files(artist_name="drake")
    
    # Uncomment to also process Kendrick Lamar songs
    # print("\n\nStarting to process Kendrick Lamar songs...")
    # process_not_found_files(artist_name="goat")

