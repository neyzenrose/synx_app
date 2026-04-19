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
PROXY_URL = "http://snrkekxx-11:fcadsu23a4e1@p.webshare.io:80"

@app.route('/')
def index(): return render_template('index.html')

@app.route('/app')
@app.route('/app.html')
def app_page(): return render_template('app.html')

@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    if not url: return jsonify({"error": "No URL provided"}), 400
    
    format_type = data.get('format', 'mp4')
    quality = data.get('quality', 'best')

    # Instant Metadata Extraction with Proxy
    ydl_opts = {
        'proxy': PROXY_URL,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'ios'], 'skip': ['hls', 'dash']}},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # We DONT download, we just extract the best URL
            info = ydl.extract_info(url, download=False)
            
            # Find the best format URL based on user's choice
            formats = info.get('formats', [])
            best_url = None
            
            if format_type == 'mp3':
                # Find best audio only
                for f in reversed(formats):
                    if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                        best_url = f.get('url')
                        break
            else:
                # Find best video+audio combined or best video
                for f in reversed(formats):
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                        best_url = f.get('url')
                        break
            
            if not best_url:
                best_url = info.get('url') # Fallback to single link

            return jsonify({
                "status": "success",
                "title": info.get('title', 'Video'),
                "download_url": best_url,
                "message": "Link extracted successfully using Synx Proxy Engine"
            })
            
    except Exception as e:
        # Emergency Redirect Fallback (Cobalt/Vevioz)
        vid_id = None
        if "youtu.be" in url: vid_id = url.split("/")[-1]
        elif "v=" in url: vid_id = url.split("v=")[1].split("&")[0]
        
        if vid_id:
             return jsonify({
                'status': 'success',
                'title': 'Video Ready (Global Bypass)',
                'download_url': f"https://vevioz.com/api/button/videos/{vid_id}",
                'message': 'Switched to backup channel.'
            })
        
        return jsonify({'status': 'error', 'message': "System busy. Please try another link.", 'debug': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
