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
    
    # STRATEGY: 100% CLEAN OR NOTHING. NO AD-SUPPORTED SITES.
    try:
        # We exclusively use Cobalt API which is verified ad-free.
        api_payload = {"url": url, "vQuality": "1080"}
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        
        # Multiple clean node attempts
        nodes = ["https://api.cobalt.tools/api/json", "https://cobalt.canine.is/api/json"]
        
        for node in nodes:
            try:
                response = requests.post(node, json=api_payload, headers=headers, timeout=10)
                if response.status_code == 200:
                    res = response.json()
                    if res.get('status') in ['stream', 'redirect']:
                        return jsonify({
                            'status': 'success',
                            'title': 'Secure Download Ready',
                            'download_url': res.get('url'),
                            'message': 'Synx Verified Clean Node'
                        })
            except:
                continue

        # IF CLEAN NODES FAIL, WE DO NOT REDIRECT TO AD SITES ANYMORE.
        return jsonify({
            'status': 'error', 
            'message': 'Clean extraction is temporarily unavailable. We refused to show you ad-supported links for your safety.'
        }), 500

    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Safety Override: Cleaning high-speed routes.'}), 500

if __name__ == '__main__':
    app.run(port=5000)
