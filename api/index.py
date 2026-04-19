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
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/124.0.6367.88 Mobile/15E148 Safari/604.1'
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
                'player_client': ['android', 'ios', 'tv', 'mweb'],
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
                'preferredquality': quality if quality in ['128', '256', '320'] else '192',
            }]
        else:
            if quality == 'best':
                ydl_opts['format'] = f'bestvideo[ext={format_type}]+bestaudio[ext=m4a]/best[ext={format_type}]/best'
            else:
                ydl_opts['format'] = f'bestvideo[height<={quality}][ext={format_type}]+bestaudio[ext=m4a]/best[height<={quality}][ext={format_type}]/best'
            ydl_opts['merge_output_format'] = format_type
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

    # Step 0: INSTANT BYPASS FOR YOUTUBE (Vercel IP is heavily blocked)
    if vid_id or "youtube.com" in url or "youtu.be" in url:
        print(f"Instant Bypass triggered for YouTube: {vid_id}")
        return jsonify({
            'status': 'success',
            'title': 'Video Ready for Download',
            'download_url': f"https://api.vevioz.com/api/button/videos/{vid_id}" if vid_id else f"https://api.cobalt.tools/api/json?url={url}",
            'message': 'Fast Bypass Activated'
        })

    # Step 1: Try local download (for other platforms like Instagram/TikTok)
    try:
        ydl_opts = get_ydl_opts(format_type, quality, PROXY_URL)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ... (rest of local logic)
        
        # STEP 2: EMERGENCY FALLBACK - STAGE A (Vevioz API)
        if vid_id:
            try:
                # Direct Stream API Fallback
                return jsonify({
                    'status': 'success',
                    'title': 'Video Ready (Bypass)',
                    'download_url': f"https://api.vevioz.com/api/button/videos/{vid_id}",
                    'message': 'Bypassed via Synx Engine'
                })
            except:
                pass

        # STEP 3: EMERGENCY FALLBACK - STAGE B (Cobalt API)
        try:
            external_api = "https://api.cobalt.tools/api/json"
            headers = { "Accept": "application/json", "Content-Type": "application/json" }
            payload = { "url": url, "vQuality": "1080" if quality == "best" else "1080", "isAudioOnly": (format_type == "mp3") }
            resp = requests.post(external_api, json=payload, headers=headers, timeout=10)
            ext_result = resp.json()
            if ext_result.get("status") in ["stream", "redirect"]:
                return jsonify({
                    'status': 'success',
                    'title': ext_result.get("text", "Video"),
                    'download_url': ext_result.get("url")
                })
        except:
            pass
        
        return jsonify({'status': 'error', 'message': "YouTube security is currently very high. Please use the 'Download App' link for 100% success or try again in 5 minutes.", 'debug': error_str}), 500

@app.route('/files/<path:filename>')
def serve_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename)

if __name__ == '__main__':
    app.run(port=5000)
