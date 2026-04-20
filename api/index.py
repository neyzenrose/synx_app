import os
import urllib.parse
from flask import Flask, render_template, request, jsonify, Response, send_file
import requests
import time

# TRY TO IMPORT THE NEW ENGINE
try:
    from pytubefix import YouTube
    PYTUBE_AVAILABLE = True
except ImportError:
    PYTUBE_AVAILABLE = False

app = Flask(__name__)

# ROBUST PROXY CONFIG
PROXY_URL = "http://8pqu8nrvp4760s8:pndg6nphvup6nd9@p.webshare.io:80"
PROXIES = {"http": PROXY_URL, "https": PROXY_URL}

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
        url = data.get('url', '').split()[0]
        req_format = data.get('format', 'mp4')
        if not url: return jsonify({"status":"error","message":"No URL"}), 400

        # --- STRATEGY 1: TRY PYTUBEFIX (THE MASTER KEY) ---
        if PYTUBE_AVAILABLE and "youtube.com" in url or "youtu.be" in url:
            try:
                print(f"DEBUG: Attempting PytubeFix for {url}")
                yt = YouTube(url, proxies=PROXIES)
                
                if req_format in ['mp3', 'm4a', 'wav']:
                    stream = yt.streams.get_audio_only()
                else:
                    stream = yt.streams.get_highest_resolution()
                
                # We can't stream directly easily, so we get the direct URL if possible
                # Or we use a public mirror as fallback
                video_url = stream.url
                if video_url:
                    base_url = request.url_root.rstrip('/')
                    s_url = urllib.parse.quote(video_url)
                    s_file = urllib.parse.quote(f"synx_media.{req_format}")
                    return jsonify({
                        'status': 'success',
                        'title': yt.title,
                        'download_url': f"{base_url}/api/proxy?url={s_url}&filename={s_file}"
                    })
            except Exception as pe:
                print(f"DEBUG: PytubeFix failed -> {str(pe)}")

        # --- STRATEGY 2: TRY PUBLIC COBALT ENGINES ---
        ENDPOINTS = ["https://cobalt.moe/api/json", "https://api.cobalt.tools", "https://cobalt.api.unblocker.xyz"]
        for api in ENDPOINTS:
            try:
                payload = {"url": url, "videoQuality": "720", "downloadMode": "audio" if req_format in ['mp3', 'm4a'] else "video"}
                resp = requests.post(api, json=payload, timeout=10)
                if resp.status_code == 200:
                    res_json = resp.json()
                    if res_json.get('url'):
                        base_url = request.url_root.rstrip('/')
                        s_url = urllib.parse.quote(res_json.get('url'))
                        s_file = urllib.parse.quote(f"synx_media.{req_format}")
                        return jsonify({'status': 'success','title': 'Download Ready','download_url': f"{base_url}/api/proxy?url={s_url}&filename={s_file}"})
            except: continue

        return jsonify({"status": "error", "message": "YouTube security is unbeatable tonight. Try Instagram/TikTok or wait."}), 503
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/proxy')
def proxy():
    target_url = request.args.get('url')
    filename = request.args.get('filename', 'video.mp4')
    if not target_url: return "No URL", 400
    try:
        req = requests.get(target_url, stream=True, timeout=300, proxies=PROXIES)
        def generate():
            for chunk in req.iter_content(chunk_size=131072):
                if chunk: yield chunk
        response = Response(generate(), content_type=req.headers.get('content-type'))
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except: return "Proxy Error", 500

if __name__ == '__main__':
    app.run()
