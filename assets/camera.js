window.dash_clientside = Object.assign({}, window.dash_clientside, {
    camera_namespace: {
        streamCamera: function(tab_value) {
            if (tab_value !== '1') {
                return '';
            }

            const initializeCamera = () => {
                const vid = document.getElementById('video');
                
                if (!vid) {
                    setTimeout(initializeCamera, 50);
                    return;
                }

                if (vid.srcObject && vid.srcObject.getTracks && vid.srcObject.getTracks().length > 0) {
                    return;
                }

                navigator.mediaDevices.getUserMedia({ 
                    video: { 
                    width: { ideal: 240 },
                    height: { ideal: 180 },
                    frameRate: { ideal: 24, max: 24 } 
                    } 
                    })
                    .then(function(stream) {
                        vid.srcObject = stream;
                        vid.onloadedmetadata = function() { 
                            vid.play().catch(e => console.error("Playback error:", e)); 
                        };
                    })
                    .catch(function(err) {
                        console.error('getUserMedia error:', err);
                    });
            };

            initializeCamera();
            return '';
        },

        captureImage: function(n_clicks) {
            if (!n_clicks) return 0;

            const video = document.getElementById('video');
            const flash = document.getElementById('camera-flash');

            if (!video || !video.videoWidth) {
                console.error("Video element not ready for capture.");
                return 0;
            }

            if (video && flash) {
                video.pause();

                flash.style.transition = 'none';
                flash.style.opacity = '0.9';

                setTimeout(() => {
                    flash.style.transition = 'opacity 0.3s ease-out';
                    flash.style.opacity = '0';
                    video.play().catch(e => console.error("Video resume error:", e));
                }, 100);
            }

            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const context = canvas.getContext('2d');
            context.drawImage(video, 0, 0);

            const dataUrl = canvas.toDataURL('image/png');

            return fetch("/upload_image", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ image: dataUrl })
            })
            .then(resp => {
                if (!resp.ok) {
                    console.error("Upload failed");
                    return 0;
                }
                return (new Date()).getTime();
            })
            .catch(err => {
                console.error("Error sending image:", err);
                return 0;
            });
        }
    }
});