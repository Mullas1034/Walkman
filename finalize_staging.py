"""
Finalize staging: Move approved songs to downloaded_songs folder.

Use this after you've dragged music/staging/ into iTunes.
This moves songs from staging to downloaded_songs (ultimate ledger).
"""

import shutil
from pathlib import Path

staging_folder = Path('music/staging')
downloaded_songs_folder = Path('downloaded_songs')

print("="*80)
print("FINALIZE STAGING -> DOWNLOADED_SONGS")
print("="*80)

# Check if staging has files
mp3_files = list(staging_folder.glob("*.mp3"))

if not mp3_files:
    print("\nNo MP3 files found in music/staging/")
    print("Either:")
    print("  1. Songs already moved to downloaded_songs/")
    print("  2. No approved songs processed yet")
    exit(0)

print(f"\nFound {len(mp3_files)} MP3 files in staging folder")
print("\nThese songs will be moved to downloaded_songs/ (ultimate ledger)")
print("Only proceed AFTER you've added them to iTunes!")

confirm = input("\nHave you moved songs from staging to iTunes? (yes/no): ").strip().lower()

if confirm == "yes":
    downloaded_songs_folder.mkdir(parents=True, exist_ok=True)

    moved_count = 0
    for mp3_file in mp3_files:
        dest = downloaded_songs_folder / mp3_file.name
        shutil.move(str(mp3_file), str(dest))
        print(f"  [MOVED] {mp3_file.name}")
        moved_count += 1

    print(f"\n{'='*80}")
    print(f"[OK] Moved {moved_count} songs to downloaded_songs/")
    print(f"[OK] Staging folder cleared")
    print(f"{'='*80}")
    print(f"\nAll approved songs now in: {downloaded_songs_folder.absolute()}")
else:
    print("\nCancelled. Songs remain in music/staging/")
    print("Run this script again after adding to iTunes")
