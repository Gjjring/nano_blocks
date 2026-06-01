import dash
import numpy as np
from dash import html
import plotly.graph_objects as go
from dash import dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import skimage as ski
import time
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import cv2
from flask import Flask, Response, request, make_response, stream_with_context, copy_current_request_context
import threading
from PIL import Image
import requests
from io import BytesIO
import os
#import joblib
from flask import Flask, Response, session, g
import cv2
from tempfile import mkdtemp
savedir = mkdtemp()
filename = os.path.join(savedir, 'test.joblib')

# Flask server instance
server = Flask(__name__)
server.secret_key ="mykey"
app = dash.Dash(__name__, server=server)

# Shared resources
#frame_lock = threading.Lock()
current_frame = None
saved_frame = None

class VideoCamera(object):
    def __init__(self):       
        print("init VC") 
        self.video = cv2.VideoCapture(1)        

    def __del__(self):
        print("del VC")
        self.video.release()

    def get_frame(self):
        #global current_frame
        frameId = int(round(self.video.get(1)))
        success, image = self.video.read()
        #current_frame = image
        #session['current_frame'] = image
        
        #g.current_frame = image
        fps = self.video.get(cv2.CAP_PROP_FPS)               
        if success and frameId % fps == 0:
            joblib.dump(image, filename)
        #     path = os.path.join("test", "video_feed")
        #     ext ="jpg"
        #     cv2.imwrite('{}.{}'.format(path, ext), image)
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

# def pattern_data(data):
#     return (b'--frame\r\n'
#         b'Content-Type: image/jpeg\r\n\r\n' + data + b'\r\n\r\n')

def gen(camera):
    #global FEED_ON    
    while True:        
        frame = camera.get_frame()        
        # yield frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        
# def convert_type(frame):
#     return (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@server.route('/video_feed')
def video_feed():
    print("in video feed")
    #try:    
    if True:
        feed = gen(VideoCamera()) 
        return Response(stream_with_context(feed),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
    # except:    

    #     return Response("feed stopped", mimetype="text/html")    


# @server.route('/')
# def index():    
#     print("in index")
#     @copy_current_request_context
#     def do_some_work():        
#         global current_frame        
#         current_frame = session['current_frame']
#         print(current_frame.shape)
#     gevent.spawn(do_some_work)
#     return 'Regular response'

# @server.route('/print_frame')
# def print_frame():        
#     if True:
#         feed = gen(VideoCamera()) 
#         return Response(feed,
#                     mimetype='multipart/x-mixed-replace; boundary=frame')

# # Flask route to stream the MJPEG video
# @server.route('/video_feed')
# def video_feed():
#     return Response(generate_mjpeg(),
#                     mimetype='multipart/x-mixed-replace; boundary=frame')

# Dash layout
app.layout = html.Div([
    html.H3("Live Webcam Feed"),
    html.Img(src="/video_feed", style={"width": "640px", "height": "480px"}),
    # html.Button("Capture Frame", id="capture-btn"),
    # html.Div(id="capture-status"),
    # html.Img(id="captured-frame", style={"display": "none", "marginTop": "10px", "border": "2px solid #333"})
])

# # Dash callback to capture a frame
# @app.callback(
#     Output("capture-status", "children"),
#     Output("captured-frame", "src"),
#     Output("captured-frame", "style"),
#     Input("capture-btn", "n_clicks"),
#     prevent_initial_call=True
# )
# def capture_frame(n_clicks):
#     global saved_frame

#     with frame_lock:
#         if current_frame is None:
#             return "No frame available.", "", {"display": "none"}

#         saved_frame = current_frame.copy()
#         ret, buffer = cv2.imencode('.jpg', saved_frame)
#         if not ret:
#             return "Failed to encode frame.", "", {"display": "none"}

#         jpg_as_text = base64.b64encode(buffer).decode('utf-8')
#         img_src = f"data:image/jpeg;base64,{jpg_as_text}"
#         return "Frame captured!", img_src, {"display": "block", "marginTop": "10px", "width": "320px", "border": "2px solid #333"}

# Start the video capture thread





# Run Dash app
if __name__ == '__main__':
    app.run_server(debug=True)
    