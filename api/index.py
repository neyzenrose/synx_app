import os
from flask import Flask, render_template, request, jsonify, Response
import requests

app = Flask(__name__)

# COBALT EXTERNAL ENGINE (Independent & Powerful)
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
    
    try:
        # Precise payload for Cobalt 11
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
        
        print(f"DEBUG: Connecting to Cobalt at {COBALT_API} with URL {url}")
        
        # INCREASE TIMEOUT for server-side processing
        response = requests.post(COBALT_API, json=payload, headers=headers, timeout=60)
        
        # DEBUG LOGGING
        print(f"DEBUG: Cobalt Status Body: {response.text}")
        
        if response.status_code != 200:
            return jsonify({"status": "error", "message": f"Engine Status {response.status_code}: {response.text[:100]}"}), 500

        result = response.json()
        
        if result.get('status') == 'error':
            return jsonify({"status": "error", "message": f"Engine Error: {result.get('text', 'Unknown')}"}), 500
            
        if result.get('url'):
            direct_url = result.get('url')
            filename = f"synx_download.{req_format}"
            proxy_url = f"/api/proxy?url={requests.utils.quote(direct_url)}&filename={requests.utils.quote(filename)}"
            
            return jsonify({
                'status': 'success',
                'title': 'Media Ready',
                'download_url': proxy_url,
                'message': 'Synx Engine: Ready'
            })
        else:
            return jsonify({"status": "error", "message": f"Engine Response: {str(result)[:100]}"}), 500
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return jsonify({"status": "error", "message": f"System Error: {str(e)}"}), 500

@app.route('/api/proxy')
def proxy():
    target_url = request.args.get('url')
    filename = request.args.get('filename', 'video.mp4')
    if not target_url: return "No URL", 400
    
    try:
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
