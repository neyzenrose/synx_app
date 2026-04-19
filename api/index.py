import os
import json
import subprocess
import random
import requests
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
                'player_client': ['tv', 'mweb', 'android', 'ios'],
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

    # Step 1: Try local download (yt-dlp)
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
        error_str = str(e)
        print(f"Local Engine Error: {error_str}")
        
        # STEP 2: EMERGENCY FALLBACK - STAGE A (Cobalt API)
        try:
            print("Trying Bypass Stage A (Cobalt)...")
            external_api = "https://api.cobalt.tools/api/json"
            headers = { "Accept": "application/json", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0" }
            payload = { "url": url, "vQuality": "1080" if quality == "best" else quality, "isAudioOnly": (format_type == "mp3") }
            
            resp = requests.post(external_api, json=payload, headers=headers, timeout=12)
            ext_result = resp.json()
            
            if ext_result.get("status") in ["stream", "redirect"]:
                return jsonify({
                    'status': 'success',
                    'title': ext_result.get("text", "Video (Synced)"),
                    'download_url': ext_result.get("url"),
                    'message': 'Bypassed successfully'
                })
        except Exception as stage_a_err:
            print(f"Stage A Failed: {stage_a_err}")
            
        # STEP 3: EMERGENCY FALLBACK - STAGE B (Invidious API / Direct Download)
        try:
            print("Trying Bypass Stage B (Invidious)...")
            # Extract video ID
            import re
            video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
            if video_id_match:
                video_id = video_id_match.group(1)
                # We use a known working public instance
                inv_url = f"https://invidious.snopyta.org/api/v1/videos/{video_id}"
                inv_resp = requests.get(inv_url, timeout=10).json()
                formats = inv_resp.get("formatStreams", [])
                if formats:
                    best_stream = formats[0].get("url") # Usually the first one is best
                    return jsonify({
                        'status': 'success',
                        'title': inv_resp.get("title", "Video (Bypass)"),
                        'download_url': best_stream,
                        'message': 'Bypassed via Invidious'
                    })
        except Exception as stage_b_err:
            print(f"Stage B Failed: {stage_b_err}")
        
        # FINAL ATTEMPT: Return a more helpful error
        return jsonify({
            'status': 'error', 
            'message': "All engines are currently blocked by YouTube security. We are working on a fix. Please try again in a few minutes.",
            'debug': error_str
        }), 500

@app.route('/files/<path:filename>')
def serve_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename)

if __name__ == '__main__':
    app.run(port=5000)
