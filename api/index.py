import os
import urllib.parse
from flask import Flask, render_template, request, jsonify, Response
import requests

app = Flask(__name__)

# REFINED MOTOR LIST FOR INSTAGRAM & YOUTUBE
ENDPOINTS = [
    "https://cobalt.moe/api/json", # THE MOST STABLE ONE
    "https://api.cobalt.tools",
    "https://cobalt.api.unblocker.xyz",
    "https://v1.cobalt.sh"
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
        # Handle empty/mangled input
        url = data.get('url', '').strip().split()[0]
        req_format = data.get('format', 'mp4')
        if not url: return jsonify({"status":"error","message":"No URL provided"}), 400

        for api in ENDPOINTS:
            try:
                # Payload adjusted to latest Cobalt standards
                payload = {
                    "url": url,
                    "videoQuality": "720",
                    "filenameStyle": "pretty",
                    "downloadMode": "audio" if req_format in ['mp3', 'm4a'] else "video"
                }
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
                }
                
                resp = requests.post(api, json=payload, headers=headers, timeout=12)
                if resp.status_code == 200:
                    res_json = resp.json()
                    if res_json.get('url'):
                        base_url = request.url_root.rstrip('/')
                        s_url = urllib.parse.quote(res_json.get('url'))
                        s_file = urllib.parse.quote(f"synx_media.{req_format}")
                        return jsonify({
                            'status': 'success',
                            'title': 'Download Ready',
                            'download_url': f"{base_url}/api/proxy?url={s_url}&filename={s_file}"
                        })
            except: continue

        return jsonify({"status": "error", "message": "Engines are under maintenance. Try again in 2 minutes."}), 503
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/proxy')
def proxy():
    t_url = request.args.get('url')
    f_name = request.args.get('filename', 'media.mp4')
    if not t_url: return "No URL", 400
    try:
        # User's Webshare proxy for reliable streaming
        proxies = {"http": "http://8pqu8nrvp4760s8:pndg6nphvup6nd9@p.webshare.io:80", "https": "http://8pqu8nrvp4760s8:pndg6nphvup6nd9@p.webshare.io:80"}
        r = requests.get(t_url, stream=True, timeout=180, proxies=proxies)
        def gen():
            for c in r.iter_content(chunk_size=65536):
                if c: yield c
        res = Response(gen(), content_type=r.headers.get('content-type'))
        res.headers['Content-Disposition'] = f'attachment; filename="{f_name}"'
        return res
    except: return "Proxy Stream Error", 500

if __name__ == '__main__': app.run()
