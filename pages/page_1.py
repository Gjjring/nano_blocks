import dash
from dash import html, dcc, Input, Output, State, ctx, ClientsideFunction, MATCH, ALL
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate
from flask import request, jsonify
from flask import Flask, session
from flask_session import Session
from cachelib.file import FileSystemCache
import os, base64
import cv2
from io import BytesIO
from PIL import Image
from datetime import datetime
import numpy as np
import skimage as ski
import shapely
import jcmwave

dash.register_page(__name__, path = "/")
app = dash.get_app()
server = app.server

layout = html.Div([
    html.H3("Camera Stream"),

            html.Div([
                html.Video(id="video", width="640", height="480", autoPlay=True,
                       style={"border": "1px solid black"}),

                html.Div(id="camera-flash", style={
                "position": "absolute",
                "top": "0", "left": "0", "width": "100%", "height": "100%",
                "backgroundColor": "white",
                "opacity": "0",
                "pointerEvents": "none",
                "transition": "opacity 0.1s ease-out"
                })
            ], style={"position": "relative", "display": "inline-block"}),

            html.Div([
                html.Img(id="capture-preview", style={
                    "width": "150px", 
                    "height": "112px", 
                    "objectFit": "cover",
                    "border": "2px solid #fff",
                    "boxShadow": "0 0 8px rgba(0,0,0,0.3)",
                    "opacity": "0",
                    "transition": "opacity 0.3s ease-in-out, transform 0.3s ease-in-out",
                    "transform": "scale(0.8)",
                    "marginLeft": "15px",
                    "verticalAlign": "top"
                })
            ], style={"display": "inline-block"}),
        
            
            html.Button("Capture", id="capture-btn", n_clicks=0),
])


dash.clientside_callback(
    ClientsideFunction(
        namespace='camera_namespace',
        function_name='streamCamera'
    ),
    Output("camera-start-dummy", "children"),
    Input("page-tabs", "value")
)


dash.clientside_callback(
    ClientsideFunction(
        namespace='camera_namespace',
        function_name='captureImage'
    ),
    Output("capture-dummy", "children"),
    Input("capture-btn", "n_clicks"),
    prevent_initial_call=True
)


@server.route("/upload_image", methods=["POST"])
def upload_image():
    data = request.get_json(force=True)
    image_data = data.get("image")
    
    if not image_data:
        return jsonify({"message": "No image provided"}), 400

    try:
        header, encoded = image_data.split(",", 1)
    except Exception:
        return jsonify({"message": "Bad image data"}), 400

    current_time = datetime.now()
    id_val = current_time.strftime("%Y%m%d%H%M%S%f")
    try:
        stored = session.get("saved_images", [])
        stored.append({
            "id": id_val,
            "image": image_data, 
            "timestamp": current_time.isoformat()
        })
        session["saved_images"] = stored
        session.modified = True
    except Exception as exp:
        print(str(exp))
        return jsonify({"message": f"{str(exp)}"}), 400
    
   
    stored = session.get("saved_images", [])
    print(f"N stored images: {len(stored)}")
    return jsonify({"message": f"Image saved as {id_val}"})



@app.callback(
    Output("capture-preview", "src"),
    Input("capture-dummy", "children"),
    prevent_initial_call=True
)
def update_preview_src(capture_trigger):
    if not capture_trigger or capture_trigger == 0:
        raise PreventUpdate

    images = session.get("saved_images", [])
    if not images:
        raise PreventUpdate
        
    return images[-1]["image"]


app.clientside_callback(
    """
    function(img_src) {
        // Ignorieren, wenn beim Laden noch kein Bild da ist
        if (!img_src) {
            return window.dash_clientside.no_update;
        }
        
        const previewImg = document.getElementById('capture-preview');
        if (previewImg) {
            // 1. Sofort sichtbar machen und reinskalieren
            previewImg.style.opacity = '1';
            previewImg.style.transform = 'scale(1.0)';
            
            // 2. Nach 1000ms (1 Sekunde) elegant wieder ausblenden
            setTimeout(() => {
                previewImg.style.opacity = '0';
                previewImg.style.transform = 'scale(0.8)';
            }, 1000);
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output("capture-preview", "id"),
    Input("capture-preview", "src"), 
    prevent_initial_call=True
)

