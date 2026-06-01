import dash
from dash import Dash, html, dcc, Input, Output, State, ctx, MATCH, ALL
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

dash.register_page(__name__, path = "/page_2")
app = dash.get_app()
server = app.server

layout = html.Div([
    html.Div(id="gallery"),
            html.Br(),

            html.Button("Delete Selected Images", id="delete-selected-btn", n_clicks=0),
            dcc.ConfirmDialog(
                id='single-selection-message',
                message='You may only select one image at a time for processing',
            ),
])


def render_tile(img):        
    return html.Div([
        dcc.Store(id='click-state', data=False),
        html.Div([
            html.Img(src=img["image"], id= {"type": "clickable-image", "index": img["id"]}, n_clicks=0, style={
            "width": "200px",
            "height": "150px",
            "objectFit": "cover",
            "display": "block",
            "border": "1px solid Black"
            }),
            html.P(id={"type": "img-select", "index": img["id"]}, children="Select")
        ]),
        #dcc.Checklist(
        #    id={"type": "img-select", "index": img["id"]},
        #    options=[{"label": "Select", "value": img["id"]}],
        #    value=[],
        #    style={"textAlign": "center"}
        #)

        ], style={
        "display": "inline-block",
        "margin": "10px",
        "textAlign": "center"
        })
    
@app.callback(
        Output({"type": "clickable-image", "index": ALL}, "style"),
        Output({"type": "clickable-image", "index": ALL}, "n_clicks"),
        Output({"type": "img-select", "index": ALL}, "children"),
        Input({"type": "clickable-image", "index": ALL}, "n_clicks"),
        State({"type": "clickable-image", "index": ALL}, "id"),
        prevent_initial_call=True
)   
def mutually_exclusive_selection(all_n_clicks, all_ids):
    if not all_n_clicks or not ctx.triggered_id:
        raise PreventUpdate
    
    triggered_component = ctx.triggered_id
    triggered_index = triggered_component["index"]

    new_styles = []
    new_clicks = []
    new_texts = []

    active_style ={
        "width": "195px",
        "height": "145px",
        "objectFit": "cover",
        "display": "block",
        "border": "5px solid black",
        'transform': 'scale(0.95)',
        'cursor': 'pointer',
        "transition": "all 0.3s ease"
    }
    normal_style = {
        "width": "200px",
        "height": "150px",
        "objectFit": "cover",
        "display": "block",
        "border": "1px solid black",
        "transition": "all 0.3s ease"
    }

    for comp_id in all_ids:
        current_index = comp_id["index"]

        if current_index == triggered_index:
            new_styles.append(active_style)
            new_clicks.append(1)
            new_texts.append("Selected")
        else:
            new_styles.append(normal_style)
            new_clicks.append(0)
            new_texts.append("Select")
    return new_styles, new_clicks, new_texts

@app.callback(
    Output("gallery", "children"),
    Input("capture-dummy", "children"),
    Input("delete-selected-btn", "n_clicks"),
    State({"type": "clickable-image", "index": ALL}, "n_clicks"),
    State({"type": "clickable-image", "index": ALL}, "id"),
)
def manage_gallery(capture_trigger, delete_clicks, all_n_clicks, all_ids):
    triggered_id = ctx.triggered_id

    if not triggered_id or ctx.triggered is None:
        raise PreventUpdate

    print(f"Triggered by: {triggered_id}")

    if triggered_id == 'delete-selected-btn':
        if all_n_clicks and all_ids:
            selected_ids = {
            comp_id["index"] 
            for clicks, comp_id in zip(all_n_clicks, all_ids) 
            if clicks and clicks % 2 == 1
            }
            if selected_ids:
                imgs = session.get("saved_images", [])
            print(f"len imgs: {len(imgs)}")
            imgs = [img for img in imgs if img["id"] not in selected_ids]
            print(f"len imgs: {len(imgs)}")
            session["saved_images"] = imgs
            session.modified = True
    elif triggered_id == 'capture-dummy':
        pass
        

    images = session.get("saved_images", [])
    print(f"rendering {len(images)} images")
        
    return [render_tile(img) for img in images]

@app.callback(
    Output("_pages_location", "pathname", allow_duplicate=True),             # Redirects browser to page 3
    Input('current-page-store','data'),
    State({"type": "clickable-image", "index": ALL}, "n_clicks"), 
    State({"type": "clickable-image", "index": ALL}, "id"),
    prevent_initial_call='initial_duplicate'
)
def processing_redirect(data, all_n_clicks, all_ids):
    if not all_ids or not all_n_clicks or all_ids is None:
        raise PreventUpdate
    
    if len(all_ids) == 0 or len(all_n_clicks) == 0:
        raise PreventUpdate

    selected_ids = [
        comp_id["index"]
        for clicks, comp_id in zip(all_n_clicks, all_ids)
        if clicks and clicks % 2 == 1
    ]

    if not selected_ids:
        # No image selected, don't redirect
        return dash.no_update
        
    if len(selected_ids) > 1:
        # Alert user if they selected more than one image
        return dash.no_update
    
    # Exactly 1 image is selected! Pull it and process it into session memory
    imgs = session.get("saved_images", [])
    selected_id = selected_ids[0]
    
    str_image = None
    for img in imgs:
        if img['id'] == selected_id:
            str_image = img['image']
            break    

    if not str_image:
        return dash.no_update
    
    # Process Base64 string to a Numpy array
    png_base64 = str_image.strip().replace("data:image/png;base64,", "")
    image_bytes = base64.b64decode(png_base64)
    img_file = Image.open(BytesIO(image_bytes))
    raw_image_data = np.array(img_file, dtype=np.uint8)

    # Save globally to the session cache
    session["current_raw_image"] = raw_image_data
    session.modified = True
    
    # Success! Tell Dash to change pages to Page 3
    return "/page_3"