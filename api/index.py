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

# PROXY CONFIGURATION
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
    
    vid_id = None
    if "youtu.be" in url:
        vid_id = url.split("/")[-1].split("?")[0]
    elif "v=" in url:
        vid_id = url.split("v=")[1].split("&")[0]

    # STABLE BYPASS STRATEGY (Consistent across Canada/USA/Safari)
    if vid_id:
         return jsonify({
            'status': 'success',
            'title': 'Media Prepared',
            'download_url': f"https://loader.to/api/card/?url=https://www.youtube.com/watch?v={vid_id}",
            'message': 'Synx Engine: Ready for download.'
        })

    # Default logic for other platforms using Residential Proxy
    try:
        ydl_opts = {'proxy': PROXY_URL, 'quiet': True, 'nocheckcertificate': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "status": "success",
                "title": info.get('title', 'Media'),
                "download_url": info.get('url'),
                "message": "Direct link extracted."
            })
    except Exception as e:
        return jsonify({'status': 'error', 'message': "Please try a different link or platform."}), 500

if __name__ == '__main__':
    app.run(port=5000)
