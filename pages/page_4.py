import dash
from dash import Dash, html, dcc, Input, Output, State, ctx, MATCH, ALL
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

dash.register_page(__name__, path = '/page_4')
app = dash.get_app()
server = app.server

layout = html.Div([
    dcc.Graph(id = 'threshold_image'),

            dbc.Row([
                dbc.Col([
                        html.P('Hue', id='hue_label'),
                    ],
                    width=1
                    ),
                dbc.Col([
                        dcc.RangeSlider(0, 1.0, 0.01, value=[0.4, 0.5], marks=None, allowCross=False, id='hue_slider')
                        ],
                    width=7
                    ),
                ],
                justify='center'
            ),
            dbc.Row([
                dbc.Col([
                        html.P('Saturation', id='saturation_label'),
                    ],
                    width=1
                    ),
                dbc.Col([
                        dcc.RangeSlider(0, 1.0, 0.01, value=[0.5, 1.0], marks=None, allowCross=False, id='saturation_slider')
                        ],
                    width=7
                    ),
                ],
                justify='center'
            ),
            dbc.Row([
                dbc.Col([
                        html.P(' Value ', id='value_label'),
                    ],
                    width=1
                    ),
                dbc.Col([
                        dcc.RangeSlider(0, 1.0, 0.01, value=[0.1, 1.0], marks=None, allowCross=False, id='value_slider')
                        ],
                    width=7
                    ),
                ],
                justify='center'
            ),

])


@app.callback(
    Output('hue_slider', 'value'),
    Output('saturation_slider', 'value'),
    Output('value_slider', 'value'),
    Input('threshold_color', 'data'),
    Input('hue_slider', 'id')
)
def initialize_or_restore_sliders(target_color, page_init):
    active_img_id = session.get('active_image_id', None)
    last_img_id = session.get('slider_last_image_id', None)

    default_hue = [0.4, 0.5]
    default_sat = [0.5, 1.0]
    default_val = [0.1, 1.0]

    if target_color and target_color != 'None' and not any(val is None for val in target_color if isinstance(target_color, list)):
        try:
            hsv_target_color = ski.color.rgb2hsv(np.array(target_color, dtype=np.uint8))
            lower_hue_bound = float(np.clip(hsv_target_color[0] - 0.15, 0.0, 1.0))
            upper_hue_bound = float(np.clip(hsv_target_color[0] + 0.15, 0.0, 1.0))
            default_hue = [lower_hue_bound, upper_hue_bound]
        except:
            pass

    if active_img_id == last_img_id and last_img_id is not None:
        hue = session.get('slider_hue', default_hue)
        sat = session.get('slider_sat', default_sat)
        val = session.get('slider_val', default_val)
        return hue, sat, val
    else:
        session['slider_last_image_id'] = active_img_id
        session['slider_hue'] = default_hue
        session['slider_sat'] = default_sat
        session['slider_val'] = default_val
        session.modified = True
        return default_hue, default_sat, default_val



@app.callback(Output(component_id='threshold_image', component_property= 'figure'),
              Input('hue_slider', 'value'),
              Input('saturation_slider', 'value'),
              Input('value_slider', 'value'))
def make_threshold_image(hue_range, saturation_range, value_range):
    try:
        img_data = session['current_raw_image']
    except:
        raise PreventUpdate()

    session['slider_hue'] = hue_range
    session['slider_sat'] = saturation_range
    session['slider_val'] = value_range
    session.modified = True

    if(img_data.shape[2] == 4):
        np_data = np.array(img_data[..., :3], dtype=np.uint8)
    else:
        np_data = img_data


    print('img data shape: {}'.format(img_data.shape))
    for ii in range(3):
        print(ii, np.min(img_data[..., ii]), np.max(img_data[..., ii]))

    hsv_lower = np.array([hue_range[0], saturation_range[0], value_range[0]], dtype = float)
    hsv_higher = np.array([hue_range[1], saturation_range[1], value_range[1]], dtype = float)

    print('HSV LOWER: ', hsv_lower)
    print('HSV HIGHER: ', hsv_higher)
    print('np data shape: {}'.format(np_data.shape))
    blurred_image = ski.filters.gaussian(np_data, sigma=2.0)
    print('blurred image shape: {}'.format(blurred_image.shape))
    hsv_image = ski.color.rgb2hsv(blurred_image)

    try:
        binary_mask = cv2.inRange(hsv_image, hsv_lower, hsv_higher)
    except:
        binary_mask = np.zeros(np_data.shape[:2], dtype=bool)
        print ('BINARY MASK: ', binary_mask)
    #binary_mask = ski.filters.gaussian(binary_mask, sigma=3.0)
    edge = 20
    half_edge = int(edge/2)
    ix, iy = binary_mask.shape
    new_mask = np.zeros((ix+edge, iy+edge), dtype=np.int64)
    new_mask[half_edge:-half_edge, half_edge:-half_edge] = binary_mask

    session['current_threshold_image'] = new_mask

    palette = qualitative.Safe
    palette2 = qualitative.Alphabet
    colors = []
    colors.append(palette2[8])
    colors.append(palette[0])

    fig = px.imshow(
        new_mask,
        color_continuous_scale=[
            [0.0, colors[0]],  # value 0
            [1.0, colors[1]],  # value 1
        ],
        zmin=0.,
        zmax=1.0,
    )


    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)
    return fig

app.callback
