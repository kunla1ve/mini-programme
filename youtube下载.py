# -*- coding: utf-8 -*-
"""
Created on Fri Jul 11 01:00:36 2025

@author: kunlave
"""


import yt_dlp
import os

def download_playlist_videos(
    playlist_url: str,
    start: int = 1,
    end: int = None,
    output_path: str = None,
) -> None:
    """
    下载YouTube播放列表中的视频（默认分辨率）
    
    :param playlist_url: 播放列表URL
    :param start: 开始下载的视频序号（从1开始）
    :param end: 结束下载的视频序号（包含），None表示下载到列表末尾
    :param output_path: 输出目录，None表示用户下载目录
    """
    if output_path is None:
        output_path = os.path.join(os.path.expanduser('~'), 'Downloads')
    os.makedirs(output_path, exist_ok=True)
    
    ydl_opts = {
        'format': 'best',  # 选择最佳质量的单个视频文件（含音频）
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'playliststart': start,
        'playlistend': end,
        'ignoreerrors': True,  # 忽略错误继续下载
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([playlist_url])

# 示例用法
playlist_url = "https://www.youtube.com/watch?v=o7zZOCuxUrs"
download_playlist_videos(
    playlist_url,
    start=1,
    end=1,
    output_path=None,
)




# import yt_dlp
# import os

# def download_playlist_videos(
#     url,
#     start=1,
#     end=1,
#     video_resolution="1080p",
#     audio_format="m4a",
#     output_path=None,
#     download_video=True,
#     download_audio=True
# ):
#     """
#     下载YouTube播放列表中指定范围的视频和音频
    
#     参数:
#         url: 播放列表URL
#         start: 开始下载的位置（从1开始）
#         end: 结束下载的位置
#         video_resolution: 视频分辨率 ('144p', '240p', '360p', '480p', '720p', '1080p', '1440p', '2160p')
#         audio_format: 音频格式 ('m4a', 'mp3', 'opus', 'wav')
#         output_path: 输出目录路径 (默认为用户下载目录)
#         download_video: 是否下载视频
#         download_audio: 是否下载音频
#     """
#     if output_path is None:
#         output_path = os.path.join(os.path.expanduser('~'), 'Downloads')
#     os.makedirs(output_path, exist_ok=True)
    
#     # 验证分辨率
#     resolutions = ['144p', '240p', '360p', '480p', '720p', '1080p', '1440p', '2160p']
#     if video_resolution not in resolutions:
#         print(f"⚠️ 警告: 不支持的分辨率 '{video_resolution}'，将使用1080p")
#         video_resolution = '1080p'
    
#     # 验证音频格式
#     audio_formats = ['m4a', 'mp3', 'opus', 'wav']
#     if audio_format not in audio_formats:
#         print(f"⚠️ 警告: 不支持的音频格式 '{audio_format}'，将使用m4a")
#         audio_format = 'm4a'
    
#     # 视频下载选项
#     video_opts = {
#         'format': f'bestvideo[height<={video_resolution[:-1]}][ext=mp4]',
#         'outtmpl': f'{output_path}/%(playlist_index)s_%(title)s_video.%(ext)s',
#         'playliststart': start,
#         'playlistend': end,
#         'ignoreerrors': True,
#     }
    
#     # 音频下载选项
#     audio_opts = {
#         'format': f'bestaudio[ext={audio_format}]',
#         'outtmpl': f'{output_path}/%(playlist_index)s_%(title)s_audio.%(ext)s',
#         'playliststart': start,
#         'playlistend': end,
#         'ignoreerrors': True,
#     }
    
#     try:
#         if download_video:
#             print(f"正在下载第 {start} 到 {end} 个视频 (分辨率: {video_resolution})...")
#             with yt_dlp.YoutubeDL(video_opts) as ydl:
#                 ydl.download([url])
        
#         if download_audio:
#             print(f"正在下载第 {start} 到 {end} 个音频 (格式: {audio_format})...")
#             with yt_dlp.YoutubeDL(audio_opts) as ydl:
#                 ydl.download([url])
        
#         print(f"✅ 下载完成！路径：{output_path}")
#     except Exception as e:
#         print(f"❌ 下载失败: {e}")

# playlist_url = "https://www.youtube.com/watch?v=4DJQq3GvyCEa"
# download_playlist_videos(
#     playlist_url,
#     start=1,
#     end=1,
#     video_resolution="1080p",
#     audio_format="m4a",
#     output_path=None,
#     download_video=True,
#     download_audio=True
# )
