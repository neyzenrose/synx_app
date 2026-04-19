import os
import json
import subprocess
import random
import requests
import re
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import yt_dlp

app = Flask(__name__, template_folder='templates')
CORS(app)

# Use /tmp for everything in Vercel
DOWNLOAD_DIR = '/tmp'

def ensure_ffmpeg():
    """Check if ffmpeg is available."""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return 'ffmpeg'
    except:
        try:
            import static_ffmpeg
            static_ffmpeg.add_paths()
            return 'ffmpeg'
        except:
            return None

def get_ydl_opts(format_type, quality, proxy):
    USER_AGENTS = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/124.0.6367.88 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    ]
    
    ffmpeg_bin = ensure_ffmpeg()
    
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'user_agent': random.choice(USER_AGENTS),
        'proxy': proxy if proxy else None,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios'],
                'skip': ['hls', 'dash']
            }
        },
    }

    if ffmpeg_bin:
        ydl_opts['ffmpeg_location'] = ffmpeg_bin
        if format_type in ['mp3', 'wav', 'aac']:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format_type,
                'preferredquality': '192',
            }]
        else:
            ydl_opts['format'] = f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]/best'
            ydl_opts['merge_output_format'] = 'mp4'
    else:
        ydl_opts['format'] = 'best'
    
    return ydl_opts

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/app')
@app.route('/app.html')
def app_page():
    return render_template('app.html')

@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    format_type = data.get('format', 'mp4')
    quality = data.get('quality', 'best')
    PROXY_URL = os.environ.get('PROXY_URL')

    # Link Normalization
    vid_id = None
    if "youtu.be" in url:
        vid_id = url.split("/")[-1].split("?")[0]
    elif "v=" in url:
        vid_id = url.split("v=")[1].split("&")[0]

    # STRATEGY 2024: INSTANT BYPASS FOR YOUTUBE ON CLOUD
    if "youtube.com" in url or "youtu.be" in url:
        if vid_id:
            # These APIs bypass YouTube's BotGuard by acting as proxies
            return jsonify({
                'status': 'success',
                'title': 'Video Ready (Synx Ultra Bypass)',
                'download_url': f"https://api.vevioz.com/api/button/videos/{vid_id}",
                'message': 'Connected to High-Speed Download Engine'
            })

    # DEFAULT ENGINE: For Instagram, TikTok, etc.
    try:
        ydl_opts = get_ydl_opts(format_type, quality, PROXY_URL)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return jsonify({
                "status": "success",
                "title": info.get('title', 'Video'),
                "download_url": f"/files/{os.path.basename(filename)}"
            })
    except Exception as e:
        # Final fallback if even the direct bypass logic didn't catch it
        return jsonify({
            'status': 'error', 
            'message': "This link is currently restricted. Please try another link or download our mobile app for unlimited access.",
            'debug': str(e)
        }), 500

@app.route('/files/<path:filename>')
def serve_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename)

if __name__ == '__main__':
    app.run(port=5000)
