import dash
from dash import Dash, html, dcc, Input, Output, State, ctx, MATCH, ALL, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.colors import qualitative
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

dash.register_page(__name__, path = '/page_5')
app = dash.get_app()

empty_fig = go.Figure()
empty_fig.update_layout(
    template=None,
    paper_bgcolor="white",
    plot_bgcolor="white",
    xaxis=dict(showgrid=False, visible=False),
    yaxis=dict(showgrid=False, visible=False),
)


layout = html.Div([
    
    dcc.Graph(id = 'threshold-image2', figure=empty_fig, config={'displayModeBar': False}),
    dbc.Row([
        dbc.Col([
                html.P('Min-Size', id='min-size_label'),
            ],
            width=1
            ),
        dbc.Col([
                dcc.Slider(0, 100, 1, value=10, marks=None, id='min-size_slider'),
                ],
            width=7
            ),
        ],
        justify='center'
    ),
    dbc.Row([
        dbc.Col([
                html.P('Simplify', id='simplify_label'),
            ],
            width=1
            ),
        dbc.Col([
                dcc.Slider(0, 3.0, 0.1, value=0.1, marks=None, id='simplify_slider'),
                ],
            width=7
            ),
        ],
        justify='center'
    ),
    dbc.Row([
        dbc.Col([
                html.P('Blur', id='blur_label'),
            ],
            width=1
            ),
        dbc.Col([
                dcc.Slider(0, 1.0, 0.01, value=0.5, marks=None, id='blur_slider'),
                ],
            width=7
            ),
        ],
        justify='center'
    ),
]),
    


# 2. Adjust
@app.callback(
    Output('min-size_slider', 'value'),
    Output('simplify_slider', 'value'),
    Output('blur_slider', 'value'),    
    Input('current-page-store', 'data'),
    State('slider-geo-store', 'data')
)
def initialize_or_restore_sliders2(current_page, slider_data):
    if current_page != 5:
        raise PreventUpdate
    

    default_min_size = 10.
    default_simplify = 0.1
    default_blur     = 0.12
    
    min_size = slider_data.get('min_size', default_min_size)
    simplify = slider_data.get('simplify', default_simplify)
    blur     = slider_data.get('blur', default_blur)
    return min_size, simplify, blur
    

@app.callback(Output("slider-geo-store", 'data'),
              Input("min-size_slider", "value"),
              Input("simplify_slider", "value"),
              Input("blur_slider", "value"),
              State("slider-geo-store", 'data'),
)
def store_hue_slider(mins_val, simp_val, blur_val, current_data):
    current_data['min_size'] = mins_val
    current_data['simplify'] = simp_val
    current_data['blur'] = blur_val
    return current_data

@app.callback(
    Output(component_id='threshold-image2', component_property='figure'),
    Input('min-size_slider', 'value'),          # Argument 3: min_size_val
    Input('simplify_slider', 'value'),         # Argument 4: simplify_val
    Input('blur_slider', 'value'),             # Argument 5: blur_val
    #State('current-page-store', 'data'),        # Argument 7: current_page
    Input('dropdown-selection-store', 'data'),  # Argument 2: task_selection
    prevent_initial_call=True,
)
def make_threshold_image2(min_size_val, simplify_val, blur_val, task_selection):
    # if current_page != 5:
    #     raise PreventUpdate

    if min_size_val is None: min_size_val = 40
    if simplify_val is None: simplify_val = 0.1
    if blur_val is None: blur_val = 0.5

    binary_mask = session.get('current_threshold_image')

    if binary_mask is None:
        print("\n[KONSOLE] DEBUG: binary_mask in Session ist absolut leer (None)!")
        raise PreventUpdate

    binary_mask = np.array(binary_mask, dtype=np.float64)

    if blur_val > 0:
        smoothed = ski.filters.gaussian(binary_mask, sigma=blur_val * 5.0)
        binary_mask = (smoothed > 0.3).astype(np.uint8)
    else:
        binary_mask = (binary_mask > 0.5).astype(np.uint8)

    # print("\n=== VISUELLER MASKEN-CHECK IN DER KONSOLE ===")
    # print(f"Dimensionen des Bildes: {binary_mask.shape}")
    # print(f"Gesamtsumme aktiver Pixel im Array: {np.sum(binary_mask)}")

    # verkleinerte_maske = binary_mask[::4, ::4]

    # for zeile in verkleinerte_maske:
    #     print_zeile = ""
    #     for pixel in zeile:
    #         if pixel > 0:
    #             print_zeile += "#"
    #         else:
    #             print_zeile += " "
    #     print(print_zeile)
    # print("=============================================\n")

    session['current_threshold_image2'] = binary_mask

    image_height = binary_mask.shape[0]
    image_width = binary_mask.shape[1]

    print(f"image_height: {image_height}")
    print(f"image_width: {image_width}")

    keys = {'polygons': []}

    contours = ski.measure.find_contours(binary_mask.T, 0.5)
    for contour in contours:
        p = shapely.Polygon(contour)
        min_area_threshold = min_size_val**2 #* 0.01
        if p.area > min_area_threshold:
            p2 = p.simplify(simplify_val * 5.0)
            keys['polygons'].append(p2)


    np_polys = []
    for i, poly in enumerate(keys['polygons']):
        c = np.array(poly.exterior.coords)
        c = c[:-1, :]
        c[:, 1] = image_height - c[:, 1]
        np_polys.append(np.ceil(c))
    keys['polygons'] = np_polys

    for i, poly in enumerate(keys['polygons']):
        orientation = polygon_orientation(poly)
        if orientation == "CW":
            poly = poly[::-1]
        keys['polygons'][i] = poly

    session['polygons'] = keys['polygons']

    # for polygon in keys['polygons']:
    #     print('page 4 end polygon ymin: {}, ymax: {}, x min: {}, x max: {}'.format(np.min(polygon[:, 1]), np.max(polygon[:, 1]), np.min(polygon[:, 0]), np.max(polygon[:, 0])))

    #session['nesting_levels'] = nesting_levels
    palette = qualitative.Safe
    palette2 = qualitative.Alphabet
    colors = [palette2[8], palette[0]]

    h, w = binary_mask.shape[:2]
    fig = go.Figure()

    for polygon in keys['polygons']:
        closed_polygon = np.vstack([polygon, polygon[0]])
        fig.add_trace(go.Scatter(
            x=closed_polygon[:, 0],
            y=closed_polygon[:, 1],
            fill="toself",
            fillcolor="rgba(0, 123, 255, 0.4)",
            line=dict(color="blue", width=3),
            mode="lines+markers",
        ))

    match task_selection:
        case "btn-opt-a": task_src = '/assets/aufgabe0.png'
        case "btn-opt-b": task_src = '/assets/aufgabe1.png'
        case "btn-opt-c": task_src = '/assets/aufgabe2.png'
        case "btn-opt-d": task_src = '/assets/aufgabe3.png'
        case _ : task_src = '/assets/aufgabe0.png'

    fig.update_layout(
        xaxis=dict(range=[0, w], showgrid=False, mirror=True, showline=True, linecolor='black', scaleanchor="y", scaleratio=1),
        yaxis=dict(range=[0, h], showgrid=False, mirror=True, showline=True, linecolor='black'),
        plot_bgcolor="white",
        width=800,
        height=int(800 * (h / w)),
        showlegend=False,
        images=[dict(source=task_src, xref="paper", yref="paper", x=0.5, y=0.5, sizex=1.5, sizey=1.5, xanchor="center", yanchor="middle")],
        margin=dict(t=100, b=100, l=50, r=50)
    )
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)

    geo_data = {'min_size': min_size_val, 'simplify': simplify_val, 'blur': blur_val}
    return fig

def polygon_orientation(vertices):
    """
    vertices: list of (x, y) tuples
    returns: 'CCW', 'CW', or 'DEGENERATE'
    """
    area2 = 0

    n = len(vertices)
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]
        area2 += x1 * y2 - x2 * y1

    if area2 > 0:
        return "CCW"
    elif area2 < 0:
        return "CW"
    else:
        return "DEGENERATE"
