import os
import subprocess

async def download_youtube_audio(search_query):
    try:
        # Search and download using yt-dlp
        print(f"Searching for: {search_query}")
        command = [
            "yt-dlp",
            "-x", "--audio-format", "mp3",
            "--output", "temp.mp3",  # Save as temp.mp3
            f"ytsearch1:{search_query}"
        ]
        subprocess.run(command, check=True)
        return './temp/temp.mp3'
    except Exception as e:
        print(f"An error occurred: {e}")
        return './temp/temp.mp3'

if __name__ == "__main__":
    query = input("Enter YouTube search query: ")
    download_youtube_audio(query)
