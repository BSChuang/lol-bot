import os
import subprocess

async def download_youtube_audio(search_query):
    temp_file = "./temp/temp.mp3"

    if os.path.exists(temp_file):
        print(f"Deleting existing file: {temp_file}")
        os.remove(temp_file)

    try:
        # Search and download using yt-dlp
        print(f"Searching for: {search_query}")
        command = [
            "yt-dlp",
            "-x", "--audio-format", "mp3",
            "--output", temp_file,  # Save as temp.mp3
            f"ytsearch1:{search_query}"
        ]
        subprocess.run(command, check=True)
        return temp_file
    except Exception as e:
        print(f"An error occurred: {e}")
        return temp_file

if __name__ == "__main__":
    query = input("Enter YouTube search query: ")
    download_youtube_audio(query)
