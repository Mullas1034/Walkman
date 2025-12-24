"""
Utility functions for Walkman music discovery system.

Provides common functionality used across all modules including:
- Logging configuration
- String normalization and fuzzy matching
- Filename sanitization
- Spotify authentication
- Path management

Author: Kieran
"""

import os
import logging
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher
from typing import Optional, Tuple
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Load environment variables
load_dotenv()

# Constants
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'https://mullas1034.github.io/Walkman/callback')
DEFAULT_SPOTIFY_SCOPE = 'user-library-read playlist-modify-public playlist-modify-private'

# Paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / 'data'
MUSIC_DIR = ROOT_DIR / 'music'
LOGS_DIR = ROOT_DIR / 'logs'

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
MUSIC_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
(DATA_DIR / 'spotify').mkdir(exist_ok=True)
(DATA_DIR / 'discovered').mkdir(exist_ok=True)
(DATA_DIR / 'tracking').mkdir(exist_ok=True)
(MUSIC_DIR / 'library').mkdir(exist_ok=True)
(MUSIC_DIR / 'discovered').mkdir(exist_ok=True)
(MUSIC_DIR / 'staging').mkdir(exist_ok=True)


def setup_logging(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Configure logging for a module.

    Args:
        name: Logger name (usually __name__)
        log_file: Optional log file path relative to logs/ directory
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logging(__name__, 'spotify_sync.log')
        >>> logger.info('Starting sync...')
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_path = LOGS_DIR / log_file
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def normalize_string(s: str) -> str:
    """
    Normalize string for comparison by removing special characters and lowercasing.

    Args:
        s: Input string

    Returns:
        Normalized string (alphanumeric + spaces only, lowercase)

    Example:
        >>> normalize_string("The Suburbs - Arcade Fire")
        'the suburbs arcade fire'
    """
    return ''.join(c.lower() for c in s if c.isalnum() or c.isspace()).strip()


def similarity_ratio(a: str, b: str) -> float:
    """
    Calculate similarity between two strings using SequenceMatcher.

    Args:
        a: First string
        b: Second string

    Returns:
        Similarity ratio between 0.0 and 1.0

    Example:
        >>> similarity_ratio("The Suburbs", "Suburbs")
        0.85
    """
    return SequenceMatcher(None, normalize_string(a), normalize_string(b)).ratio()


def sanitize_filename(filename: str) -> str:
    """
    Remove invalid filename characters and handle Unicode.

    Args:
        filename: Input filename

    Returns:
        Sanitized filename safe for all filesystems

    Example:
        >>> sanitize_filename('Artist: "Song Name"')
        'Artist Song Name'
    """
    # Normalize Unicode characters to ASCII
    filename = unicodedata.normalize('NFKD', filename)
    filename = filename.encode('ascii', 'ignore').decode('ascii')

    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '')

    return filename.strip()


def authenticate_spotify(scope: str = DEFAULT_SPOTIFY_SCOPE) -> spotipy.Spotify:
    """
    Authenticate with Spotify using OAuth.

    Uses cached token if available, otherwise prompts for authorization.

    Args:
        scope: Spotify API scope (default: read library + modify playlists)

    Returns:
        Authenticated Spotipy client

    Raises:
        ValueError: If credentials are not configured
        SpotifyException: If authentication fails

    Example:
        >>> sp = authenticate_spotify()
        >>> results = sp.current_user_saved_tracks()
    """
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        raise ValueError(
            "Spotify credentials not configured. "
            "Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env file"
        )

    auth_manager = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=scope,
        open_browser=True
    )

    # Check for cached token
    token_info = auth_manager.get_cached_token()

    if not token_info:
        # Prompt for authorization
        auth_url = auth_manager.get_authorize_url()
        print(f"\nPlease visit this URL to authorize:\n{auth_url}\n")
        print("After authorizing, copy the authorization code below:\n")

        auth_code = input("Enter authorization code: ").strip()
        token_info = auth_manager.get_access_token(auth_code, as_dict=True)

    # Create authenticated client
    return spotipy.Spotify(auth_manager=auth_manager)


def find_matching_file(
    metadata: dict,
    file_list: list[Path],
    threshold: float = 0.75
) -> Tuple[Optional[Path], float]:
    """
    Find best matching file for given metadata using fuzzy string matching.

    Args:
        metadata: Dict with 'title' and 'artist' keys
        file_list: List of file paths to match against
        threshold: Minimum similarity score (0.0-1.0)

    Returns:
        Tuple of (matching_file_path, similarity_score) or (None, best_score)

    Example:
        >>> metadata = {'title': 'Infrunami', 'artist': 'Steve Lacy'}
        >>> files = [Path('Infrunami - Steve Lacy.mp3')]
        >>> match, score = find_matching_file(metadata, files)
        >>> match.name
        'Infrunami - Steve Lacy.mp3'
    """
    best_match = None
    best_score = 0.0

    expected_pattern = f"{metadata['title']} - {metadata['artist']}"

    for file_path in file_list:
        filename = file_path.stem  # Without extension
        score = similarity_ratio(expected_pattern, filename)

        if score > best_score:
            best_score = score
            best_match = file_path

    if best_score >= threshold:
        return best_match, best_score

    return None, best_score


# Path constants for easy access
SPOTIFY_METADATA_PATH = DATA_DIR / 'spotify' / 'liked_songs_metadata.json'
LIKED_SONGS_TXT_PATH = DATA_DIR / 'spotify' / 'liked_songs.txt'
APPROVED_SONGS_PATH = DATA_DIR / 'spotify' / 'approved_discovered_songs.json'
DISCOVERED_METADATA_PATH = DATA_DIR / 'discovered' / 'discovered_songs_metadata.json'
DISCOVERED_URLS_PATH = DATA_DIR / 'discovered' / 'discovered_songs_youtube_urls.txt'
REJECTED_SONGS_PATH = DATA_DIR / 'tracking' / 'rejected_discovered_songs.json'
COMPLETED_DOWNLOADS_PATH = DATA_DIR / 'tracking' / 'completed_downloads.txt'

LIBRARY_DIR = MUSIC_DIR / 'library'
DISCOVERED_DIR = MUSIC_DIR / 'discovered'
STAGING_DIR = MUSIC_DIR / 'staging'
