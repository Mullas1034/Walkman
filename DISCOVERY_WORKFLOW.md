# Music Discovery Workflow

Complete guide for discovering new music and integrating it into your library.

## Overview

The music discovery system uses Spotify's recommendation API to find 100 new songs based on your taste, downloads them from YouTube, and lets you approve/reject them using your iPod's "On-The-Go" playlist.

---

## Prerequisites

Install required Python packages:
```bash
pip install pywin32
```

Ensure iTunes is installed on your computer.

---

## Complete Workflow

### Step 1: Generate Discoveries

Run the discovery script:
```bash
python discover_music.py
```

**What it does:**
- Analyzes your liked songs and previously approved discoveries
- Generates 100 recommendations:
  - 40 genre-based songs (prioritizing your most-listened genres)
  - 30 artist-based songs (similar artists, collaborators, deep cuts)
  - 20 temporal diversity songs (different decades)
  - 10 random exploration songs (break filter bubbles)
- Downloads all songs from YouTube to `discovered_songs/` folder
- Embeds metadata (title, artist, album, genre, year, BPM, album art)
- Saves metadata to `discovered_songs_metadata.json`

**Time:** ~30-60 minutes (depending on download speeds)

---

### Step 2: Import to iTunes

1. Open iTunes
2. Drag the `discovered_songs/` folder into iTunes library
3. All 100 songs are now in your iTunes

---

### Step 3: Sync to iPod

1. Connect your iPod
2. Sync the newly added songs to your iPod
3. Disconnect and enjoy

---

### Step 4: Review & Curate (Natural Listening)

Over the next days/weeks:
1. Listen to the discovered songs on your iPod
2. When you hear a song you LIKE:
   - Add it to the **"On-The-Go"** playlist on your iPod
3. Continue listening naturally - no rush!

**Important:** Only add songs you genuinely enjoy. The "On-The-Go" playlist is your approval mechanism.

---

### Step 5: Sync Back to iTunes

Once you've reviewed the songs (or whenever you're ready):
1. Connect your iPod to your computer
2. Sync back to iTunes
3. The "On-The-Go" playlist now contains your approved songs

---

### Step 6: Integrate Approved Songs

Run the integration script:
```bash
python integrate_discoveries.py
```

**What it does:**

**For APPROVED songs (in On-The-Go):**
- Copies MP3 to `downloaded_songs/` (your main library)
- Copies MP3 to `temp_for_itunes/` (for you to organize in iTunes)
- Appends metadata to `approved_discovered_songs.json`
- These songs will influence future recommendations!

**For REJECTED songs (NOT in On-The-Go):**
- Appends metadata to `rejected_discovered_songs.json` (tracking only)
- Deletes MP3 from `discovered_songs/` (cleanup)
- These songs will NOT influence future recommendations

**Cleanup:**
- Clears the "On-The-Go" playlist in iTunes
- Empties `discovered_songs/` folder
- Clears `discovered_songs_metadata.json`

---

### Step 7: Final Manual Step

1. Drag `temp_for_itunes/` folder into iTunes
2. Organize the approved songs in your iTunes library
3. Manually empty the `temp_for_itunes/` folder when ready

---

## File Structure

```
Walkman/
├── downloaded_songs/              # Your main library (liked + approved)
├── discovered_songs/              # Current discovery batch (pending review)
├── temp_for_itunes/               # Approved songs ready for iTunes import
├── liked_songs_metadata.json      # Your Spotify liked songs
├── approved_discovered_songs.json # Approved discoveries (influences recommendations)
├── discovered_songs_metadata.json # Current batch metadata (cleared after integration)
└── rejected_discovered_songs.json # Rejected songs (tracked but not used)
```

---

## Discovery Strategy Explained

### Genre-Based (40 songs)
- **20 direct neighbors:** Same genre or very similar
- **10 one-hop genres:** Related genres (e.g., grime → UK drill)
- **10 wildcards:** Different genres with shared characteristics

### Artist-Based (30 songs)
- Artists similar to those you already like
- Collaborators of your favorite artists
- Deep cuts from artists you only know one song from
- Emerging artists in your scenes

### Temporal Diversity (20 songs)
- Songs from decades you don't usually listen to
- Proto-genres (early influences of what you like)
- Decade exploration beyond your usual range

### Random Exploration (10 songs)
- Pure random sampling to break filter bubbles
- Prevents algorithmic homogenization

---

## Exclusions & Smart Filtering

The discovery engine **automatically excludes**:
- ✅ Songs you've already liked on Spotify
- ✅ Songs you've previously approved
- ✅ Songs currently in discovery batch
- ✅ Songs you've previously rejected

This ensures you **never get duplicate recommendations**.

---

## Tips & Best Practices

1. **Don't rush the review process** - Listen naturally over days/weeks
2. **Only approve songs you genuinely enjoy** - Quality over quantity
3. **Be selective** - The "On-The-Go" playlist trains your taste profile
4. **Run discovery periodically** - Weekly/monthly for fresh recommendations
5. **Clear temp_for_itunes/ regularly** - Prevents clutter

---

## Troubleshooting

### "On-The-Go playlist not found"
- Create an "On-The-Go" playlist in iTunes manually first

### "Error connecting to iTunes"
- Ensure iTunes is installed
- Try running as administrator

### "No recommendations generated"
- Ensure `liked_songs_metadata.json` exists
- Run `python spotify_liked_songs.py` first

### Downloads failing
- Check internet connection
- Ensure `yt-dlp` is installed: `pip install yt-dlp`
- Check that YouTube URLs are accessible

---

## Example Session

```bash
# Week 1: Generate discoveries
python discover_music.py
# → 100 songs downloaded to discovered_songs/

# Import to iTunes and sync to iPod
# Listen naturally over 2 weeks

# Week 3: After reviewing
python integrate_discoveries.py
# → 23 songs approved and moved to downloaded_songs/
# → 77 songs rejected and deleted

# Drag temp_for_itunes/ into iTunes
# Empty temp_for_itunes/ manually

# Week 4: Get fresh recommendations
python discover_music.py
# → New 100 songs, influenced by your 23 approved songs!
```

---

## Next Steps

1. Run `python discover_music.py` to start discovering!
2. Enjoy your new music on your iPod
3. Repeat the cycle whenever you want fresh recommendations

Happy discovering! 🎵
