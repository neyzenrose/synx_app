import os
import urllib.parse
from flask import Flask, render_template, request, jsonify, Response
import requests

app = Flask(__name__)

# ENGINE ENDPOINTS
LOCAL_COBALT = "http://127.0.0.1:3000"
FALLBACK_1 = "https://api.cobalt.tools"
FALLBACK_2 = "https://cobalt.api.unblocker.xyz"

@app.route('/')
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
    req_format = data.get('format', 'mp4')
    if not url: return jsonify({"error": "No URL"}), 400
    
    endpoints = [LOCAL_COBALT, FALLBACK_1, FALLBACK_2]
    for api in endpoints:
        try:
            return process_with_engine(url, req_format, api)
        except Exception as e:
            print(f"Engine {api} failed: {e}")
            continue
    return jsonify({"status": "error", "message": "YouTube security block. Try again in minutes."}), 500

def process_with_engine(url, req_format, api_endpoint):
    payload = {
        "url": url,
        "videoQuality": "1080",
        "audioFormat": "mp3",
        "downloadMode": "audio" if req_format in ['mp3', 'm4a', 'wav'] else "auto"
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Origin": "https://cobalt.tools",
        "Referer": "https://cobalt.tools/"
    }
    response = requests.post(api_endpoint, json=payload, headers=headers, timeout=40)
    if response.status_code != 200: raise Exception("Status error")
    result = response.json()
    if result.get('status') == 'error': raise Exception(result.get('text'))
    if result.get('url'):
        s_url = urllib.parse.quote(result.get('url'))
        s_file = urllib.parse.quote(f"synx_media.{req_format}")
        return jsonify({
            'status': 'success',
            'title': 'Media Ready',
            'download_url': f"/api/proxy?url={s_url}&filename={s_file}"
        })
    raise Exception("No URL")

@app.route('/api/proxy')
def proxy():
    target_url = request.args.get('url')
    filename = request.args.get('filename', 'video.mp4')
    if not target_url: return "No URL", 400
    try:
        req = requests.get(target_url, stream=True, timeout=300)
        def generate():
            for chunk in req.iter_content(chunk_size=1024*1024):
                if chunk: yield chunk
        response = Response(generate(), content_type=req.headers.get('content-type'))
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e: return str(e), 500

if __name__ == '__main__':
    app.run(debug=True)
