import os
import json
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = '/tmp/downloads'
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@app.route('/')
@app.route('/index.html')
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
    if not url: return jsonify({"error": "No URL"}), 400
    format_type = data.get('format', 'mp4')
    quality = data.get('quality', 'best')
    ydl_opts = {'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s', 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return jsonify({"status": "success", "title": info.get('title'), "filename": os.path.basename(filename), "download_url": f"/files/{os.path.basename(filename)}"})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/files/<path:filename>')
def serve_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
