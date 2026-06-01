window.dash_clientside = Object.assign({}, window.dash_clientside, {
    camera_namespace: {
        streamCamera: function(tab_value) {
            // 1. Only run if we are looking at the Camera tab
            if (tab_value !== '1') {
                return '';
            }

            // 2. Poll for the video element safely within Dash's ecosystem
            const initializeCamera = () => {
                const vid = document.getElementById('video');
                
                // If Dash is still drawing the layout, check again in 50ms
                if (!vid) {
                    setTimeout(initializeCamera, 50);
                    return;
                }

                // If camera track is active, don't restart it
                if (vid.srcObject && vid.srcObject.getTracks && vid.srcObject.getTracks().length > 0) {
                    return;
                }

                // 3. Fire up the camera stream
                navigator.mediaDevices.getUserMedia({ video: true })
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
            // Prevent execution on initial page render
            if (!n_clicks) return 0;

            const video = document.getElementById('video');
            if (!video || !video.videoWidth) {
                console.error("Video element not ready for capture.");
                return 0;
            }

            // Draw current video frame to a canvas
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const context= canvas.getContext('2d');
            context.drawImage(video, 0, 0);

            const dataUrl = canvas.toDataURL('image/png');

            // Send image up to the Flask route endpoint
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
                // Return a timestamp token to satisfy the Output element
                return (new Date()).getTime();
            })
            .catch(err => {
                console.error("Error sending image:", err);
                return 0;
            });
        }
    }
});