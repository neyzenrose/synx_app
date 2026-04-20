import os
from flask import Flask, render_template, request, jsonify, Response
import requests

app = Flask(__name__)

# LOCAL ENGINE
COBALT_API = "http://127.0.0.1:3000"

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
    
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    # Strategy 1: Local Cobalt (Fastest)
    try:
        return process_with_cobalt(url, req_format, COBALT_API)
    except Exception as e:
        print(f"Local Cobalt failed: {e}")
        
    # Strategy 2: Global Fallback (Reliable)
    # If our server is blocked, we use an external trusted extractor
    try:
        # Using a reliable public extraction helper
        external_api = "https://api.cobalt.tools" 
        return process_with_cobalt(url, req_format, external_api)
    except Exception as e:
        print(f"Global Fallback failed: {e}")

    return jsonify({"status": "error", "message": "All extraction methods failed. YouTube is being extremely difficult today. Please try again later."}), 500

def process_with_cobalt(url, req_format, api_endpoint):
    payload = {
        "url": url,
        "videoQuality": "1080",
        "audioFormat": "mp3",
        "downloadMode": "audio" if req_format in ['mp3', 'm4a', 'wav'] else "auto",
        "filenameStyle": "pretty"
    }
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    response = requests.post(api_endpoint, json=payload, headers=headers, timeout=30)
    result = response.json()
    
    if result.get('status') == 'error':
        raise Exception(result.get('text', 'API Error'))
        
    if result.get('url'):
        direct_url = result.get('url')
        filename = f"synx_download.{req_format}"
        # Still using our local proxy to hide the source and force download
        proxy_url = f"/api/proxy?url={requests.utils.quote(direct_url)}&filename={requests.utils.quote(filename)}"
        
        return jsonify({
            'status': 'success',
            'title': 'Media Ready',
            'download_url': proxy_url,
            'message': 'Synx Smart-Engine Active'
        })
    else:
        raise Exception("No URL in response")

@app.route('/api/proxy')
def proxy():
    target_url = request.args.get('url')
    filename = request.args.get('filename', 'video.mp4')
    if not target_url: return "No URL", 400
    
    try:
        # Stream through our VPS to provide clean "Save As" experience
        req = requests.get(target_url, stream=True, timeout=180)
        def generate():
            for chunk in req.iter_content(chunk_size=1024*1024):
                if chunk: yield chunk
        response = Response(generate(), content_type=req.headers.get('content-type'))
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True)
