import os
import urllib.parse
from flask import Flask, render_template, request, jsonify, Response
import requests

app = Flask(__name__)

# STRONGEST ENGINE FIRST
ENDPOINTS = [
    "https://cobalt.api.unblocker.xyz",
    "https://api.cobalt.tools",
    "http://127.0.0.1:3000"
]

@app.route('/')
def index(): return render_template('index.html')

@app.route('/app')
@app.route('/app.html')
@app.route('/ultra')
@app.route('/ultra.html')
def app_page(): return render_template('ultra.html')

@app.route('/api/download', methods=['POST'])
def download():
    try:
        data = request.json
        if not data: return jsonify({"status":"error","message":"No data"}), 400
        url = data.get('url')
        req_format = data.get('format', 'mp4')
        
        if not url: return jsonify({"status":"error","message":"No URL provided"}), 400

        for api in ENDPOINTS:
            try:
                res = process_with_engine(url, req_format, api)
                if res: return res
            except Exception as e:
                print(f"DEBUG: {api} failed -> {str(e)}")
                continue

        return jsonify({"status": "error", "message": "All engines are busy. Please try another video or try again in 1 minute."}), 503
    except Exception as ge:
        return jsonify({"status": "error", "message": str(ge)}), 500

def process_with_engine(url, req_format, api_endpoint):
    payload = {
        "url": url,
        "videoQuality": "720", # Lower quality for better success rate during high load
        "audioFormat": "mp3",
        "downloadMode": "audio" if req_format in ['mp3', 'm4a', 'wav'] else "auto"
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # 20 second timeout is safer for VPS memory
    response = requests.post(api_endpoint, json=payload, headers=headers, timeout=20)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('url'):
            base_url = request.url_root.rstrip('/')
            s_url = urllib.parse.quote(result.get('url'))
            s_file = urllib.parse.quote(f"synx_media.{req_format}")
            return jsonify({
                'status': 'success',
                'title': 'Download Ready',
                'download_url': f"{base_url}/api/proxy?url={s_url}&filename={s_file}"
            })
    return None

@app.route('/api/proxy')
def proxy():
    target_url = request.args.get('url')
    filename = request.args.get('filename', 'video.mp4')
    if not target_url: return "No URL", 400
    try:
        req = requests.get(target_url, stream=True, timeout=120)
        def generate():
            for chunk in req.iter_content(chunk_size=65536): # Smaller chunks for low RAM VPS
                if chunk: yield chunk
        response = Response(generate(), content_type=req.headers.get('content-type'))
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e: return str(e), 500

if __name__ == '__main__':
    app.run()
