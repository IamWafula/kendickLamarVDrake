import os
import json
import csv

def safe_filename(title):
    """Convert title to safe filename format (matching the scraper logic)"""
    return title.replace("/", "_").replace("\\", "_").replace(" ", "_")

def find_json_file(title, artist):
    """Find the JSON file for a given title and artist"""
    safe_title = safe_filename(title)
    
    # Determine which directories to search based on artist
    if artist.lower() in ['drake', 'Drake']:
        search_dirs = [
            "output_metadata/drake-only",
            "output_metadata/drake-features"
        ]
        not_found_dir = "output_metadata/drake-not-found"
    else:  # kendrick or other
        search_dirs = [
            "output_metadata_goat/goat-only",
            "output_metadata_goat/goat-features"
        ]
        not_found_dir = "output_metadata_goat/goat-not-found"
    
    # Search for the file
    for search_dir in search_dirs:
        filepath = os.path.join(search_dir, f"{safe_title}.json")
        if os.path.exists(filepath):
            return filepath, search_dir, not_found_dir
    
    return None, None, not_found_dir

def move_to_not_found(json_filepath, not_found_dir):
    """Remove lyrics field and move file to not-found directory"""
    try:
        # Read the JSON file
        with open(json_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Remove lyrics field if it exists
        if 'lyrics' in data:
            del data['lyrics']
        
        # Update status
        data['status'] = 'needs_reprocessing'
        
        # Create not-found directory if it doesn't exist
        os.makedirs(not_found_dir, exist_ok=True)
        
        # Get filename
        filename = os.path.basename(json_filepath)
        new_filepath = os.path.join(not_found_dir, filename)
        
        # Save to not-found directory
        with open(new_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Remove original file
        os.remove(json_filepath)
        
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    # Read the CSV file
    print("Reading CSV file...")
    
    rows_to_process = []
    with open('drake_kendrick_lyrics.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i < 387:  # First 387 rows
                rows_to_process.append(row)
            else:
                break
    
    print(f"\nProcessing {len(rows_to_process)} rows (rows 1-387)...")
    print("=" * 60)
    
    # Track statistics
    processed = 0
    moved = 0
    not_found = 0
    errors = 0
    
    # Get unique title-artist combinations to avoid duplicates
    seen = set()
    unique_songs = []
    for row in rows_to_process:
        key = (row['title'], row['artist'])
        if key not in seen:
            seen.add(key)
            unique_songs.append(row)
    
    print(f"\nFound {len(unique_songs)} unique songs to process")
    print("=" * 60 + "\n")
    
    for row in unique_songs:
        title = row['title']
        artist = row['artist']
        
        print(f"[{processed + 1}/{len(unique_songs)}] Processing: {title} by {artist}")
        
        # Find the JSON file
        json_filepath, source_dir, not_found_dir = find_json_file(title, artist)
        
        if json_filepath:
            # Move to not-found
            success, error = move_to_not_found(json_filepath, not_found_dir)
            
            if success:
                print(f"  ✓ Moved from {source_dir} to {not_found_dir}")
                moved += 1
            else:
                print(f"  ✗ Error moving file: {error}")
                errors += 1
        else:
            print(f"  ⚠️  JSON file not found")
            not_found += 1
        
        processed += 1
        
        # Progress update every 50 songs
        if processed % 50 == 0:
            print(f"\n{'=' * 60}")
            print(f"Progress: {processed}/{len(unique_songs)}")
            print(f"Moved: {moved} | Not Found: {not_found} | Errors: {errors}")
            print(f"{'=' * 60}\n")
    
    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Total unique songs processed: {processed}")
    print(f"Successfully moved: {moved}")
    print(f"JSON files not found: {not_found}")
    print(f"Errors: {errors}")
    print("=" * 60)
    
    print("\nFiles have been moved to not-found directories.")
    print("You can now run retry_not_found.py to re-extract the lyrics.")

if __name__ == "__main__":
    main()

