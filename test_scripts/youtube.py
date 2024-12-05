import os
import subprocess

def download_youtube_audio(search_query):
    try:
        # Search and download using yt-dlp
        print(f"Searching for: {search_query}")
        command = [
            "yt-dlp",
            "-x", "--audio-format", "mp3",
            f"ytsearch1:{search_query}"
        ]
        subprocess.run(command, check=True)
        print("Download complete!")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    query = input("Enter YouTube search query: ")
    download_youtube_audio(query)
