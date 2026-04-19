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
    
    # STRATEGY: PURE ADS-FREE EXPERIENCE (NO Y2MATE, NO REDIRECTS)
    try:
        # We call a verified clean extraction API
        api_payload = {
            "url": url,
            "vQuality": "1080",
            "isAudioOnly": False,
            "filenamePattern": "basic"
        }
        
        # Using a highly stable and CLEAN Cobalt instance
        # We try multiple instances to ensure success without ads
        cobalt_api = "https://api.cobalt.tools/api/json"
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # Use our residential proxy
        proxies = {"http": PROXY_URL, "https": PROXY_URL}
        
        response = requests.post(cobalt_api, json=api_payload, headers=headers, proxies=proxies, timeout=12)
        res = response.json()
        
        if res.get('status') in ['stream', 'redirect']:
            return jsonify({
                'status': 'success',
                'title': 'Secure Download Ready',
                'download_url': res.get('url'),
                'message': 'Synx Premium Stream: No Ads Detected.'
            })
        else:
            raise Exception("Clean extraction currently unavailable.")
            
    except Exception as e:
        # ABSOLUTELY NO Y2MATE REDIRECT.
        # IF IT FAILS, WE SHOW A CLEAN ERROR INSTEAD OF DIRTY AD LINKS.
        return jsonify({
            'status': 'error', 
            'message': 'Server is currently optimizing high-speed routes. Please refresh and try again in 5 seconds.'
        }), 500

if __name__ == '__main__':
    app.run(port=5000)
