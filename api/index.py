import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import yt_dlp








app = Flask(__name__)
CORS(app) # Enable CORS for all routes








# Directory where downloads will be stored
# Note: In serverless (Vercel), only /tmp is writable
DOWNLOAD_DIR = '/tmp/downloads'
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)















@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    # Route for serving static files from the root
    if path.startswith('api/'):
        return "Not Found", 404
    target = path if path else 'index.html'
    return send_from_directory('.', target)

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
