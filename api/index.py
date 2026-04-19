import os
import json
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__, template_folder='templates')
CORS(app)

# PROXY CONFIGURATION
PROXY_URL = "http://snrkekxx-11:fcadsu23a4e1@p.webshare.io:80"

@app.route('/')
def index(): return render_template('index.html')

@app.route('/app')
@app.route('/app.html')
def app_page(): return render_template('app.html')

@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    if not url: return jsonify({"error": "No URL provided"}), 400
    
    # SYSTEM: TWIN CLEAN ENGINES (NO ADS)
    # 1. PRIMARY: COBALT NODE
    try:
        api_payload = {"url": url, "vQuality": "1080", "isAudioOnly": False}
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        
        # We try without proxy first for speed, if it fails, we will fallback
        response = requests.post("https://api.cobalt.tools/api/json", json=api_payload, headers=headers, timeout=8)
        if response.status_code == 200:
            res = response.json()
            if res.get('status') in ['stream', 'redirect']:
                return jsonify({
                    'status': 'success',
                    'title': 'High-Speed Ready',
                    'download_url': res.get('url'),
                    'message': 'Synx Clean Node 1'
                })
    except:
        pass

    # 2. SECONDARY: INVIDIOUS NODE (SUPER CLEAN)
    try:
        # Extract ID
        vid_id = url.split("v=")[1].split("&")[0] if "v=" in url else url.split("/")[-1]
        # Invidious provides clean direct links
        return jsonify({
            'status': 'success',
            'title': 'Alternative Clean Node Found',
            'download_url': f"https://invidious.snopyta.org/latest_version?id={vid_id}&itag=22",
            'message': 'Synx Clean Node 2'
        })
    except:
        pass

    return jsonify({
        'status': 'error', 
        'message': 'All nodes busy. We only provide ad-free high-speed links. Please try again in 10 seconds.'
    }), 500

if __name__ == '__main__':
    app.run(port=5000)
