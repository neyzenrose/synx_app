import os
import urllib.parse
from flask import Flask, render_template, request, jsonify, Response, redirect
import requests
import subprocess
import json

app = Flask(__name__)

# UPDATED ENGINE LIST
ENDPOINTS = [
    "https://cobalt-api.meowing.de",
    "https://cobalt-backend.canine.tools",
    "https://capi.3kh0.net",
    "https://kityune.imput.net",
    "https://nachos.imput.net"
]

@app.route('/')
def index(): return render_template('index.html')

@app.route('/app')
@app.route('/app.html')
def app_page(): return render_template('ultra.html')

@app.route('/api/download', methods=['POST'])
def download():
    try:
        data = request.json
        url = data.get('url', '').strip()
        req_format = data.get('format', 'mp4')
        if not url: return jsonify({"status":"error","message":"No URL provided"}), 400

        # STAGE 1: Try Cobalt Engines (Fastest)
        payload = {
            "url": url,
            "videoQuality": "720",
            "filenameStyle": "pretty",
            "downloadMode": "audio" if req_format in ['mp3', 'm4a'] else "video"
        }
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        for api in ENDPOINTS:
            try:
                resp = requests.post(api, json=payload, headers=headers, timeout=10)
                if resp.status_code == 200:
                    res_json = resp.json()
                    target_url = res_json.get('url')
                    if target_url:
                        base_url = request.url_root.rstrip('/')
                        s_url = urllib.parse.quote(target_url)
                        return jsonify({
                            'status': 'success',
                            'title': res_json.get('filename', 'Download Ready'),
                            'download_url': f"{base_url}/api/proxy?url={s_url}&filename={urllib.parse.quote(res_json.get('filename', 'file'))}",
                            'direct_url': target_url
                        })
            except: continue

        # STAGE 2: Master-Key Fallback (yt-dlp)
        # We use yt-dlp to get the direct stream link using our proxy
        print(f"DEBUG: Falling back to Master-Key for {url}")
        proxy_url = "http://8pqu8nrvp4760s8:pndg6nphvup6nd9@p.webshare.io:80"
        
        try:
            # Command to get the best direct URL for video+audio
            cmd = [
                'yt-dlp', 
                '--proxy', proxy_url,
                '-g', # Get URL
                '-f', 'best[ext=mp4]/best',
                '--get-title',
                url
            ]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            
            lines = stdout.strip().split('\n')
            if len(lines) >= 2:
                title = lines[0]
                stream_url = lines[-1]
                base_url = request.url_root.rstrip('/')
                s_url = urllib.parse.quote(stream_url)
                s_file = urllib.parse.quote(f"{title}.mp4")
                
                return jsonify({
                    'status': 'success',
                    'title': title,
                    'download_url': f"{base_url}/api/proxy?url={s_url}&filename={s_file}",
                    'direct_url': stream_url
                })
        except Exception as e:
            print(f"DEBUG: Master-Key Failed: {e}")

        return jsonify({"status": "error", "message": "High traffic detected. Please try a different link or try again in 5 minutes."}), 503
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/proxy')
def proxy():
    t_url = request.args.get('url')
    f_name = request.args.get('filename', 'media.mp4')
    if not t_url: return "No URL", 400
    try:
        proxy_str = "http://8pqu8nrvp4760s8:pndg6nphvup6nd9@p.webshare.io:80"
        proxies = {"http": proxy_str, "https": proxy_str}
        
        try:
            r = requests.get(t_url, stream=True, timeout=15, proxies=proxies)
            r.raise_for_status()
            def gen():
                for c in r.iter_content(chunk_size=256*1024):
                    if c: yield c
            res = Response(gen(), content_type=r.headers.get('content-type'))
            res.headers['Content-Disposition'] = f'attachment; filename="{f_name}"'
            return res
        except:
            return redirect(t_url)
    except: return "Proxy Error", 500

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
