import os
import json
import yt_dlp
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__, template_folder='templates')
CORS(app)

# YOUR RESIDENTIAL PROXY - OUR ONLY OUTSIDE TOOL
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
    
    # INDEPENDENT ENGINE: Using only Synx Proxy and yt-dlp library
    # No 3rd party APIs, no ad-supported redirectors.
    try:
        ydl_opts = {
            'proxy': PROXY_URL,
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'format': 'best', # We grab the best ready-to-download format
            'skip_download': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Step 1: Extract info directly on our server using your proxy
            info = ydl.extract_info(url, download=False)
            
            # Step 2: Find the direct download URL
            formats = info.get('formats', [])
            # Look for a direct video link that is usually hosted on googlevideo.com
            direct_url = None
            
            # We filter for a stable format (usually mp4 with audio included)
            for f in formats:
                if f.get('acodec') != 'none' and f.get('vcodec') != 'none' and f.get('ext') == 'mp4':
                    direct_url = f.get('url')
                    break
            
            if not direct_url and formats:
                direct_url = formats[-1].get('url') # Fallback to last format if needed

            if direct_url:
                return jsonify({
                    'status': 'success',
                    'title': info.get('title', 'Video Ready'),
                    'download_url': direct_url,
                    'message': 'Synx In-House Engine Activated.'
                })
            else:
                raise Exception("Could not find a direct download link.")

    except Exception as e:
        # If YouTube blocks us even with our proxy, we let the user know cleanly.
        return jsonify({
            'status': 'error', 
            'message': 'The video link is temporarily restricted by the source platform. Our engine is working to bypass this.'
        }), 500

if __name__ == '__main__':
    app.run(port=5000)
