# Walkman API Documentation

Developer reference for the Walkman music discovery system.

---

## Table of Contents

1. [Module Overview](#module-overview)
2. [src.utils](#srcutils)
3. [src.spotify_sync](#srcspotify_sync)
4. [src.music_discovery](#srcmusic_discovery)
5. [src.youtube_downloader](#srcyoutube_downloader)
6. [src.metadata_embedder](#srcmetadata_embedder)
7. [src.itunes_integrator](#srcitunes_integrator)
8. [Data Structures](#data-structures)
9. [Error Handling](#error-handling)
10. [Extension Points](#extension-points)

---

## Module Overview

```python
src/
├── __init__.py              # Package initialization
├── utils.py                 # Common utilities and path management
├── spotify_sync.py          # Spotify API integration
├── music_discovery.py       # Recommendation engine
├── youtube_downloader.py    # YouTube search and download
├── metadata_embedder.py     # ID3 tag embedding
└── itunes_integrator.py     # iTunes COM integration
```

---

## src.utils

Common utilities used across all modules.

### Functions

#### `setup_logging(name, log_file=None, level=logging.INFO)`

Configure logging for a module.

**Parameters**:
- `name` (str): Logger name (usually `__name__`)
- `log_file` (str, optional): Log file path relative to `logs/` directory
- `level` (int): Logging level (default: INFO)

**Returns**: `logging.Logger`

**Example**:
```python
from src.utils import setup_logging

logger = setup_logging(__name__, 'my_module.log')
logger.info("Starting process...")
```

---

#### `normalize_string(s)`

Normalize string for comparison.

**Parameters**:
- `s` (str): Input string

**Returns**: `str` - Lowercase alphanumeric + spaces only

**Example**:
```python
from src.utils import normalize_string

result = normalize_string("The Suburbs - Arcade Fire")
# Returns: 'the suburbs arcade fire'
```

---

#### `similarity_ratio(a, b)`

Calculate similarity between two strings.

**Parameters**:
- `a` (str): First string
- `b` (str): Second string

**Returns**: `float` - Similarity ratio (0.0 to 1.0)

**Example**:
```python
from src.utils import similarity_ratio

score = similarity_ratio("The Suburbs", "Suburbs")
# Returns: ~0.85
```

---

#### `sanitize_filename(filename)`

Remove invalid filename characters.

**Parameters**:
- `filename` (str): Input filename

**Returns**: `str` - Sanitized filename safe for all filesystems

**Example**:
```python
from src.utils import sanitize_filename

safe = sanitize_filename('Artist: "Song Name"')
# Returns: 'Artist Song Name'
```

---

#### `authenticate_spotify(scope=DEFAULT_SPOTIFY_SCOPE)`

Authenticate with Spotify using OAuth.

**Parameters**:
- `scope` (str): Spotify API scope

**Returns**: `spotipy.Spotify` - Authenticated client

**Raises**:
- `ValueError`: If credentials not configured
- `SpotifyException`: If authentication fails

**Example**:
```python
from src.utils import authenticate_spotify

sp = authenticate_spotify(scope='user-library-read')
results = sp.current_user_saved_tracks()
```

---

#### `find_matching_file(metadata, file_list, threshold=0.75)`

Find best matching file for given metadata.

**Parameters**:
- `metadata` (dict): Dict with 'title' and 'artist' keys
- `file_list` (list[Path]): List of file paths to match
- `threshold` (float): Minimum similarity score (0.0-1.0)

**Returns**: `Tuple[Optional[Path], float]` - (matching_file, score)

**Example**:
```python
from src.utils import find_matching_file
from pathlib import Path

metadata = {'title': 'Infrunami', 'artist': 'Steve Lacy'}
files = list(Path('music').glob('*.mp3'))
match, score = find_matching_file(metadata, files)

if match:
    print(f"Matched: {match.name} (score: {score:.2f})")
```

---

### Path Constants

```python
from src.utils import (
    ROOT_DIR,                    # Project root directory
    DATA_DIR,                    # data/ directory
    MUSIC_DIR,                   # music/ directory
    LOGS_DIR,                    # logs/ directory

    SPOTIFY_METADATA_PATH,       # data/spotify/liked_songs_metadata.json
    LIKED_SONGS_TXT_PATH,        # data/spotify/liked_songs.txt
    APPROVED_SONGS_PATH,         # data/spotify/approved_discovered_songs.json
    DISCOVERED_METADATA_PATH,    # data/discovered/discovered_songs_metadata.json
    DISCOVERED_URLS_PATH,        # data/discovered/discovered_songs_youtube_urls.txt
    REJECTED_SONGS_PATH,         # data/tracking/rejected_discovered_songs.json
    COMPLETED_DOWNLOADS_PATH,    # data/tracking/completed_downloads.txt

    LIBRARY_DIR,                 # music/library/
    DISCOVERED_DIR,              # music/discovered/
    STAGING_DIR,                 # music/staging/
)
```

---

## src.spotify_sync

Spotify API integration for fetching liked songs with metadata.

### Class: `SpotifySync`

```python
from src.spotify_sync import SpotifySync

sync = SpotifySync()
sync.run()
```

#### `__init__()`

Initialize Spotify sync client.

---

#### `authenticate()`

Authenticate with Spotify API.

**Raises**:
- `ValueError`: If credentials not configured
- `SpotifyException`: If authentication fails

---

#### `fetch_all_liked_songs()`

Fetch all liked songs with basic metadata.

**Returns**: `List[Dict]` - List of song dictionaries

**Raises**:
- `ValueError`: If not authenticated

**Example**:
```python
sync = SpotifySync()
sync.authenticate()
songs = sync.fetch_all_liked_songs()
print(f"Fetched {len(songs)} songs")
```

---

#### `fetch_audio_features()`

Fetch audio features (BPM) for all songs.

Updates `self.liked_songs` with BPM data.

---

#### `fetch_artist_genres()`

Fetch genres from artists for all songs.

Updates `self.liked_songs` with genre data.

---

#### `save_metadata()`

Save liked songs metadata to JSON and text files.

**Saves to**:
- `data/spotify/liked_songs_metadata.json`
- `data/spotify/liked_songs.txt`

---

#### `run()`

Execute complete Spotify sync workflow.

**Steps**:
1. Authenticate
2. Fetch liked songs
3. Fetch audio features
4. Fetch artist genres
5. Save metadata

---

## src.music_discovery

Music recommendation engine with multi-strategy approach.

### Class: `MusicDiscovery`

```python
from src.music_discovery import MusicDiscovery

discovery = MusicDiscovery()
discovery.run(target_count=100)
```

#### `__init__()`

Initialize music discovery engine.

---

#### `authenticate()`

Authenticate with Spotify API.

---

#### `load_existing_songs()`

Load all existing songs to avoid duplicates.

Loads from:
- `liked_songs_metadata.json`
- `approved_discovered_songs.json`
- `discovered_songs_metadata.json`
- `rejected_discovered_songs.json`

---

#### `analyze_taste_profile()`

Analyze user's music taste.

**Returns**: `Optional[Dict]` - Taste profile or None

**Profile structure**:
```python
{
    'top_genres': [(genre, count), ...],
    'top_artists': [(artist, count), ...],
    'top_artist_ids': [spotify_id, ...],
    'track_ids': [track_id, ...],
    'avg_bpm': float,
    'decades': Counter({2020: 50, 2010: 30, ...}),
    'total_songs': int
}
```

---

#### `generate_recommendations(target_count=100)`

Generate recommendations using multi-strategy engine.

**Parameters**:
- `target_count` (int): Number of songs to recommend

**Returns**: `List[Dict]` - List of Spotify track objects

**Strategy breakdown**:
- 40 songs: Genre-based (top artists)
- 30 songs: Artist exploration (middle-tier)
- 20 songs: Temporal diversity (random)
- 10 songs: Random exploration (lesser-known)

**Example**:
```python
discovery = MusicDiscovery()
discovery.authenticate()
discovery.load_existing_songs()
recommendations = discovery.generate_recommendations(target_count=200)
```

---

#### `convert_spotify_tracks_to_metadata(tracks)`

Convert Spotify track objects to Walkman metadata format.

**Parameters**:
- `tracks` (List[Dict]): Spotify track objects

**Returns**: `List[Dict]` - Metadata dictionaries

---

#### `process_discoveries(metadata_list)`

Download and tag discovered songs.

**Parameters**:
- `metadata_list` (List[Dict]): Song metadata

**Returns**: `Tuple[int, int]` - (successful, failed)

---

#### `run(target_count=100)`

Execute complete discovery workflow.

**Parameters**:
- `target_count` (int): Number of songs to discover

---

## src.youtube_downloader

YouTube search and MP3 download functionality.

### Class: `YouTubeDownloader`

```python
from src.youtube_downloader import YouTubeDownloader

downloader = YouTubeDownloader(download_folder='music/discovered')
downloader.process_metadata(metadata_list)
```

#### `__init__(download_folder=DISCOVERED_DIR)`

Initialize YouTube downloader.

**Parameters**:
- `download_folder` (Path): Target folder for downloads

---

#### `search_youtube(song_name, artist)` (static method)

Search YouTube for a song.

**Parameters**:
- `song_name` (str): Song title
- `artist` (str): Artist name

**Returns**: `Optional[str]` - YouTube URL or None

**Example**:
```python
from src.youtube_downloader import YouTubeDownloader

url = YouTubeDownloader.search_youtube("Infrunami", "Steve Lacy")
if url:
    print(f"Found: {url}")
```

---

#### `search_batch(songs)`

Search YouTube for multiple songs.

**Parameters**:
- `songs` (List[Dict]): List of dicts with 'title' and 'artist' keys

**Returns**: `List[Tuple[Dict, Optional[str]]]` - List of (song, url) tuples

---

#### `download_song(url, song_name, index, total)`

Download single song from YouTube.

**Parameters**:
- `url` (str): YouTube URL
- `song_name` (str): Song name for filename
- `index` (int): Current song number
- `total` (int): Total songs to download

**Returns**: `bool` - True if successful

---

#### `download_batch(songs_with_urls)`

Download multiple songs from YouTube.

**Parameters**:
- `songs_with_urls` (List[Tuple[Dict, str]]): List of (song, url) tuples

**Returns**: `Tuple[int, int]` - (successful, failed)

---

#### `process_metadata(metadata_list)`

Complete pipeline: search + download.

**Parameters**:
- `metadata_list` (List[Dict]): Song metadata

**Returns**: `Tuple[int, int]` - (successful, failed)

---

## src.metadata_embedder

ID3 tag embedding into MP3 files.

### Class: `MetadataEmbedder`

```python
from src.metadata_embedder import MetadataEmbedder

embedder = MetadataEmbedder(
    source_folder='music/library',
    metadata_path='data/spotify/liked_songs_metadata.json'
)
embedder.run()
```

#### `__init__(source_folder=LIBRARY_DIR, metadata_path=SPOTIFY_METADATA_PATH)`

Initialize metadata embedder.

**Parameters**:
- `source_folder` (Path): Folder with MP3 files
- `metadata_path` (Path): Path to metadata JSON

---

#### `scan_mp3_files()`

Scan source folder for MP3 files.

**Returns**: `int` - Number of files found

**Raises**:
- `ValueError`: If source folder doesn't exist

---

#### `load_metadata()`

Load metadata from JSON file.

**Returns**: `List[Dict]` - Song metadata list

**Raises**:
- `ValueError`: If metadata file doesn't exist

---

#### `embed_metadata(mp3_path, metadata)`

Embed ID3 tags into MP3 file.

**Parameters**:
- `mp3_path` (Path): Path to MP3 file
- `metadata` (Dict): Song metadata

**Returns**: `bool` - True if successful

**Tags embedded**:
- TIT2: Title
- TPE1: Artist
- TPE2: Album Artist
- TALB: Album
- TCON: Genre
- TDRC: Year
- TBPM: BPM
- APIC: Album artwork (JPEG)

---

#### `process_batch(metadata_list, similarity_threshold=0.75)`

Process batch of songs and embed metadata.

**Parameters**:
- `metadata_list` (List[Dict]): Song metadata
- `similarity_threshold` (float): Minimum similarity for matching

**Returns**: `Tuple[List[Dict], List[Dict]]` - (successful, failed)

---

#### `generate_reports(successful, failed)`

Generate success and failure reports.

**Parameters**:
- `successful` (List[Dict]): Successfully processed songs
- `failed` (List[Dict]): Failed songs with reasons

**Saves to**:
- `logs/metadata_embedding_success.txt`
- `logs/metadata_embedding_failed.txt`

---

#### `run(similarity_threshold=0.75)`

Execute complete metadata embedding workflow.

**Parameters**:
- `similarity_threshold` (float): Matching threshold

**Returns**: `Tuple[int, int]` - (successful, failed)

---

## src.itunes_integrator

iTunes COM integration for approval workflow.

### Class: `iTunesIntegrator`

```python
from src.itunes_integrator import iTunesIntegrator

integrator = iTunesIntegrator()
approved, rejected = integrator.run()
```

#### `__init__()`

Initialize iTunes integrator.

**Raises**:
- `ImportError`: If pywin32 not installed

---

#### `connect_to_itunes()`

Connect to iTunes via COM interface.

**Returns**: `bool` - True if successful

**Raises**:
- `RuntimeError`: If iTunes not installed

---

#### `get_on_the_go_playlist_tracks()`

Get tracks from "On-The-Go" playlist.

**Returns**: `List[Dict]` - Track info dictionaries

**Raises**:
- `ValueError`: If not connected to iTunes

**Track structure**:
```python
{
    'title': str,
    'artist': str,
    'album': str
}
```

---

#### `load_discovered_metadata()`

Load discovered songs metadata.

**Returns**: `List[Dict]` - Song metadata

**Raises**:
- `ValueError`: If metadata file doesn't exist

---

#### `classify_songs()`

Classify songs as approved or rejected.

**Returns**: `Tuple[List[Dict], List[Dict]]` - (approved, rejected)

---

#### `integrate_approved_songs(approved)`

Integrate approved songs into library.

**Parameters**:
- `approved` (List[Dict]): Approved song metadata

**Returns**: `int` - Number successfully integrated

**Actions**:
- Copies to `music/library/`
- Copies to `music/staging/`
- Deletes from `music/discovered/`

---

#### `handle_rejected_songs(rejected)`

Delete rejected songs from discovered folder.

**Parameters**:
- `rejected` (List[Dict]): Rejected song metadata

**Returns**: `int` - Number deleted

---

#### `update_metadata_files(approved, rejected)`

Update all metadata tracking files.

**Parameters**:
- `approved` (List[Dict]): Approved songs
- `rejected` (List[Dict]): Rejected songs

**Updates**:
- Appends to `approved_discovered_songs.json`
- Appends to `rejected_discovered_songs.json`
- Deletes `discovered_songs_metadata.json`

---

#### `clear_on_the_go_playlist()`

Clear all tracks from "On-The-Go" playlist.

**Raises**:
- `ValueError`: If not connected to iTunes

---

#### `run()`

Execute complete iTunes integration workflow.

**Returns**: `Tuple[int, int]` - (approved_count, rejected_count)

---

## Data Structures

### Song Metadata

Complete metadata structure used throughout the system:

```python
{
    'track_id': str,          # Spotify track ID (required)
    'title': str,             # Song title (required)
    'artist': str,            # Primary artist (required)
    'album_artist': str,      # Album artist
    'album': str,             # Album name
    'year': str,              # Release year (YYYY format)
    'genre': str,             # Semicolon-separated genres
    'bpm': int,               # Tempo in beats per minute
    'uri': str,               # Spotify URI
    'album_art_url': str,     # Album artwork URL
    'added_at': str,          # ISO timestamp when liked
    'youtube_url': str        # YouTube URL (discoveries only)
}
```

### Taste Profile

Generated by `analyze_taste_profile()`:

```python
{
    'top_genres': [
        ('indie rock', 45),
        ('alternative', 30),
        ...
    ],
    'top_artists': [
        ('Arcade Fire', 15),
        ('The National', 12),
        ...
    ],
    'top_artist_ids': [
        '3kjuyTCjPG1WMFCiyc5IuB',  # Spotify IDs
        ...
    ],
    'track_ids': [
        '4bHsxqR3GMrXTxEPLuK5ue',  # All track IDs
        ...
    ],
    'avg_bpm': 120.5,
    'decades': {
        2020: 50,
        2010: 120,
        2000: 80,
        ...
    },
    'total_songs': 1046
}
```

---

## Error Handling

### Common Exceptions

#### `ValueError`
Raised when required data is missing or invalid.

```python
try:
    sync = SpotifySync()
    sync.fetch_all_liked_songs()  # Will raise if not authenticated
except ValueError as e:
    logger.error(f"Not authenticated: {e}")
    sync.authenticate()
```

#### `SpotifyException`
Raised for Spotify API errors.

```python
from spotipy.exceptions import SpotifyException

try:
    sp.current_user_saved_tracks()
except SpotifyException as e:
    logger.error(f"Spotify API error: {e}")
```

#### `ImportError`
Raised when optional dependencies are missing.

```python
try:
    from src.itunes_integrator import iTunesIntegrator
except ImportError:
    logger.error("pywin32 not installed")
```

### Logging Best Practices

```python
import logging
from src.utils import setup_logging

logger = setup_logging(__name__, 'my_module.log', level=logging.INFO)

# Log levels
logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical error")

# Log exceptions
try:
    risky_operation()
except Exception as e:
    logger.exception(f"Operation failed: {e}")  # Includes stack trace
```

---

## Extension Points

### Custom Recommendation Strategy

```python
from src.music_discovery import MusicDiscovery

class CustomDiscovery(MusicDiscovery):
    def get_custom_recommendations(self, profile, count):
        """Custom recommendation logic."""
        # Your algorithm here
        return recommendations

    def generate_recommendations(self, target_count=100):
        """Override to use custom strategy."""
        profile = self.analyze_taste_profile()
        return self.get_custom_recommendations(profile, target_count)
```

### Custom Metadata Source

```python
from src.metadata_embedder import MetadataEmbedder

class LastFMEmbedder(MetadataEmbedder):
    def load_metadata(self):
        """Load from Last.fm instead of Spotify."""
        # Fetch from Last.fm API
        return lastfm_metadata
```

### Custom Download Source

```python
from src.youtube_downloader import YouTubeDownloader

class SoundCloudDownloader(YouTubeDownloader):
    @staticmethod
    def search_soundcloud(song_name, artist):
        """Search SoundCloud instead of YouTube."""
        # SoundCloud API logic
        return soundcloud_url
```

---

## Examples

### Complete Discovery Pipeline

```python
from src.spotify_sync import SpotifySync
from src.music_discovery import MusicDiscovery
from src.itunes_integrator import iTunesIntegrator

# 1. Sync Spotify (first time only)
sync = SpotifySync()
sync.run()

# 2. Generate discoveries
discovery = MusicDiscovery()
discovery.run(target_count=100)

# 3. (Manual: Listen on iPod, add to On-The-Go)

# 4. Integrate approvals
integrator = iTunesIntegrator()
approved, rejected = integrator.run()

print(f"Approved {approved}, rejected {rejected}")
```

### Batch Metadata Embedding

```python
from src.metadata_embedder import MetadataEmbedder
from pathlib import Path

folders = [
    Path('music/library'),
    Path('music/discovered'),
    Path('custom_folder')
]

for folder in folders:
    embedder = MetadataEmbedder(source_folder=folder)
    success, failed = embedder.run()
    print(f"{folder}: {success} success, {failed} failed")
```

### Custom Taste Analysis

```python
from src.music_discovery import MusicDiscovery
import json

discovery = MusicDiscovery()
discovery.authenticate()
discovery.load_existing_songs()

profile = discovery.analyze_taste_profile()

# Save profile for analysis
with open('taste_profile.json', 'w') as f:
    json.dump({
        'top_genres': profile['top_genres'],
        'top_artists': profile['top_artists'],
        'avg_bpm': profile['avg_bpm'],
        'decades': dict(profile['decades'])
    }, f, indent=2)
```

---

For more examples, see [WORKFLOW.md](WORKFLOW.md) and [README.md](../README.md).
