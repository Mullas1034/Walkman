"""
Remove duplicate songs from iPod Music library.
"""

import win32com.client
from src.utils import normalize_string, similarity_ratio

def remove_ipod_duplicates():
    """Remove duplicate songs from iPod Music library."""

    print("="*80)
    print("REMOVE DUPLICATES FROM IPOD MUSIC LIBRARY")
    print("="*80)

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

    # Get iPod "Music" playlist
    ipod_library = None
    playlists = ipod_source.Playlists

    print(f"\nSearching for 'Music' playlist...")

    for i in range(1, playlists.Count + 1):
        playlist = playlists.Item(i)
        if playlist.Name.lower() == "music":
            ipod_library = playlist
            print(f"Found Music playlist: {playlist.Tracks.Count} tracks")
            break

    if not ipod_library:
        print("\nERROR: Could not find 'Music' playlist on iPod!")
        return

    # Find duplicates
    print("\n" + "="*80)
    print("FINDING DUPLICATES")
    print("="*80)

    tracks = ipod_library.Tracks
    total_tracks = tracks.Count

    seen_songs = {}  # pattern -> track info
    duplicates = []  # List of duplicate tracks to delete

    print(f"\nScanning {total_tracks} tracks...")

    for i in range(1, tracks.Count + 1):
        try:
            track = tracks.Item(i)
            pattern = normalize_string(f"{track.Artist} {track.Name}")

            if pattern in seen_songs:
                # This is a duplicate
                duplicates.append({
                    'track': track,
                    'title': track.Name,
                    'artist': track.Artist,
                    'album': track.Album,
                    'original_index': seen_songs[pattern]['index']
                })
            else:
                # First occurrence - keep it
                seen_songs[pattern] = {
                    'index': i,
                    'title': track.Name,
                    'artist': track.Artist
                }

        except Exception as e:
            print(f"Error processing track {i}: {e}")
            continue

        if i % 100 == 0:
            print(f"  Processed {i}/{total_tracks} tracks...")

    print(f"\nFound {len(duplicates)} duplicate tracks")

    if not duplicates:
        print("\n[OK] No duplicates found!")
        return

    # Show duplicates
    print("\nDuplicates found:")
    print("-"*80)
    for i, dup in enumerate(duplicates[:20], 1):
        try:
            print(f"{i:3d}. {dup['title']} - {dup['artist']}")
        except:
            print(f"{i:3d}. [encoding error]")

    if len(duplicates) > 20:
        print(f"... and {len(duplicates) - 20} more")

    # Auto-proceed with deletion
    print("\n" + "="*80)
    print(f"Deleting {len(duplicates)} duplicate songs from your iPod...")
    print("="*80)

    # Delete duplicates
    print("\n" + "="*80)
    print("DELETING DUPLICATES")
    print("="*80)

    deleted_count = 0
    failed_count = 0

    # Create list of songs to delete (pattern + metadata, not track references)
    songs_to_delete = []
    for dup in duplicates:
        songs_to_delete.append({
            'title': dup['title'],
            'artist': dup['artist'],
            'pattern': normalize_string(f"{dup['artist']} {dup['title']}")
        })

    # Delete each song by re-finding it in the current track list
    for i, song_info in enumerate(songs_to_delete, 1):
        print(f"[{i}/{len(songs_to_delete)}] {song_info['title']} - {song_info['artist']}")

        # Rebuild track list (to avoid stale references)
        tracks = ipod_library.Tracks
        matched_track = None

        # Find this song in current tracks
        for j in range(1, tracks.Count + 1):
            try:
                track = tracks.Item(j)
                track_pattern = normalize_string(f"{track.Artist} {track.Name}")

                if track_pattern == song_info['pattern']:
                    matched_track = track
                    break
            except:
                continue

        if matched_track:
            try:
                matched_track.Delete()
                print(f"  [DELETED]")
                deleted_count += 1
            except Exception as e:
                print(f"  [FAIL] {e}")
                failed_count += 1
        else:
            print(f"  [NOT FOUND] (already deleted or not on iPod)")
            failed_count += 1

    # Summary
    print("\n" + "="*80)
    print("COMPLETE!")
    print("="*80)
    print(f"Duplicates deleted: {deleted_count}")
    print(f"Failed to delete: {failed_count}")
    print(f"Original track count: {total_tracks}")
    print(f"New track count (approx): {total_tracks - deleted_count}")
    print("="*80)

    if deleted_count > 0:
        print("\nNext steps:")
        print("1. Sync your iPod to apply the changes")
        print("2. The duplicate songs are now removed from your iPod")

if __name__ == '__main__':
    remove_ipod_duplicates()
