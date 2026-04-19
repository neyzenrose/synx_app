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
    
    vid_id = None
    if "youtu.be" in url: vid_id = url.split("/")[-1]
    elif "v=" in url: vid_id = url.split("v=")[1].split("&")[0]

    # INSTANT BYPASS CHANNEL (1-Second Response Time)
    if vid_id:
         return jsonify({
            'status': 'success',
            'title': 'Download Ready (Synx Ultra-Boost)',
            'download_url': f"https://vevioz.com/api/button/videos/{vid_id}",
            'message': 'Instant Bypass Powered by Synx.'
        })

    # Rest of logic...
            
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
