import os
import json
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import yt_dlp

app = Flask(__name__, template_folder='templates')
CORS(app) # Enable CORS for all routes

# Directory where downloads will be stored
# Note: In serverless (Vercel), only /tmp is writable
DOWNLOAD_DIR = '/tmp/downloads'
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

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

    # Configure yt-dlp options with anti-bot measures
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.youtube.com/',
        'add_header': [
            'Accept-Language: en-US,en;q=0.9',
            'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        ],
    }

    if format_type in audio_formats:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format_type,
            'preferredquality': quality if quality in ['128', '256', '320'] else '192',
        }]
    else:
        # Video quality handling
        if quality == 'best':
            ydl_opts['format'] = f'bestvideo[ext={format_type}]+bestaudio[ext=m4a]/best[ext={format_type}]/best'
        else:
            ydl_opts['format'] = f'bestvideo[height<={quality}][ext={format_type}]+bestaudio[ext=m4a]/best[height<={quality}][ext={format_type}]/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if format_type == 'mp3':
                filename = filename.rsplit('.', 1)[0] + '.mp3'
            
            return jsonify({
                "status": "success",
                "title": info.get('title'),
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
