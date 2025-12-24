"""Quick script to move approved songs to staging."""

import json
import shutil
from pathlib import Path
from src.utils import find_matching_file

# Paths
approved_path = Path('data/spotify/approved_discovered_songs.json')
discovered_folder = Path('discovered_songs')
staging_folder = Path('music/staging')
library_folder = Path('music/library')

# Create folders
staging_folder.mkdir(parents=True, exist_ok=True)
library_folder.mkdir(parents=True, exist_ok=True)

# Load approved songs
with open(approved_path, 'r', encoding='utf-8') as f:
    approved_songs = json.load(f)

print("="*80)
print("MOVING APPROVED SONGS TO STAGING")
print("="*80)

mp3_files = list(discovered_folder.glob("*.mp3"))
moved_count = 0
moved_files = []

for metadata in approved_songs:
    # Find matching MP3
    matched_file, score = find_matching_file(metadata, mp3_files, threshold=0.75)

    if matched_file:
        print(f"[MOVING] {matched_file.name}")

        # Move to staging
        staging_dest = staging_folder / matched_file.name
        shutil.move(str(matched_file), str(staging_dest))

        # Copy to library
        library_dest = library_folder / matched_file.name
        shutil.copy2(str(staging_dest), str(library_dest))

        moved_files.append(staging_dest)
        moved_count += 1
        print(f"  -> music/staging/ (for iTunes)")
        print(f"  -> music/library/ (permanent)")

print(f"\n{'='*80}")
print(f"Moved {moved_count} songs")
print(f"{'='*80}")

# iTunes option
print("\nOptions:")
print("  1. Auto-add to iTunes")
print("  2. Manual drag-and-drop")

choice = input("\nChoose (1/2) [default: 2]: ").strip()

if choice == "1":
    try:
        import win32com.client
        print("\nConnecting to iTunes...")
        itunes = win32com.client.Dispatch("iTunes.Application")

        for mp3_file in moved_files:
            itunes.LibraryPlaylist.AddFile(str(mp3_file.absolute()))
            print(f"  [ADDED] {mp3_file.name}")

        print(f"\n✓ Added {len(moved_files)} songs to iTunes")
    except Exception as e:
        print(f"ERROR: {e}")
        choice = "2"

if choice != "1":
    print("\nManual steps:")
    print("  1. Drag music/staging/ into iTunes")
    print("  2. Sync iPod")

print(f"\n{'='*80}")
print(f"Songs ready in: {staging_folder.absolute()}")
print(f"{'='*80}")
