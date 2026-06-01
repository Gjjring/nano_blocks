# -*- coding: utf-8 -*-
"""
Created on Fri Dec  5 21:30:23 2025

@author: Phill
"""

from flask import Flask, render_template_string, request, jsonify
import os
import base64
from datetime import datetime

app = Flask(__name__)

# Directory to save uploaded images
SAVE_DIR = "saved_images"
os.makedirs(SAVE_DIR, exist_ok=True)

# Simple HTML template for camera streaming and capture
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Camera Stream</title>
</head>
<body>
    <h2>Camera Stream</h2>
    <video id="video" width="640" height="480" autoplay></video><br>
    <input id="username" placeholder="Enter your username" />
    <button onclick="capture()">Capture Image</button>

    <script>
        const video = document.getElementById('video');

        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => video.srcObject = stream)
            .catch(err => console.error('Camera error:', err));

        function capture() {
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0);

            const username = document.getElementById('username').value || 'unknown_user';
            const imageData = canvas.toDataURL('image/png');

            fetch('/upload_image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: username,
                    image: imageData
                })
            })
            .then(res => res.json())
            .then(data => alert(data.message))
            .catch(err => console.error(err));
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/upload_image', methods=['POST'])
def upload_image():
    data = request.get_json()
    username = data.get('username', 'unknown_user')
    image_data = data.get('image')

    if not image_data:
        return jsonify({ 'message': 'No image received' }), 400

    # Decode base64 image
    header, encoded = image_data.split(',', 1)
    decoded = base64.b64decode(encoded)

    # Save with timestamp and username
    filename = f"{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(SAVE_DIR, filename)

    with open(filepath, 'wb') as f:
        f.write(decoded)

    return jsonify({ 'message': f'Image saved as {filename}' })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

