// Sicherstellen, dass das Namespace-Objekt existiert
window.dash_clientside = window.dash_clientside || {};
window.dash_clientside.camera_namespace = {
    
    streamCamera: function(main_page, inner_tab) {
        if (main_page === undefined || inner_tab === undefined) {
            return '';
        }

        // Sicherstellen, dass main_page als String verglichen wird ("1" statt 1)
        if (String(main_page) !== '1' || String(inner_tab) !== 'camera') {
            var vid = document.getElementById('video');
            if (vid && vid.srcObject) {
                try {
                    if (typeof vid.srcObject.getTracks === 'function') {
                        var tracks = vid.srcObject.getTracks();
                        tracks.forEach(function(track) { if (track) track.stop(); });
                    }
                } catch (e) { console.log(e); }
                vid.srcObject = null;
            }
            return '';
        }


        // Kamera-Initialisierung definieren
        var initializeCamera = function() {
            var vid = document.getElementById('video');
            
            // Falls Dash das Layout noch nicht im DOM aufgebaut hat, im nächsten Frame wieder versuchen
            if (!vid) {
                setTimeout(initializeCamera, 50);
                return;
            }

            // Falls die Kamera auf diesem Element bereits aktiv läuft, nichts tun
            if (vid.srcObject && vid.srcObject.active) {
                return;
            }

            // Stream anfordern
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                navigator.mediaDevices.getUserMedia({ 
                    video: { 
                        width: { ideal: 240 },
                        height: { ideal: 180 },
                        frameRate: { ideal: 24, max: 24 } 
                    } 
                })
                .then(function(stream) {
                    var currentVid = document.getElementById('video');
                    if (currentVid) {
                        currentVid.srcObject = stream;
                        currentVid.onloadedmetadata = function() { 
                            currentVid.play().catch(function(e) { 
                                console.error("Wiedergabefehler Kamera:", e); 
                            }); 
                        };
                    }
                })
                .catch(function(err) {
                    console.error('getUserMedia Fehler (Kamera eventuell blockiert):', err);
                });
            } else {
                console.error("Kamera-API (mediaDevices) wird von diesem Browser nicht unterstützt.");
            }
        };

        initializeCamera();
        return '';
    },

    captureImage: function(n_clicks) {
        if (!n_clicks) return null;

        var video = document.getElementById('video');
        var flash = document.getElementById('camera-flash');

        if (!video || !video.videoWidth) {
            console.error("Video-Element nicht bereit für Capture.");
            return null;
        }

        if (video && flash) {
            video.pause();
            flash.style.transition = 'none';
            flash.style.opacity = '0.9';

            setTimeout(function() {
                flash.style.transition = 'opacity 0.3s ease-out';
                flash.style.opacity = '0';
                if (video) {
                    video.play().catch(function(e) { 
                        console.error("Video resume error:", e); 
                    });
                }
            }, 100);
        }

        var canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        var context = canvas.getContext('2d');
        if (context) {
            context.drawImage(video, 0, 0);
        }

        return canvas.toDataURL('image/png'); 
    }
};