import dash
from dash import Dash, html, dcc, Input, Output, State, ctx, MATCH, ALL, no_update
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

dash.register_page(__name__, path = '/page_3')
app = dash.get_app()
server = app.server

layout = html.Div([
            html.Hr(),
            dcc.Graph(id = 'raw-camera', config={'displayModeBar': False}),
            html.Hr(),
            
            html.Div(
                [
                    html.Button(
                        '', id='temporary_color_output',
                        disabled=True,
                        style={'width':'50px', 'height':'50px', 'background-color':'white', 'marginRight': '10px'}
                    ),                    
                    html.Button(
                        '', id='color_output',
                        disabled=True,
                        style={'width':'50px', 'height':'50px', 'background-color':'white'}
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "center",
                    "gap": "10px",
                    "marginBottom": "15px",
                },
            ),            
            html.Div(
                [
                    dbc.InputGroup([
                        dbc.InputGroupText("Red"),
                        dcc.Input(id='red_input', type='number', min=0, max=255, step=1, placeholder='255', className='form-control'),
                    ],
                    #size="sm"
                    style={"width": "180px"},
                    ),                
                    dbc.InputGroup([
                        dbc.InputGroupText("Green"),
                        dcc.Input(id='green_input', type='number', min=0, max=255, step=1, placeholder='255', className='form-control'),
                    ],
                    #size="sm"
                    style={"width": "180px"},
                    ),                
                    dbc.InputGroup([
                        dbc.InputGroupText("Blue"),
                        dcc.Input(id='blue_input', type='number', min=0, max=255, step=1, placeholder='255', className='form-control'),
                    ],
                    #size="sm"
                    style={"width": "180px"},
                    ),
                
                ],            
                 style={
                "display": "flex",
                "flexDirection": "column",
                "alignItems": "center",
                "justifyContent": "center",
                #"height": "40vh",   # adjust as needed
                #"gap": "10px",
            },
            )
            
])

@app.callback(
    Output('raw-camera', 'figure'),
    [Input('camera-start-dummy', 'id'), 
     Input('dropdown-selection-store', 'data')]
)
def load_selected_image_into_graph(_, task_selection):
    current_raw_image = session.get('current_raw_image', None)
    
    if current_raw_image is None:
        fig = go.Figure()
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)
        fig.update_layout(    
            plot_bgcolor="white",
            paper_bgcolor="white",
        )        
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)        
        return fig
        
    fig = px.imshow(current_raw_image)

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
    return fig


def make_color(r=0,g=0,b=0):
    color_str = 'rgb({}, {}, {})'.format(r,g,b)
    return color_str
    
@app.callback(Output('temporary_color_output','style'),
              Input('raw-camera', 'hoverData'),
              prevent_initial_call=True)
def update_temporary_color_state(hover_data):
    if hover_data is None:
        raise PreventUpdate()
    else:
        color = hover_data['points'][0]['color']
        red = color['0']
        green = color['1']
        blue = color['2']
        color = make_color(red, green, blue)
        style = {'textAlign':'center', 'width':'50px', 'height':'50px', 'background-color':color}
        return style




@app.callback(Output('color_output','style'),
               Output('threshold_color','data'),
               Input('red_input', 'value'),
               Input('green_input', 'value'),
               Input('blue_input', 'value'),               
               State("threshold_color", "data"),
               prevent_initial_call=True)
def color_box_update(red, green, blue, threshold_color):
    if ctx.triggered_id == "current-page-store":
        red = threshold_color[0]
        green = threshold_color[1]
        blue = threshold_color[2]
    color = make_color(red, green, blue)
    print(color)
    style = {'textAlign':'center', 'width':'50px', 'height':'50px', 'background-color':color}
    data = [red, green, blue]
    return style, data



@app.callback(Output('red_input', 'value'),
              Output('green_input', 'value'),
              Output('blue_input', 'value'),
              Input('raw-camera', 'clickData'),
              Input('current-page-store', 'data'),
              State('threshold_color','data'),
               prevent_initial_call=False)
def update_color_state(click_data, current_page, current_color):

    print(f"update_color_state current page: {current_page}")
    if not current_page == 3:
        print("raising prevent update")
        raise PreventUpdate()
    if click_data is None:
        return current_color
    else:
        #print(hover_data)
        color = click_data['points'][0]['color']
        red = color['0']
        green = color['1']
        blue = color['2']
        session['target_color_updated'] = True
        return red, green, blue


