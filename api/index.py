import os
import urllib.parse
from flask import Flask, render_template, request, jsonify, Response, redirect
import requests
import subprocess
import json

app = Flask(__name__)

# EXPANDED STABLE ENGINE LIST - APRIL 2026
ENDPOINTS = [
    "https://cobalt-api.meowing.de",
    "https://cobalt-backend.canine.tools",
    "https://capi.3kh0.net",
    "https://kityune.imput.net",
    "https://nachos.imput.net",
    "https://sunny.imput.net",
    "https://cobalt.perisic.io",
    "https://cobalt-proxy.perisic.io"
]

@app.route('/')
def index(): return render_template('index.html')

@app.route('/app')
@app.route('/app.html')
def app_page(): return render_template('ultra.html')

@app.route('/api/download', methods=['POST'])
def download():
    last_error = "None"
    try:
        data = request.json
        url = data.get('url', '').strip()
        req_format = data.get('format', 'mp4')
        if not url: return jsonify({"status":"error","message":"No URL provided"}), 400

        # STAGE 1: Aggressive Engine Check
        payload = {
            "url": url,
            "videoQuality": "720",
            "filenameStyle": "pretty",
            "downloadMode": "audio" if req_format in ['mp3', 'm4a'] else "video"
        }
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        for api in ENDPOINTS:
            try:
                resp = requests.post(api, json=payload, headers=headers, timeout=12)
                if resp.status_code == 200:
                    res_json = resp.json()
                    target_url = res_json.get('url')
                    if target_url:
                        return jsonify({
                            'status': 'success',
                            'title': res_json.get('filename', 'Download Ready'),
                            'download_url': f"{request.url_root.rstrip('/')}/api/proxy?url={urllib.parse.quote(target_url)}&filename={urllib.parse.quote(res_json.get('filename', 'file'))}",
                            'direct_url': target_url
                        })
                else:
                    last_error = f"Engine {api} responded with {resp.status_code}"
            except Exception as e:
                last_error = f"Engine {api} timeout/fail: {str(e)}"
                continue

        # STAGE 2: Master-Key Fallback (yt-dlp) with TV/iOS Bypass
        proxy_url = "http://8pqu8nrvp4760s8:pndg6nphvup6nd9@p.webshare.io:80"
        cookies_path = "/var/www/synx/api/cookies.txt"
        
        for client in ['tv', 'ios', 'web_embedded']:
            try:
                cmd = [
                    'yt-dlp', '-g', '-f', 'best[ext=mp4]/best', 
                    '--get-title', '--no-check-certificates', 
                    '--extractor-args', f'youtube:player_client={client};player_skip=configs,webpage'
                ]
                if os.path.exists(cookies_path): cmd.extend(['--cookies', cookies_path])
                
                for use_proxy in [True, False]:
                    current_cmd = list(cmd)
                    if use_proxy: current_cmd.extend(['--proxy', proxy_url])
                    current_cmd.append(url)
                    
                    process = subprocess.Popen(current_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    stdout, stderr = process.communicate()
                    
                    if process.returncode == 0:
                        lines = stdout.strip().split('\n')
                        if len(lines) >= 2:
                            title, stream_url = lines[0], lines[-1]
                            return jsonify({
                                'status': 'success',
                                'title': title,
                                'download_url': f"{request.url_root.rstrip('/')}/api/proxy?url={urllib.parse.quote(stream_url)}&filename={urllib.parse.quote(title)}.mp4",
                                'direct_url': stream_url
                            })
                    else:
                        last_error = stderr.strip().split('\n')[-1] if stderr else "Local Extraction Failed"
            except Exception as e:
                last_error = str(e)
                continue

        return jsonify({
            "status": "error", 
            "message": "YouTube security block detected. Try Instagram/TikTok or refresh cookies.",
            "details": last_error
        }), 503
    except Exception as e:
        return jsonify({"status": "error", "message": "System Overload", "details": str(e)}), 500

@app.route('/api/proxy')
def proxy():
    t_url = request.args.get('url')
    f_name = request.args.get('filename', 'media')
    if not t_url: return "No URL", 400
    if not (f_name.endswith('.mp4') or f_name.endswith('.mp3')): f_name += '.mp4'
    try:
        proxy_str = "http://8pqu8nrvp4760s8:pndg6nphvup6nd9@p.webshare.io:80"
        proxies = {"http": proxy_str, "https": proxy_str}
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Safari/537.36'}
        r = requests.get(t_url, stream=True, timeout=30, proxies=proxies, headers=headers)
        def gen():
            for c in r.iter_content(chunk_size=512*1024):
                if c: yield c
        res = Response(gen(), content_type=r.headers.get('content-type', 'application/octet-stream'))
        res.headers['Content-Disposition'] = f'attachment; filename="{urllib.parse.quote(f_name)}"; filename*=UTF-8\'\'{urllib.parse.quote(f_name)}'
        res.headers['X-Content-Type-Options'] = 'nosniff'
        return res
    except: return redirect(t_url)

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
