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


layout = html.Div([
    dcc.Tabs(id = 'adjusting-tabs', value = 'adjust1', children=[
        dcc.Tab(label = 'Adjust 1', value = 'adjust1', children=[
            dcc.Graph(id = 'threshold-image1', config={'displayModeBar': False}),

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

        ]),
        dcc.Tab(label = 'Adjust 2', value = 'adjust2', children=[
            dcc.Graph(id = 'threshold-image2', config={'displayModeBar': False}),
            dbc.Row([
                dbc.Col([
                        html.P('Min-Size', id='min-size_label'),
                    ],
                    width=1
                    ),
                dbc.Col([
                        dcc.Slider(0, 100, 1, value=40, marks=None, id='min-size_slider'),
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
    ])
])

@callback(
    Output('deine-inneren-tabs-id', 'value'),
    Input('inner-tab-store2', 'data')
)
def sync_inner_tabs(store_data):
    return store_data


@dash.callback(
    Output('hue_slider', 'value'),
    Output('saturation_slider', 'value'),
    Output('value_slider', 'value'),
    Input('threshold_color', 'data'),
    Input('current-page-store', 'data')
)
def initialize_or_restore_sliders(target_color, current_page):
    if current_page != 4:
        raise PreventUpdate

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



@dash.callback(Output(component_id='threshold-image1', component_property= 'figure'),
              Output('slider-hsv-store', 'data'),
              Input('hue_slider', 'value'),
              Input('saturation_slider', 'value'),
              Input('value_slider', 'value'),
              Input('dropdown-selection-store', 'data'),
              prevent_initial_call=True,
              )
def make_threshold_image(hue_range, saturation_range, value_range, task_selection):
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
                #layer="above"
            )
        ]
    )
    fig.update_layout(
       margin=dict(t=100, b=100, l=50, r=50)
    )


    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)

    slider_data = {'hue': hue_range, 'sat': saturation_range, 'val': value_range}
    return fig, slider_data


# 2. Adjust
@dash.callback(
    Output('min-size_slider', 'value'),
    Output('simplify_slider', 'value'),
    Output('blur_slider', 'value'),
    Input('threshold-image2', 'id'),
    Input('current-page-store', 'data')
)
def initialize_or_restore_sliders2(page_init, current_page):
    if current_page != 4:
        raise PreventUpdate

    active_img_id = session.get('active_image_id', None)
    last_img_id = session.get('slider2_last_image_id', None)

    default_min_size = 0.4
    default_simplify = 0.1
    default_blur     = 0.12

    if active_img_id == last_img_id and last_img_id is not None:
        min_size = session.get('slider_min_size', default_min_size)
        simplify = session.get('slider_simplify', default_simplify)
        blur     = session.get('slider_blur', default_blur)
        return min_size, simplify, blur
    else:
        session['slider2_last_image_id'] = active_img_id
        session['slider_min_size'] = default_min_size
        session['slider_simplify'] = default_simplify
        session['slider_blur'] = default_blur
        session.modified = True
        return default_min_size, default_simplify, default_blur
    

@dash.callback(
    Output(component_id='threshold-image2', component_property='figure'),
    Output('slider-geo-store', 'data'),
    Input('dropdown-selection-store', 'data'),
    Input('inner-tab-store2', 'data'),
    Input('min-size_slider', 'value'),
    Input('simplify_slider', 'value'),
    Input('blur_slider', 'value'),
    State('current-page-store', 'data'),
    prevent_initial_call=True,
)
def make_threshold_image2(task_selection, current_subpage, current_page, min_size_val, simplify_val, blur_val):
    if current_page != 4:
        raise PreventUpdate
        
    if min_size_val is None: min_size_val = 0.4
    if simplify_val is None: simplify_val = 0.1
    if blur_val is None: blur_val = 0.12

    session['slider_min_size'] = min_size_val
    session['slider_simplify'] = simplify_val
    session['slider_blur'] = blur_val

    if blur_val > 0:
        binary_mask = ski.filters.gaussian(binary_mask, sigma=blur_val * 5.0)
        binary_mask = (binary_mask > 0.5).astype(np.int64)
    else:
        binary_mask = binary_mask.astype(np.int64)

    session['current_threshold_image2'] = binary_mask
    session.modified = True

    image_width = binary_mask.shape[1]
    image_height = binary_mask.shape[0]
    image_buffer  = 20
    half_buffer = int(image_buffer / 2)
    image_width_without_buffer = image_width - image_buffer
    image_height_without_buffer = image_height - image_buffer
    keys = {}
    keys['polygons'] = []
    
    print('image shape: {}'.format(binary_mask.shape))
    print('image dimensions: {} x {}'.format(image_width, image_height))
    print('image width without buffer: {}, image height without buffer: {}'.format(image_width_without_buffer, image_height_without_buffer))
    
    min_size_val = session.get('slider_min_size', 0.4)
    simplify_val = session.get('slider_simplify', 0.1)

    contours = ski.measure.find_contours(binary_mask.T, 0.5)
    for contour in contours:
        p = shapely.Polygon(contour)
        
        min_area_threshold = min_size_val * 100  
        if p.area > min_area_threshold:
            simplify_tolerance = simplify_val * 5.0  
            p2 = p.simplify(simplify_tolerance)
            keys['polygons'].append(p2)

    nesting_levels = {}
    for i, poly in enumerate(keys['polygons']):
        nesting_levels[i] = 0
        for j, other_poly in enumerate(keys['polygons']):
            if i != j and poly.within(other_poly):
                nesting_levels[i] += 1

    np_polys = []
    for i, poly in enumerate(keys['polygons']):
        c = np.array(poly.exterior.coords)
        c = c[:-1, :]
        c[:, 1] = image_height-c[:, 1]
        np_polys.append(np.ceil(c))
    keys['polygons'] = np_polys

    for i, poly in enumerate(keys['polygons']):
        orientation = polygon_orientation(poly)
        if orientation == "CW":
            poly = poly[::-1]
        keys['polygons'][i] = poly

    palette = qualitative.Safe
    palette2 = qualitative.Alphabet
    colors = [palette2[8], palette[0]]

    h, w = binary_mask.shape[:2]

    fig = go.Figure()

    for polygon in keys['polygons']:
        closed_polygon = np.vstack([polygon, polygon[0]])

        x_coords = closed_polygon[:, 0]
        y_coords = closed_polygon[:, 1]
        
        fig.add_trace(go.Scatter(
            x=x_coords, 
            y=y_coords, 
            fill="toself",              
            fillcolor="rgba(0, 123, 255, 0.4)", 
            line=dict(color="blue", width=3),   
            mode="lines+markers", 
        ))

    fig.update_layout(
        xaxis=dict(
            range=[0, w], 
            showgrid=False, 
            mirror=True, 
            showline=True, 
            linecolor='black',
            scaleanchor="y",  
            scaleratio=1
        ),
        yaxis=dict(
            range=[0, h], 
            showgrid=False, 
            mirror=True, 
            showline=True, 
            linecolor='black'
        ),
        
        plot_bgcolor="white",
        
        width=800,
        height=int(800 * (h / w)),
        
        showlegend=True
    )

    match task_selection:
        case "btn-opt-a": task_src = '/assets/aufgabe0.png'
        case "btn-opt-b": task_src = '/assets/aufgabe1.png'
        case "btn-opt-c": task_src = '/assets/aufgabe2.png'
        case "btn-opt-d": task_src = '/assets/aufgabe3.png'
        case _ : task_src = '/assets/aufgabe0.png'

    fig.update_layout(
        images=[dict(source=task_src, xref="paper", yref="paper", x=0.5, y=0.5, sizex=1.5, sizey=1.5, xanchor="center", yanchor="middle")],
        margin=dict(t=100, b=100, l=50, r=50),
        coloraxis_showscale=False
    )
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)
    
    geo_data = {'min_size': min_size_val, 'simplify': simplify_val, 'blur': blur_val}

    return fig, geo_data


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