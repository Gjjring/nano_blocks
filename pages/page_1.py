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

            # Video element that clientside JS will attach to
            html.Video(id="video", width="640", height="480", autoPlay=True,
                       style={"border": "1px solid black"}),

            html.Br(),
            
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
