"""
Generate discovered songs metadata from iPod's XFactor playlist.

This script reads all tracks from the XFactor playlist on your iPod
and creates the discovered_songs_metadata.json file that the integrator needs.
"""

import json
import win32com.client
from pathlib import Path

def generate_metadata_from_ipod():
    """Generate metadata file from iPod's XFactor playlist."""

    # Connect to iTunes
    print("Connecting to iTunes...")
    itunes = win32com.client.Dispatch("iTunes.Application")
    print("Connected!\n")

    # Find iPod source
    sources = itunes.Sources
    ipod_source = None
    for i in range(1, sources.Count + 1):
        src = sources.Item(i)
        if src.Kind == 2:  # Kind 2 = iPod
            ipod_source = src
            print(f"Found iPod: {src.Name}")
            break

    if not ipod_source:
        print("ERROR: No iPod found!")
        return

    # Find XFactor playlist
    playlists = ipod_source.Playlists
    xfactor_playlist = None
    for i in range(1, playlists.Count + 1):
        playlist = playlists.Item(i)
        if playlist.Name.lower() == "xfactor":
            xfactor_playlist = playlist
            break

    if not xfactor_playlist:
        print("ERROR: XFactor playlist not found on iPod!")
        return

    print(f"Found XFactor playlist with {xfactor_playlist.Tracks.Count} tracks\n")

    # Extract metadata from all tracks
    metadata_list = []
    tracks = xfactor_playlist.Tracks

    print("Extracting metadata from tracks...")
    for i in range(1, tracks.Count + 1):
        track = tracks.Item(i)

        metadata = {
            'track_id': f'ipod_track_{i}',
            'title': track.Name or 'Unknown',
            'artist': track.Artist or 'Unknown Artist',
            'album_artist': track.AlbumArtist or track.Artist or 'Unknown',
            'album': track.Album or 'Unknown Album',
            'year': str(track.Year) if track.Year else '',
            'genre': track.Genre or '',
            'bpm': track.BPM if hasattr(track, 'BPM') else 0,
            'uri': '',
            'added_at': '',
            'album_art_url': '',
            'youtube_url': ''
        }

        metadata_list.append(metadata)

        if i % 10 == 0:
            print(f"  Processed {i}/{tracks.Count} tracks...")

    print(f"\nExtracted metadata for {len(metadata_list)} songs")

    # Create data/discovered folder if needed
    data_dir = Path("data/discovered")
    data_dir.mkdir(parents=True, exist_ok=True)

    # Save metadata file
    output_file = data_dir / "discovered_songs_metadata.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(metadata_list, f, indent=2, ensure_ascii=False)

    print(f"\nMetadata saved to: {output_file}")
    print(f"Total songs: {len(metadata_list)}")
    print("\nYou can now run test_integration.py!")

if __name__ == '__main__':
    generate_metadata_from_ipod()
