# Walkman 🎵

**Intelligent Music Discovery System** for Spotify, YouTube, and iTunes/iPod

Walkman is a sophisticated music discovery pipeline that analyzes your Spotify listening history to find new songs you'll love, automatically downloads them from YouTube with full metadata, and integrates seamlessly with iTunes and iPod.

---

## Features

### 🎯 Core Capabilities

- **Spotify Sync**: Fetch all liked songs with complete metadata (BPM, genres, album art, etc.)
- **Music Discovery**: AI-powered recommendations using 4-strategy engine
- **YouTube Download**: Automatic search and download of high-quality MP3s (320kbps)
- **Metadata Embedding**: Professional ID3v2.3 tag embedding with album artwork
- **iTunes Integration**: Seamless approval workflow using iPod's "On-The-Go" playlist

### 🧠 Discovery Engine

Multi-strategy recommendation system:
- **40 songs**: Genre-based (from your top artists' albums)
- **30 songs**: Artist exploration (middle-tier artists)
- **20 songs**: Temporal diversity (random sampling for variety)
- **10 songs**: Random exploration (lesser-known artists)

### 📊 Metadata Support

Comprehensive ID3 tags:
- Title, Artist, Album Artist, Album
- Genre, Year, BPM
- Album Artwork (high-resolution JPEG)

---

## Quick Start

### Prerequisites

- Python 3.8+
- Spotify Developer Account ([Get credentials](https://developer.spotify.com/dashboard))
- iTunes installed (Windows only for COM integration)
- FFmpeg ([Download](https://ffmpeg.org/download.html))

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/Walkman.git
cd Walkman

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Edit .env with your Spotify credentials
```

### Basic Usage

```python
# 1. Sync your Spotify liked songs
python -m src.spotify_sync

# 2. Discover new music (100 songs)
python -m src.music_discovery

# 3. Listen on iPod and add favorites to "On-The-Go" playlist

# 4. Integrate approved songs into library
python -m src.itunes_integrator
```

---

## Architecture

```
Walkman/
├── src/                    # Core Python package
│   ├── spotify_sync.py     # Fetch Spotify metadata
│   ├── music_discovery.py  # Recommendation engine
│   ├── youtube_downloader.py  # YouTube search & download
│   ├── metadata_embedder.py   # ID3 tag embedding
│   ├── itunes_integrator.py   # iTunes approval workflow
│   └── utils.py            # Common utilities
│
├── data/                   # Metadata storage
│   ├── spotify/            # Spotify metadata JSON
│   ├── discovered/         # Discovery metadata
│   └── tracking/           # Completion tracking
│
├── music/                  # MP3 file storage
│   ├── library/            # Permanent library
│   ├── discovered/         # Pending discoveries
│   └── staging/            # iTunes import staging
│
├── logs/                   # Application logs
├── docs/                   # Documentation
└── tests/                  # Unit tests
```

---

## Workflow

### Phase 1: Initial Setup
1. Authenticate with Spotify API
2. Sync all liked songs (~1000+ songs with metadata)
3. Download from YouTube and embed metadata

### Phase 2: Discovery Loop
1. **Generate**: Run discovery engine → 100 new recommendations
2. **Listen**: Sync to iPod and listen during the week
3. **Approve**: Add favorites to "On-The-Go" playlist
4. **Integrate**: Run integrator to process approvals
5. **Repeat**: Discovery learns from your approvals

---

## Technology Stack

- **API Integration**: `spotipy` (Spotify), `yt-dlp` (YouTube)
- **Audio Processing**: `mutagen` (ID3 tags), FFmpeg (audio extraction)
- **Windows Automation**: `pywin32` (iTunes COM interface)
- **Data Management**: JSON files for metadata tracking
- **Logging**: Python `logging` module throughout

---

## Project Structure

### Core Modules

#### `spotify_sync.py`
Fetches Spotify liked songs with extended metadata including audio features (BPM), artist genres, and album art URLs. Saves to `data/spotify/liked_songs_metadata.json`.

#### `music_discovery.py`
Analyzes your taste profile and generates personalized recommendations using a 4-strategy engine. Excludes already-owned songs and previously rejected recommendations.

#### `youtube_downloader.py`
Searches YouTube for songs and downloads as high-quality MP3s (320kbps). Tracks completed downloads to support resume capability.

#### `metadata_embedder.py`
Embeds ID3v2.3 tags into MP3 files using fuzzy string matching. Handles album art download and embedding.

#### `itunes_integrator.py`
Reads iTunes "On-The-Go" playlist to determine approved songs. Moves approved songs to library, deletes rejected songs, and updates tracking files.

#### `utils.py`
Common utilities including logging setup, Spotify authentication, string normalization, fuzzy matching, and path management.

---

## Configuration

### Environment Variables (`.env`)

```bash
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=https://yourdomain.com/callback
```

### Path Constants

All paths are managed in `src/utils.py`:
- `SPOTIFY_METADATA_PATH`: Liked songs metadata
- `DISCOVERED_METADATA_PATH`: Discovery metadata
- `LIBRARY_DIR`: Permanent music library
- `DISCOVERED_DIR`: Pending discoveries
- `STAGING_DIR`: iTunes import staging

---

## Advanced Usage

### Custom Discovery Count

```python
from src.music_discovery import MusicDiscovery

discovery = MusicDiscovery()
discovery.run(target_count=200)  # Discover 200 songs instead of 100
```

### Metadata Embedding for Specific Folder

```python
from src.metadata_embedder import MetadataEmbedder
from pathlib import Path

embedder = MetadataEmbedder(
    source_folder=Path('custom_folder'),
    metadata_path=Path('custom_metadata.json')
)
embedder.run()
```

### Manual YouTube Download

```python
from src.youtube_downloader import YouTubeDownloader

downloader = YouTubeDownloader(download_folder='custom_output')
success, failed = downloader.process_metadata(metadata_list)
```

---

## Troubleshooting

### Spotify Authentication Issues
- Ensure `.env` file has correct credentials
- Check redirect URI matches Spotify app settings
- Delete `.cache` file and re-authenticate

### YouTube Download Failures
- Install/update FFmpeg: `ffmpeg -version`
- Export cookies for age-restricted content: See `EXPORT_COOKIES_INSTRUCTIONS.txt`
- Check internet connection and YouTube availability

### iTunes Integration Errors
- Run Command Prompt as Administrator
- Ensure iTunes is installed and running
- Check "On-The-Go" playlist exists in iTunes

---

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_spotify_sync.py

# Run with coverage
pytest --cov=src tests/
```

---

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## License

MIT License - See [LICENSE](LICENSE) for details

---

## Author

**Kieran**

- GitHub: [@yourusername](https://github.com/yourusername)
- Project: [Walkman](https://github.com/yourusername/Walkman)

---

## Acknowledgments

- [Spotify Web API](https://developer.spotify.com/documentation/web-api/) for music metadata
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube downloading
- [mutagen](https://mutagen.readthedocs.io/) for audio metadata handling
- [spotipy](https://spotipy.readthedocs.io/) for Spotify API wrapper

---

## Roadmap

- [ ] Add web UI for discovery management
- [ ] Support for Apple Music API
- [ ] Collaborative filtering recommendations
- [ ] Playlist generation from discoveries
- [ ] Cross-platform iTunes alternative (Linux/Mac)

---

**Built with ❤️ for music lovers who want to discover their next favorite song**
