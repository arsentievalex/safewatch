import yt_dlp
import os
from pathlib import Path


def download_youtube_video(url, output_path=os.getcwd(), quality="medium"):
    """
    Download a YouTube video in the selected quality and MP4 format using yt-dlp.

    Args:
        url (str): The URL of the YouTube video
        output_path (str, optional): Directory to save the video. Defaults to Downloads folder.
        quality (str, optional): Video quality. Options are "high", "medium", or "low". Defaults to "high".

    Returns:
        str: Path to the downloaded video file
    """
    try:
        # Define yt-dlp format strings for different quality levels, all in MP4 format
        quality_formats = {
            "high": 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            "medium": 'bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720][ext=mp4]',
            "low": 'bv*[height<=480][ext=mp4]+ba[ext=m4a]/b[height<=480][ext=mp4]',
        }

        # Set selected format, default to "high" if input is invalid
        selected_format = quality_formats.get(quality.lower(), quality_formats["high"])

        # Configure yt-dlp options
        ydl_opts = {
            'format': selected_format,
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [lambda d: print(f"Downloading: {d['_percent_str']} of {d['_total_bytes_str']}")],
        }

        # Create yt-dlp object and download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("Getting video information...")
            info = ydl.extract_info(url, download=False)
            print(f"\nTitle: {info['title']}")
            print(f"Duration: {info['duration']} seconds")
            print(f"Resolution: {info.get('resolution', 'N/A')}")

            print("\nStarting download...")
            ydl.download([url])

            # Get the output filename
            video_path = os.path.join(output_path, f"{info['title']}.mp4")

        print(f"\nDownload completed successfully!")
        print(f"Video saved to: {video_path}")
        return video_path

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None
