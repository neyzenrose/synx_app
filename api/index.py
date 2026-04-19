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
        # STEP 2: EMERGENCY FALLBACK (Using external engine if blocked)
        if "Sign in" in error_str or "unsupported" in error_str or "403" in error_str:
            try:
                external_api = "https://api.cobalt.tools/api/json"
                headers = { "Accept": "application/json", "Content-Type": "application/json" }
                payload = { "url": url, "vQuality": quality, "isAudioOnly": (format_type == "mp3") }
                
                resp = requests.post(external_api, json=payload, headers=headers, timeout=10)
                ext_result = resp.json()
                
                if ext_result.get("status") in ["stream", "redirect"]:
                    return jsonify({
                        'status': 'success',
                        'title': ext_result.get("text", "Video"),
                        'download_url': ext_result.get("url"),
                        'message': 'Bypassed via Synx Engine'
                    })
            except Exception as inner_e:
                print(f"Fallback failed: {inner_e}")
        
        return jsonify({'status': 'error', 'message': error_str}), 500

@app.route('/files/<path:filename>')
def serve_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename)

if __name__ == '__main__':
    app.run(port=5000)
