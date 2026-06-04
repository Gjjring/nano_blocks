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

dash.register_page(__name__, path = '/page_3')
app = dash.get_app()
server = app.server

layout = html.Div([
            html.Hr(),
            dcc.Graph(id = 'raw-camera'),
            html.Hr(),
            
            dbc.Row([
        
            # Linke Spalte (Breite 3 von 12) für die quadratischen Farbanzeigen
            dbc.Col([
                html.Button(
                    '', id='temporary_color_output',
                    disabled=True,
                    style={'width':'50px', 'height':'50px', 'background-color':'white', 'marginRight': '10px'} # kleiner Abstand nach rechts
                ),
                
                html.Button(
                    '', id='color_output',
                    disabled=True,
                    style={'width':'50px', 'height':'50px', 'background-color':'white'}
                ),
            ], width=3, style={'display': 'flex', 'flexDirection': 'row'}), # Setzt die Buttons sauber nebeneinander
            
            # Rechte Spalte (Breite 9 von 12) für die RGB-Inputs
            dbc.Col([
                dbc.Row([
                    dbc.Col([
                        dbc.InputGroup([
                            dbc.InputGroupText("Red"),
                            dcc.Input(id='red_input', type='number', min=0, max=255, step=1, placeholder='255', className='form-control'),
                        ], size="sm"),
                    ], width=4),
                    
                    dbc.Col([
                        dbc.InputGroup([
                            dbc.InputGroupText("Green"),
                            dcc.Input(id='green_input', type='number', min=0, max=255, step=1, placeholder='255', className='form-control'),
                        ], size="sm"),
                    ], width=4),
                    
                    dbc.Col([
                        dbc.InputGroup([
                            dbc.InputGroupText("Blue"),
                            dcc.Input(id='blue_input', type='number', min=0, max=255, step=1, placeholder='255', className='form-control'),
                        ], size="sm"),
                    ], width=4),
                ], className="g-2"),
            ], width=9),
            
        ], align="center"),
])

@app.callback(
    Output('raw-camera', 'figure'),
    [Input('camera-start-dummy', 'id'), # Fires instantly on page load because this element renders
     Input('dropdown-selection-store', 'data')]
)
def load_selected_image_into_graph(_, task_selection):
    current_raw_image = session.get('current_raw_image', None)
    
    if current_raw_image is None:
        # If no image has been processed yet, return an empty figure placeholder
        return go.Figure()
        
    # Plot the raw data safely now that the element exists on screen
    fig = px.imshow(current_raw_image)

    if task_selection == "btn-opt-a":
        task_src ='/assets/aufgabe0.png'
    elif task_selection == "btn-opt-b":
        task_src ='/assets/aufgabe1.png'
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
    return fig


def make_color(r=0,g=0,b=0):
    color_str = 'rgb({}, {}, {})'.format(r,g,b)
    return color_str
    
@dash.callback(Output(component_id='temporary_color_output', component_property= 'style'),
              dash.dependencies.Input('raw-camera', 'hoverData'),
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

@dash.callback(Output(component_id='color_output', component_property= 'style'),
               Output(component_id='threshold_color', component_property= 'data'),
               Input(component_id='red_input', component_property= 'value'),
               Input(component_id='green_input', component_property= 'value'),
               Input(component_id='blue_input', component_property= 'value'),
               prevent_initial_call=True)
def color_box_update(red, green, blue):
    color = make_color(red, green, blue)
    print(color)
    style = {'textAlign':'center', 'width':'50px', 'height':'50px', 'background-color':color}
    data = [red, green, blue]
    return style, data


@dash.callback(dash.dependencies.Output('red_input', 'value'),
               dash.dependencies.Output('green_input', 'value'),
               dash.dependencies.Output('blue_input', 'value'),
               dash.dependencies.Input('raw-camera', 'clickData'),
               prevent_initial_call=True)
def update_color_state(click_data):
    if click_data is None:
        raise PreventUpdate()
    else:
        #print(hover_data)
        color = click_data['points'][0]['color']
        red = color['0']
        green = color['1']
        blue = color['2']
        return red, green, blue
