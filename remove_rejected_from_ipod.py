"""
Remove rejected songs from iPod.

This script removes all rejected songs from your iPod library.
Uses the rejected_discovered_songs.json file to identify songs to remove.
"""

import json
from pathlib import Path
from src.utils import setup_logging, normalize_string, similarity_ratio

try:
    import win32com.client
    ITUNES_AVAILABLE = True
except ImportError:
    ITUNES_AVAILABLE = False

logger = setup_logging(__name__, 'remove_rejected.log')

def remove_rejected_songs():
    """Remove rejected songs from iPod."""

    if not ITUNES_AVAILABLE:
        print("ERROR: pywin32 not installed!")
        print("Install with: pip install pywin32")
        return

    # Load rejected songs
    rejected_path = Path('data/tracking/rejected_discovered_songs.json')

    if not rejected_path.exists():
        print("ERROR: rejected_discovered_songs.json not found!")
        return

    with open(rejected_path, 'r', encoding='utf-8') as f:
        rejected_songs = json.load(f)

    print("="*80)
    print("REMOVE REJECTED SONGS FROM IPOD")
    print("="*80)
    print(f"\nFound {len(rejected_songs)} rejected songs to remove")

    # Show sample
    print("\nSample rejected songs:")
    for i, song in enumerate(rejected_songs[:5], 1):
        print(f"  {i}. {song['title']} - {song['artist']}")
    if len(rejected_songs) > 5:
        print(f"  ... and {len(rejected_songs) - 5} more")

    # Confirm
    print("\n" + "="*80)
    print("WARNING: This will DELETE these songs from your iPod!")
    print("="*80)
    confirm = input("\nProceed with deletion? (yes/no): ").strip().lower()

    if confirm != "yes":
        print("\nCancelled. No songs were deleted.")
        return

    # Connect to iTunes
    print("\nConnecting to iTunes...")
    try:
        itunes = win32com.client.Dispatch("iTunes.Application")
        print("Connected!")
    except Exception as e:
        print(f"ERROR: Could not connect to iTunes: {e}")
        return

    # Find iPod
    print("\nSearching for iPod...")
    sources = itunes.Sources
    ipod_source = None

    for i in range(1, sources.Count + 1):
        source = sources.Item(i)
        if source.Kind == 2:  # Kind 2 = iPod
            ipod_source = source
            print(f"Found iPod: {source.Name}")
            break

    if not ipod_source:
        print("ERROR: No iPod found!")
        print("Make sure your iPod is connected to iTunes.")
        return

    # Get iPod "Music" playlist specifically
    ipod_library = None
    playlists = ipod_source.Playlists

    print(f"\nSearching for 'Music' playlist...")
    print(f"Total playlists on iPod: {playlists.Count}")

    for i in range(1, playlists.Count + 1):
        playlist = playlists.Item(i)
        print(f"  {i}. {playlist.Name} ({playlist.Tracks.Count} tracks)")
        if playlist.Name.lower() == "music":
            ipod_library = playlist
            print(f"    ^ Found Music playlist!")

    if not ipod_library:
        print("\nERROR: Could not find 'Music' playlist on iPod!")
        print("Available playlists shown above.")
        return

    print(f"\nUsing playlist: {ipod_library.Name}")
    print(f"Total tracks in Music: {ipod_library.Tracks.Count}")

    # Find and delete rejected songs
    print("\n" + "="*80)
    print("SEARCHING FOR REJECTED SONGS ON IPOD")
    print("="*80)

    deleted_count = 0
    not_found_count = 0

    for i, rejected_song in enumerate(rejected_songs, 1):
        song_name = f"{rejected_song['title']} - {rejected_song['artist']}"
        rejected_pattern = normalize_string(f"{rejected_song['title']} {rejected_song['artist']}")

        print(f"\n[{i}/{len(rejected_songs)}] {song_name}")

        # Rebuild track list each time (to avoid stale references)
        tracks = ipod_library.Tracks
        matched_track = None
        best_score = 0

        # Search through current tracks
        for j in range(1, tracks.Count + 1):
            try:
                track = tracks.Item(j)
                track_pattern = normalize_string(f"{track.Name} {track.Artist}")
                score = similarity_ratio(rejected_pattern, track_pattern)

                if score > best_score:
                    best_score = score
                    if score >= 0.75:  # 75% similarity threshold
                        matched_track = track
            except:
                continue

        if matched_track:
            try:
                # Delete from iPod
                matched_track.Delete()
                print(f"  [DELETED] (similarity: {best_score:.2f})")
                deleted_count += 1
            except Exception as e:
                print(f"  [FAILED] Could not delete: {e}")
        else:
            print(f"  [NOT FOUND] Not on iPod (best match: {best_score:.2f})")
            not_found_count += 1

    # Summary
    print("\n" + "="*80)
    print("COMPLETE!")
    print("="*80)
    print(f"Deleted from iPod: {deleted_count}")
    print(f"Not found on iPod: {not_found_count}")
    print(f"Total rejected songs: {len(rejected_songs)}")
    print("="*80)

    if deleted_count > 0:
        print("\nNext steps:")
        print("1. Sync your iPod to apply the changes")
        print("2. The rejected songs are now removed from your iPod")

if __name__ == '__main__':
    remove_rejected_songs()
