import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Spotify API credentials from environment variables
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback')

# Scopes needed to access user's liked songs
SCOPE = 'user-library-read'


def authenticate_spotify():
    """
    Authenticate with Spotify using automatic local callback server.
    First run: Opens browser for authorization, then auto-completes.
    Subsequent runs: Uses cached token automatically (no interaction needed).
    """
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        open_browser=True,
        cache_path='.cache'  # Store token cache
    )

    # This automatically handles the OAuth flow:
    # - First run: Opens browser, starts local server, receives callback
    # - Subsequent runs: Uses cached token and auto-refreshes if expired
    sp = spotipy.Spotify(auth_manager=auth_manager)

    return sp


def get_all_liked_songs(sp):
    """Retrieve all liked songs from Spotify."""
    liked_songs = []
    offset = 0
    limit = 50  # Max allowed by Spotify API

    while True:
        results = sp.current_user_saved_tracks(limit=limit, offset=offset)

        if not results['items']:
            break

        for item in results['items']:
            track = item['track']
            song_info = {
                'name': track['name'],
                'artists': ', '.join([artist['name'] for artist in track['artists']]),
                'album': track['album']['name'],
                'uri': track['uri'],
                'added_at': item['added_at']
            }
            liked_songs.append(song_info)

        offset += limit
        print(f"Fetched {len(liked_songs)} songs so far...")

        # Break if we've fetched all songs
        if len(results['items']) < limit:
            break

    return liked_songs


def main():
    print("Authenticating with Spotify...")
    print("(First run: Browser will open for authorization)")
    print("(Subsequent runs: Automatic - no interaction needed)\n")

    sp = authenticate_spotify()

    print("Successfully authenticated!")
    print("Fetching liked songs...")
    liked_songs = get_all_liked_songs(sp)

    print(f"\nTotal liked songs: {len(liked_songs)}")

    # Write songs to text file
    output_file = "liked_songs.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        for song in liked_songs:
            f.write(f"{song['name']} - {song['artists']}\n")

    print(f"Songs written to {output_file}")


if __name__ == '__main__':
    main()
