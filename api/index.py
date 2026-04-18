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
    
    video_formats = ['mp4', 'webm', 'mkv', 'mov', 'avi']
    audio_formats = ['mp3', 'm4a', 'wav', 'flac', 'ogg', 'aac']

    # Configure yt-dlp options
    ffmpeg_bin = ensure_ffmpeg()
    
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'add_header': [
            'Accept-Language: en-US,en;q=0.9',
            'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Sec-Fetch-Mode: navigate',
            'Sec-Fetch-Dest: document',
            'Sec-Fetch-Site: none',
        ],
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios'],
                'skip': ['webpage', 'hls'],
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
        # Fallback if FFmpeg is not available: download best single file
        ydl_opts['format'] = 'best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # If we asked for mp3 but ffmpeg was missing, the ext might still be video
            # or the user gets the best audio-only file available without conversion.
            
            return jsonify({
                "status": "success",
                "title": info.get('title', 'Video'),
                "filename": os.path.basename(filename),
                "download_url": f"/files/{os.path.basename(filename)}"
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/files/<path:filename>')
def serve_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename)

if __name__ == '__main__':
    # Run server locally for testing
    app.run(port=5000, debug=True)
