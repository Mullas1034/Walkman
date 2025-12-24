"""
List all playlists on connected iPod device.
"""

import win32com.client

def list_ipod_playlists():
    """List all playlists on the connected iPod."""
    try:
        # Connect to iTunes
        itunes = win32com.client.Dispatch("iTunes.Application")
        print("Connected to iTunes successfully!\n")

        # Get all sources (Library, iPod, etc.)
        sources = itunes.Sources

        print("="*80)
        print(f"FOUND {sources.Count} SOURCES")
        print("="*80)

        # Find iPod source
        ipod_source = None
        for i in range(1, sources.Count + 1):
            source = sources.Item(i)
            print(f"Source {i}: {source.Name} (Kind: {source.Kind})")
            # Kind 2 = iPod
            if source.Kind == 2:
                ipod_source = source
                print(f"  ^ This is the iPod!")

        print()

        if not ipod_source:
            print("No iPod found!")
            print("Make sure your iPod is connected and recognized by iTunes.")
            return

        # List playlists on iPod
        playlists = ipod_source.Playlists

        print("="*80)
        print(f"FOUND {playlists.Count} PLAYLISTS ON IPOD")
        print("="*80)

        playlist_list = []
        for i in range(1, playlists.Count + 1):
            playlist = playlists.Item(i)
            track_count = playlist.Tracks.Count
            playlist_list.append({
                'name': playlist.Name,
                'tracks': track_count
            })

        # Sort by name
        playlist_list.sort(key=lambda x: x['name'].lower())

        # Display all playlists
        for i, pl in enumerate(playlist_list, 1):
            print(f"{i:3d}. {pl['name']:<50} ({pl['tracks']} tracks)")

        print("="*80)
        print("\nThese are the playlists on your iPod.")
        print("Look for 'on-the-go 2', 'on-the-go 3', and 'XFactor' above.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    list_ipod_playlists()
