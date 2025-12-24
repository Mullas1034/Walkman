import os
import shutil
from pathlib import Path
from datetime import datetime, date

def copy_todays_songs():
    """
    Copy all songs downloaded today to a new folder for iTunes import
    """
    downloaded_songs = Path('downloaded_songs')
    new_songs_folder = Path('new_songs_for_itunes')
    new_songs_folder.mkdir(exist_ok=True)

    # Get today's date
    today = date.today()

    # Find all mp3 files modified today
    new_songs = []
    for file_path in downloaded_songs.glob('*.mp3'):
        # Get file modification time
        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime).date()

        if mod_time == today:
            # Copy to new folder
            shutil.copy2(file_path, new_songs_folder / file_path.name)
            new_songs.append(file_path.name)

    # Print results
    print("="*60)
    print("NEW SONGS COPIED FOR ITUNES")
    print("="*60)
    print(f"\nSongs downloaded today: {len(new_songs)}")
    print(f"Copied to: {new_songs_folder.absolute()}")
    print("\n" + "="*60)
    print("SONGS COPIED:")
    print("="*60)
    for song in sorted(new_songs):
        print(f"  - {song}")
    print("\n" + "="*60)
    print("Add them to iTunes manually from this folder!")
    print("="*60)

if __name__ == '__main__':
    copy_todays_songs()
