"""
iTunes integration module for Walkman.

Manages the approval workflow for discovered songs using iTunes and iPod:
1. Reads "On-The-Go" playlist from iTunes (user's approved songs)
2. Compares with discovered songs metadata
3. Moves approved songs to library + staging folders
4. Deletes rejected songs
5. Updates metadata tracking files
6. Clears "On-The-Go" playlist for next batch

This module provides the human feedback loop for the discovery engine,
using the iPod's native "On-The-Go" playlist as a binary approval signal.

Author: Kieran
"""

import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple

try:
    import win32com.client
    ITUNES_AVAILABLE = True
except ImportError:
    ITUNES_AVAILABLE = False

from .utils import (
    setup_logging,
    similarity_ratio,
    normalize_string,
    DISCOVERED_METADATA_PATH,
    APPROVED_SONGS_PATH,
    REJECTED_SONGS_PATH,
    LIBRARY_DIR,
    DISCOVERED_DIR,
    STAGING_DIR,
)

# Configure logging
logger = setup_logging(__name__, 'itunes_integrator.log')


class iTunesIntegrator:
    """
    Integrates discovered songs with iTunes approval workflow.

    Uses iTunes COM interface to read "On-The-Go" playlist and determine
    which discovered songs the user approved. Approved songs are moved to
    the library, rejected songs are deleted.

    Attributes:
        itunes: iTunes COM object
        on_the_go_tracks: List of tracks from On-The-Go playlist
        discovered_metadata: List of discovered song metadata
    """

    def __init__(self, playlist_names: Optional[List[str]] = None, use_ipod: bool = False):
        """
        Initialize iTunes integrator.

        Args:
            playlist_names: List of playlist names to read approved songs from.
                          If None, defaults to ["On-The-Go"]
            use_ipod: If True, read playlists from connected iPod instead of iTunes library
        """
        if not ITUNES_AVAILABLE:
            logger.error("pywin32 not installed. iTunes integration requires pywin32.")
            raise ImportError("pywin32 is required for iTunes integration")

        self.itunes = None
        self.playlist_names = playlist_names or ["On-The-Go"]
        self.use_ipod = use_ipod
        self.on_the_go_tracks: List[Dict] = []
        self.discovered_metadata: List[Dict] = []

        logger.info(f"iTunes integrator initialized with playlists: {self.playlist_names}")
        logger.info(f"Source: {'iPod' if use_ipod else 'iTunes Library'}")

    def connect_to_itunes(self) -> bool:
        """
        Connect to iTunes via Windows COM interface.

        Returns:
            True if connection successful, False otherwise

        Raises:
            RuntimeError: If iTunes is not installed
        """
        logger.info("Connecting to iTunes...")
        try:
            self.itunes = win32com.client.Dispatch("iTunes.Application")
            logger.info("Successfully connected to iTunes")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to iTunes: {e}")
            logger.info("Make sure iTunes is installed and try running as administrator")
            return False

    def get_on_the_go_playlist_tracks(self) -> List[Dict]:
        """
        Get all tracks from the configured playlists in iTunes or iPod.

        Returns:
            List of track info dictionaries with 'title', 'artist', 'album' keys

        Raises:
            ValueError: If not connected to iTunes
        """
        if not self.itunes:
            raise ValueError("Not connected to iTunes. Call connect_to_itunes() first.")

        logger.info(f"Reading playlists: {self.playlist_names}...")

        all_track_info = []

        try:
            # Get source (either iTunes library or iPod)
            if self.use_ipod:
                # Find iPod source
                sources = self.itunes.Sources
                source = None
                for i in range(1, sources.Count + 1):
                    src = sources.Item(i)
                    if src.Kind == 2:  # Kind 2 = iPod
                        source = src
                        logger.info(f"Found iPod: {src.Name}")
                        break

                if not source:
                    logger.error("No iPod found! Make sure it's connected.")
                    return []
            else:
                source = self.itunes.LibrarySource

            # Get all playlists from source
            playlists = source.Playlists

            # Process each configured playlist name
            for playlist_name in self.playlist_names:
                # Find matching playlist
                found_playlist = None
                for i in range(1, playlists.Count + 1):
                    playlist = playlists.Item(i)
                    if playlist.Name.lower() == playlist_name.lower():
                        found_playlist = playlist
                        break

                if not found_playlist:
                    logger.warning(f"Playlist '{playlist_name}' not found!")
                    continue

                # Get all tracks from this playlist
                tracks = found_playlist.Tracks
                track_count = tracks.Count

                logger.info(f"Found '{playlist_name}' playlist with {track_count} tracks")

                for i in range(1, track_count + 1):
                    track = tracks.Item(i)
                    info = {
                        'title': track.Name,
                        'artist': track.Artist,
                        'album': track.Album,
                    }
                    all_track_info.append(info)

            logger.info(f"Read {len(all_track_info)} total tracks from {len(self.playlist_names)} playlists")
            return all_track_info

        except Exception as e:
            logger.error(f"Error reading playlists: {e}")
            return []

    def load_discovered_metadata(self) -> List[Dict]:
        """
        Load discovered songs metadata from JSON file.

        Returns:
            List of song metadata dictionaries

        Raises:
            ValueError: If metadata file doesn't exist
        """
        logger.info("Loading discovered songs metadata...")

        if not DISCOVERED_METADATA_PATH.exists():
            logger.error(f"Metadata file not found: {DISCOVERED_METADATA_PATH}")
            logger.info("Have you run music_discovery.py yet?")
            raise ValueError(f"Metadata file not found: {DISCOVERED_METADATA_PATH}")

        with open(DISCOVERED_METADATA_PATH, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        logger.info(f"Loaded {len(metadata)} discovered songs")
        return metadata

    def classify_songs(self) -> Tuple[List[Dict], List[Dict]]:
        """
        Classify discovered songs as approved or rejected based on On-The-Go playlist.

        Songs in the On-The-Go playlist (with >= 75% name similarity) are approved.
        All other songs are rejected.

        Returns:
            Tuple of (approved_songs, rejected_songs) metadata lists
        """
        logger.info("="*80)
        logger.info("CLASSIFYING DISCOVERED SONGS")
        logger.info("="*80)

        approved = []
        rejected = []

        # Create set of On-The-Go track patterns for faster lookup
        on_the_go_patterns = set()
        for track in self.on_the_go_tracks:
            pattern = normalize_string(f"{track['title']} {track['artist']}")
            on_the_go_patterns.add(pattern)

        logger.info(f"Comparing {len(self.discovered_metadata)} discovered songs "
                   f"with {len(self.on_the_go_tracks)} On-The-Go tracks...")

        for metadata in self.discovered_metadata:
            song_pattern = normalize_string(f"{metadata['title']} {metadata['artist']}")
            song_name = f"{metadata['title']} - {metadata['artist']}"

            # Check if this song is in On-The-Go
            is_approved = False
            for otg_pattern in on_the_go_patterns:
                if similarity_ratio(song_pattern, otg_pattern) >= 0.75:
                    is_approved = True
                    break

            if is_approved:
                approved.append(metadata)
                try:
                    logger.info(f"  ✓ APPROVED: {song_name}")
                except UnicodeEncodeError:
                    logger.info(f"  ✓ APPROVED: (song with special characters)")
            else:
                rejected.append(metadata)
                try:
                    logger.info(f"  ✗ REJECTED: {song_name}")
                except UnicodeEncodeError:
                    logger.info(f"  ✗ REJECTED: (song with special characters)")

        logger.info("="*80)
        logger.info("CLASSIFICATION COMPLETE")
        logger.info("="*80)
        logger.info(f"Approved: {len(approved)}")
        logger.info(f"Rejected: {len(rejected)}")
        logger.info("="*80)

        return approved, rejected

    def integrate_approved_songs(self, approved: List[Dict]) -> int:
        """
        Integrate approved songs into main library.

        Copies approved songs from discovered/ to:
        - library/ (permanent storage)
        - staging/ (for iTunes import)

        Then deletes songs from discovered/ folder.

        Args:
            approved: List of approved song metadata

        Returns:
            Number of successfully integrated songs
        """
        if not approved:
            logger.info("No approved songs to integrate")
            return 0

        logger.info("="*80)
        logger.info("INTEGRATING APPROVED SONGS")
        logger.info("="*80)

        # Ensure folders exist
        LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
        STAGING_DIR.mkdir(parents=True, exist_ok=True)

        successful = 0
        failed = 0

        for metadata in approved:
            song_name = f"{metadata['title']} - {metadata['artist']}"

            try:
                # Find MP3 file in discovered/
                mp3_files = list(DISCOVERED_DIR.glob("*.mp3"))
                source_file = None

                for mp3_file in mp3_files:
                    if similarity_ratio(song_name, mp3_file.stem) >= 0.75:
                        source_file = mp3_file
                        break

                if not source_file:
                    logger.warning(f"MP3 not found for: {song_name}")
                    failed += 1
                    continue

                # Copy to library/
                dest_library = LIBRARY_DIR / source_file.name
                shutil.copy2(source_file, dest_library)

                # Copy to staging/
                dest_staging = STAGING_DIR / source_file.name
                shutil.copy2(source_file, dest_staging)

                # Delete from discovered/
                source_file.unlink()

                logger.info(f"  ✓ Integrated: {source_file.name}")
                successful += 1

            except Exception as e:
                logger.error(f"Failed to integrate {song_name}: {e}")
                failed += 1

        logger.info("="*80)
        logger.info("INTEGRATION COMPLETE")
        logger.info("="*80)
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info("="*80)

        return successful

    def handle_rejected_songs(self, rejected: List[Dict]) -> int:
        """
        Handle rejected songs by deleting from discovered/ folder.

        Args:
            rejected: List of rejected song metadata

        Returns:
            Number of successfully deleted songs
        """
        if not rejected:
            logger.info("No rejected songs to handle")
            return 0

        logger.info("="*80)
        logger.info("HANDLING REJECTED SONGS")
        logger.info("="*80)

        deleted = 0

        for metadata in rejected:
            song_name = f"{metadata['title']} - {metadata['artist']}"

            try:
                # Find and delete MP3 file
                mp3_files = list(DISCOVERED_DIR.glob("*.mp3"))
                source_file = None

                for mp3_file in mp3_files:
                    if similarity_ratio(song_name, mp3_file.stem) >= 0.75:
                        source_file = mp3_file
                        break

                if source_file:
                    source_file.unlink()
                    logger.info(f"  ✓ Deleted: {source_file.name}")
                    deleted += 1
                else:
                    logger.warning(f"MP3 not found: {song_name}")

            except Exception as e:
                logger.error(f"Failed to delete {song_name}: {e}")

        logger.info("="*80)
        logger.info("CLEANUP COMPLETE")
        logger.info("="*80)
        logger.info(f"Deleted: {deleted}")
        logger.info("="*80)

        return deleted

    def update_metadata_files(
        self,
        approved: List[Dict],
        rejected: List[Dict]
    ) -> None:
        """
        Update all metadata tracking files.

        - Appends approved songs to approved_discovered_songs.json
        - Appends rejected songs to rejected_discovered_songs.json
        - Deletes discovered_songs_metadata.json (processed)

        Args:
            approved: List of approved song metadata
            rejected: List of rejected song metadata
        """
        logger.info("Updating metadata files...")

        # Append to approved_discovered_songs.json
        if approved:
            existing_approved = []
            if APPROVED_SONGS_PATH.exists():
                with open(APPROVED_SONGS_PATH, 'r', encoding='utf-8') as f:
                    existing_approved = json.load(f)

            existing_approved.extend(approved)

            with open(APPROVED_SONGS_PATH, 'w', encoding='utf-8') as f:
                json.dump(existing_approved, f, indent=2, ensure_ascii=False)

            logger.info(f"  Appended {len(approved)} songs to approved_discovered_songs.json")

        # Append to rejected_discovered_songs.json
        if rejected:
            existing_rejected = []
            if REJECTED_SONGS_PATH.exists():
                with open(REJECTED_SONGS_PATH, 'r', encoding='utf-8') as f:
                    existing_rejected = json.load(f)

            existing_rejected.extend(rejected)

            with open(REJECTED_SONGS_PATH, 'w', encoding='utf-8') as f:
                json.dump(existing_rejected, f, indent=2, ensure_ascii=False)

            logger.info(f"  Appended {len(rejected)} songs to rejected_discovered_songs.json")

        # Clear discovered_songs_metadata.json
        if DISCOVERED_METADATA_PATH.exists():
            DISCOVERED_METADATA_PATH.unlink()
            logger.info(f"  Cleared discovered_songs_metadata.json")

    def clear_on_the_go_playlist(self) -> None:
        """
        Clear all tracks from the configured playlists.

        Deletes tracks in reverse order to avoid index shifting issues.

        Raises:
            ValueError: If not connected to iTunes
        """
        if not self.itunes:
            raise ValueError("Not connected to iTunes. Call connect_to_itunes() first.")

        logger.info(f"Clearing playlists: {self.playlist_names}...")

        try:
            playlists = self.itunes.LibrarySource.Playlists

            for playlist_name in self.playlist_names:
                # Find matching playlist
                found_playlist = None
                for i in range(1, playlists.Count + 1):
                    playlist = playlists.Item(i)
                    if playlist.Name.lower() == playlist_name.lower():
                        found_playlist = playlist
                        break

                if found_playlist:
                    tracks = found_playlist.Tracks

                    # Delete tracks in reverse order to avoid index issues
                    for i in range(tracks.Count, 0, -1):
                        track = tracks.Item(i)
                        track.Delete()

                    logger.info(f"Cleared '{playlist_name}' playlist")
                else:
                    logger.warning(f"Playlist '{playlist_name}' not found")

        except Exception as e:
            logger.error(f"Error clearing playlists: {e}")

    def run(self) -> Tuple[int, int]:
        """
        Execute complete iTunes integration workflow.

        Steps:
            1. Connect to iTunes
            2. Read On-The-Go playlist
            3. Load discovered songs metadata
            4. Classify songs (approved vs rejected)
            5. Integrate approved songs
            6. Delete rejected songs
            7. Update metadata files
            8. Clear On-The-Go playlist

        Returns:
            Tuple of (approved_count, rejected_count)

        Example:
            >>> integrator = iTunesIntegrator()
            >>> approved, rejected = integrator.run()
            >>> print(f"Approved {approved}, rejected {rejected}")
        """
        logger.info("="*80)
        logger.info("ITUNES INTEGRATION - Starting")
        logger.info("="*80)

        try:
            # Connect to iTunes
            if not self.connect_to_itunes():
                logger.error("Failed to connect to iTunes")
                return 0, 0

            # Get On-The-Go playlist tracks
            self.on_the_go_tracks = self.get_on_the_go_playlist_tracks()

            if not self.on_the_go_tracks:
                logger.info("No tracks found in 'On-The-Go' playlist")
                logger.info("If you haven't added any songs yet, there's nothing to integrate")
                return 0, 0

            # Load discovered songs metadata
            self.discovered_metadata = self.load_discovered_metadata()

            if not self.discovered_metadata:
                logger.warning("No discovered metadata found")
                return 0, 0

            # Classify songs
            approved, rejected = self.classify_songs()

            # Integrate approved songs
            if approved:
                self.integrate_approved_songs(approved)

            # Handle rejected songs
            if rejected:
                self.handle_rejected_songs(rejected)

            # Update metadata files
            self.update_metadata_files(approved, rejected)

            # Clear On-The-Go playlist
            self.clear_on_the_go_playlist()

            logger.info("="*80)
            logger.info("ITUNES INTEGRATION - Complete")
            logger.info(f"Approved: {len(approved)}")
            logger.info(f"Rejected: {len(rejected)}")
            logger.info("="*80)

            logger.info("\nNext steps:")
            logger.info("1. Drag music/staging/ folder into iTunes to organize approved songs")
            logger.info("2. Empty music/staging/ folder when ready")
            logger.info("3. Run music_discovery.py again for more recommendations")

            return len(approved), len(rejected)

        except Exception as e:
            logger.error(f"iTunes integration failed: {e}")
            raise


def main():
    """Command-line entry point for iTunes integrator."""
    integrator = iTunesIntegrator()
    approved, rejected = integrator.run()

    logger.info(f"Complete: {approved} approved, {rejected} rejected")


if __name__ == '__main__':
    main()
