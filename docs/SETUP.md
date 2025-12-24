# Walkman Setup Guide

Complete installation and configuration guide for the Walkman music discovery system.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Spotify API Setup](#spotify-api-setup)
3. [Python Environment](#python-environment)
4. [FFmpeg Installation](#ffmpeg-installation)
5. [iTunes Configuration](#itunes-configuration)
6. [Environment Variables](#environment-variables)
7. [First Run](#first-run)
8. [Verification](#verification)
9. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements

- **Operating System**: Windows 10+ (iTunes integration requires Windows)
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 50GB+ for music library
- **Internet**: Broadband connection (for API calls and downloads)

### Required Software

- Python 3.8+ ([Download](https://www.python.org/downloads/))
- iTunes (Windows) ([Download](https://www.apple.com/itunes/download/))
- FFmpeg ([Download](https://ffmpeg.org/download.html))
- Git (optional, for cloning) ([Download](https://git-scm.com/downloads))

---

## Spotify API Setup

### 1. Create Spotify Developer Account

1. Visit [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click "Create an App"

### 2. Configure Your App

1. **App Name**: `Walkman` (or any name)
2. **App Description**: `Personal music discovery system`
3. **Redirect URIs**: Add your callback URL
   - Development: `http://localhost:8888/callback`
   - Production: `https://yourdomain.com/callback`
4. Click "Save"

### 3. Get API Credentials

1. Click "Settings" in your app dashboard
2. Copy **Client ID**
3. Click "View client secret" and copy **Client Secret**
4. Save these for the environment variables step

### 4. Enable Required Scopes

The following scopes are automatically requested:
- `user-library-read`: Read liked songs
- `playlist-modify-public`: Modify public playlists
- `playlist-modify-private`: Modify private playlists

---

## Python Environment

### Option 1: Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on Linux/Mac
source venv/bin/activate

# Verify activation
which python  # Should show venv path
```

### Option 2: System Python

```bash
# Check Python version
python --version  # Should be 3.8+

# Update pip
python -m pip install --upgrade pip
```

### Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list
```

### Key Dependencies

- `spotipy==2.23.0`: Spotify API wrapper
- `yt-dlp==2023.10.13`: YouTube downloader
- `mutagen==1.47.0`: Audio metadata handling
- `python-dotenv==1.0.0`: Environment variable management
- `requests==2.31.0`: HTTP library
- `pywin32==306`: Windows COM automation (iTunes)

---

## FFmpeg Installation

FFmpeg is required for audio extraction from YouTube videos.

### Windows

#### Method 1: Download Binary

1. Download from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract to `C:\ffmpeg`
3. Add to PATH:
   - Open System Properties → Environment Variables
   - Edit "Path" variable
   - Add `C:\ffmpeg\bin`
4. Verify: `ffmpeg -version`

#### Method 2: Chocolatey

```bash
choco install ffmpeg
```

#### Method 3: Scoop

```bash
scoop install ffmpeg
```

### Linux

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Fedora
sudo dnf install ffmpeg

# Arch
sudo pacman -S ffmpeg
```

### Mac

```bash
brew install ffmpeg
```

### Verification

```bash
ffmpeg -version
# Should show FFmpeg version and configuration
```

---

## iTunes Configuration

### Installation

1. Download iTunes from [Apple](https://www.apple.com/itunes/download/)
2. Install and launch iTunes
3. Sign in with your Apple ID

### Create "On-The-Go" Playlist

1. Open iTunes
2. File → New → Playlist
3. Name it exactly: `On-The-Go`
4. This playlist will be used for approval workflow

### Enable COM Automation (Windows)

- iTunes COM interface is automatically available on Windows
- Run Python scripts as Administrator if you encounter permission errors

---

## Environment Variables

### 1. Create `.env` File

```bash
# Copy example file
cp .env.example .env

# Or create manually
# Windows
type nul > .env

# Linux/Mac
touch .env
```

### 2. Configure Variables

Edit `.env` file:

```bash
# Spotify API Credentials
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback

# Optional: Custom paths (defaults are fine for most users)
# CUSTOM_DATA_DIR=C:\Users\YourName\WalkmanData
# CUSTOM_MUSIC_DIR=C:\Users\YourName\Music\Walkman
```

### 3. Security

**Important**: Never commit `.env` to version control

```bash
# Verify .gitignore includes .env
cat .gitignore | grep ".env"
```

---

## First Run

### 1. Verify Installation

```bash
# Check all dependencies
python -c "import spotipy, yt_dlp, mutagen, dotenv, win32com.client; print('All dependencies OK')"

# Check environment variables
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Spotify ID:', os.getenv('SPOTIFY_CLIENT_ID')[:10] + '...')"
```

### 2. Test Spotify Authentication

```bash
python -m src.spotify_sync
```

Expected output:
```
================================================================================
SPOTIFY SYNC - Starting
================================================================================
Authenticating with Spotify...
Successfully authenticated with Spotify
Fetching liked songs from Spotify...
Fetched 50 songs so far...
...
```

### 3. Initial Sync (First Time Only)

This will take several minutes depending on your library size:

```bash
# Sync all liked songs from Spotify
python -m src.spotify_sync

# Expected: data/spotify/liked_songs_metadata.json created
```

---

## Verification

### Check Folder Structure

```bash
tree /F  # Windows
# Or
find . -type d  # Linux/Mac
```

Expected structure:
```
Walkman/
├── data/
│   ├── spotify/
│   │   ├── liked_songs_metadata.json  ✓
│   │   └── liked_songs.txt  ✓
│   ├── discovered/
│   └── tracking/
├── music/
│   ├── library/
│   ├── discovered/
│   └── staging/
└── logs/
    └── spotify_sync.log  ✓
```

### Verify Metadata File

```bash
# Check JSON is valid
python -c "import json; print(f'{len(json.load(open(\"data/spotify/liked_songs_metadata.json\")))} songs loaded')"
```

### Test YouTube Download

```bash
# Test single download
python -c "
from src.youtube_downloader import YouTubeDownloader
dl = YouTubeDownloader()
url = YouTubeDownloader.search_youtube('Infrunami', 'Steve Lacy')
print(f'Found: {url}')
"
```

---

## Troubleshooting

### Spotify Authentication Fails

**Error**: `SpotifyOauthError: No token provided`

**Solution**:
1. Delete `.cache` file
2. Verify `.env` has correct credentials
3. Check redirect URI matches Spotify app settings
4. Try manual authentication:

```python
from src.utils import authenticate_spotify
sp = authenticate_spotify()
# Follow prompts
```

### FFmpeg Not Found

**Error**: `FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'`

**Solution**:
1. Verify FFmpeg is in PATH: `where ffmpeg` (Windows) or `which ffmpeg` (Linux/Mac)
2. Reinstall FFmpeg
3. Manually specify FFmpeg path in yt-dlp options

### iTunes COM Error

**Error**: `pywintypes.com_error: (-2147221005, 'Invalid class string', None, None)`

**Solution**:
1. Verify iTunes is installed
2. Run Command Prompt/PowerShell as Administrator
3. Reinstall pywin32:

```bash
pip uninstall pywin32
pip install pywin32
python Scripts\pywin32_postinstall.py -install
```

### YouTube Download Fails (Age-Restricted Content)

**Error**: `ERROR: Sign in to confirm you're not a bot`

**Solution**:
1. Export cookies from browser
2. Save as `cookies.txt` in project root
3. See `EXPORT_COOKIES_INSTRUCTIONS.txt` for detailed steps

### Permission Errors (Windows)

**Error**: `PermissionError: [WinError 5] Access is denied`

**Solution**:
1. Run terminal as Administrator
2. Check antivirus isn't blocking file operations
3. Verify folders aren't read-only

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'src'`

**Solution**:
```bash
# Ensure you're in project root
cd Walkman

# Install in development mode
pip install -e .
```

---

## Next Steps

Once setup is complete:

1. Read [WORKFLOW.md](WORKFLOW.md) for usage guide
2. Run initial sync: `python -m src.spotify_sync`
3. Generate first discoveries: `python -m src.music_discovery`
4. Follow the discovery workflow

---

## Advanced Configuration

### Custom Data Directories

Edit `src/utils.py` to customize paths:

```python
# Custom paths (lines 34-48)
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = Path(r'D:\WalkmanData')  # Custom data location
MUSIC_DIR = Path(r'E:\Music\Walkman')  # Custom music location
```

### Logging Configuration

Edit logging level in any module:

```python
logger = setup_logging(__name__, 'module.log', level=logging.DEBUG)
# Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Download Quality

Edit `src/youtube_downloader.py` line 192:

```python
'preferredquality': '320',  # Options: 128, 192, 256, 320
```

---

## Getting Help

- Check [README.md](../README.md) for overview
- See [WORKFLOW.md](WORKFLOW.md) for usage examples
- Review [API.md](API.md) for developer documentation
- Open GitHub issue for bugs/features

---

**Setup complete! You're ready to discover new music 🎵**
