import dash
from dash import html, dcc, Input, Output, State, ctx, ClientsideFunction, MATCH, ALL, callback_context
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import time
from dash.exceptions import PreventUpdate
from flask import request, jsonify
from flask import Flask, session
from flask_session import Session
from cachelib.file import FileSystemCache
import os, base64
import cv2
from io import BytesIO
from PIL import Image, ImageDraw
from datetime import datetime
import numpy as np
import skimage as ski
import shapely
import jcmwave

dash.register_page(__name__, path = "/")
app = dash.get_app()
server = app.server

layout = html.Div([
    dcc.Tabs(id="image-tabs", value='camera', children=[
        dcc.Tab(label='Camera', value='camera', children=[
            html.H3("Camera Stream"),

            html.Div([
                html.Video(id="video", width="640", height="480", autoPlay=True,
                       style={"border": "1px solid black"}),

                html.Div(id="camera-flash", style={
                "position": "absolute",
                "top": "0", "left": "0", "width": "640px", "height": "480px",
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
        ]),
        dcc.Tab(label='Draw Shapes', value='draw', children=[
            html.Div([
                html.Div([
                    html.Label("Form auswählen: ", style={"fontWeight": "bold", "marginRight": "10px"}),
                    dcc.RadioItems(
                        id="shape-selector",
                        options=[
                            {"label": " Rechteck", "value": "rect"},
                            {"label": " Kreis", "value": "circle"}
                        ],
                        value="rect",
                        inline=True,
                        style={"display": "inline-block"}
                    )
                ], style={"padding": "15px", "backgroundColor": "#f9f9f9", "borderBottom": "1px solid #ddd"}),
            
                html.Div([
                    dcc.Graph(
                        id="drawing-area",
                        config={
                            "modeBarButtonsToAdd": ["eraseshape"],
                            "displayModeBar": True,
                            "toImageButtonOptions": {
                                "format": "png",
                                "filename": "meine_zeichnung",
                                "height": 480,
                                "width": 640,
                                "scale": 1
                            }
                        },
                        style={"height": "480", "width": "640"}
                    )
                ], style={"border": "2px solid #333", "marginTop": "20px", "borderRadius": "5px", "padding": "10px", "width": "fit-content"}),
            
            html.Button(
                "Bild speichern", 
                id="btn-download", 
                n_clicks=0, 
                style={
                    "backgroundColor": "#28a745", 
                    "color": "white", 
                    "border": "none", 
                    "padding": "12px 25px", 
                    "borderRadius": "5px", 
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "marginTop": "20px",
                    "display": "block"
                }
            )
            ])
        ]),
    ]),
    

            
])

@app.callback(
    Output("inner-tab-store", "data"),
    Input("image-tabs", "value"),
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def sync_inner_tab_to_store(tab_value):
    if not tab_value:
        raise PreventUpdate
    return tab_value


app.clientside_callback(
    ClientsideFunction(
        namespace='camera_namespace',
        function_name='streamCamera'
    ),
    Output("camera-start-dummy", "children"),
    Input("current-page-store", "data"),
    Input("inner-tab-store", "data"), 
    prevent_initial_call=True
)


app.clientside_callback(
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
    Output("capture-preview", "style"),  # Wir machen das Bild auch gleich sichtbar
    Input("capture-dummy", "children"),
    prevent_initial_call=True
)
def update_preview_src(image_data_uri):
    # Wenn kein Bild-String ankommt, abbrechen
    if not image_data_uri or isinstance(image_data_uri, int):
        raise PreventUpdate

    # 1. Bild in der Flask-Session speichern (für spätere Pages)
    current_time = datetime.now()
    id_val = current_time.strftime("%Y%m%d%H%M%S%f")
    
    stored = session.get("saved_images", [])
    stored.append({
        "id": id_val,
        "image": image_data_uri, 
        "timestamp": current_time.isoformat()
    })
    session["saved_images"] = stored
    session.modified = True
    
    print(f"N stored images: {len(stored)}")

    # 2. Styling anpassen, damit das Bild von opacity: 0 auf 1 wechselt
    visible_style = {
        "width": "150px", 
        "height": "112px", 
        "objectFit": "cover",
        "border": "2px solid #fff",
        "boxShadow": "0 0 8px rgba(0,0,0,0.3)",
        "opacity": "1",  # Sichbarkeit eingeschaltet
        "transition": "opacity 0.3s ease-in-out, transform 0.3s ease-in-out",
        "transform": "scale(1.0)", # Leichtes Hereinzoomen
        "marginLeft": "15px",
        "verticalAlign": "top"
    }

    # Wir geben die Bilddaten direkt an das src-Attribut weiter
    return image_data_uri, visible_style


#interactive Drawing
@app.callback(
    Output("drawing-area", "figure"),
    Input("shape-selector", "value"),
    Input("drawing-area", "relayoutData"),
    State("drawing-area", "figure")
)
def update_canvas(selected_shape, relayout_data, current_figure):
    if current_figure is None:
        fig = go.Figure()
        fig.update_xaxes(range=[0, 100], showgrid=False, zeroline=False, visible=False, fixedrange=True)
        fig.update_yaxes(range=[0, 100], showgrid=False, zeroline=False, visible=False, fixedrange=True)
        fig.update_layout(
            plot_bgcolor="white",
            margin=dict(l=0, r=0, t=0, b=0),
            
            width=640,
            height=480
        )
    else:
        fig = go.Figure(current_figure)

    if relayout_data and "shapes" in relayout_data:
        fig.layout.shapes = relayout_data["shapes"]

    fig.layout.dragmode = f"draw{selected_shape}"
    fig.layout.newshape = dict(
        fillcolor="blue",
        line=dict(color="blue", width=2)
    )
    
    return fig

@app.callback(
    Output("capture-preview", "src", allow_duplicate=True),
    Input("btn-download", "n_clicks"),
    State("drawing-area", "figure"),
    prevent_initial_call=True
)
def save_drawn_canvas_to_session(n_clicks, current_figure):
    if not n_clicks or current_figure is None:
        raise PreventUpdate

    width, height = 240, 180
    img = Image.new("RGB", (width, height), "white")
    canvas = ImageDraw.Draw(img)

    shapes = current_figure.get("layout", {}).get("shapes", [])
    
    if not shapes:
        raise PreventUpdate

    for shape in shapes:
        shape_type = shape.get("type")

        x0 = float(shape.get("x0", 0)) * (width / 100.0)
        x1 = float(shape.get("x1", 0)) * (width / 100.0)
        y0 = float(shape.get("y0", 0)) * (height / 100.0)
        y1 = float(shape.get("y1", 0)) * (height / 100.0)

        y0 = height - y0
        y1 = height - y1

        left, right = min(x0, x1), max(x0, x1)
        top, bottom = min(y0, y1), max(y0, y1)

        if shape_type == "rect":
            canvas.rectangle([left, top, right, bottom], fill="blue", outline="blue")
        elif shape_type == "circle":
            canvas.ellipse([left, top, right, bottom], fill="blue", outline="blue")

    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    image_data_uri = f"data:image/png;base64,{img_str}"

    current_time = datetime.now()
    id_val = current_time.strftime("%Y%m%d%H%M%S%f")
    
    stored = session.get("saved_images", [])
    stored.append({
        "id": id_val,
        "image": image_data_uri, 
        "timestamp": current_time.isoformat()
    })
    session["saved_images"] = stored
    session.modified = True
    
    return image_data_uri