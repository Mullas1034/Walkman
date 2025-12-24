"""
Spotify synchronization module for Walkman.

Fetches all liked songs from Spotify with complete metadata including:
- Track information (title, artist, album, year)
- Audio features (BPM, key, energy, etc.)
- Artist genres
- Album artwork URLs

The metadata is saved to JSON for use by the discovery engine.

Author: Kieran
"""

import json
from typing import List, Dict, Optional
from collections import Counter

from .utils import (
    setup_logging,
    authenticate_spotify,
    SPOTIFY_METADATA_PATH,
    LIKED_SONGS_TXT_PATH,
)

# Configure logging
logger = setup_logging(__name__, 'spotify_sync.log')


class SpotifySync:
    """Syncs Spotify liked songs with local metadata database."""

    def __init__(self):
        """Initialize Spotify sync client."""
        self.sp = None
        self.liked_songs: List[Dict] = []

    def authenticate(self) -> None:
        """
        Authenticate with Spotify API.

        Raises:
            ValueError: If credentials not configured
            SpotifyException: If authentication fails
        """
        logger.info("Authenticating with Spotify...")
        try:
            self.sp = authenticate_spotify(scope='user-library-read')
            logger.info("Successfully authenticated with Spotify")
        except Exception as e:
            logger.error(f"Spotify authentication failed: {e}")
            raise

    def fetch_all_liked_songs(self) -> List[Dict]:
        """
        Fetch all liked songs from Spotify with basic metadata.

        Returns:
            List of song dictionaries with track metadata

        Raises:
            ValueError: If not authenticated
        """
        if not self.sp:
            raise ValueError("Not authenticated. Call authenticate() first.")

        logger.info("Fetching liked songs from Spotify...")
        liked_songs = []
        offset = 0
        limit = 50  # Spotify API max

        while True:
            try:
                results = self.sp.current_user_saved_tracks(limit=limit, offset=offset)

                if not results['items']:
                    break

                for item in results['items']:
                    track = item['track']
                    album = track['album']

                    # Extract year from release date
                    release_date = album.get('release_date', '')
                    year = release_date.split('-')[0] if release_date else ''

                    # Get album art URL
                    album_art_url = album['images'][0]['url'] if album.get('images') else None

                    song_info = {
                        'track_id': track['id'],
                        'title': track['name'],
                        'artist': ', '.join([artist['name'] for artist in track['artists']]),
                        'album_artist': album['artists'][0]['name'] if album.get('artists') else '',
                        'album': album['name'],
                        'year': year,
                        'uri': track['uri'],
                        'added_at': item['added_at'],
                        'album_art_url': album_art_url,
                        'bpm': None,  # Filled later
                        'genre': '',  # Filled later
                    }
                    liked_songs.append(song_info)

                offset += limit
                logger.info(f"Fetched {len(liked_songs)} songs so far...")

                if len(results['items']) < limit:
                    break

            except Exception as e:
                logger.error(f"Error fetching liked songs: {e}")
                raise

        logger.info(f"Total liked songs fetched: {len(liked_songs)}")
        self.liked_songs = liked_songs
        return liked_songs

    def fetch_audio_features(self) -> None:
        """
        Fetch audio features (including BPM) for all songs in batches.

        Updates self.liked_songs with BPM data.
        """
        if not self.liked_songs:
            logger.warning("No liked songs to fetch audio features for")
            return

        logger.info("Fetching audio features (BPM, etc.)...")
        track_ids = [song['track_id'] for song in self.liked_songs if song['track_id']]

        batch_size = 100  # Spotify API max
        all_audio_features = []

        try:
            for i in range(0, len(track_ids), batch_size):
                batch = track_ids[i:i + batch_size]
                features = self.sp.audio_features(batch)
                all_audio_features.extend(features)
                logger.info(f"Processed {min(i + batch_size, len(track_ids))}/{len(track_ids)} tracks...")

            # Create BPM mapping
            bpm_map = {}
            for feature in all_audio_features:
                if feature:
                    bpm_map[feature['id']] = round(feature['tempo'])

            # Update songs with BPM
            for song in self.liked_songs:
                song['bpm'] = bpm_map.get(song['track_id'])

            logger.info("Audio features fetched successfully")

        except Exception as e:
            logger.warning(f"Could not fetch audio features: {e}")
            logger.info("Continuing without BPM data...")
            for song in self.liked_songs:
                song['bpm'] = None

    def fetch_artist_genres(self) -> None:
        """
        Fetch genres from artists for all songs in batches.

        Updates self.liked_songs with genre data.
        """
        if not self.liked_songs:
            logger.warning("No liked songs to fetch genres for")
            return

        logger.info("Fetching artist genres...")

        try:
            # Get track IDs
            track_ids = [song['track_id'] for song in self.liked_songs if song['track_id']]

            # Fetch artist IDs from tracks in batches
            artist_ids = []
            batch_size = 50

            for i in range(0, len(track_ids), batch_size):
                batch = track_ids[i:i + batch_size]
                tracks_data = self.sp.tracks(batch)

                for track in tracks_data['tracks']:
                    if track and track.get('artists'):
                        for artist in track['artists']:
                            artist_ids.append(artist['id'])

                logger.info(f"Processed {min(i + batch_size, len(track_ids))}/{len(track_ids)} tracks...")

            # Get unique artist IDs
            unique_artist_ids = list(set(artist_ids))
            artist_counts = Counter(artist_ids)

            # Fetch artist details in batches
            genre_map = {}
            for i in range(0, len(unique_artist_ids), batch_size):
                batch = unique_artist_ids[i:i + batch_size]
                artists = self.sp.artists(batch)['artists']

                for artist in artists:
                    if artist and artist.get('genres'):
                        genre_map[artist['id']] = '; '.join(artist['genres'])

                logger.info(f"Processed {min(i + batch_size, len(unique_artist_ids))}/{len(unique_artist_ids)} artists...")

            # Update songs with primary artist's genre
            for i, song in enumerate(self.liked_songs):
                # Get artist ID from the track
                track_data = self.sp.track(song['track_id'])
                if track_data and track_data.get('artists'):
                    primary_artist_id = track_data['artists'][0]['id']
                    song['genre'] = genre_map.get(primary_artist_id, '')

            logger.info("Artist genres fetched successfully")

        except Exception as e:
            logger.warning(f"Could not fetch artist genres: {e}")
            logger.info("Continuing without genre data...")
            for song in self.liked_songs:
                song['genre'] = ''

    def save_metadata(self) -> None:
        """
        Save liked songs metadata to JSON and text files.

        Saves to:
            - data/spotify/liked_songs_metadata.json (full metadata)
            - data/spotify/liked_songs.txt (simple title - artist format)
        """
        if not self.liked_songs:
            logger.warning("No liked songs to save")
            return

        # Save JSON metadata
        logger.info(f"Saving metadata to {SPOTIFY_METADATA_PATH}")
        with open(SPOTIFY_METADATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.liked_songs, f, indent=2, ensure_ascii=False)

        # Save simple text format
        logger.info(f"Saving simple list to {LIKED_SONGS_TXT_PATH}")
        with open(LIKED_SONGS_TXT_PATH, 'w', encoding='utf-8') as f:
            for song in self.liked_songs:
                f.write(f"{song['title']} - {song['artist']}\n")

        logger.info(f"Metadata saved successfully ({len(self.liked_songs)} songs)")

    def run(self) -> None:
        """
        Execute complete Spotify sync workflow.

        Steps:
            1. Authenticate with Spotify
            2. Fetch all liked songs
            3. Fetch audio features (BPM)
            4. Fetch artist genres
            5. Save metadata to files
        """
        logger.info("="*80)
        logger.info("SPOTIFY SYNC - Starting")
        logger.info("="*80)

        try:
            self.authenticate()
            self.fetch_all_liked_songs()
            self.fetch_audio_features()
            self.fetch_artist_genres()
            self.save_metadata()

            logger.info("="*80)
            logger.info("SPOTIFY SYNC - Complete")
            logger.info(f"Total songs synced: {len(self.liked_songs)}")
            logger.info("="*80)

        except Exception as e:
            logger.error(f"Spotify sync failed: {e}")
            raise


def main():
    """Command-line entry point for Spotify sync."""
    sync = SpotifySync()
    sync.run()


if __name__ == '__main__':
    main()
