import os
from flask import Flask, render_template, request, jsonify, Response
import yt_dlp
import requests

app = Flask(__name__)

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
    
    # Try with Proxy first, then fallback to Direct
    try:
        return process_request(url, req_format, req_quality, use_proxy=True)
    except Exception as e:
        print(f"Proxy failed, falling back to direct: {e}")
        try:
            return process_request(url, req_format, req_quality, use_proxy=False)
        except Exception as e2:
            return jsonify({"status": "error", "message": str(e2)}), 500

def process_request(url, req_format, req_quality, use_proxy=True):
    # VPS optimized format selection
    if req_quality == 'best':
        format_str = f'bestvideo[ext={req_format}]+bestaudio/best'
    elif req_format in ['mp3', 'm4a', 'wav']:
        format_str = 'bestaudio/best'
    else:
        format_str = f'bestvideo[height<={req_quality}][ext={req_format}]+bestaudio/best/best'

    ydl_opts = {
        'quiet': True,
        'format': format_str,
        'skip_download': True,
        'nocheckcertificate': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android'],
                'player_skip': ['webpage', 'configs']
            }
        },
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1'
    }
    
    if use_proxy:
        ydl_opts['proxy'] = PROXY_URL
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])
        
        direct_url = info.get('url')
        if not direct_url:
            for f in reversed(formats):
                if f.get('url'):
                    direct_url = f.get('url')
                    break

        if direct_url:
            filename = f"synx_{info.get('id', 'video')}.{req_format}"
            proxy_url = f"/api/proxy?url={requests.utils.quote(direct_url)}&filename={requests.utils.quote(filename)}&use_proxy={'1' if use_proxy else '0'}"
            
            return jsonify({
                'status': 'success',
                'title': info.get('title', 'Video Ready'),
                'download_url': proxy_url,
                'message': f'Synx High-Speed ({ "Proxy" if use_proxy else "Direct" }): {req_quality}p'
            })
        else:
            raise Exception("Could not extract media link.")

@app.route('/api/proxy')
def proxy():
    target_url = request.args.get('url')
    filename = request.args.get('filename', 'video.mp4')
    use_proxy = request.args.get('use_proxy') == '1'
    
    if not target_url:
        return "No direct link provided", 400
    
    try:
        proxy_opts = {'http': PROXY_URL, 'https': PROXY_URL} if use_proxy else None
        req = requests.get(target_url, stream=True, proxies=proxy_opts, timeout=120)
        
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
