# Walkman Workflow Guide

Complete guide to using the Walkman music discovery system for finding and integrating new music.

---

## Table of Contents

1. [Overview](#overview)
2. [Initial Setup Workflow](#initial-setup-workflow)
3. [Discovery Loop](#discovery-loop)
4. [File Structure](#file-structure)
5. [Command Reference](#command-reference)
6. [Best Practices](#best-practices)
7. [Common Scenarios](#common-scenarios)
8. [Tips & Tricks](#tips--tricks)

---

## Overview

Walkman operates in a continuous discovery loop:

```
Spotify Sync → Generate Discoveries → Listen on iPod → Approve Favorites → Integrate → Repeat
```

### Key Concepts

- **Liked Songs**: Your Spotify liked songs (source of truth for taste)
- **Discovered Songs**: AI-recommended songs (pending review)
- **Approved Songs**: Discoveries you liked (added to library)
- **Rejected Songs**: Discoveries you didn't like (tracked to avoid re-recommendation)

---

## Initial Setup Workflow

### Step 1: Sync Spotify Library

**Purpose**: Download your complete Spotify liked songs library with metadata

```bash
python -m src.spotify_sync
```

**What happens**:
1. Authenticates with Spotify API
2. Fetches all liked songs (paginated, 50 at a time)
3. Fetches audio features (BPM) in batches of 100
4. Fetches artist genres in batches of 50
5. Saves to `data/spotify/liked_songs_metadata.json`

**Output files**:
- `data/spotify/liked_songs_metadata.json` - Full metadata
- `data/spotify/liked_songs.txt` - Simple text list
- `logs/spotify_sync.log` - Execution log

**Time**: ~2-5 minutes for 1000 songs

---

## Discovery Loop

### Phase 1: Generate Recommendations

**Command**:
```bash
python -m src.music_discovery
```

**What happens**:
1. Loads liked songs + approved discoveries for taste analysis
2. Analyzes genres, artists, BPM, decades
3. Generates 100 recommendations using 4-strategy engine:
   - 40 songs from top artists' albums
   - 30 songs from middle-tier artists
   - 20 songs for temporal diversity
   - 10 songs for random exploration
4. Excludes already-owned songs and rejected songs
5. Searches YouTube for each song
6. Downloads as 320kbps MP3s
7. Embeds ID3 metadata + album art
8. Saves to `music/discovered/`

**Output files**:
- `data/discovered/discovered_songs_metadata.json` - Discovery metadata
- `data/discovered/discovered_songs_youtube_urls.txt` - YouTube URLs
- `music/discovered/*.mp3` - Downloaded MP3 files
- `logs/music_discovery.log` - Execution log

**Time**: ~30-60 minutes for 100 songs

### Phase 2: Import to iTunes

**Manual steps**:
1. Open iTunes
2. Drag `music/discovered/` folder into iTunes
3. Sync iTunes with your iPod

**What happens**:
- Songs appear in iTunes library
- Songs sync to iPod during next sync

### Phase 3: Listen & Approve

**On your iPod**:
1. Listen to discovered songs during the week
2. For songs you like: Add to "On-The-Go" playlist
   - While song is playing: Hold Center button → "Add to On-The-Go"
3. For songs you don't like: Do nothing (they'll be auto-rejected)

**Best practice**: Listen to all 100 songs at least once before integrating

### Phase 4: Integrate Approvals

**Command**:
```bash
python -m src.itunes_integrator
```

**What happens**:
1. Connects to iTunes via COM interface
2. Reads "On-The-Go" playlist tracks
3. Matches playlist tracks to discovery metadata (fuzzy matching)
4. Classifies songs:
   - **Approved**: In "On-The-Go" playlist → Copy to `music/library/` and `music/staging/`
   - **Rejected**: Not in playlist → Delete from `music/discovered/`
5. Updates tracking files:
   - Appends to `data/spotify/approved_discovered_songs.json`
   - Appends to `data/tracking/rejected_discovered_songs.json`
6. Clears "On-The-Go" playlist
7. Deletes `data/discovered/discovered_songs_metadata.json`

**Output files**:
- `music/library/*.mp3` - Approved songs (permanent)
- `music/staging/*.mp3` - Approved songs (for iTunes organization)
- `data/spotify/approved_discovered_songs.json` - Updated
- `data/tracking/rejected_discovered_songs.json` - Updated
- `logs/itunes_integrator.log` - Execution log

**Time**: ~1-2 minutes

### Phase 5: Organize in iTunes

**Manual steps**:
1. Drag `music/staging/` folder into iTunes
2. Add songs to playlists, rate them, etc.
3. Empty `music/staging/` folder when done

**Why staging folder?**
- Separates new approvals from existing library
- Makes it easy to organize new songs before final placement
- Prevents accidental re-organization of library

---

## File Structure

### Data Files

```
data/
├── spotify/
│   ├── liked_songs_metadata.json       # All Spotify liked songs
│   ├── liked_songs.txt                 # Simple text list
│   └── approved_discovered_songs.json  # Approved discoveries (grows over time)
│
├── discovered/
│   ├── discovered_songs_metadata.json  # Current pending discoveries (cleared after integration)
│   └── discovered_songs_youtube_urls.txt  # YouTube search results
│
└── tracking/
    ├── completed_downloads.txt         # Downloaded YouTube URLs (resume support)
    └── rejected_discovered_songs.json  # Rejected discoveries (never re-recommended)
```

### Music Files

```
music/
├── library/                # Permanent approved songs
│   └── *.mp3
│
├── discovered/             # Pending discoveries (cleared after integration)
│   └── *.mp3
│
└── staging/                # Approved songs ready for iTunes organization
    └── *.mp3               # (manually empty after organizing)
```

### Log Files

```
logs/
├── spotify_sync.log         # Spotify sync execution
├── music_discovery.log      # Discovery generation
├── youtube_downloader.log   # YouTube downloads
├── metadata_embedder.log    # Metadata embedding
└── itunes_integrator.log    # Integration workflow
```

---

## Command Reference

### Core Modules

```bash
# Sync Spotify liked songs
python -m src.spotify_sync

# Generate music discoveries
python -m src.music_discovery

# Integrate iTunes approvals
python -m src.itunes_integrator

# Embed metadata (standalone)
python -m src.metadata_embedder

# Download from YouTube (standalone)
python -m src.youtube_downloader
```

### Programmatic Usage

```python
# Spotify Sync
from src.spotify_sync import SpotifySync
sync = SpotifySync()
sync.run()

# Music Discovery
from src.music_discovery import MusicDiscovery
discovery = MusicDiscovery()
discovery.run(target_count=100)

# iTunes Integration
from src.itunes_integrator import iTunesIntegrator
integrator = iTunesIntegrator()
approved, rejected = integrator.run()
```

---

## Best Practices

### Discovery Generation

1. **Run weekly**: Fresh recommendations based on evolving taste
2. **Listen fully**: Give each song at least 30 seconds
3. **Be selective**: Only approve songs you'd listen to repeatedly
4. **Provide feedback**: Rejections help the algorithm learn

### Metadata Management

1. **Keep liked_songs_metadata.json**: Source of truth for taste
2. **Backup approved_discovered_songs.json**: Permanent approval history
3. **Review rejected_discovered_songs.json**: Verify no good songs rejected
4. **Clear staging/ folder**: Prevents duplicate imports

### iTunes Integration

1. **Sync regularly**: Don't let discoveries pile up
2. **Use On-The-Go correctly**: Only add truly approved songs
3. **Clear playlist**: Integration clears it automatically
4. **Organize immediately**: Process staging/ folder promptly

---

## Common Scenarios

### Scenario 1: "I want more/fewer discoveries"

**Solution**: Adjust target count

```python
# Generate 200 songs instead of 100
from src.music_discovery import MusicDiscovery
discovery = MusicDiscovery()
discovery.run(target_count=200)
```

### Scenario 2: "Discovery recommended song I already rejected"

**Possible causes**:
- Song not in `rejected_discovered_songs.json`
- Different artist name spelling
- Integration didn't run properly

**Solution**:
1. Check `data/tracking/rejected_discovered_songs.json`
2. Verify track_id is present
3. Re-run integration if needed

### Scenario 3: "Integration matched wrong song"

**Cause**: Fuzzy matching threshold (75%) too low

**Solution**:
Edit `src/itunes_integrator.py` line 179:
```python
if similarity_ratio(song_pattern, otg_pattern) >= 0.85:  # Increase to 85%
```

### Scenario 4: "YouTube download failed for many songs"

**Possible causes**:
- Age-restricted content (requires cookies)
- Regional restrictions
- Video removed/private

**Solution**:
1. Export browser cookies → `cookies.txt`
2. See `EXPORT_COOKIES_INSTRUCTIONS.txt`
3. Re-run discovery (skips completed downloads)

### Scenario 5: "Spotify sync is slow"

**Cause**: Large library (1000+ songs) + API rate limits

**Solution**:
- Normal for first sync (~5 minutes for 1000 songs)
- Subsequent syncs faster (only new songs)
- Run during off-hours if network is slow

### Scenario 6: "I want to reset everything"

**Warning**: This deletes all discoveries and approvals

```bash
# Backup first
cp -r data/ data_backup/
cp -r music/ music_backup/

# Clear discoveries
rm -rf music/discovered/*
rm -rf music/staging/*
rm data/discovered/*
rm data/tracking/rejected_discovered_songs.json

# Clear approved (optional, be careful!)
# rm data/spotify/approved_discovered_songs.json
```

---

## Tips & Tricks

### Speed Up Discovery

```bash
# Run discovery in background
start /B python -m src.music_discovery

# Check progress in logs
tail -f logs/music_discovery.log
```

### Batch Processing

```python
# Process multiple metadata files
from src.metadata_embedder import MetadataEmbedder

for metadata_file in metadata_files:
    embedder = MetadataEmbedder(metadata_path=metadata_file)
    embedder.run()
```

### Export Discoveries Playlist

```python
# Create Spotify playlist from discoveries
import json
from src.utils import authenticate_spotify

with open('data/discovered/discovered_songs_metadata.json') as f:
    discoveries = json.load(f)

sp = authenticate_spotify()
user_id = sp.current_user()['id']
playlist = sp.user_playlist_create(user_id, 'Walkman Discoveries')

track_uris = [song['uri'] for song in discoveries if song.get('uri')]
sp.playlist_add_items(playlist['id'], track_uris)

print(f"Created playlist with {len(track_uris)} songs")
```

### Monitor File Sizes

```bash
# Check library size
du -sh music/library/

# Count songs
ls music/library/*.mp3 | wc -l

# Check largest log files
ls -lh logs/ | sort -k5 -h
```

### Automated Weekly Discovery

**Windows Task Scheduler**:
1. Create batch file `weekly_discovery.bat`:
```batch
@echo off
cd C:\Users\YourName\Walkman
call venv\Scripts\activate
python -m src.music_discovery
```

2. Schedule to run every Sunday at 2 AM

**Linux cron**:
```bash
0 2 * * 0 cd /home/user/Walkman && /home/user/Walkman/venv/bin/python -m src.music_discovery
```

---

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    WALKMAN WORKFLOW                          │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  Spotify Sync    │  ← Run once initially, then monthly
│  liked_songs     │     or when library changes significantly
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Discovery       │  ← Run weekly for fresh recommendations
│  (100 songs)     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Import to       │  ← Drag music/discovered/ into iTunes
│  iTunes          │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Sync to iPod    │  ← Standard iTunes sync
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Listen          │  ← Listen on iPod during the week
│  (1 week)        │     Add favorites to "On-The-Go"
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Integration     │  ← Process approvals/rejections
│  (iTunes)        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Organize        │  ← Drag music/staging/ to iTunes playlists
│  in iTunes       │     Empty staging/ folder
└────────┬─────────┘
         │
         └──────────────────────┐
                                │
         ┌──────────────────────┘
         │
         ▼
   (Repeat weekly)
```

---

## Next Steps

- Review [API.md](API.md) for developer documentation
- Check [SETUP.md](SETUP.md) for configuration options
- See [README.md](../README.md) for feature overview

---

**Happy discovering! 🎵**
