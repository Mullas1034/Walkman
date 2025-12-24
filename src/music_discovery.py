"""
Music discovery module for Walkman.

Generates personalized music recommendations based on Spotify listening history
using a multi-strategy approach:
- Genre-based recommendations (40 songs from top artists)
- Artist exploration (30 songs from middle-tier artists)
- Temporal diversity (20 songs from random artists)
- Random exploration (10 songs from lesser-known artists)

Integrates with YouTube downloader and metadata embedder to create a
complete discovery pipeline from recommendation to tagged MP3 files.

Author: Kieran
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import Counter

from .utils import (
    setup_logging,
    authenticate_spotify,
    SPOTIFY_METADATA_PATH,
    APPROVED_SONGS_PATH,
    DISCOVERED_METADATA_PATH,
    REJECTED_SONGS_PATH,
    DISCOVERED_DIR,
)
from .youtube_downloader import YouTubeDownloader
from .metadata_embedder import MetadataEmbedder

# Configure logging
logger = setup_logging(__name__, 'music_discovery.log')


class MusicDiscovery:
    """
    Generates personalized music recommendations based on listening history.

    Uses multi-strategy recommendation engine that analyzes:
    - Genre preferences (weighted by frequency)
    - Artist preferences (top and middle-tier)
    - Temporal patterns (decades, years)
    - Audio features (BPM averages)

    Attributes:
        sp: Authenticated Spotipy client
        liked_songs: List of liked song metadata
        approved_songs: List of approved discovered songs
        discovered_songs: List of pending discovered songs
        rejected_songs: List of rejected discovered songs
        excluded_track_ids: Set of track IDs to exclude from recommendations
    """

    def __init__(self):
        """Initialize music discovery engine."""
        self.sp = None
        self.liked_songs: List[Dict] = []
        self.approved_songs: List[Dict] = []
        self.discovered_songs: List[Dict] = []
        self.rejected_songs: List[Dict] = []
        self.excluded_track_ids: set = set()

        logger.info("Music discovery engine initialized")

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

    def load_existing_songs(self) -> None:
        """
        Load all existing song metadata to avoid duplicate recommendations.

        Loads songs from:
        - liked_songs_metadata.json (Spotify liked songs)
        - approved_discovered_songs.json (Previously approved discoveries)
        - discovered_songs_metadata.json (Pending discoveries)
        - rejected_discovered_songs.json (Rejected discoveries)

        Builds exclusion set from all track IDs to prevent duplicates.
        """
        logger.info("Loading existing song libraries...")

        # Load liked songs
        if SPOTIFY_METADATA_PATH.exists():
            with open(SPOTIFY_METADATA_PATH, 'r', encoding='utf-8') as f:
                self.liked_songs = json.load(f)
            logger.info(f"  Loaded {len(self.liked_songs)} liked songs")

        # Load approved discoveries
        if APPROVED_SONGS_PATH.exists():
            with open(APPROVED_SONGS_PATH, 'r', encoding='utf-8') as f:
                self.approved_songs = json.load(f)
            logger.info(f"  Loaded {len(self.approved_songs)} approved discoveries")

        # Load current discovered songs (pending)
        if DISCOVERED_METADATA_PATH.exists():
            with open(DISCOVERED_METADATA_PATH, 'r', encoding='utf-8') as f:
                self.discovered_songs = json.load(f)
            logger.info(f"  Loaded {len(self.discovered_songs)} pending discoveries")

        # Load rejected songs
        if REJECTED_SONGS_PATH.exists():
            with open(REJECTED_SONGS_PATH, 'r', encoding='utf-8') as f:
                self.rejected_songs = json.load(f)
            logger.info(f"  Loaded {len(self.rejected_songs)} rejected songs")

        # Build exclusion set
        all_songs = (
            self.liked_songs +
            self.approved_songs +
            self.discovered_songs +
            self.rejected_songs
        )
        self.excluded_track_ids = {
            song['track_id'] for song in all_songs if song.get('track_id')
        }

        logger.info(f"  Total exclusions: {len(self.excluded_track_ids)} tracks")

    def analyze_taste_profile(self) -> Optional[Dict]:
        """
        Analyze user's music taste from liked + approved songs.

        Returns:
            Dictionary with taste profile data:
            - top_genres: List of (genre, count) tuples
            - top_artists: List of (artist_name, count) tuples
            - top_artist_ids: List of Spotify artist IDs
            - track_ids: List of all track IDs
            - avg_bpm: Average BPM across songs
            - decades: Counter of decades represented
            - total_songs: Total songs analyzed

        Returns None if no songs available for analysis.
        """
        logger.info("Analyzing music taste profile...")

        # Combine liked and approved for taste analysis
        taste_songs = self.liked_songs + self.approved_songs

        if not taste_songs:
            logger.warning("No songs found to analyze!")
            return None

        # Analyze genres
        genres = []
        for song in taste_songs:
            if song.get('genre'):
                # Split multiple genres (separated by semicolons)
                song_genres = [g.strip() for g in song['genre'].split(';')]
                genres.extend(song_genres)

        genre_counts = Counter(genres)
        top_genres = genre_counts.most_common(10)

        # Get top artists
        artists = [song.get('artist', '') for song in taste_songs if song.get('artist')]
        artist_counts = Counter(artists)
        top_artists = artist_counts.most_common(20)

        # Get track IDs
        track_ids = [song['track_id'] for song in taste_songs if song.get('track_id')]

        # Get artist IDs from tracks
        top_artist_ids = []
        if track_ids:
            logger.info("  Fetching artist IDs from Spotify...")
            try:
                # Sample tracks to get artist IDs
                sample_size = min(50, len(track_ids))
                sample_tracks = track_ids[:sample_size]

                # Batch fetch tracks (50 at a time)
                for i in range(0, len(sample_tracks), 50):
                    batch = sample_tracks[i:i+50]
                    tracks_data = self.sp.tracks(batch)

                    for track in tracks_data['tracks']:
                        if track and track.get('artists'):
                            for artist in track['artists']:
                                top_artist_ids.append(artist['id'])

                # Get most common artist IDs
                artist_id_counts = Counter(top_artist_ids)
                top_artist_ids = [aid for aid, count in artist_id_counts.most_common(50)]

            except Exception as e:
                logger.warning(f"Error fetching artist IDs: {e}")
                top_artist_ids = []

        # Analyze audio features
        bpms = [song['bpm'] for song in taste_songs if song.get('bpm')]
        avg_bpm = sum(bpms) / len(bpms) if bpms else None

        # Get decades
        years = [
            int(song['year']) for song in taste_songs
            if song.get('year') and song['year'].isdigit()
        ]
        decades = Counter([year // 10 * 10 for year in years])

        profile = {
            'top_genres': top_genres,
            'top_artists': top_artists,
            'top_artist_ids': top_artist_ids,
            'track_ids': track_ids,
            'avg_bpm': avg_bpm,
            'decades': decades,
            'total_songs': len(taste_songs)
        }

        logger.info(f"  Analyzed {len(taste_songs)} songs")
        logger.info(f"  Top 5 genres: {', '.join([f'{g[0]} ({g[1]})' for g in top_genres[:5]])}")
        logger.info(f"  Top 5 artists: {', '.join([a[0] for a in top_artists[:5]])}")
        if top_artist_ids:
            logger.info(f"  Found {len(top_artist_ids)} unique artist IDs")
        if avg_bpm:
            logger.info(f"  Average BPM: {avg_bpm:.0f}")

        return profile

    def _get_album_tracks_from_artists(
        self,
        artist_ids: List[str],
        max_tracks: int
    ) -> List[Dict]:
        """
        Get tracks from albums of given artists.

        Args:
            artist_ids: List of Spotify artist IDs
            max_tracks: Maximum number of tracks to return

        Returns:
            List of Spotify track objects
        """
        discovered_tracks = []

        for artist_id in artist_ids:
            if len(discovered_tracks) >= max_tracks:
                break

            try:
                # Get artist's albums
                albums = self.sp.artist_albums(
                    artist_id,
                    album_type='album,single',
                    limit=10
                )

                for album in albums['items']:
                    if len(discovered_tracks) >= max_tracks:
                        break

                    try:
                        # Get tracks from album
                        album_tracks = self.sp.album_tracks(album['id'], limit=10)

                        for track in album_tracks['items']:
                            if (track['id'] and
                                track['id'] not in self.excluded_track_ids):
                                # Get full track info
                                full_track = self.sp.track(track['id'])
                                discovered_tracks.append(full_track)
                                self.excluded_track_ids.add(track['id'])

                            if len(discovered_tracks) >= max_tracks:
                                break

                    except Exception:
                        continue

            except Exception:
                continue

        return discovered_tracks

    def get_genre_based_recommendations(
        self,
        profile: Dict,
        count: int = 40
    ) -> List[Dict]:
        """
        Get recommendations from top artists' albums.

        Strategy 1: Explores albums from your most-listened artists.

        Args:
            profile: Taste profile dictionary
            count: Number of recommendations to generate

        Returns:
            List of Spotify track objects
        """
        logger.info(f"Generating {count} recommendations from top artists' albums...")
        recommendations = []

        if not profile['top_artist_ids']:
            logger.warning("No artist IDs found, skipping genre-based recommendations")
            return []

        try:
            recommendations = self._get_album_tracks_from_artists(
                profile['top_artist_ids'][:10],
                max_tracks=count
            )
        except Exception as e:
            logger.error(f"Error generating genre-based recommendations: {e}")

        logger.info(f"  Found {len(recommendations)} songs")
        return recommendations

    def get_artist_based_recommendations(
        self,
        profile: Dict,
        count: int = 30
    ) -> List[Dict]:
        """
        Get tracks from middle-tier artists.

        Strategy 2: Explores artists you listen to moderately (not top 10).

        Args:
            profile: Taste profile dictionary
            count: Number of recommendations to generate

        Returns:
            List of Spotify track objects
        """
        logger.info(f"Generating {count} tracks from middle-tier artists...")
        recommendations = []

        if not profile['top_artist_ids']:
            logger.warning("No artist IDs found, skipping artist-based recommendations")
            return []

        try:
            # Use middle-tier artists (11-30)
            middle_artists = (
                profile['top_artist_ids'][10:30]
                if len(profile['top_artist_ids']) > 30
                else profile['top_artist_ids'][5:]
            )

            recommendations = self._get_album_tracks_from_artists(
                middle_artists,
                max_tracks=count
            )
        except Exception as e:
            logger.error(f"Error generating artist-based recommendations: {e}")

        logger.info(f"  Found {len(recommendations)} songs")
        return recommendations

    def get_temporal_diversity_recommendations(
        self,
        profile: Dict,
        count: int = 20
    ) -> List[Dict]:
        """
        Get tracks from random artists for diversity.

        Strategy 3: Random sampling to introduce variety.

        Args:
            profile: Taste profile dictionary
            count: Number of recommendations to generate

        Returns:
            List of Spotify track objects
        """
        logger.info(f"Generating {count} tracks from random artists...")
        recommendations = []

        if not profile['top_artist_ids']:
            logger.warning("No artist IDs found, skipping temporal diversity")
            return []

        try:
            # Random sample of artists
            artist_sample = random.sample(
                profile['top_artist_ids'],
                min(15, len(profile['top_artist_ids']))
            )

            recommendations = self._get_album_tracks_from_artists(
                artist_sample,
                max_tracks=count
            )
        except Exception as e:
            logger.error(f"Error generating temporal diversity recommendations: {e}")

        logger.info(f"  Found {len(recommendations)} songs")
        return recommendations

    def get_random_exploration_recommendations(
        self,
        profile: Dict,
        count: int = 10
    ) -> List[Dict]:
        """
        Get tracks from lesser-known artists.

        Strategy 4: Explores artists you listen to infrequently.

        Args:
            profile: Taste profile dictionary
            count: Number of recommendations to generate

        Returns:
            List of Spotify track objects
        """
        logger.info(f"Generating {count} tracks from lesser-known artists...")
        recommendations = []

        if not profile['top_artist_ids']:
            logger.warning("No artist IDs found, skipping random exploration")
            return []

        try:
            # Use artists from end of list (less frequently listened)
            less_common_artists = (
                profile['top_artist_ids'][30:]
                if len(profile['top_artist_ids']) > 30
                else profile['top_artist_ids'][15:]
            )

            if not less_common_artists:
                less_common_artists = profile['top_artist_ids']

            recommendations = self._get_album_tracks_from_artists(
                less_common_artists,
                max_tracks=count
            )
        except Exception as e:
            logger.error(f"Error generating random exploration recommendations: {e}")

        logger.info(f"  Found {len(recommendations)} songs")
        return recommendations

    def generate_recommendations(self, target_count: int = 100) -> List[Dict]:
        """
        Generate all recommendations using multi-strategy approach.

        Strategy breakdown:
        - 40 songs: Genre-based (top artists' albums)
        - 30 songs: Artist-based (middle-tier artists)
        - 20 songs: Temporal diversity (random artists)
        - 10 songs: Random exploration (lesser-known artists)

        Args:
            target_count: Total number of recommendations to generate

        Returns:
            List of Spotify track objects
        """
        logger.info("="*80)
        logger.info("GENERATING MUSIC RECOMMENDATIONS")
        logger.info("="*80)

        profile = self.analyze_taste_profile()
        if not profile:
            return []

        all_recommendations = []

        # Execute 4-strategy recommendation engine
        all_recommendations.extend(self.get_genre_based_recommendations(profile, 40))
        all_recommendations.extend(self.get_artist_based_recommendations(profile, 30))
        all_recommendations.extend(self.get_temporal_diversity_recommendations(profile, 20))
        all_recommendations.extend(self.get_random_exploration_recommendations(profile, 10))

        # Fill remaining slots if needed
        if len(all_recommendations) < target_count:
            logger.info(f"Filling remaining slots ({target_count - len(all_recommendations)} songs)...")
            remaining = target_count - len(all_recommendations)

            try:
                if profile['top_artist_ids']:
                    more_tracks = self._get_album_tracks_from_artists(
                        profile['top_artist_ids'],
                        max_tracks=remaining
                    )
                    all_recommendations.extend(more_tracks)
                    logger.info(f"  Filled to {len(all_recommendations)}/{target_count} songs")
            except Exception as e:
                logger.error(f"Error filling recommendations: {e}")

        # Trim to exact count
        all_recommendations = all_recommendations[:target_count]

        logger.info("="*80)
        logger.info(f"TOTAL RECOMMENDATIONS: {len(all_recommendations)}")
        logger.info("="*80)

        return all_recommendations

    def convert_spotify_tracks_to_metadata(
        self,
        tracks: List[Dict]
    ) -> List[Dict]:
        """
        Convert Spotify track objects to Walkman metadata format.

        Args:
            tracks: List of Spotify track objects

        Returns:
            List of metadata dictionaries
        """
        logger.info("Converting Spotify tracks to metadata format...")
        metadata_list = []

        for track in tracks:
            album = track['album']
            release_date = album.get('release_date', '')
            year = release_date.split('-')[0] if release_date else ''
            album_art_url = album['images'][0]['url'] if album.get('images') else None

            metadata = {
                'track_id': track['id'],
                'title': track['name'],
                'artist': ', '.join([artist['name'] for artist in track['artists']]),
                'album_artist': album['artists'][0]['name'] if album.get('artists') else '',
                'album': album['name'],
                'year': year,
                'uri': track['uri'],
                'album_art_url': album_art_url,
                'bpm': None,  # Not fetched for discoveries
                'genre': ''   # Not fetched for discoveries
            }

            metadata_list.append(metadata)

        logger.info(f"  Converted {len(metadata_list)} tracks")
        return metadata_list

    def process_discoveries(
        self,
        metadata_list: List[Dict]
    ) -> Tuple[int, int]:
        """
        Download and tag discovered songs.

        Args:
            metadata_list: List of song metadata dictionaries

        Returns:
            Tuple of (successful_count, failed_count)
        """
        logger.info("="*80)
        logger.info("PROCESSING DISCOVERED SONGS")
        logger.info("="*80)

        # Download from YouTube
        downloader = YouTubeDownloader(download_folder=DISCOVERED_DIR)
        success, failed = downloader.process_metadata(metadata_list)

        # Embed metadata
        if success > 0:
            logger.info("Embedding metadata into downloaded MP3s...")
            embedder = MetadataEmbedder(
                source_folder=DISCOVERED_DIR,
                metadata_path=DISCOVERED_METADATA_PATH
            )
            embedder.scan_mp3_files()
            embedder.process_batch(metadata_list)

        return success, failed

    def run(self, target_count: int = 100) -> None:
        """
        Execute complete music discovery workflow.

        Steps:
            1. Authenticate with Spotify
            2. Load existing songs (for exclusion)
            3. Generate recommendations
            4. Convert to metadata format
            5. Download from YouTube
            6. Embed metadata
            7. Save metadata file

        Args:
            target_count: Number of songs to discover
        """
        logger.info("="*80)
        logger.info("MUSIC DISCOVERY ENGINE - Starting")
        logger.info("="*80)

        try:
            # Authenticate
            self.authenticate()

            # Load existing songs
            self.load_existing_songs()

            # Generate recommendations
            recommendations = self.generate_recommendations(target_count=target_count)

            if not recommendations:
                logger.error("No recommendations generated!")
                return

            # Convert to metadata format
            metadata_list = self.convert_spotify_tracks_to_metadata(recommendations)

            # Process (download + embed)
            success, failed = self.process_discoveries(metadata_list)

            # Save metadata file
            logger.info(f"Saving metadata to {DISCOVERED_METADATA_PATH}")
            with open(DISCOVERED_METADATA_PATH, 'w', encoding='utf-8') as f:
                json.dump(metadata_list, f, indent=2, ensure_ascii=False)

            logger.info("="*80)
            logger.info("MUSIC DISCOVERY - Complete")
            logger.info(f"Total recommendations: {len(metadata_list)}")
            logger.info(f"Successfully downloaded: {success}")
            logger.info(f"Failed: {failed}")
            logger.info("="*80)

            logger.info("\nNext steps:")
            logger.info("1. Drag discovered songs to iTunes")
            logger.info("2. Sync to iPod and listen")
            logger.info("3. Add favorites to 'On-The-Go' playlist")
            logger.info("4. Run itunes_integrator to process approvals")

        except Exception as e:
            logger.error(f"Music discovery failed: {e}")
            raise


def main():
    """Command-line entry point for music discovery."""
    discovery = MusicDiscovery()
    discovery.run(target_count=100)


if __name__ == '__main__':
    main()
