import os
import subprocess
from datetime import datetime
from yt_dlp import YoutubeDL
import instaloader
from TikTokApi import TikTokApi

BASE_DIR = "downloads"
os.makedirs(BASE_DIR, exist_ok=True)

# ---------- Helper Functions ----------

def create_folder(platform, channel="Unknown", content_type="All"):
    folder = os.path.join(BASE_DIR, platform, channel, content_type)
    os.makedirs(folder, exist_ok=True)
    return folder

def check_duplicate(file_path):
    return os.path.exists(file_path)

def merge_video_audio(video_path, audio_path, output_path):
    cmd = f'ffmpeg -y -i "{video_path}" -i "{audio_path}" -c copy "{output_path}"'
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    if os.path.exists(output_path):
        os.remove(video_path)
        os.remove(audio_path)

def generate_metadata(title, channel, hashtags=[]):
    hashtags_text = " ".join(f"#{tag}" for tag in hashtags)
    return f"{title} by {channel} {hashtags_text}"

def create_gif(video_path, start_time=0, duration=5):
    gif_path = video_path.replace(".mp4", ".gif")
    cmd = f'ffmpeg -y -ss {start_time} -t {duration} -i "{video_path}" -vf "fps=15,scale=320:-1:flags=lanczos" "{gif_path}"'
    subprocess.run(cmd, shell=True)
    print(f"✅ GIF created: {gif_path}")

# ---------- YouTube Downloader ----------

def youtube_download(url, quality="best", max_videos=None, download_type="all", trending_shorts=False, audio_only=False):
    type_folder = "Shorts" if download_type.lower()=="shorts" or trending_shorts else "Full_Videos"
    folder = create_folder("YouTube", "%(uploader)s", type_folder)

    ydl_opts = {
        "format": f"bestaudio/best" if audio_only else (f"bestvideo[height<={quality}]+bestaudio/best" if quality != "best" else "best"),
        "outtmpl": os.path.join(folder, "%(title)s.%(ext)s"),
        "noplaylist": False,
        "playlistend": max_videos,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "writethumbnail": True,
        "merge_output_format": "mp4",
        "ignoreerrors": True,
        "continuedl": True
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    print("✅ YouTube download finished!")

# ---------- Instagram Downloader ----------

def instagram_download(url):
    L = instaloader.Instaloader(dirname_pattern=create_folder("Instagram"))
    try:
        post = instaloader.Post.from_shortcode(L.context, url.split("/")[-2])
        L.download_post(post, target='')
        print("✅ Instagram download finished!")
    except Exception as e:
        print("❌ Failed:", e)

# ---------- TikTok Downloader ----------

def tiktok_download(url, audio_only=False):
    api = TikTokApi()
    try:
        video = api.video(url=url)
        data = video.bytes()
        folder = create_folder("TikTok")
        filename = os.path.join(folder, f"{url.split('/')[-1]}.mp4")
        if check_duplicate(filename):
            print("⚠️ Skipping duplicate video:", filename)
            return
        with open(filename, "wb") as f:
            f.write(data)
        print("✅ TikTok download finished!")
        if audio_only:
            audio_path = filename.replace(".mp4", ".mp3")
            cmd = f'ffmpeg -y -i "{filename}" -q:a 0 -map a "{audio_path}"'
            subprocess.run(cmd, shell=True)
            print(f"✅ Audio extracted: {audio_path}")
    except Exception as e:
        print("❌ Failed:", e)

# ---------- Batch Download ----------

def batch_download(file_path):
    with open(file_path, "r") as f:
        urls = f.read().splitlines()
    for url in urls:
        if "youtube" in url:
            youtube_download(url)
        elif "instagram" in url:
            instagram_download(url)
        elif "tiktok" in url:
            tiktok_download(url)
        else:
            print("❌ Unsupported URL:", url)

# ---------- Scheduler ----------

def schedule_daily(url, platform="youtube", time="09:00"):
    # Uses cron to schedule
    command = f'(crontab -l 2>/dev/null; echo "0 9 * * * python3 {os.path.abspath(__file__)} --auto {url} {platform}") | crontab -'
    subprocess.run(command, shell=True)
    print(f"✅ Scheduled daily download for {platform} at {time}")

# ---------- CLI ----------

def main():
    print("=== Ultimate Social Media Downloader ===")
    print("1. YouTube")
    print("2. Instagram")
    print("3. TikTok")
    print("4. Batch download from file")
    print("5. Schedule daily download")
    choice = input("Choose platform/mode (1/2/3/4/5): ")

    if choice == "1":
        url = input("Enter YouTube URL / Playlist / Channel: ")
        quality = input("Video quality (360,720,1080,best) [default best]: ") or "best"
        max_videos = input("Number of videos/shorts to download (Enter for all): ")
        max_videos = int(max_videos) if max_videos.strip() else None
        download_type = input("Download type (shorts/full/all) [default all]: ") or "all"
        trending_shorts = input("Auto-detect trending shorts? (y/n) [default n]: ") == "y"
        audio_only = input("Audio-only? (y/n) [default n]: ") == "y"
        youtube_download(url, quality, max_videos, download_type, trending_shorts, audio_only)

    elif choice == "2":
        url = input("Enter Instagram post URL: ")
        instagram_download(url)

    elif choice == "3":
        url = input("Enter TikTok URL: ")
        audio_only = input("Audio-only? (y/n) [default n]: ") == "y"
        tiktok_download(url, audio_only)

    elif choice == "4":
        file_path = input("Enter path to text file with URLs: ")
        batch_download(file_path)

    elif choice == "5":
        url = input("Enter channel/playlist URL: ")
        platform = input("Platform (youtube/instagram/tiktok): ")
        schedule_daily(url, platform)

    else:
        print("❌ Invalid choice!")

if __name__ == "__main__":
    main()
