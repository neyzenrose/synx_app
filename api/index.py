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
    
    # Try multiple extraction strategies automatically
    # 1. IOS/Android (Mobile)
    # 2. TV (Non-bot client)
    # 3. Web Embedded (Browser client)
    strategies = [
        {'player_client': 'tv', 'player_skip': ['webpage']},
        {'player_client': 'ios,android'},
        {'player_client': 'web_embedded'}
    ]

    for strategy in strategies:
        try:
            return process_request(url, req_format, req_quality, strategy)
        except Exception as e:
            print(f"Strategy {strategy} failed: {e}")
            continue

    return jsonify({"status": "error", "message": "YouTube is strictly blocking the server. Try again in a few minutes or use a different URL."}), 500

def process_request(url, req_format, req_quality, strategy):
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
            'youtube': strategy
        },
        # Rotate user agents to avoid fingerprinting
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        direct_url = info.get('url')
        if not direct_url:
            for f in reversed(info.get('formats', [])):
                if f.get('url'):
                    direct_url = f.get('url')
                    break

        if direct_url:
            filename = f"synx_{info.get('id', 'video')}.{req_format}"
            proxy_url = f"/api/proxy?url={requests.utils.quote(direct_url)}&filename={requests.utils.quote(filename)}"
            
            return jsonify({
                'status': 'success',
                'title': info.get('title', 'Video Ready'),
                'download_url': proxy_url,
                'message': f'Synx Super-Mode Enabled'
            })
        else:
            raise Exception("Link extraction failed.")

@app.route('/api/proxy')
def proxy():
    target_url = request.args.get('url')
    filename = request.args.get('filename', 'video.mp4')
    if not target_url: return "No URL", 400
    
    try:
        # Sunucu üzerinden akıtma (Save As zorlama)
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
