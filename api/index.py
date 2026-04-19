import os
import json
import subprocess
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import yt_dlp

app = Flask(__name__, template_folder='templates')
CORS(app)

# Use /tmp for everything in Vercel
DOWNLOAD_DIR = '/tmp'
FFMPEG_PATH = '/tmp/ffmpeg'

def ensure_ffmpeg():
    """Check if ffmpeg is available, if not, try to use the one from static-ffmpeg or system."""
    try:
        # Check if already in path
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return 'ffmpeg'
    except:
        try:
            import static_ffmpeg
            static_ffmpeg.add_paths()
            return 'ffmpeg'
        except:
            return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/index.html')
def index_html():
    return render_template('index.html')

@app.route('/app')
def app_page():
    return render_template('app.html')

@app.route('/app.html')
def app_html():
    return render_template('app.html')

@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    format_type = data.get('format', 'mp4') # mp4 or mp3
    
    quality = data.get('quality', 'best')
    
    # Video and Audio Quality
    video_formats = ['mp4', 'webm', 'mkv', 'mov', 'avi']
    audio_formats = ['mp3', 'm4a', 'wav', 'flac', 'ogg', 'aac']

    # Professional User-Agents for rotation
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/124.0.6367.88 Mobile/15E148 Safari/604.1'
    ]
    import random

    # Configure Proxy (Optional - set via Env Var for security)
    PROXY_URL = os.environ.get('PROXY_URL') # Format: http://user:pass@host:port

    # Configure yt-dlp options
    ffmpeg_bin = ensure_ffmpeg()
    
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'user_agent': random.choice(USER_AGENTS),
        'proxy': PROXY_URL if PROXY_URL else None,
        'add_header': [
            'Accept-Language: en-US,en;q=0.9',
            'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        ],
        'extractor_args': {
            'youtube': {
                'player_client': ['tv', 'mweb', 'android', 'ios'],
            }
        },
    }

    if ffmpeg_bin:
        ydl_opts['ffmpeg_location'] = ffmpeg_bin
        if format_type in audio_formats:
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

@app.route('/index.html')
def index_html():
    return render_template('index.html')

@app.route('/app')
def app_page():
    return render_template('app.html')

@app.route('/app.html')
def app_html():
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
                "filename": os.path.basename(filename),
                "download_url": f"/files/{os.path.basename(filename)}"
            })
    except Exception as e:
        error_str = str(e)
        if "Sign in to confirm you're not a bot" in error_str or "HTTP Error 403" in error_str:
            # STEP 2: EMERGENCY FALLBACK (Using a robust external engine)
            print("Local engine blocked. Switching to Emergency Bypass...")
            try:
                external_api = "https://api.cobalt.tools/api/json"
                headers = { "Accept": "application/json", "Content-Type": "application/json" }
                payload = { "url": url, "vQuality": quality, "isAudioOnly": (format_type == "mp3") }
                
                resp = requests.post(external_api, json=payload, headers=headers)
                ext_result = resp.json()
                
                if ext_result.get("status") == "stream" or ext_result.get("status") == "redirect":
                    return jsonify({
                        'status': 'success',
                        'title': ext_result.get("text", "Video"),
                        'download_url': ext_result.get("url"),
                        'message': 'Downloaded via Synx Ultra Bypass'
                    })
            except:
                pass
        
        # If everything fails
        return jsonify({'status': 'error', 'message': error_str}), 500

@app.route('/files/<path:filename>')
def serve_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename)

if __name__ == '__main__':
    # Run server locally for testing
    app.run(port=5000, debug=True)
