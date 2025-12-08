import os
import yt_dlp
from pathlib import Path


class YouTubeMP3Downloader:
    def __init__(self, urls_file='youtube_urls.txt', download_folder='downloaded_songs'):
        """
        Initialize the downloader using yt-dlp

        Args:
            urls_file (str): Path to file with format "Song - Artist | URL"
            download_folder (str): Folder to save MP3 files
        """
        self.urls_file = urls_file
        self.download_folder = Path(download_folder)
        self.download_folder.mkdir(exist_ok=True)
        self.completed_log = Path('completed_downloads.txt')

    def load_songs(self):
        """Load songs from youtube_urls.txt"""
        if not os.path.exists(self.urls_file):
            raise FileNotFoundError(f"File not found: {self.urls_file}")

        songs = []
        with open(self.urls_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or '|' not in line:
                    continue

                # Parse format: "Song - Artist | URL"
                song_info, url = line.split('|', 1)
                song_info = song_info.strip()
                url = url.strip()

                if url == 'NOT FOUND' or url == 'INVALID FORMAT':
                    continue

                songs.append({
                    'info': song_info,
                    'url': url
                })

        print(f"Loaded {len(songs)} songs from {self.urls_file}")
        return songs

    def get_completed_urls(self):
        """Get set of already downloaded URLs"""
        if not self.completed_log.exists():
            return set()

        with open(self.completed_log, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f)

    def mark_completed(self, url):
        """Mark a URL as successfully downloaded"""
        with open(self.completed_log, 'a', encoding='utf-8') as f:
            f.write(f"{url}\n")

    def sanitize_filename(self, filename):
        """Remove invalid filename characters"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        return filename

    def download_song(self, song, index, total):
        """
        Download a single song as MP3

        Args:
            song (dict): Dict with 'info' and 'url' keys
            index (int): Current song number
            total (int): Total songs to download
        """
        song_info = song['info']
        url = song['url']

        try:
            print(f"\n[{index}/{total}] Downloading: {song_info}")
            print(f"  URL: {url}")

            # Sanitize filename
            safe_filename = self.sanitize_filename(song_info)
            output_path = self.download_folder / f"{safe_filename}.mp3"

            # yt-dlp options
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': str(self.download_folder / f"{safe_filename}.%(ext)s"),
                'quiet': True,
                'no_warnings': True,
                'ffmpeg_location': os.path.abspath('.'),
            }

            # Download and convert
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            print(f"  [OK] Downloaded: {safe_filename}.mp3")
            self.mark_completed(url)
            return True

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            return False

    def download_all(self):
        """Download all songs from the list"""
        try:
            # Load songs
            songs = self.load_songs()

            if not songs:
                print("No valid songs found to download")
                return

            # Get completed downloads
            completed = self.get_completed_urls()

            # Filter out already downloaded
            remaining = [s for s in songs if s['url'] not in completed]

            if completed:
                print(f"Skipping {len(completed)} already downloaded songs")

            if not remaining:
                print("All songs already downloaded!")
                return

            print(f"\nStarting download of {len(remaining)} songs...")
            print(f"Saving to: {self.download_folder.absolute()}\n")

            # Track stats
            successful = 0
            failed = 0

            # Download each song
            for i, song in enumerate(remaining, 1):
                if self.download_song(song, i, len(remaining)):
                    successful += 1
                else:
                    failed += 1

            # Summary
            print("\n" + "="*60)
            print("DOWNLOAD SUMMARY")
            print("="*60)
            print(f"Successful: {successful}")
            print(f"Failed: {failed}")
            print(f"Files saved to: {self.download_folder.absolute()}")
            print("="*60)

        except Exception as e:
            print(f"\nError: {str(e)}")


def main():
    print("="*60)
    print("YouTube to MP3 Downloader (using yt-dlp)")
    print("="*60)
    print("\nNOTE: Ensure you have the rights to download this content.")
    print("This tool is for personal archival purposes only.\n")

    downloader = YouTubeMP3Downloader(
        urls_file='youtube_urls.txt',
        download_folder='downloaded_songs'
    )

    downloader.download_all()


if __name__ == '__main__':
    main()
