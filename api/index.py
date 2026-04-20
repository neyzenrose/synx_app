import os
from flask import Flask, render_template, request, jsonify, Response
import yt_dlp
import requests

app = Flask(__name__)

# SYX Independent Proxy Engine
PROXY_URL = "http://8pqu8nrvp4760s8:pndg6nphvup6nd9@p.webshare.io:80"

# SYX Independent Proxy Engine
PROXY_URL = "http://8pqu8nrvp4760s8:pndg6nphvup6nd9@p.webshare.io:80"

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
    req_quality = data.get('quality', 'best')

    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    try:
        # VPS optimized format selection
        if req_quality == 'best':
            format_str = f'bestvideo[ext={req_format}]+bestaudio/best'
        elif req_format in ['mp3', 'm4a', 'wav']:
            format_str = 'bestaudio/best'
        else:
            format_str = f'bestvideo[height<={req_quality}][ext={req_format}]+bestaudio/best/best'

        ydl_opts = {
            'proxy': PROXY_URL,
            'quiet': True,
            'format': format_str,
            'skip_download': True,
            'nocheckcertificate': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            # Find the direct link
            direct_url = info.get('url')
            if not direct_url:
                for f in reversed(formats):
                    if f.get('url'):
                        direct_url = f.get('url')
                        break

            if direct_url:
                # Independent Proxy: No more redirects to 3rd party sites!
                filename = f"synx_{info.get('id', 'video')}.{req_format}"
                proxy_url = f"/api/proxy?url={requests.utils.quote(direct_url)}&filename={requests.utils.quote(filename)}"
                
                return jsonify({
                    'status': 'success',
                    'title': info.get('title', 'Video Ready'),
                    'download_url': proxy_url,
                    'message': f'Synx High-Speed Proxy: {req_quality}p'
                })
            else:
                raise Exception("Could not extract media link.")

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/proxy')
def proxy():
    # Force 'Save As' by streaming through our independent server
    target_url = request.args.get('url')
    filename = request.args.get('filename', 'video.mp4')
    
    if not target_url:
        return "No direct link provided", 400
    
    try:
        # Yetkilendirilmiş proxy üzerinden akıtıyoruz
        req = requests.get(target_url, stream=True, proxies={'http': PROXY_URL, 'https': PROXY_URL}, timeout=60)
        
        def generate():
            for chunk in req.iter_content(chunk_size=1024*1024):
                if chunk:
                    yield chunk

        response = Response(generate(), content_type=req.headers.get('content-type'))
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True)
