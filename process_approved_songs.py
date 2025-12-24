"""
Complete workflow for approved songs:
1. Search Spotify for complete metadata
2. Embed ID3 tags into MP3 files
3. Append to liked_songs_metadata.json
"""

import json
from pathlib import Path
from src.utils import authenticate_spotify, setup_logging, find_matching_file
from src.metadata_embedder import MetadataEmbedder

logger = setup_logging(__name__, 'process_approved.log')

def get_complete_spotify_metadata(sp, title, artist):
    """Search Spotify and return complete metadata."""
    try:
        query = f"track:{title} artist:{artist}"
        results = sp.search(q=query, type='track', limit=1)

        if not results['tracks']['items']:
            logger.warning(f"No Spotify results for: {title} - {artist}")
            return None

        track = results['tracks']['items'][0]

        # Get audio features for BPM
        try:
            audio_features = sp.audio_features([track['id']])[0]
            bpm = int(audio_features['tempo']) if audio_features else 0
        except:
            bpm = 0
            logger.warning(f"Could not fetch BPM for: {title}")

        # Get artist genres
        try:
            artist_id = track['artists'][0]['id']
            artist_info = sp.artist(artist_id)
            genres = '; '.join(artist_info['genres']) if artist_info.get('genres') else ''
        except:
            genres = ''
            logger.warning(f"Could not fetch genres for: {title}")

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
        }

        return metadata

    except Exception as e:
        logger.error(f"Error searching Spotify for '{title} - {artist}': {e}")
        return None

def main():
    """Process approved songs complete workflow."""

    print("="*80)
    print("PROCESSING APPROVED SONGS - COMPLETE WORKFLOW")
    print("="*80)

    # Load approved songs
    approved_path = Path('data/spotify/approved_discovered_songs.json')
    if not approved_path.exists():
        print("ERROR: approved_discovered_songs.json not found!")
        return

    with open(approved_path, 'r', encoding='utf-8') as f:
        approved_songs = json.load(f)

    print(f"\nLoaded {len(approved_songs)} approved songs")

    # STEP 1: Get complete Spotify metadata
    print("\n" + "="*80)
    print("STEP 1: FETCHING COMPLETE SPOTIFY METADATA")
    print("="*80)

    sp = authenticate_spotify()
    enriched_metadata = []

    for i, song in enumerate(approved_songs, 1):
        title = song['title']
        artist = song['artist']
        print(f"\n[{i}/{len(approved_songs)}] {title} - {artist}")

        metadata = get_complete_spotify_metadata(sp, title, artist)
        if metadata:
            print(f"  [SUCCESS] Found complete metadata")
            print(f"    Album: {metadata['album']}")
            print(f"    BPM: {metadata['bpm']}")
            print(f"    Genre: {metadata['genre'][:50] if metadata['genre'] else 'None'}")
            enriched_metadata.append(metadata)
        else:
            print(f"  [FAIL] Using iPod metadata")
            enriched_metadata.append(song)

    # STEP 2: Embed ID3 tags into MP3 files
    print("\n" + "="*80)
    print("STEP 2: EMBEDDING ID3 METADATA INTO MP3 FILES")
    print("="*80)

    discovered_folder = Path('discovered_songs')
    embedder = MetadataEmbedder()
    embedder.source_folder = discovered_folder
    embedder.mp3_files = list(discovered_folder.glob("*.mp3"))

    print(f"\nFound {len(embedder.mp3_files)} MP3 files in {discovered_folder}")

    embedded_count = 0
    failed_embed = 0

    for i, metadata in enumerate(enriched_metadata, 1):
        song_name = f"{metadata['title']} - {metadata['artist']}"
        print(f"\n[{i}/{len(enriched_metadata)}] {song_name}")

        # Find matching MP3
        matched_file, score = find_matching_file(
            metadata,
            embedder.mp3_files,
            threshold=0.75
        )

        if matched_file:
            print(f"  [MATCH] {matched_file.name} (similarity: {score:.2f})")

            # Embed metadata
            if embedder.embed_metadata(matched_file, metadata):
                print(f"  [SUCCESS] ID3 tags embedded")
                embedded_count += 1
            else:
                print(f"  [FAIL] Could not embed metadata")
                failed_embed += 1
        else:
            print(f"  [SKIP] No matching MP3 file")
            failed_embed += 1

    # STEP 3: Append to liked_songs_metadata.json
    print("\n" + "="*80)
    print("STEP 3: APPENDING TO LIKED SONGS METADATA")
    print("="*80)

    liked_songs_path = Path('liked_songs_metadata.json')

    if not liked_songs_path.exists():
        print("ERROR: liked_songs_metadata.json not found!")
        return

    with open(liked_songs_path, 'r', encoding='utf-8') as f:
        liked_songs = json.load(f)

    print(f"\nCurrent liked songs: {len(liked_songs)}")

    # Check for duplicates
    existing_track_ids = {s.get('track_id') for s in liked_songs if s.get('track_id')}

    added_count = 0
    duplicate_count = 0

    for metadata in enriched_metadata:
        track_id = metadata.get('track_id')
        if track_id and track_id in existing_track_ids:
            duplicate_count += 1
            print(f"  [SKIP] Duplicate: {metadata['title']} - {metadata['artist']}")
        else:
            liked_songs.append(metadata)
            if track_id:
                existing_track_ids.add(track_id)
            added_count += 1
            print(f"  [ADD] {metadata['title']} - {metadata['artist']}")

    # Backup and save
    backup_path = Path('liked_songs_metadata.backup.json')
    print(f"\nBacking up to: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(liked_songs, f, indent=2, ensure_ascii=False)

    print(f"Saving updated metadata to: {liked_songs_path}")
    with open(liked_songs_path, 'w', encoding='utf-8') as f:
        json.dump(liked_songs, f, indent=2, ensure_ascii=False)

    # STEP 4: Move to staging and optionally add to iTunes
    print("\n" + "="*80)
    print("STEP 4: MOVING APPROVED SONGS TO STAGING")
    print("="*80)

    discovered_folder = Path('discovered_songs')
    staging_folder = Path('music/staging')
    library_folder = Path('music/library')

    # Create folders
    staging_folder.mkdir(parents=True, exist_ok=True)
    library_folder.mkdir(parents=True, exist_ok=True)

    # Get MP3s for approved songs only
    mp3_files = list(discovered_folder.glob("*.mp3"))

    moved_count = 0
    moved_files = []

    for metadata in enriched_metadata:
        song_name = f"{metadata['title']} - {metadata['artist']}"

        # Find matching MP3
        matched_file, score = find_matching_file(metadata, mp3_files, threshold=0.75)

        if matched_file:
            print(f"  [MOVING] {matched_file.name}")

            # Move to staging
            staging_dest = staging_folder / matched_file.name
            import shutil
            shutil.move(str(matched_file), str(staging_dest))

            # Copy to library for permanent storage
            library_dest = library_folder / matched_file.name
            shutil.copy2(str(staging_dest), str(library_dest))

            moved_files.append(staging_dest)
            moved_count += 1
            print(f"    -> staging/ (for iTunes)")
            print(f"    -> library/ (permanent)")

    print(f"\nMoved {moved_count} songs to staging folder")

    # Ask about auto-adding to iTunes
    print("\n" + "="*80)
    print("ITUNES INTEGRATION")
    print("="*80)
    print("\nOptions:")
    print("  1. Auto-add to iTunes (uses COM interface)")
    print("  2. Manual drag-and-drop (you drag music/staging/ into iTunes)")

    choice = input("\nChoose option (1/2) [default: 2]: ").strip()

    if choice == "1":
        try:
            import win32com.client
            print("\nConnecting to iTunes...")
            itunes = win32com.client.Dispatch("iTunes.Application")
            print("Connected!")

            added_count = 0
            for mp3_file in moved_files:
                try:
                    itunes.LibraryPlaylist.AddFile(str(mp3_file.absolute()))
                    print(f"  [ADDED] {mp3_file.name}")
                    added_count += 1
                except Exception as e:
                    print(f"  [FAIL] {mp3_file.name}: {e}")

            print(f"\n✓ Added {added_count}/{len(moved_files)} songs to iTunes")

        except ImportError:
            print("\nERROR: pywin32 not installed")
            print("Install with: pip install pywin32")
            print("Falling back to manual method...")
            choice = "2"
        except Exception as e:
            print(f"\nERROR: {e}")
            print("Falling back to manual method...")
            choice = "2"

    if choice != "1":
        print("\nManual steps:")
        print(f"  1. Drag music/staging/ folder into iTunes")
        print(f"  2. Sync your iPod")
        print(f"  3. Come back here to finalize")

    # STEP 5: Move to downloaded_songs (ultimate ledger)
    print("\n" + "="*80)
    print("STEP 5: MOVE TO DOWNLOADED_SONGS FOLDER (ULTIMATE LEDGER)")
    print("="*80)
    print("\nThis will move approved songs from staging/ to downloaded_songs/")
    print("Only proceed after you've added songs to iTunes!")

    confirm = input("\nHave you moved songs from staging to iTunes? (yes/no) [default: no]: ").strip().lower()

    if confirm == "yes":
        downloaded_songs_folder = Path('downloaded_songs')
        downloaded_songs_folder.mkdir(parents=True, exist_ok=True)

        ledger_count = 0
        for mp3_file in moved_files:
            if mp3_file.exists():
                dest = downloaded_songs_folder / mp3_file.name
                shutil.move(str(mp3_file), str(dest))
                print(f"  [MOVED] {mp3_file.name} -> downloaded_songs/")
                ledger_count += 1

        print(f"\n✓ Moved {ledger_count} songs to downloaded_songs/ (ultimate ledger)")
        print(f"✓ Staging folder cleared")
    else:
        print("\nSkipping move to downloaded_songs/")
        print("You can manually move from music/staging/ later")
        print(f"Files remain in: {staging_folder.absolute()}")

    # Final summary
    print("\n" + "="*80)
    print("COMPLETE!")
    print("="*80)
    print(f"Approved songs processed: {len(approved_songs)}")
    print(f"Spotify metadata fetched: {len([m for m in enriched_metadata if m.get('track_id')])}")
    print(f"ID3 tags embedded: {embedded_count}")
    print(f"Added to liked songs: {added_count}")
    print(f"Duplicates skipped: {duplicate_count}")
    print(f"Moved to staging: {moved_count}")
    print(f"Total liked songs now: {len(liked_songs)}")
    print("="*80)
    print(f"\nSongs ready in: {staging_folder.absolute()}")
    print(f"Permanent copies in: {library_folder.absolute()}")
    print("="*80)

if __name__ == '__main__':
    main()
