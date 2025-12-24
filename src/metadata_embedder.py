"""
Metadata embedding module for Walkman.

Embeds ID3 tags into MP3 files using Spotify metadata including:
- Title, Artist, Album Artist, Album
- Genre, Year, BPM
- Album artwork

Uses fuzzy string matching to link metadata to MP3 files and handles
missing data gracefully. Generates success/failure reports for tracking.

Author: Kieran
"""

import json
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from mutagen.id3 import ID3, TIT2, TPE1, TPE2, TALB, TCON, TDRC, TBPM, APIC
from mutagen.mp3 import MP3

from .utils import (
    setup_logging,
    find_matching_file,
    SPOTIFY_METADATA_PATH,
    LIBRARY_DIR,
    DISCOVERED_DIR,
    LOGS_DIR,
)

# Configure logging
logger = setup_logging(__name__, 'metadata_embedder.log')


class MetadataEmbedder:
    """
    Embeds Spotify metadata as ID3 tags into MP3 files.

    Attributes:
        source_folder: Folder containing MP3 files to tag
        metadata_path: Path to JSON file with song metadata
        mp3_files: List of MP3 file paths found in source folder
    """

    def __init__(
        self,
        source_folder: Path = LIBRARY_DIR,
        metadata_path: Path = SPOTIFY_METADATA_PATH
    ):
        """
        Initialize metadata embedder.

        Args:
            source_folder: Folder containing MP3 files to process
            metadata_path: Path to metadata JSON file
        """
        self.source_folder = Path(source_folder)
        self.metadata_path = Path(metadata_path)
        self.mp3_files: List[Path] = []

        logger.info(f"Metadata embedder initialized")
        logger.info(f"  Source folder: {self.source_folder}")
        logger.info(f"  Metadata file: {self.metadata_path}")

    def scan_mp3_files(self) -> int:
        """
        Scan source folder for MP3 files.

        Returns:
            Number of MP3 files found

        Raises:
            ValueError: If source folder doesn't exist
        """
        if not self.source_folder.exists():
            raise ValueError(f"Source folder not found: {self.source_folder}")

        logger.info(f"Scanning for MP3 files in {self.source_folder}...")
        self.mp3_files = list(self.source_folder.glob("*.mp3"))
        logger.info(f"Found {len(self.mp3_files)} MP3 files")

        return len(self.mp3_files)

    def load_metadata(self) -> List[Dict]:
        """
        Load metadata from JSON file.

        Returns:
            List of song metadata dictionaries

        Raises:
            ValueError: If metadata file doesn't exist
            json.JSONDecodeError: If metadata file is invalid JSON
        """
        if not self.metadata_path.exists():
            raise ValueError(f"Metadata file not found: {self.metadata_path}")

        logger.info(f"Loading metadata from {self.metadata_path}...")
        with open(self.metadata_path, 'r', encoding='utf-8') as f:
            metadata_list = json.load(f)

        logger.info(f"Loaded {len(metadata_list)} songs from metadata file")
        return metadata_list

    @staticmethod
    def _download_album_art(url: str) -> Optional[bytes]:
        """
        Download album art from URL.

        Args:
            url: Album art image URL

        Returns:
            Image bytes, or None if download failed
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.warning(f"Could not download album art: {e}")
            return None

    def embed_metadata(self, mp3_path: Path, metadata: Dict) -> bool:
        """
        Embed ID3 tags into MP3 file.

        Writes the following ID3v2.3 tags:
        - TIT2: Title
        - TPE1: Artist
        - TPE2: Album Artist
        - TALB: Album
        - TCON: Genre
        - TDRC: Year
        - TBPM: BPM
        - APIC: Album artwork (JPEG)

        Args:
            mp3_path: Path to MP3 file
            metadata: Song metadata dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load or create ID3 tags
            try:
                audio = MP3(mp3_path, ID3=ID3)
                if audio.tags is None:
                    audio.add_tags()
            except:
                audio = MP3(mp3_path)
                audio.add_tags()

            # Clear existing tags for clean slate
            audio.tags.clear()

            # Add text tags (encoding=3 is UTF-8)
            audio.tags.add(TIT2(encoding=3, text=metadata['title']))
            audio.tags.add(TPE1(encoding=3, text=metadata['artist']))

            if metadata.get('album_artist'):
                audio.tags.add(TPE2(encoding=3, text=metadata['album_artist']))

            if metadata.get('album'):
                audio.tags.add(TALB(encoding=3, text=metadata['album']))

            if metadata.get('genre'):
                audio.tags.add(TCON(encoding=3, text=metadata['genre']))

            if metadata.get('year'):
                audio.tags.add(TDRC(encoding=3, text=metadata['year']))

            if metadata.get('bpm'):
                audio.tags.add(TBPM(encoding=3, text=str(metadata['bpm'])))

            # Add album artwork
            if metadata.get('album_art_url'):
                album_art_data = self._download_album_art(metadata['album_art_url'])
                if album_art_data:
                    audio.tags.add(
                        APIC(
                            encoding=3,
                            mime='image/jpeg',
                            type=3,  # 3 = Cover (front)
                            desc='Cover',
                            data=album_art_data
                        )
                    )

            # Save tags to file
            audio.save()
            return True

        except Exception as e:
            logger.error(f"Failed to embed metadata: {e}")
            return False

    def process_batch(
        self,
        metadata_list: List[Dict],
        similarity_threshold: float = 0.75
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Process batch of songs and embed metadata.

        Args:
            metadata_list: List of song metadata dictionaries
            similarity_threshold: Minimum similarity for file matching (0.0-1.0)

        Returns:
            Tuple of (successful_items, failed_items) lists
        """
        if not self.mp3_files:
            logger.warning("No MP3 files to process. Call scan_mp3_files() first.")
            return [], []

        logger.info("="*80)
        logger.info(f"Processing {len(metadata_list)} songs...")
        logger.info("="*80)

        successful = []
        failed = []

        for idx, metadata in enumerate(metadata_list, 1):
            song_name = f"{metadata['title']} - {metadata['artist']}"

            try:
                logger.info(f"[{idx}/{len(metadata_list)}] {song_name}")
            except UnicodeEncodeError:
                logger.info(f"[{idx}/{len(metadata_list)}] (Song with special characters)")

            # Find matching MP3 file
            matched_file, score = find_matching_file(
                metadata,
                self.mp3_files,
                threshold=similarity_threshold
            )

            if matched_file is None:
                logger.warning(f"  [SKIP] No matching MP3 file (best score: {score:.2f})")
                failed.append({
                    'song': song_name,
                    'reason': f'No matching MP3 file (best score: {score:.2f})'
                })
                continue

            logger.info(f"  [MATCH] {matched_file.name} (similarity: {score:.2f})")

            # Embed metadata
            logger.info(f"  [EMBED] Writing metadata...")
            if self.embed_metadata(matched_file, metadata):
                logger.info(f"  [SUCCESS] Metadata embedded")
                successful.append({
                    'song': song_name,
                    'file': matched_file.name
                })
            else:
                logger.warning(f"  [FAIL] Failed to embed metadata")
                failed.append({
                    'song': song_name,
                    'reason': 'Failed to write ID3 tags',
                    'file': matched_file.name
                })

        logger.info("="*80)
        logger.info("SUMMARY")
        logger.info("="*80)
        logger.info(f"Total songs: {len(metadata_list)}")
        logger.info(f"Successfully processed: {len(successful)}")
        logger.info(f"Failed: {len(failed)}")
        logger.info(f"Success rate: {len(successful)/len(metadata_list)*100:.1f}%")
        logger.info("="*80)

        return successful, failed

    def generate_reports(
        self,
        successful: List[Dict],
        failed: List[Dict]
    ) -> None:
        """
        Generate success and failure reports.

        Args:
            successful: List of successfully processed songs
            failed: List of failed songs with reasons
        """
        # Success log
        success_log_path = LOGS_DIR / 'metadata_embedding_success.txt'
        logger.info(f"Writing success log to {success_log_path}")

        with open(success_log_path, 'w', encoding='utf-8') as f:
            f.write("SUCCESSFULLY EMBEDDED METADATA\n")
            f.write("="*80 + "\n\n")
            for item in successful:
                f.write(f"{item['song']}\n")
                f.write(f"  File: {item['file']}\n\n")

        # Failure log
        if failed:
            failure_log_path = LOGS_DIR / 'metadata_embedding_failed.txt'
            logger.info(f"Writing failure log to {failure_log_path}")

            with open(failure_log_path, 'w', encoding='utf-8') as f:
                f.write("FAILED TO EMBED METADATA\n")
                f.write("="*80 + "\n\n")
                for item in failed:
                    f.write(f"{item['song']}\n")
                    f.write(f"  Reason: {item['reason']}\n")
                    if 'file' in item:
                        f.write(f"  File: {item['file']}\n")
                    f.write("\n")

        logger.info("Reports generated successfully")

    def run(self, similarity_threshold: float = 0.75) -> Tuple[int, int]:
        """
        Execute complete metadata embedding workflow.

        Steps:
            1. Scan source folder for MP3 files
            2. Load metadata from JSON
            3. Match metadata to MP3 files
            4. Embed ID3 tags
            5. Generate reports

        Args:
            similarity_threshold: Minimum similarity for file matching (0.0-1.0)

        Returns:
            Tuple of (successful_count, failed_count)

        Example:
            >>> embedder = MetadataEmbedder()
            >>> success, failed = embedder.run()
            >>> print(f"Embedded metadata for {success} songs")
        """
        logger.info("="*80)
        logger.info("METADATA EMBEDDING - Starting")
        logger.info("="*80)

        try:
            # Scan for MP3 files
            if self.scan_mp3_files() == 0:
                logger.error("No MP3 files found in source folder!")
                return 0, 0

            # Load metadata
            metadata_list = self.load_metadata()

            # Process batch
            successful, failed = self.process_batch(
                metadata_list,
                similarity_threshold=similarity_threshold
            )

            # Generate reports
            self.generate_reports(successful, failed)

            logger.info("="*80)
            logger.info("METADATA EMBEDDING - Complete")
            logger.info("="*80)

            return len(successful), len(failed)

        except Exception as e:
            logger.error(f"Metadata embedding failed: {e}")
            raise


def main():
    """Command-line entry point for metadata embedder."""
    # Default: Process library files with Spotify metadata
    embedder = MetadataEmbedder(
        source_folder=LIBRARY_DIR,
        metadata_path=SPOTIFY_METADATA_PATH
    )

    success, failed = embedder.run()

    logger.info(f"Complete: {success} successful, {failed} failed")


if __name__ == '__main__':
    main()
