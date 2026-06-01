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

dash.register_page(__name__, path = "/page_4")
app = dash.get_app()
server = app.server

layout = html.Div([
    dcc.Graph(id = 'threshold_image'),

            dbc.Row([
                dbc.Col([                                 
                        html.P("Hue", id="hue_label"),
                    ],
                    width=1
                    ),
                dbc.Col([
                        dcc.RangeSlider(0, 1.0, 0.01, value=[0.4, 0.5], marks=None, allowCross=False, id='hue_slider')
                        ],
                    width=7
                    ),
                ],
                justify="center"
            ),
            dbc.Row([
                dbc.Col([                                 
                        html.P("Saturation", id="saturation_label"),
                    ],
                    width=1
                    ),
                dbc.Col([
                        dcc.RangeSlider(0, 1.0, 0.01, value=[0.5, 1.0], marks=None, allowCross=False, id='saturation_slider')
                        ],
                    width=7
                    ),
                ],
                justify="center"
            ),
            dbc.Row([
                dbc.Col([                                 
                        html.P(" Value ", id="value_label"),
                    ],
                    width=1
                    ),
                dbc.Col([
                        dcc.RangeSlider(0, 1.0, 0.01, value=[0.1, 1.0], marks=None, allowCross=False, id='value_slider')
                        ],
                    width=7
                    ),
                ],
                justify="center"
            ),

])


@app.callback(Output(component_id='hue_slider', component_property= 'value'),
              Input('threshold_color','data'))
def update_hue_threshold(target_color):
    if not target_color or target_color is None:
        raise PreventUpdate
    if len(target_color) == 0:
        raise PreventUpdate()
    if isinstance(target_color, (list, tuple, np.ndarray)):
        if len(target_color) == 0 or any(val is None for val in target_color):
            raise PreventUpdate
    if target_color == [None] or target_color == "None":
        raise PreventUpdate
    
    hsv_target_color = ski.color.rgb2hsv(np.array(target_color, dtype=np.uint8))
    lower_hue_bound = np.clip(hsv_target_color[0]-0.15, 0.0, 1.0)
    upper_hue_bound = np.clip(hsv_target_color[0]+0.15, 0.0, 1.0)
    return [lower_hue_bound, upper_hue_bound]



@app.callback(Output(component_id='threshold_image', component_property= 'figure'),
              Input('hue_slider', 'value'), 
              Input('saturation_slider', 'value'),
              Input('value_slider', 'value'))
def make_threshold_image(#n_clicks,
                          hue_range, saturation_range, value_range):
    #if n_clicks is None:
    #    raise PreventUpdate()
    #else:
    try:
        img_data = session["current_raw_image"]
    except:
        raise PreventUpdate()
    
        
    print("img data shape: {}".format(img_data.shape))
    for ii in range(4):
        print(ii, np.min(img_data[..., ii]), np.max(img_data[..., ii]))
    np_data = np.array(img_data[..., :3], dtype=np.uint8)

    hsv_lower = np.array([hue_range[0], saturation_range[0], value_range[0]], dtype = float)
    hsv_higher = np.array([hue_range[1], saturation_range[1], value_range[1]], dtype = float)
    
    print("HSV LOWER: ", hsv_lower)
    print("HSV HIGHER: ", hsv_higher)
    print("np data shape: {}".format(np_data.shape))
    blurred_image = ski.filters.gaussian(np_data, sigma=1.0)
    print("blurred image shape: {}".format(blurred_image.shape))
    hsv_image = ski.color.rgb2hsv(blurred_image)

    try:
        binary_mask = cv2.inRange(hsv_image, hsv_lower, hsv_higher)
    except:
        binary_mask = np.zeros(np_data.shape[:2], dtype=bool)
        print ("BINARY MASK: ", binary_mask)
    binary_mask = ski.filters.gaussian(binary_mask, sigma=3.0)
    edge = 20
    half_edge = int(edge/2)
    ix, iy = binary_mask.shape
    new_mask = np.zeros((ix+edge, iy+edge), dtype=np.bool_)
    new_mask[half_edge:-half_edge, half_edge:-half_edge] = binary_mask

    session['current_threshold_image'] = new_mask

    fig = px.imshow(new_mask)


    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)
    return fig

