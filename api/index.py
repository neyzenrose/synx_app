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
    req_format = data.get('format', 'mp4') # Cobalt uses 'audio' or 'video' usually
    
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    try:
        # Connect to your own independent Cobalt engine
        payload = {
            "url": url,
            "videoQuality": "1080",
            "downloadMode": "audio" if req_format in ['mp3', 'm4a', 'wav'] else "video",
            "filenameStyle": "pretty"
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": COBALT_API,
            "Referer": COBALT_API + "/"
        }
        
        print(f"Requesting Cobalt: {url}")
        response = requests.post(COBALT_API, json=payload, headers=headers, timeout=30)
        result = response.json()
        
        if result.get('status') == 'error':
            raise Exception(result.get('text', 'Cobalt error'))
            
        if result.get('url'):
            # Double Proxy layers for maximum independence
            direct_url = result.get('url')
            filename = f"synx_download.{req_format}"
            proxy_url = f"/api/proxy?url={requests.utils.quote(direct_url)}&filename={requests.utils.quote(filename)}"
            
            return jsonify({
                'status': 'success',
                'title': 'Media Ready',
                'download_url': proxy_url,
                'message': 'Synx Cobalt-Engine: High-Speed'
            })
        else:
            raise Exception("No download link returned by engine.")
            
    except Exception as e:
        print(f"Cobalt Error: {e}")
        return jsonify({"status": "error", "message": f"Engine Error: {str(e)}"}), 500

@app.route('/api/proxy')
def proxy():
    target_url = request.args.get('url')
    filename = request.args.get('filename', 'video.mp4')
    if not target_url: return "No URL", 400
    
    try:
        # Proxy through our independent server
        req = requests.get(target_url, stream=True, timeout=120)
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
