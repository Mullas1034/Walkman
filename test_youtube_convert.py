"""
Test script for YouTube to MP3 Downloader
Downloads 3 random songs to verify the script works
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class YouTubeMP3DownloaderTest:
    def __init__(self, urls_file='test_youtube_urls.txt', download_folder='test_downloads'):
        """
        Initialize the test downloader

        Args:
            urls_file (str): Path to text file with format "Song - Artist | URL"
            download_folder (str): Folder name to save downloaded MP3s
        """
        self.urls_file = urls_file
        self.download_folder = os.path.abspath(download_folder)
        self.driver = None

        # Create download folder if it doesn't exist
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)
            print(f"Created folder: {self.download_folder}")

    def setup_driver(self):
        """Set up Chrome driver with download preferences"""
        chrome_options = Options()

        # Configure download settings
        prefs = {
            "download.default_directory": self.download_folder,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # Disable automation flags (helps avoid detection)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Initialize the driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.maximize_window()

        print("Chrome driver initialized")

    def load_urls(self):
        """Load URLs from text file (format: 'Song - Artist | URL')"""
        if not os.path.exists(self.urls_file):
            raise FileNotFoundError(f"URLs file not found: {self.urls_file}")

        urls = []
        with open(self.urls_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or '|' not in line:
                    continue

                # Extract URL from format "Song - Artist | URL"
                _, url = line.split('|', 1)
                url = url.strip()

                # Skip invalid entries
                if url and url not in ['NOT FOUND', 'INVALID FORMAT']:
                    urls.append(url)

        print(f"Loaded {len(urls)} valid URLs from {self.urls_file}")
        return urls

    def wait_for_download_complete(self, timeout=120):
        """
        Wait for download to complete by checking for .crdownload files

        Args:
            timeout (int): Maximum time to wait in seconds
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check for Chrome's temporary download files
            downloading = False
            for filename in os.listdir(self.download_folder):
                if filename.endswith('.crdownload') or filename.endswith('.tmp'):
                    downloading = True
                    break

            if not downloading:
                time.sleep(2)  # Extra buffer to ensure file is fully written
                return True

            time.sleep(1)

        print("Download timeout - file may not have completed")
        return False

    def download_url(self, url, index, total):
        """
        Download a single YouTube URL as MP3

        Args:
            url (str): YouTube URL to download
            index (int): Current URL index (for progress tracking)
            total (int): Total number of URLs
        """
        try:
            print(f"\n[{index}/{total}] Processing: {url}")

            # Navigate to the converter site
            self.driver.get("https://ezconv.cc/")

            # Wait for page to load
            time.sleep(2)

            # Find the input box by name attribute (more reliable than dynamic ID)
            wait = WebDriverWait(self.driver, 10)
            input_box = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="url"]'))
            )

            # Clear and enter the URL
            input_box.clear()
            input_box.send_keys(url)
            print("  URL entered")

            # Find and click the convert button
            convert_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))
            )
            convert_button.click()
            print("  Conversion started...")

            # Wait for the download button to appear (conversion complete)
            # Try multiple selectors to find the button
            download_button = None
            try:
                # Try exact text match first
                download_button = wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[text()='Download MP3']")
                    )
                )
            except:
                try:
                    # Try with contains and MUI classes
                    download_button = wait.until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//button[contains(@class, 'MuiButton-contained') and contains(., 'Download MP3')]")
                        )
                    )
                except:
                    # Last resort - any button with "Download" text
                    download_button = wait.until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//button[contains(., 'Download')]")
                        )
                    )

            if not download_button:
                raise Exception("Download button not found")

            print("  Conversion complete")

            # Get count of files before download
            files_before = set(os.listdir(self.download_folder))

            # Click download button
            download_button.click()
            print("  Download started...")

            # Wait for download to complete
            if self.wait_for_download_complete():
                # Get the new file
                files_after = set(os.listdir(self.download_folder))
                new_files = files_after - files_before

                if new_files:
                    new_file = list(new_files)[0]
                    print(f"  Downloaded: {new_file}")
                else:
                    print("  Download completed but new file not detected")

            # Add delay between downloads to avoid rate limiting
            delay = 5
            print(f"  Waiting {delay} seconds before next download...")
            time.sleep(delay)

            return True

        except Exception as e:
            print(f"  Error downloading {url}: {str(e)}")
            return False

    def download_all(self):
        """Main function to download all URLs"""
        try:
            # Set up the driver
            self.setup_driver()

            # Load URLs
            urls = self.load_urls()

            if not urls:
                print("No URLs found in file")
                return

            print(f"\nStarting download of {len(urls)} test videos...")
            print(f"Downloads will be saved to: {self.download_folder}\n")

            # Track statistics
            successful = 0
            failed = 0

            # Process each URL
            for i, url in enumerate(urls, 1):
                if self.download_url(url, i, len(urls)):
                    successful += 1
                else:
                    failed += 1

            # Print summary
            print("\n" + "="*60)
            print("TEST DOWNLOAD SUMMARY")
            print("="*60)
            print(f"Successful: {successful}")
            print(f"Failed: {failed}")
            print(f"Files saved to: {self.download_folder}")
            print("="*60)

        except Exception as e:
            print(f"\nFatal error: {str(e)}")

        finally:
            # Clean up
            if self.driver:
                print("\nClosing browser...")
                self.driver.quit()
                print("Done!")


def main():
    """Main entry point"""
    print("="*60)
    print("YouTube to MP3 Test Downloader (3 songs)")
    print("="*60)

    # Create downloader instance
    downloader = YouTubeMP3DownloaderTest(
        urls_file='test_youtube_urls.txt',
        download_folder='test_downloads'
    )

    # Start downloading
    downloader.download_all()


if __name__ == "__main__":
    main()
