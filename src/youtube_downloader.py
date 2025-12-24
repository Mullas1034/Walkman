"""
YouTube downloader module for Walkman.

Handles searching for songs on YouTube and downloading them as MP3 files.
Combines search and download functionality into a single cohesive pipeline.

Uses yt-dlp for reliable YouTube searching and downloading with FFmpeg
integration for audio extraction at 320kbps.

Author: Kieran
"""

import sys
import io
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import yt_dlp

from .utils import (
    setup_logging,
    sanitize_filename,
    DISCOVERED_URLS_PATH,
    DISCOVERED_DIR,
    LIBRARY_DIR,
    COMPLETED_DOWNLOADS_PATH,
)

# Fix console encoding for Unicode on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configure logging
logger = setup_logging(__name__, 'youtube_downloader.log')


class YouTubeDownloader:
    """
    Handles YouTube search and MP3 download operations.

    Attributes:
        download_folder: Target folder for downloaded MP3s
        completed_urls: Set of already-downloaded URLs
    """

    def __init__(self, download_folder: Path = DISCOVERED_DIR):
        """
        Initialize YouTube downloader.

        Args:
            download_folder: Path to folder for downloaded MP3s
        """
        self.download_folder = Path(download_folder)
        self.download_folder.mkdir(parents=True, exist_ok=True)
        self.completed_urls = self._load_completed_urls()

        logger.info(f"YouTube downloader initialized (folder: {self.download_folder})")

    def _load_completed_urls(self) -> set:
        """
        Load set of already-downloaded URLs from tracking file.

        Returns:
            Set of completed URL strings
        """
        if not COMPLETED_DOWNLOADS_PATH.exists():
            return set()

        with open(COMPLETED_DOWNLOADS_PATH, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())

    def _mark_completed(self, url: str) -> None:
        """
        Mark a URL as successfully downloaded.

        Args:
            url: YouTube URL that was downloaded
        """
        with open(COMPLETED_DOWNLOADS_PATH, 'a', encoding='utf-8') as f:
            f.write(f"{url}\n")
        self.completed_urls.add(url)

    @staticmethod
    def search_youtube(song_name: str, artist: str) -> Optional[str]:
        """
        Search YouTube for a song and return the first result's URL.

        Args:
            song_name: Song title
            artist: Artist name

        Returns:
            YouTube URL of first result, or None if not found

        Example:
            >>> url = YouTubeDownloader.search_youtube("Infrunami", "Steve Lacy")
            >>> print(url)
            'https://www.youtube.com/watch?v=...'
        """
        query = f"ytsearch1:{song_name} {artist}"

        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                results = ydl.extract_info(query, download=False)

                if results and 'entries' in results and len(results['entries']) > 0:
                    video_id = results['entries'][0]['id']
                    return f"https://www.youtube.com/watch?v={video_id}"

            return None

        except Exception as e:
            logger.error(f"Error searching for '{song_name} {artist}': {e}")
            return None

    def search_batch(self, songs: List[Dict]) -> List[Tuple[Dict, Optional[str]]]:
        """
        Search YouTube for multiple songs and return URLs.

        Args:
            songs: List of dicts with 'title' and 'artist' keys

        Returns:
            List of (song_dict, url_or_none) tuples

        Example:
            >>> songs = [{'title': 'Infrunami', 'artist': 'Steve Lacy'}]
            >>> results = downloader.search_batch(songs)
        """
        logger.info(f"Searching YouTube for {len(songs)} songs...")
        results = []

        for i, song in enumerate(songs, 1):
            try:
                logger.info(f"[{i}/{len(songs)}] Searching: {song['title']} - {song['artist']}")
            except UnicodeEncodeError:
                logger.info(f"[{i}/{len(songs)}] Searching: (special characters)")

            url = self.search_youtube(song['title'], song['artist'])

            if url:
                logger.info(f"  Found: {url}")
            else:
                logger.warning(f"  Not found")

            results.append((song, url))

        found_count = sum(1 for _, url in results if url)
        logger.info(f"Search complete: {found_count}/{len(songs)} songs found")

        return results

    def download_song(
        self,
        url: str,
        song_name: str,
        index: int,
        total: int
    ) -> bool:
        """
        Download a single song from YouTube as MP3.

        Args:
            url: YouTube URL
            song_name: Song name for filename (will be sanitized)
            index: Current song number (for progress)
            total: Total songs to download

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"[{index}/{total}] Downloading: {song_name}")
            logger.info(f"  URL: {url}")

            # Sanitize filename
            safe_filename = sanitize_filename(song_name)
            output_path = self.download_folder / f"{safe_filename}.mp3"

            # yt-dlp options
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'outtmpl': str(self.download_folder / f"{safe_filename}.%(ext)s"),
                'quiet': True,
                'no_warnings': True,
            }

            # Check for cookies file
            cookies_file = Path('cookies.txt')
            if cookies_file.exists():
                ydl_opts['cookiefile'] = str(cookies_file)

            # Download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            logger.info(f"  [SUCCESS] Downloaded: {safe_filename}.mp3")
            self._mark_completed(url)
            return True

        except Exception as e:
            logger.error(f"  [ERROR] {str(e)}")
            return False

    def download_batch(
        self,
        songs_with_urls: List[Tuple[Dict, str]]
    ) -> Tuple[int, int]:
        """
        Download multiple songs from YouTube.

        Args:
            songs_with_urls: List of (song_dict, url) tuples

        Returns:
            Tuple of (successful_count, failed_count)

        Example:
            >>> results = [(song1, url1), (song2, url2)]
            >>> success, failed = downloader.download_batch(results)
        """
        # Filter out already completed and invalid URLs
        to_download = [
            (song, url) for song, url in songs_with_urls
            if url and url not in self.completed_urls
        ]

        if not to_download:
            logger.info("All songs already downloaded or no valid URLs!")
            return 0, 0

        skipped = len(songs_with_urls) - len(to_download)
        if skipped > 0:
            logger.info(f"Skipping {skipped} already downloaded songs")

        logger.info(f"Starting download of {len(to_download)} songs...")

        successful = 0
        failed = 0

        for i, (song, url) in enumerate(to_download, 1):
            song_name = f"{song['title']} - {song['artist']}"

            if self.download_song(url, song_name, i, len(to_download)):
                successful += 1
            else:
                failed += 1

        logger.info("="*80)
        logger.info(f"DOWNLOAD SUMMARY: {successful} successful, {failed} failed")
        logger.info("="*80)

        return successful, failed

    def process_metadata(self, metadata_list: List[Dict]) -> Tuple[int, int]:
        """
        Complete pipeline: search YouTube + download MP3s.

        Args:
            metadata_list: List of song metadata dicts

        Returns:
            Tuple of (successful_count, failed_count)

        Example:
            >>> downloader = YouTubeDownloader()
            >>> songs = [{'title': 'Infrunami', 'artist': 'Steve Lacy'}]
            >>> success, failed = downloader.process_metadata(songs)
        """
        # Search for all songs
        search_results = self.search_batch(metadata_list)

        # Save URLs to file
        self._save_urls_file(search_results)

        # Download all songs
        songs_with_urls = [(song, url) for song, url in search_results if url]
        return self.download_batch(songs_with_urls)

    def _save_urls_file(self, search_results: List[Tuple[Dict, Optional[str]]]) -> None:
        """
        Save search results to URL file.

        Args:
            search_results: List of (song_dict, url_or_none) tuples
        """
        logger.info(f"Saving URLs to {DISCOVERED_URLS_PATH}")

        with open(DISCOVERED_URLS_PATH, 'w', encoding='utf-8') as f:
            for song, url in search_results:
                song_name = f"{song['title']} - {song['artist']}"
                url_str = url if url else 'NOT FOUND'
                f.write(f"{song_name} | {url_str}\n")


def main():
    """Command-line entry point for YouTube downloader."""
    import json

    # Example: Load metadata and download
    metadata_file = DISCOVERED_URLS_PATH.parent / 'discovered_songs_metadata.json'

    if not metadata_file.exists():
        logger.error(f"Metadata file not found: {metadata_file}")
        return

    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    downloader = YouTubeDownloader()
    success, failed = downloader.process_metadata(metadata)

    logger.info(f"Complete: {success} successful, {failed} failed")


if __name__ == '__main__':
    main()
