import os
import urllib.parse
from flask import Flask, render_template, request, jsonify, Response
import requests

app = Flask(__name__)

# BULLETPROOF ULTIMATE ENGINE LIST
ENDPOINTS = [
    "https://cobalt.moe/api/json",
    "https://api.cobalt.tools",
    "https://cobalt.api.unblocker.xyz",
    "https://v1.cobalt.sh",
    "https://api.v2.cobalt.tools"
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
        url = data.get('url', '').split()[0] # Auto-sanitize just in case
        req_format = data.get('format', 'mp4')
        if not url: return jsonify({"status":"error","message":"No URL"}), 400

        for api in ENDPOINTS:
            try:
                # Latest Cobalt API V2/V3 compatibility
                payload = {
                    "url": url,
                    "videoQuality": "720",
                    "audioFormat": "mp3",
                    "filenameStyle": "pretty",
                    "downloadMode": "audio" if req_format in ['mp3', 'm4a', 'wav'] else "video"
                }
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                    "Origin": "https://cobalt.tools",
                    "Referer": "https://cobalt.tools/"
                }
                
                resp = requests.post(api, json=payload, headers=headers, timeout=15)
                if resp.status_code == 200:
                    result = resp.json()
                    if result.get('url'):
                        base_url = request.url_root.rstrip('/')
                        s_url = urllib.parse.quote(result.get('url'))
                        s_file = urllib.parse.quote(f"synx_media.{req_format}")
                        return jsonify({
                            'status': 'success',
                            'title': 'Download Ready',
                            'download_url': f"{base_url}/api/proxy?url={s_url}&filename={s_file}"
                        })
            except: continue

        return jsonify({"status": "error", "message": "Server temporarily overloaded. Try with another link or wait 2 mins."}), 503
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/proxy')
def proxy():
    t_url = request.args.get('url')
    f_name = request.args.get('filename', 'video.mp4')
    if not t_url: return "No URL", 400
    try:
        r = requests.get(t_url, stream=True, timeout=120)
        def gen():
            for c in r.iter_content(chunk_size=65536):
                if c: yield c
        res = Response(gen(), content_type=r.headers.get('content-type'))
        res.headers['Content-Disposition'] = f'attachment; filename="{f_name}"'
        return res
    except: return "Proxy Error", 500

if __name__ == '__main__': app.run()
