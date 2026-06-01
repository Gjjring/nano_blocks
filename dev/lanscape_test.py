# -*- coding: utf-8 -*-
"""
Created on Mon Jan 12 21:36:07 2026

@author: Phill
"""
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  5 22:15:41 2025

@author: Phill
"""
# app.py
from dash import Dash, html, dcc, Input, Output, State, ctx
import dash
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

from landscape_plotly import Landscape, Landscape_Plotter

app = Dash(__name__, suppress_callback_exceptions=True,
           external_stylesheets=[dbc.themes.MORPH])
server = app.server




app.layout = html.Div([       
    dcc.Store(id='selections',
              data={'n_selections':0, "best_func_val":None, "func_vals":[]}),    
    dbc.Row(
        dbc.Col(
            html.H1("Function Landscape"),
            width=4,
            className="text-center"
        ),
        justify="center",
        #align="center"
    ),
    dbc.Row(        
        children = [
            dbc.Col(
                children = [  
                    dbc.ButtonGroup(
                        [dbc.Button("N Guesses: 0",
                                    id="n-guesses-btn",
                                    disabled=True,
                                    color="secondary"),
                         dbc.Button("Current Max: ",
                                id="current-max-btn",
                                    disabled=True,
                                    color="secondary",)
                         ] 
                        )
                    # dbc.Button("N Guesses: 0",
                    #         id="n-guesses-btn",
                    #         disabled=True,
                    #         color="secondary"),
                    # dbc.Button("Current Max: ",
                    #        id="current-max-btn",
                    #        disabled=True,
                    #        color="secondary",)
                ],
                width="auto"
                #width={"size": 6, "offset": 1},
            ),
            dbc.Col(
                children = [
                    html.Center("# Peaks"),
                    dcc.Slider(1, 5, 1, value=1, id='n-peaks-slider'),
                ],
                width=1,
                align='center',
            ),
        ],
        justify="center",
    ),
    # html.Hr(),
    dbc.Row(
        #align='center',
        justify='center',
        children = [
            dbc.Col(
                id='ml-col',
                width="auto",
                # style={"display": "none"},
                align='center',
                children = [
                    dcc.Graph(id = 'ml-model',
                              config={"displayModeBar": False}),
                ]
            ),            
            dbc.Col(
                width="auto",
                children = [
                    dcc.Graph(id = 'landscape',
                              config={"displayModeBar": False}),
                    #justify='center',
                ]
            ),            
            dbc.Col(
                id='gradient-col',
                width="auto",
                style={"display": "none"},
                align='center',
                children = [
                    dcc.Graph(id = 'compass',
                              config={"displayModeBar": False}),
                    # dbc.Card(
                    #     [
                    #         #dbc.CardImg(src="", top=True),
                    #         dbc.CardBody(
                    #             [
                    #                 html.H4("Card title", className="card-title"),
                    #                 html.P(
                    #                     "Some quick example text to build on the card title and "
                    #                     "make up the bulk of the card's content.",
                    #                     className="card-text",
                    #                 ),
                    #             ]
                    #         ),
                    #     ],
                    #     style={"width": "18rem"},
                    # )
                ]
            ),
        ]
    ),
    dbc.Row(
        justify="center",
        children = [
            dbc.Col(
                children = [    
                    #html.Button('Reset Mask', id='reset-mask', n_clicks=0),                    
                    dbc.Button("Reset Mask", id='reset-mask',  color="primary", n_clicks=0),
                    dbc.Button("Randomise", id='new-seed-btn',  color="primary", n_clicks=0),
                    dbc.Button("Show Gradient", id='gradient-toggle',  color="primary", n_clicks=0),
                    dbc.Button("Show AI Advisor", id='ml-toggle',  color="primary", n_clicks=0),
                    dbc.Button("Remove Mask", id='remove-mask-btn',  color="primary", n_clicks=0),
                    #dbc.Button("Left"),
                ],
                width="auto"
            ),
            # dbc.Col(
            #     children = [    
            #         dbc.Button("Left"),
            #     ]
            # ),
            # dbc.Col(                
            #     dbc.ButtonGroup(
            #         [
            #             [dbc.Button("Left"), dbc.Button("Middle"), dbc.Button("Right")],
            #         ],                        
            #     )                
            # ),
        ],
        align="center",
    ),
    html.Hr(),
    dbc.Row(
        justify="center",
        id='gradient-row',
        style={"display": "none"},
        children = [
            dbc.Col(
                children = [    
                    dbc.ButtonGroup(
                        [dbc.Button("X Gradient: ",
                                    id="x-gradient",
                                    disabled=True,
                                    color="secondary"),
                         dbc.Button("Y Gradient: ",
                                    id="y-gradient",
                                    disabled=True,
                                    color="secondary",)
                         ] 
                        )
                ],
                width="auto"
            ),
        ]
    ),
    html.Hr(),
    
            # dbc.Col(
            #     children = [    
            #         dbc.Button("Up"),                
            #     ],
            #     width='auto',
    
    
    
])

ls = Landscape()
ls.init_landscape()
ls.init_mask()
lp = Landscape_Plotter(ls)
lp.init_plot()
lp.init_ml_plot()
lp.update_landscape()
# ls.uncover([0, 0])

# @callback(
#     Output('slider-output-container', 'children'),
#     Input('n-peaks-slider', 'value'))
# def update_output(value):
#     return 'You have selected "{}"'.format(value)

@app.callback(Output(component_id='landscape', component_property= 'figure'),
              Input('selections', 'data'),
              Input('new-seed-btn', 'n_clicks'),
              Input('remove-mask-btn', 'n_clicks'),
              Input('n-peaks-slider', 'value'),
              #State({"type":"img-select","index":dash.ALL}, "value")
              )
def plot_function_landscape(data, n_clicks_seed, n_clicks_remove_mask, n_peaks):
    
    #print(data['mask'])
    # if not data['mask'] is None:
        
    #     ls.mask = np.array(data['mask'])
    print(dash.callback_context.triggered_id)
    if dash.callback_context.triggered_id == "selections":
        if 'selections' not in data:
            print("selections not in data")
            fig = lp.fig    
        else:
            selections = data['selections']
            if len(selections) == 0:
                fig = lp.reset_mask() 
            else:    
                fig = lp.update_mask(selections[-1]) 
           
        if "current_selection" not in data:
            print("selections not in data")
        else:        
            fig = lp.update_current_pos(data['current_selection'])
    elif dash.callback_context.triggered_id == "new-seed-btn":
        ls.seed += 1
        ls.init_landscape()
        ls.init_mask()
        ls.previous_pos = None
        ls.current_pos = None       
        fig = lp.update_landscape()
        fig = lp.reset_mask()
    elif dash.callback_context.triggered_id == "remove-mask-btn":
        ls.remove_mask()
        fig = lp.reset_mask()
    elif dash.callback_context.triggered_id == "n-peaks-slider":
        print(f"setting n peaks to: {n_peaks}")
        ls.n_peaks = n_peaks
        ls.init_landscape()
        ls.init_mask()
        ls.previous_pos = None
        ls.current_pos = None       
        fig = lp.update_landscape()
        fig = lp.reset_mask()
    else:
        fig = lp.fig
    return fig

@app.callback(
    Output(component_id='ml-model', component_property= 'figure'),
    Input('landscape', 'figure'),
    #Input('reset-mask', 'n_clicks'),
    #Input('new-seed-btn', 'n_clicks'),
    #Input('n-peaks-slider', 'value'),
    #Input('selections', 'data'),
)
def update_ml_model(figure):
    print("update_ml_plot called")
    
    ls.init_surrogate_model()
    fig = lp.update_ml_plot()
    return fig


@app.callback(
    Output(component_id='compass', component_property= 'figure'),
    Input('reset-mask', 'n_clicks'),
    Input('new-seed-btn', 'n_clicks'),
    Input('n-peaks-slider', 'value'),
    Input('selections', 'data'),
)
def plot_compass(n_clicks, n_clicks2, n_peaks, data):
    # if dash.callback_context.triggered_id == "selections":
        #ls.update_ml_model(data['selections'], data['func_vals'])
    
    
    fig = lp.plot_gradient_compass()
    return fig


@app.callback(
    Output("x-gradient", "children"),
    Input('reset-mask', 'n_clicks'),
    Input('new-seed-btn', 'n_clicks'),
    Input('n-peaks-slider', 'value'),
    Input('selections', 'data'),
)
def set_gradient_x(n_clicks, n_clicks2, n_peaks, data):
    if (dash.callback_context.triggered_id == "reset-mask" or
        dash.callback_context.triggered_id == "new-seed-btn"):
        text="X Gradient: "
    else:
        if ls.current_gradients is None:
            return dash.no_update    
        grad = ls.current_gradients
        text = "X Gradient: " + f"{grad[0]:.1f}"
    return text


@app.callback(
    Output("y-gradient", "children"),
    Input('reset-mask', 'n_clicks'),
    Input('new-seed-btn', 'n_clicks'),
    Input('n-peaks-slider', 'value'),
    Input('selections', 'data'),
)
def set_gradient_y(n_clicks, n_clicks2, n_peaks, data):
    if (dash.callback_context.triggered_id == "reset-mask" or
        dash.callback_context.triggered_id == "new-seed-btn"):
        text="Y Gradient: "
    else:
        if ls.current_gradients is None:
            return dash.no_update    
        grad = ls.current_gradients
        text = "Y Gradient: " + f"{grad[1]:.1f}"
    return text    
    
@app.callback(
    Output("gradient-row", "style"),
    Input("gradient-toggle", "n_clicks"),
)
def toggle_gradient_row(n):
    if n % 2 == 0:
        return {"display": "none"}
    return {"display": "flex"}

@app.callback(
    Output("gradient-col", "style"),
    Input("gradient-toggle", "n_clicks"),
)
def toggle_gradient_compass(n):
    if n % 2 == 0:
        return {"display": "none"}
    return {"display": "flex"}

@app.callback(
    Output("ml-col", "style"),
    Input("ml-toggle", "n_clicks"),
)
def toggle_ml_advisor(n):
    if n % 2 == 0:
        return {"display": "flex"}
    return {"display": "flex"}


@app.callback(
    Output("gradient-toggle", "children"),
    Input("gradient-toggle", "n_clicks"),
)
def toggle_gradient_btn(n):
    if n % 2 == 0:
        return "Show Gradient"
    return "Hide Gradient"
    

@app.callback(
    Output("n-guesses-btn", "children"),
    Input("selections", "data"),
)
def update_n_guesses_btn(data):
    if "n_selections" not in data:
        return dash.no_update
    text= f"N Guesses: {data['n_selections']}"
    return text

@app.callback(
    Output("n-guesses-btn", "color"),
    Input("selections", "data"),
)
def update_max_val_btn_color(data):
    if "best_func_val" not in data or data['best_func_val'] is None:
        return "secondary"
    if data['best_func_val'] == 100:
        return "info"
    else:
        return "secondary"

@app.callback(
    Output("current-max-btn", "children"),
    Input("selections", "data"),
)
def update_max_val_btn(data):
    if "best_func_val" not in data or data['best_func_val'] is None:
        return "Current Max : "
    text= f"Current Max: {data['best_func_val']}"
    return text

@app.callback(
    Output("current-max-btn", "color"),
    Input("selections", "data"),
)
def update_max_val_btn_color(data):
    if "best_func_val" not in data or data['best_func_val'] is None:
        return "secondary"
    if data['best_func_val'] == 100:
        return "success"
    else:
        return "secondary"



@app.callback(
    Output("selections", "data"),
    Input("landscape", "clickData"),
    Input('reset-mask', 'n_clicks'),
    Input('new-seed-btn', 'n_clicks'),
    State("selections", "data"),
    prevent_initial_call=True,
    )
def on_click(clickData, reset_n_clicks, new_seed_n_clicks, data):
    print(dash.callback_context.triggered_id)
    if dash.callback_context.triggered_id == "landscape":
        if clickData is None:
            return dash.no_update    
        
        point = clickData["points"][0]    
        
        # if data['mask'] is None:
        #     try:
        #         data['mask'] = np.copy(ls.mask)
        #     except:
        #         return dash.no_update
        # else:
        #     data['mask'] = np.array(data['mask'])
        if "selections" not in data:
            data['selections'] = []
        x= point['x']
        y= point['y']-1
        print(x, y)
        print("######## Data ######")
        print(data)
        ls.current_pos = np.array([x, y])
        data['current_selection'] = [x, y]
        new_value = True
        ls.calc_gradients()
        for selection in data['selections']:
            if selection[0] == x and selection[1] == y:
                new_value = False
        if new_value:
            data['selections'].append((x, y))
        func_landscape = ls.function_landscape.T
        func_val = int(np.round(func_landscape[x, y]))
        if "func_vals" not in data:
            data['func_vals'] = []
        func_vals = data['func_vals']
        func_vals.append(func_val)
        data['func_vals'] = func_vals
        if data['best_func_val'] is None:
            data['best_func_val'] = func_val
        if func_val > data['best_func_val']:
            data['best_func_val'] = func_val
            
        data['n_selections'] = len(data['selections'])
        
    elif dash.callback_context.triggered_id == "reset-mask":        
        #mask = np.ones((ls.board_resolution, ls.board_resolution), dtype=bool)
        ls.init_mask()
        selections = []
        #ls.mask= mask
        #ls.mask= data['selections']
        ls.current_pos = None
        
        data = {'selections':selections, 'n_selections':0, 'best_func_val':None, 'func_vals':[]}
    elif dash.callback_context.triggered_id == "new-seed-btn":
        data = {'selections':[], 'n_selections':0, 'best_func_val':None, 'func_vals':[]}
    # data['points'].append((point['x'], point['y']))    
    return data

# @app.callback(
#     Output("selections", "data"),
#     Input('reset-mask', 'n_clicks'),
#     prevent_initial_call=True,
#     allow_duplicate=True,
# )
# def reset_mask(n_clicks):
#     mask = np.ones((ls.board_resolution, ls.board_resolution), dtype=bool)
#     data = {'mask':mask}
#     return data
    
    
# @app.callback(
#     Output("debug", "children"),
#     Input("selections", "data")
# )
# def show_store(data):
#     return data

if __name__ == "__main__":
    app.run(debug=True)