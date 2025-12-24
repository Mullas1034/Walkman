"""
Find songs that are in iTunes but not in downloaded_songs folder.
"""

import win32com.client
from pathlib import Path
from src.utils import normalize_string, similarity_ratio

def find_missing_songs():
    """Compare iTunes library with downloaded_songs folder."""

    print("="*80)
    print("FINDING DISCREPANCY: iPod Music vs downloaded_songs/")
    print("="*80)

    # Get downloaded_songs MP3 files
    downloaded_folder = Path('downloaded_songs')
    downloaded_files = list(downloaded_folder.glob("*.mp3"))

    print(f"\ndownloaded_songs/ folder: {len(downloaded_files)} MP3 files")

    # Create normalized set of downloaded songs
    downloaded_patterns = {}
    for mp3 in downloaded_files:
        # Remove .mp3 extension and normalize
        name = mp3.stem
        pattern = normalize_string(name)
        downloaded_patterns[pattern] = name

    # Show sample of downloaded songs for debugging
    print("\nSample downloaded song filenames:")
    for i, (pattern, filename) in enumerate(list(downloaded_patterns.items())[:5], 1):
        print(f"  {i}. {filename}")

    # Connect to iTunes
    print("\nConnecting to iTunes...")
    itunes = win32com.client.Dispatch("iTunes.Application")

    # Find iPod
    sources = itunes.Sources
    ipod_source = None
    for i in range(1, sources.Count + 1):
        source = sources.Item(i)
        if source.Kind == 2:  # iPod
            ipod_source = source
            break

    if not ipod_source:
        print("ERROR: No iPod found!")
        return

    # Get iPod Music playlist
    playlists = ipod_source.Playlists
    music_playlist = None
    for i in range(1, playlists.Count + 1):
        playlist = playlists.Item(i)
        if playlist.Name.lower() == "music":
            music_playlist = playlist
            break

    if not music_playlist:
        print("ERROR: Music playlist not found on iPod!")
        return

    tracks = music_playlist.Tracks
    print(f"iPod Music library: {tracks.Count} tracks")

    # Find songs in iTunes but not in downloaded_songs
    print("\nSearching for songs in iTunes but not in downloaded_songs...")

    missing_in_folder = []

    for i in range(1, tracks.Count + 1):
        track = tracks.Item(i)
        # Try both "Artist Title" and "Title Artist" patterns
        pattern1 = normalize_string(f"{track.Artist} {track.Name}")
        pattern2 = normalize_string(f"{track.Name} {track.Artist}")

        # Check if this pattern exists in downloaded_songs
        found = False
        best_score = 0
        for downloaded_pattern in downloaded_patterns.keys():
            score1 = similarity_ratio(pattern1, downloaded_pattern)
            score2 = similarity_ratio(pattern2, downloaded_pattern)
            score = max(score1, score2)

            if score > best_score:
                best_score = score
            if score >= 0.75:
                found = True
                break

        if not found:
            missing_in_folder.append({
                'title': track.Name,
                'artist': track.Artist,
                'album': track.Album,
                'best_match_score': best_score
            })

    # Reverse check: Find songs in downloaded_songs but NOT on iPod
    print("\nReverse check: Finding songs in downloaded_songs but NOT on iPod...")

    missing_from_ipod = []

    for downloaded_file in downloaded_files:
        filename = downloaded_file.stem
        downloaded_pattern = normalize_string(filename)

        # Try to match against iPod tracks
        found = False
        best_score = 0

        for j in range(1, tracks.Count + 1):
            track = tracks.Item(j)
            pattern1 = normalize_string(f"{track.Artist} {track.Name}")
            pattern2 = normalize_string(f"{track.Name} {track.Artist}")

            score = max(similarity_ratio(downloaded_pattern, pattern1),
                       similarity_ratio(downloaded_pattern, pattern2))

            if score > best_score:
                best_score = score
            if score >= 0.75:
                found = True
                break

        if not found:
            missing_from_ipod.append({
                'filename': filename,
                'best_match_score': best_score
            })

    # Results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"Songs on iPod Music: {tracks.Count}")
    print(f"Songs in downloaded_songs/: {len(downloaded_files)}")
    print(f"Difference: {abs(tracks.Count - len(downloaded_files))}")
    print(f"Songs on iPod but NOT in downloaded_songs/: {len(missing_in_folder)}")
    print(f"Songs in downloaded_songs but NOT on iPod: {len(missing_from_ipod)}")
    print("="*80)

    # Write report to file
    output_file = Path('missing_songs_report.txt')
    print(f"\nWriting complete report to: {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("MISSING SONGS REPORT\n")
        f.write("="*80 + "\n\n")

        # Part 1: Songs on iPod but NOT in downloaded_songs
        f.write(f"PART 1: Songs on iPod but NOT in downloaded_songs/ ({len(missing_in_folder)} songs)\n")
        f.write("="*80 + "\n\n")

        if missing_in_folder:
            for i, song in enumerate(missing_in_folder, 1):
                f.write(f"{i:3d}. {song['title']} - {song['artist']}\n")
                if song['album']:
                    f.write(f"      Album: {song['album']}\n")
                f.write(f"      Best match score: {song['best_match_score']:.2f}\n")
        else:
            f.write("[OK] All iPod songs are in downloaded_songs/\n")

        f.write("\n" + "="*80 + "\n\n")

        # Part 2: Songs in downloaded_songs but NOT on iPod
        f.write(f"PART 2: Songs in downloaded_songs/ but NOT on iPod ({len(missing_from_ipod)} songs)\n")
        f.write("="*80 + "\n\n")

        if missing_from_ipod:
            for i, song in enumerate(missing_from_ipod, 1):
                f.write(f"{i:3d}. {song['filename']}\n")
                f.write(f"      Best match score: {song['best_match_score']:.2f}\n")
        else:
            f.write("[OK] All downloaded_songs are on iPod\n")

    print(f"[OK] Complete report written to: {output_file.absolute()}")

    # Print summary to console
    if missing_in_folder:
        print(f"\nSongs on iPod but NOT in downloaded_songs/ ({len(missing_in_folder)}):")
        print("-"*80)
        for i, song in enumerate(missing_in_folder[:10], 1):
            try:
                print(f"{i:3d}. {song['title']} - {song['artist']} (match: {song['best_match_score']:.2f})")
            except:
                print(f"{i:3d}. [encoding error]")
        if len(missing_in_folder) > 10:
            print(f"... and {len(missing_in_folder) - 10} more")

    if missing_from_ipod:
        print(f"\nSongs in downloaded_songs/ but NOT on iPod ({len(missing_from_ipod)}):")
        print("-"*80)
        for i, song in enumerate(missing_from_ipod[:10], 1):
            try:
                print(f"{i:3d}. {song['filename']} (match: {song['best_match_score']:.2f})")
            except:
                print(f"{i:3d}. [encoding error]")
        if len(missing_from_ipod) > 10:
            print(f"... and {len(missing_from_ipod) - 10} more")

    print(f"\nSee {output_file} for complete details.")

if __name__ == '__main__':
    find_missing_songs()
