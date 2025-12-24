"""
Enrich approved songs metadata by searching Spotify.

This script takes the approved songs (which have incomplete metadata from iPod)
and searches Spotify to get complete metadata including:
- Album art URLs
- BPM
- Genres
- Spotify URIs
"""

import json
from pathlib import Path
from src.utils import authenticate_spotify, setup_logging

logger = setup_logging(__name__, 'enrich_metadata.log')

def search_spotify_for_song(sp, title, artist):
    """
    Search Spotify for a song and return its metadata.

    Args:
        sp: Authenticated Spotify client
        title: Song title
        artist: Artist name

    Returns:
        Dict with complete metadata, or None if not found
    """
    try:
        # Search Spotify
        query = f"track:{title} artist:{artist}"
        results = sp.search(q=query, type='track', limit=5)

        if not results['tracks']['items']:
            logger.warning(f"No Spotify results for: {title} - {artist}")
            return None

        # Get first result (best match)
        track = results['tracks']['items'][0]

        # Get audio features for BPM
        audio_features = sp.audio_features([track['id']])[0]
        bpm = int(audio_features['tempo']) if audio_features else 0

        # Get artist genres
        artist_id = track['artists'][0]['id']
        artist_info = sp.artist(artist_id)
        genres = '; '.join(artist_info['genres']) if artist_info['genres'] else ''

        # Extract metadata
        metadata = {
            'track_id': track['id'],
            'title': track['name'],
            'artist': ', '.join(a['name'] for a in track['artists']),
            'album_artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'year': track['album']['release_date'][:4],
            'uri': track['uri'],
            'added_at': '',
            'album_art_url': track['album']['images'][0]['url'] if track['album']['images'] else '',
            'bpm': bpm,
            'genre': genres,
            'youtube_url': ''
        }

        logger.info(f"  Found on Spotify: {metadata['title']} - {metadata['artist']}")
        return metadata

    except Exception as e:
        logger.error(f"Error searching for '{title} - {artist}': {e}")
        return None

def enrich_approved_metadata():
    """Enrich approved songs metadata with Spotify data."""

    approved_path = Path('data/spotify/approved_discovered_songs.json')

    if not approved_path.exists():
        print("ERROR: approved_discovered_songs.json not found!")
        return

    # Load approved songs
    print("Loading approved songs...")
    with open(approved_path, 'r', encoding='utf-8') as f:
        approved_songs = json.load(f)

    print(f"Found {len(approved_songs)} approved songs")
    print("\nAuthenticating with Spotify...")

    # Authenticate with Spotify
    sp = authenticate_spotify()

    print("Searching Spotify for complete metadata...\n")

    enriched_songs = []
    found_count = 0
    not_found_count = 0

    for i, song in enumerate(approved_songs, 1):
        title = song['title']
        artist = song['artist']

        print(f"[{i}/{len(approved_songs)}] {title} - {artist}")

        # Search Spotify for this song
        enriched_metadata = search_spotify_for_song(sp, title, artist)

        if enriched_metadata:
            enriched_songs.append(enriched_metadata)
            found_count += 1
        else:
            # Keep original metadata if not found
            enriched_songs.append(song)
            not_found_count += 1
            print(f"  [WARNING] Not found on Spotify, keeping original metadata")

    # Save enriched metadata
    print(f"\n{'='*80}")
    print("ENRICHMENT COMPLETE")
    print(f"{'='*80}")
    print(f"Total songs: {len(approved_songs)}")
    print(f"Found on Spotify: {found_count}")
    print(f"Not found: {not_found_count}")
    print(f"{'='*80}")

    # Backup original file
    backup_path = approved_path.with_suffix('.backup.json')
    print(f"\nBacking up original approved songs to: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(approved_songs, f, indent=2, ensure_ascii=False)

    # Save enriched metadata to approved songs
    print(f"Saving enriched metadata to: {approved_path}")
    with open(approved_path, 'w', encoding='utf-8') as f:
        json.dump(enriched_songs, f, indent=2, ensure_ascii=False)

    # NOW ADD TO LIKED SONGS METADATA
    print(f"\n{'='*80}")
    print("ADDING APPROVED SONGS TO LIKED SONGS METADATA")
    print(f"{'='*80}")

    liked_songs_path = Path('data/spotify/liked_songs_metadata.json')

    if not liked_songs_path.exists():
        print(f"WARNING: {liked_songs_path} not found!")
        print("Creating new liked songs metadata file...")
        liked_songs = []
    else:
        print(f"Loading existing liked songs from: {liked_songs_path}")
        with open(liked_songs_path, 'r', encoding='utf-8') as f:
            liked_songs = json.load(f)
        print(f"  Found {len(liked_songs)} existing liked songs")

    # Get existing track IDs to avoid duplicates
    existing_track_ids = {song.get('track_id') for song in liked_songs if song.get('track_id')}
    print(f"  Checking for duplicates...")

    # Add enriched approved songs that aren't already in liked songs
    added_count = 0
    duplicate_count = 0

    for song in enriched_songs:
        track_id = song.get('track_id')
        if track_id and track_id in existing_track_ids:
            duplicate_count += 1
            print(f"  [SKIP] Already in liked songs: {song['title']} - {song['artist']}")
        else:
            liked_songs.append(song)
            if track_id:
                existing_track_ids.add(track_id)
            added_count += 1
            print(f"  [ADD] {song['title']} - {song['artist']}")

    # Backup original liked songs
    liked_backup_path = liked_songs_path.with_suffix('.backup.json')
    if liked_songs_path.exists():
        print(f"\nBacking up original liked songs to: {liked_backup_path}")
        with open(liked_songs_path, 'r', encoding='utf-8') as f:
            original_liked = json.load(f)
        with open(liked_backup_path, 'w', encoding='utf-8') as f:
            json.dump(original_liked, f, indent=2, ensure_ascii=False)

    # Save updated liked songs
    print(f"Saving updated liked songs to: {liked_songs_path}")
    with open(liked_songs_path, 'w', encoding='utf-8') as f:
        json.dump(liked_songs, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print("COMPLETE!")
    print(f"{'='*80}")
    print(f"Approved songs enriched: {found_count}/{len(approved_songs)}")
    print(f"Added to liked songs: {added_count}")
    print(f"Duplicates skipped: {duplicate_count}")
    print(f"Total liked songs now: {len(liked_songs)}")
    print(f"{'='*80}")

    print("\nYour approved songs are now part of your liked songs collection!")
    print("Future music discovery will use this expanded taste profile.")
    print("\nSample enriched song:")
    import pprint
    pprint.pprint(enriched_songs[0])

if __name__ == '__main__':
    enrich_approved_metadata()
