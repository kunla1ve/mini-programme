# -*- coding: utf-8 -*-
"""
Created on Fri May  9 15:10:22 2025

@author: kunla1ve
"""

import yt_dlp
import os

def download_playlist_first_n_videos(url, n=1, output_path=None):
    if output_path is None:
        output_path = os.path.join(os.path.expanduser('~'), 'Downloads')
    os.makedirs(output_path, exist_ok=True)

    # 下载视频（无音频）
    video_opts = {
        'format': 'bestvideo[height=1080][ext=mp4]',
        'outtmpl': f'{output_path}/%(playlist_index)s_%(title)s_video.%(ext)s',
        'playlistend': n,  # 限制只下载前 n 个视频
        'ignoreerrors': True,  # 跳过错误视频
    }
    
    # 下载音频（无视频）
    audio_opts = {
        'format': 'bestaudio[ext=m4a]',
        'outtmpl': f'{output_path}/%(playlist_index)s_%(title)s_audio.%(ext)s',
        'playlistend': n,  # 限制只下载前 n 个音频
        'ignoreerrors': True,
    }
    
    try:
        print(f"正在下载前 {n} 个视频...")
        with yt_dlp.YoutubeDL(video_opts) as ydl:
            ydl.download([url])  # 直接下载，不提取信息（避免额外请求）
        
        print(f"正在下载前 {n} 个音频...")
        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            ydl.download([url])
        
        print(f"✅ 前 {n} 个视频下载完成！路径：{output_path}")
    except Exception as e:
        print(f"❌ 下载失败: {e}")

# 示例（下载播放列表前 6 个视频）
playlist_url = "https://www.youtube.com/playlist?list=PLilKLKW6-ssjSl1PCuyTymFWQJwT_jmua"
download_playlist_first_n_videos(playlist_url, n=9)




# import yt_dlp
# import os

# def download_playlist_first_n_videos(url, n=1, output_path=None):
#     """下载 YouTube 播放列表的前 N 个视频（MP4 格式）"""
#     if output_path is None:
#         output_path = os.path.join(os.path.expanduser('~'), 'Downloads')
#     os.makedirs(output_path, exist_ok=True)

#     ydl_opts = {
#         'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',  # 优先 MP4 格式
#         'outtmpl': f'{output_path}/%(playlist_index)s_%(title)s.%(ext)s',  # 文件名带序号
#         'playlistend': n,  # 限制下载前 N 个视频
#         'quiet': False,    # 显示进度信息
#         'ignoreerrors': True,  # 跳过错误视频
#     }
    
#     try:
#         print(f"正在下载前 {n} 个视频...")
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             info = ydl.extract_info(url, download=True)
#             if '_type' in info and info['_type'] == 'playlist':
#                 print(f"✅ 前 {n} 个视频下载完成！路径：{output_path}")
#             else:
#                 print(f"✅ 单个视频下载完成: {info['title']}")
#     except Exception as e:
#         print(f"❌ 下载失败: {e}")

# # 示例（下载播放列表前 6 个视频）
# playlist_url = "https://www.youtube.com/playlist?list=PLilKLKW6-ssjSl1PCuyTymFWQJwT_jmua"
# download_playlist_first_n_videos(playlist_url, n=9)

