from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import re

app = Flask(__name__)
UPLOAD_FOLDER = 'downloads'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_qualities', methods=['POST'])
def get_qualities():
    data = request.json
    video_url = data.get('url')

    if not video_url:
        return jsonify({'success': False, 'error': 'الرجاء إدخال رابط.'})

    try:
        ydl_opts = {
            'listformats': True,
            'skip_download': True,
            'no_warnings': True,
            'ignoreerrors': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            
            if info_dict is None:
                return jsonify({'success': False, 'error': 'لا يمكن العثور على معلومات الفيديو. تأكد من الرابط.'})
            
            formats_by_ext = {}
            for f in info_dict.get('formats', []):
                ext = f.get('ext')
                if ext not in formats_by_ext:
                    formats_by_ext[ext] = []
                
                quality_name = ""
                if f.get('height') and f.get('vcodec') != 'none':
                    quality_name = f"{f.get('height')}p"
                    
                elif f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    quality_name = f.get('format_note')
                    if not quality_name:
                        quality_name = f"{f.get('ext')} - صوت فقط"

                if quality_name:
                    formats_by_ext[ext].append({
                        'quality': quality_name, 
                        'format_id': f.get('format_id'), 
                        'url': f.get('url'),
                        'ext': ext
                    })

            for ext in formats_by_ext:
                formats_by_ext[ext].sort(key=lambda x: int(re.sub('[^0-9]', '', x['quality'])) if 'p' in x['quality'] else 0, reverse=True)
            
            return jsonify({
                'success': True,
                'formats_by_ext': formats_by_ext,
                'title': info_dict.get('title')
            })

    except Exception as e:
        return jsonify({'success': False, 'error': 'حدث خطأ غير متوقع. الرجاء المحاولة مرة أخرى.'})

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    video_url = data.get('url')
    format_id = data.get('format_id')
    title = data.get('title', 'video')

    try:
        sanitized_title = "".join([c for c in title if c.isalnum() or c in (' ', '_')]).rstrip()
        filepath = os.path.join(UPLOAD_FOLDER, sanitized_title)
        
        ydl_opts = {
            'format': format_id,
            'outtmpl': f'{filepath}.%(ext)s'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            file_extension = info_dict.get('ext')
            final_filepath = f'{filepath}.{file_extension}'
            ydl.download([video_url])

        return send_file(final_filepath, as_attachment=True)
    
    except Exception as e:
        return jsonify({'success': False, 'error': 'فشل التحميل. قد يكون الرابط غير صالح.'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)