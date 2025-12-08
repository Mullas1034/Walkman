import yt_dlp


def search_youtube(song_name, artist):
    """
    Search YouTube for a song and return the first result's URL.

    Args:
        song_name: The name of the song
        artist: The artist(s) name

    Returns:
        YouTube URL of the first search result, or None if not found
    """
    # Create search query
    query = f"ytsearch1:{song_name} {artist}"

    try:
        # Configure yt-dlp options
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }

        # Search YouTube
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(query, download=False)

            # Extract the URL from the first result
            if results and 'entries' in results and len(results['entries']) > 0:
                video_id = results['entries'][0]['id']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                return video_url
            else:
                return None

    except Exception as e:
        print(f"Error searching for '{song_name} {artist}': {e}")
        return None


def process_song_file(input_file, output_file):
    """
    Read songs from input file, search YouTube for each, and write URLs to output file.

    Args:
        input_file: Path to file containing songs (format: "Song Name - Artist")
        output_file: Path to file where YouTube URLs will be written
    """
    print(f"Reading songs from {input_file}...")

    with open(input_file, 'r', encoding='utf-8') as f:
        songs = f.readlines()

    print(f"Found {len(songs)} song(s) to search.\n")

    results = []

    for i, line in enumerate(songs, 1):
        line = line.strip()
        if not line:
            continue

        # Split song name and artist (format: "Song Name - Artist")
        if ' - ' in line:
            song_name, artist = line.split(' - ', 1)
            try:
                print(f"[{i}/{len(songs)}] Searching: {song_name} by {artist}")
            except UnicodeEncodeError:
                print(f"[{i}/{len(songs)}] Searching: (special characters)")

            youtube_url = search_youtube(song_name, artist)

            if youtube_url:
                try:
                    print(f"  Found: {youtube_url}\n")
                except UnicodeEncodeError:
                    print(f"  Found: {youtube_url}\n")
                results.append(f"{line} | {youtube_url}\n")
            else:
                print(f"  Not found\n")
                results.append(f"{line} | NOT FOUND\n")
        else:
            try:
                print(f"[{i}/{len(songs)}] Skipping invalid format: {line}\n")
            except UnicodeEncodeError:
                print(f"[{i}/{len(songs)}] Skipping invalid format\n")
            results.append(f"{line} | INVALID FORMAT\n")

    # Write results to output file
    print(f"Writing results to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(results)

    print(f"Done! Results saved to {output_file}")


def main():
    input_file = "liked_songs.txt"
    output_file = "youtube_urls.txt"

    process_song_file(input_file, output_file)


if __name__ == '__main__':
    main()
