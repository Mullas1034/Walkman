import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Spotify API credentials
# You'll need to create these at https://developer.spotify.com/dashboard
CLIENT_ID = 'your_client_id_here'
CLIENT_SECRET = 'your_client_secret_here'
REDIRECT_URI = 'http://localhost:8888/callback'

# Scopes needed to access user's liked songs
SCOPE = 'user-library-read'


def authenticate_spotify():
    """Authenticate with Spotify and return a Spotipy client."""
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    ))
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
    sp = authenticate_spotify()

    print("Fetching liked songs...")
    liked_songs = get_all_liked_songs(sp)

    print(f"\nTotal liked songs: {len(liked_songs)}")
    print("\nFirst 5 songs:")
    for i, song in enumerate(liked_songs[:5], 1):
        print(f"{i}. {song['name']} by {song['artists']}")


if __name__ == '__main__':
    main()
