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

dash.register_page(__name__, path = '/page_4')
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
    dcc.Store(id='previous_threshold_color', data=[255, 255, 255]),
    dcc.Loading(
        type='circle',
        children=[
            dcc.Graph(id = 'threshold-image1', figure=empty_fig, config={'displayModeBar': False}),
        ]
    ),
    dbc.Row([
        dbc.Col([
                html.P('Hue', id='hue_label'),
            ],
            width=1
            ),
        dbc.Col([            
            html.Div(
                style={
                    "height": "20px",
                    "borderRadius": "5px",
                    "margin": "10px",
                    "background": "linear-gradient(to right, red, yellow, lime, cyan, blue, magenta, red)",
                }
            ),            
            ],
            width=7
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
            html.Div(
                style={
                    "height": "20px",
                    "borderRadius": "5px",
                    "margin": "10px",
                    "background": "linear-gradient(to right, gray, white)",
                }
            ),            
            ],
            width=7
        ),
        dbc.Col([
                dcc.RangeSlider(0, 1.0, 0.01, value=[0.05, 1.0], marks=None, allowCross=False, id='saturation_slider')
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
            html.Div(
                style={
                    "height": "20px",
                    "borderRadius": "5px",
                    "margin": "10px",
                     "background": "linear-gradient(to right, black, white)",
                }
            ),            
            ],
            width=7
        ),
        dbc.Col([
                dcc.RangeSlider(0, 1.0, 0.01, value=[0.05, 1.0], marks=None, allowCross=False, id='value_slider')
                ],
            width=7
            ),
        ],
        justify='center'
    ),

]),


@app.callback(
    Output('hue_slider', 'value'),
    Output('saturation_slider', 'value'),
    Output('value_slider', 'value'),
    #Output("previous_threshold_color", "data"),
    Input("threshold_color", 'data'),
    Input('current-page-store', 'data'),
    State("slider-hsv-store", 'data'),
    #State("previous_threshold_color", "data"),
    prevent_initial_call=False,
)
def initialize_or_restore_sliders(target_color, current_page, slider_data):
    print("##############################")
    print("##############################")    
    print(f"initialize_or_restore_sliders, current_page: {current_page}")
    print("##############################")
    print("##############################")
    if current_page != 4:
        raise PreventUpdate

    updated_target = session.get("target_color_updated", False)
    default_hue = [0.4, 0.5]
    default_sat = [0.05, 1.0]
    default_val = [0.05, 1.0]
    default_hue = slider_data.get('hue', default_hue)
    default_sat = slider_data.get('sat', default_sat)
    default_val = slider_data.get('val', default_val)
    
    print("##############################")
    print(f"target color: {target_color}")
    print(f"triggering id: {ctx.triggered_id}")
    print(f"updated_target: {updated_target}")
    #print(f"prev target color: {prev_target_color}")
    if (target_color and 
        target_color != 'None' and
        not any(val is None for val in target_color if isinstance(target_color, list)) and 
        #not np.all(target_color==prev_target_color)):
        updated_target):
        try:            
            print("taking color from target color")
            hsv_target_color = ski.color.rgb2hsv(np.array(target_color, dtype=np.uint8))
            lower_hue_bound = np.round(float(np.clip(hsv_target_color[0] - 0.15, 0.0, 1.0)), 2)
            upper_hue_bound = np.round(float(np.clip(hsv_target_color[0] + 0.15, 0.0, 1.0)), 2)
            default_hue = [lower_hue_bound, upper_hue_bound]

            lower_saturation_bound = np.round(float(np.clip(hsv_target_color[1] - 0.3, 0.0, 1.0)), 2)
            upper_saturation_bound = np.round(float(np.clip(hsv_target_color[1] + 0.3, 0.0, 1.0)), 2)
            default_sat = [lower_saturation_bound, upper_saturation_bound]

            lower_value_bound = np.round(float(np.clip(hsv_target_color[2] - 0.3, 0.0, 1.0)), 2)
            upper_value_bound = np.round(float(np.clip(hsv_target_color[2] + 0.3, 0.0, 1.0)), 2)
            default_val = [lower_value_bound, upper_value_bound]            
            #print(f"hue from target: {default_hue}")
            prev_target_color = target_color
            session['target_color_updated'] = False
        except:
            print("taking color from slider store data")
            default_hue = slider_data.get('hue')#, default_hue)
            default_sat = slider_data.get('sat')#, default_sat)
            default_val = slider_data.get('val')#, default_val)
    
    hue = default_hue    
    print(f"chosen hue: {hue}")
    sat = default_sat
    val = default_val
    #sat = slider_data.get('sat', default_sat)
    #val = slider_data.get('val', default_val)
    return hue, sat, val


@app.callback(Output("slider-hsv-store", 'data'),
              Input("hue_slider", "value"),
              Input("saturation_slider", "value"),
              Input("value_slider", "value"),              
              State("slider-hsv-store", 'data'),              
)
def store_hue_slider(hue_val, sat_val, val_val, current_data):
    print(f"calling id: {ctx.triggered_id}")
    current_data['hue'] = hue_val
    current_data['sat'] = sat_val
    current_data['val'] = val_val
    print(f"setting stored color to: {current_data}")
    return current_data

@app.callback(Output(component_id='threshold-image1', component_property= 'figure'),
              #Output('slider-hsv-store', 'data'),
              Input('hue_slider', 'value'),
              Input('saturation_slider', 'value'),
              Input('value_slider', 'value'),
              Input('dropdown-selection-store', 'data'),    
              #prevent_initial_call=True,
              )
def make_threshold_image(hue_range, saturation_range, value_range, task_selection):
    try:
        img_data = session['current_raw_image']
    except:
        raise PreventUpdate()

    

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
    
    #blurred_image = ski.filters.gaussian(np_data, sigma=2.0)
    #print('blurred image shape: {}'.format(blurred_image.shape))
    hsv_image = ski.color.rgb2hsv(np_data)

    try:
        binary_mask = cv2.inRange(hsv_image, hsv_lower, hsv_higher)
    except:
        binary_mask = np.zeros(np_data.shape[:2], dtype=bool)
        print ('BINARY MASK: ', binary_mask)
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
            [0.0, colors[0]],
            [1.0, colors[1]],
        ],
        zmin=0.,
        zmax=1.0,
    )

    if task_selection == "btn-opt-a":
        task_src ='/assets/aufgabe0.png'
    elif task_selection == "btn-opt-b":
        task_src ='/assets/aufgabe1.png'
    elif task_selection == "btn-opt-c":
        task_src ='/assets/aufgabe2.png'
    elif task_selection == "btn-opt-d":
        task_src ='/assets/aufgabe3.png'
    else:
        task_src ='/assets/aufgabe0.png'

    fig.update_layout(
        images=[
            dict(
                source=task_src,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                sizex=1.5,
                sizey=1.5,
                xanchor="center",
                yanchor="middle",
            )
        ]
    )
    fig.update_layout(
       margin=dict(t=100, b=100, l=50, r=50)
    )


    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)

    #slider_data = {'hue': hue_range, 'sat': saturation_range, 'val': value_range}
    return fig#, slider_data


