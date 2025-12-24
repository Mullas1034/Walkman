"""
List all playlists in iTunes to help identify playlist names.
"""

import win32com.client

def list_all_playlists():
    """List all playlists available in iTunes."""
    try:
        # Connect to iTunes
        itunes = win32com.client.Dispatch("iTunes.Application")
        print("Connected to iTunes successfully!\n")

        # Get all playlists
        playlists = itunes.LibrarySource.Playlists

        print("="*80)
        print(f"FOUND {playlists.Count} PLAYLISTS IN ITUNES")
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
        print("\nLook for playlists containing your discovered songs above.")
        print("Use the exact names (including capitalization) when running integration.")

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure iTunes is installed and running.")

if __name__ == '__main__':
    list_all_playlists()
