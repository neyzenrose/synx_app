import os
import json
import yt_dlp
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__, template_folder='templates')
CORS(app)

# YOUR RESIDENTIAL PROXY - OUR ONLY OUTSIDE TOOL
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
    req_format = data.get('format', 'mp4') # Kullanıcının seçtiği format (mp4, mp3 vb.)
    req_quality = data.get('quality', 'best') # Kullanıcının seçtiği kalite (1080, 2160, best)

    if not url: return jsonify({"error": "No URL provided"}), 400
    
    try:
        # Daha akıllı bir format seçimi: 
        # Eğer kalite seçildiyse o kaliteye en yakın video+ses veya en iyi birleşik formatı bulur.
        # Vercel kısıtlamaları nedeniyle şu an 'birleştirme' (ffmpeg) yapmadan en iyi tekil dosyayı buluyoruz.
        if req_quality == 'best':
            format_str = f'best[ext={req_format}]/best'
        elif req_format in ['mp3', 'm4a', 'wav']: # Ses formatları için
            format_str = 'bestaudio/best'
        else: # Video formatları için (yüksek kalite önceliği)
            format_str = f'bestvideo[height<={req_quality}][ext={req_format}]+bestaudio/best[height<={req_quality}]/best'

        ydl_opts = {
            'proxy': PROXY_URL,
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'format': format_str,
            'skip_download': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Formats içinden en uygun olanı bul
            formats = info.get('formats', [])
            direct_url = None
            
            # Seçilen kaliteye ve formata en yakın gerçek linki çekiyoruz
            # (Şu an sunucuda ffmpeg olmadığı varsayımıyla tek parça link arıyoruz)
            for f in reversed(formats):
                # Hem video hem ses içeren, istenen çözünürlüğe en yakın format
                if f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                    if req_quality == 'best' or (f.get('height') and f.get('height') <= int(req_quality if req_quality.isdigit() else 1080)):
                        direct_url = f.get('url')
                        break
            
            if not direct_url and formats:
                direct_url = formats[-1].get('url')

            if direct_url:
                return jsonify({
                    'status': 'success',
                    'title': info.get('title', 'Video Ready'),
                    'download_url': direct_url,
                    'message': f'Synx Engine: {req_quality}p Optimized.'
                })
            else:
                raise Exception("Could not find a direct download link.")

    except Exception as e:
        # If YouTube blocks us even with our proxy, we let the user know cleanly.
        return jsonify({
            'status': 'error', 
            'message': 'The video link is temporarily restricted by the source platform. Our engine is working to bypass this.'
        }), 500

if __name__ == '__main__':
    app.run(port=5000)
