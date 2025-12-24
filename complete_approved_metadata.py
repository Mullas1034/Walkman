"""
Complete approved songs metadata using the existing liked_songs_metadata.json.

This script searches the main liked_songs_metadata.json (with complete metadata)
for each approved song and updates the approved songs with complete data.
"""

import json
from pathlib import Path
from src.utils import setup_logging, normalize_string, similarity_ratio

logger = setup_logging(__name__, 'complete_metadata.log')

def find_matching_metadata(approved_song, liked_songs_list, threshold=0.75):
    """
    Find matching song in liked songs list.

    Args:
        approved_song: Approved song metadata dict
        liked_songs_list: List of liked songs with complete metadata
        threshold: Similarity threshold for matching

    Returns:
        Matched song metadata or None
    """
    approved_pattern = normalize_string(f"{approved_song['title']} {approved_song['artist']}")

    best_match = None
    best_score = 0

    for liked_song in liked_songs_list:
        liked_pattern = normalize_string(f"{liked_song['title']} {liked_song['artist']}")
        score = similarity_ratio(approved_pattern, liked_pattern)

        if score > best_score:
            best_score = score
            best_match = liked_song

    if best_score >= threshold:
        return best_match, best_score

    return None, best_score

def complete_approved_metadata():
    """Complete approved songs metadata from main liked songs."""

    # Load files
    approved_path = Path('data/spotify/approved_discovered_songs.json')
    liked_path = Path('liked_songs_metadata.json')

    if not approved_path.exists():
        print("ERROR: approved_discovered_songs.json not found!")
        return

    if not liked_path.exists():
        print("ERROR: liked_songs_metadata.json not found!")
        return

    print("Loading approved songs...")
    with open(approved_path, 'r', encoding='utf-8') as f:
        approved_songs = json.load(f)
    print(f"  Loaded {len(approved_songs)} approved songs")

    print("\nLoading complete liked songs metadata...")
    with open(liked_path, 'r', encoding='utf-8') as f:
        liked_songs = json.load(f)
    print(f"  Loaded {len(liked_songs)} liked songs with complete metadata")

    print(f"\n{'='*80}")
    print("MATCHING APPROVED SONGS WITH COMPLETE METADATA")
    print(f"{'='*80}\n")

    completed_songs = []
    found_count = 0
    not_found_count = 0

    for i, approved_song in enumerate(approved_songs, 1):
        title = approved_song['title']
        artist = approved_song['artist']

        print(f"[{i}/{len(approved_songs)}] {title} - {artist}")

        # Find matching song in liked songs
        matched, score = find_matching_metadata(approved_song, liked_songs)

        if matched:
            print(f"  [MATCH] Found in liked songs (similarity: {score:.2f})")
            print(f"    Album art: {'Yes' if matched.get('album_art_url') else 'No'}")
            print(f"    BPM: {matched.get('bpm', 0)}")
            print(f"    Genre: {matched.get('genre', 'N/A')[:50]}")
            completed_songs.append(matched)
            found_count += 1
        else:
            print(f"  [NOT FOUND] No match in liked songs (best score: {score:.2f})")
            print(f"    Keeping original metadata")
            completed_songs.append(approved_song)
            not_found_count += 1

    # Backup original
    backup_path = approved_path.with_suffix('.backup2.json')
    print(f"\n{'='*80}")
    print(f"Backing up original to: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(approved_songs, f, indent=2, ensure_ascii=False)

    # Save completed metadata
    print(f"Saving completed metadata to: {approved_path}")
    with open(approved_path, 'w', encoding='utf-8') as f:
        json.dump(completed_songs, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print("COMPLETE!")
    print(f"{'='*80}")
    print(f"Total approved songs: {len(approved_songs)}")
    print(f"Found with complete metadata: {found_count}")
    print(f"Not found: {not_found_count}")
    print(f"{'='*80}")

    print("\nSample completed song:")
    import pprint
    pprint.pprint(completed_songs[0])

if __name__ == '__main__':
    complete_approved_metadata()
