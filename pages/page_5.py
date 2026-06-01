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

dash.register_page(__name__, path = "/page_5")
app = dash.get_app()
server = app.server

layout = html.Div([
    html.Hr(),
    dcc.Graph(id = 'jcm_output'),
])

def run_jcmwave_simulation(threshold_data):
    keys = {}
    keys['cd_width'] = threshold_data.shape[1]
    keys['cd_height'] = threshold_data.shape[0]
    keys['polygons'] = []

    contours = ski.measure.find_contours(threshold_data.T, 0.5)
    for contour in contours:
        p = shapely.Polygon(contour)
        if p.area > 1000:
            big_poly = p

            
            p2 = p.simplify(15.)            
            
            c = np.array(p2.exterior.coords)
            c = c[:-1, :]            
            c[:, 1] = keys['cd_height']-c[:, 1]
            mid_point = np.tile(np.mean(c, axis=0), c.shape[0]).reshape(c.shape)            
          
            keys['polygons'].append(c)
    
    #jcmwave.jcmt2jcm("layout.jcmt", keys=keys)
    #jcmwave.geo(".")
    results = jcmwave.solve(os.path.join("jcmwave","project.jcmpt"), keys=keys)
    cart_field = results[1]

    e_field = np.linalg.norm(np.abs(cart_field['field'][0]), axis=2)**2

    return e_field

@app.callback([Output(component_id='jcm_output', component_property= 'figure'),
              ],
              [Input("current-page-store", "data"),
                ])
def make_jcmwave_simulation(data):
    print("make_jcmwave_simulation was called")
    print("Value of data: ", data, type(data))
    if data is None:
        raise PreventUpdate()
    elif not data == 5:
        raise PreventUpdate()
    else:
        try:
            threshold_data = session["current_threshold_image"]
            print("Reached")
        except:
            raise PreventUpdate()
        
            
        print("img data shape: {}".format(threshold_data.shape))
        for ii in range(1):
            print(ii, np.min(threshold_data), np.max(threshold_data))
        
        field_data = run_jcmwave_simulation(threshold_data)
    
        fig = px.imshow(field_data.T, origin="lower")

    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)
    return [fig]



