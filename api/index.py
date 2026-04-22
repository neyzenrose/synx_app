import os
import urllib.parse
from flask import Flask, render_template, request, jsonify, Response, redirect
import requests

app = Flask(__name__)

# THE ULTIMATE ENGINE LIST - UPDATED APRIL 2026
# Focus on community instances which are more stable right now
ENDPOINTS = [
    "https://cobalt-api.meowing.de",
    "https://cobalt-backend.canine.tools",
    "https://capi.3kh0.net",
    "https://kityune.imput.net",
    "https://nachos.imput.net",
    "https://sunny.imput.net"
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
        raw_url = data.get('url', '').strip()
        if not raw_url:
            return jsonify({"status": "error", "message": "Link not found. Please paste a valid URL."}), 400
            
        # Clean URL (remove tracking etc)
        url = raw_url.split()[0].split('?')[0] if 'instagram.com' in raw_url else raw_url.split()[0]
        req_format = data.get('format', 'mp4')

        payload = {
            "url": raw_url, # Pass original for Instagram/TikTok to be safe
            "videoQuality": "720",
            "filenameStyle": "pretty",
            "downloadMode": "audio" if req_format in ['mp3', 'm4a'] else "video"
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        }

        for api in ENDPOINTS:
            try:
                print(f"DEBUG: Trying engine {api}")
                resp = requests.post(api, json=payload, headers=headers, timeout=15)
                
                if resp.status_code == 200:
                    res_json = resp.json()
                    target_url = res_json.get('url')
                    
                    if target_url:
                        base_url = request.url_root.rstrip('/')
                        s_url = urllib.parse.quote(target_url)
                        s_file = urllib.parse.quote(res_json.get('filename', f"synx_media.{req_format}"))
                        
                        return jsonify({
                            'status': 'success',
                            'title': res_json.get('filename', 'Download Ready'),
                            'download_url': f"{base_url}/api/proxy?url={s_url}&filename={s_file}",
                            'direct_url': target_url
                        })
                elif resp.status_code == 400:
                    # Specific engine error, try next
                    continue
            except Exception as e:
                print(f"DEBUG: Engine {api} failed: {e}")
                continue

        return jsonify({
            "status": "error", 
            "message": "All download engines are currently busy. This usually clears up in 1-2 minutes. Please try again shortly or use another link."
        }), 503

    except Exception as e:
        return jsonify({"status": "error", "message": f"Global Error: {str(e)}"}), 500

@app.route('/api/proxy')
def proxy():
    t_url = request.args.get('url')
    f_name = request.args.get('filename', 'media.mp4')
    if not t_url: return "URL missing", 400
    
    try:
        # Webshare Proxy Credentials
        proxy_str = "http://8pqu8nrvp4760s8:pndg6nphvup6nd9@p.webshare.io:80"
        proxies = {"http": proxy_str, "https": proxy_str}
        
        # We try to stream with proxy first
        try:
            r = requests.get(t_url, stream=True, timeout=12, proxies=proxies)
            r.raise_for_status()
            
            def gen():
                for c in r.iter_content(chunk_size=256*1024):
                    if c: yield c
            
            res = Response(gen(), content_type=r.headers.get('content-type'))
            res.headers['Content-Disposition'] = f'attachment; filename="{f_name}"'
            return res
            
        except Exception as proxy_err:
            print(f"DEBUG: Proxy Failed ({proxy_err}), redirecting to direct link.")
            # If proxy fails (407 etc), redirect user directly to the media source
            return redirect(t_url)
            
    except Exception as e:
        return f"Streaming error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
