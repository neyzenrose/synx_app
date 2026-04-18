import os
import json
from flask import Flask, request, jsonify, send_from_directory
import yt_dlp

app = Flask(__name__)

# Directory where downloads will be stored
DOWNLOAD_DIR = 'downloads'
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

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
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'quiet': True,
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
