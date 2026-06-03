# -*- coding: utf-8 -*-
'''
Created on Fri Dec  5 22:15:41 2025

@author: Phill
'''
# app.py

import dash
from dash import Dash, html, dcc, Input, Output, State, ctx, no_update, callback
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

app = Dash(__name__, use_pages = True, suppress_callback_exceptions = True)
server = app.server

server.config['SESSION_TYPE'] = 'filesystem'
server.config['SESSION_FILE_DIR'] = './sessions'
server.config['SESSION_PERMANENT'] = False
server.config['SESSION_USE_SIGNER'] = True
server.config['SECRET_KEY'] = 'CHANGE_THIS'

Session(server)


# --- Layout ---
app.layout = html.Div(id = 'site', children = [
    dcc.Store(id='raw_image_data'),
    dcc.Store(id='threshold_color'),
    dcc.Store(id='current-page-store', data = 1),
    dcc.Store(id='inner-tab-store', data='camera'),
    dcc.Store(id='blocked_tabs', data=False, storage_type='session'),
    dcc.Store(id='dropdown-selection-store', data='btn-opt-a'),

    dcc.Store(id='initial-load-detector', data=False, storage_type='memory'),
    dcc.Location(id='url', refresh=False),

    html.Div(id='camera-start-dummy', style={'display': 'none'}),
    html.Div(id='capture-dummy', style={'display': 'none'}),
    html.Div(id='jcm_output-dummy', style={'display': 'none'}),

    html.Div(id = 'content', children = [
        dcc.Tabs(id='page-tabs', value = '1', children = [
            dcc.Tab(label='Create Image', value = '1'),
            dcc.Tab(label='Gallery', value = '2'),
            dcc.Tab(label='Color', value = '3'),
            dcc.Tab(label='Adjust', value = '4'),
            dcc.Tab(label='Final', value = '5'),
        ]),
        html.Div(id = 'anchor', children=[
            html.Div(dash.page_container, id = 'content-page'),
            html.Div(id='menu-container', children = [
                html.Button('Task Selection',id = 'task-selection-button'),
                html.Div(id="custom-dropdown-menu", children=[
                    html.Button("None", id="btn-opt-a", className="menu-item", n_clicks=0),
                    html.Button("Task 1", id="btn-opt-b", className="menu-item", n_clicks=0),
                    html.Button("Task 2", id="btn-opt-c", className="menu-item", n_clicks=0),
                    html.Button("Task 3", id="btn-opt-d", className="menu-item", n_clicks=0),
                ]),
            ]),
        ]),
        
    ]),

    html.Div(id = 'navigation', children = [
        html.Button('Previous', id = 'btn-prev', className = 'navBtn', n_clicks = 0, disabled = True),
        html.Span('Page 1 of 5', id = 'page-indicator'),
        html.Button('Next', id ='btn-next', className = 'navBtn', n_clicks = 0), 
    ])

])

@app.callback(
    Output('_pages_location', 'pathname', allow_duplicate=True), 
    Output('current-page-store', 'data'),   
    Output('page-tabs', 'value'),          
    Output('page-indicator', 'children'), 
    Output('btn-prev', 'disabled'),        
    Output('btn-next', 'disabled'),        
    Output('blocked_tabs', 'data'),
    Input('btn-prev', 'n_clicks'),
    Input('btn-next', 'n_clicks'),
    Input('page-tabs', 'value'),
    State('current-page-store', 'data'),
    State('blocked_tabs', 'data'),
    prevent_initial_call=True
)
def sync_navigation(prev_clicks, next_clicks, tab_value, current_page, blocked_tabs):
    triggered_id = ctx.triggered_id

    if triggered_id == 'btn-next' and current_page < 5:
        current_page += 1
    elif triggered_id == 'btn-prev' and current_page > 1:
        current_page -= 1
    elif triggered_id == 'page-tabs':
        current_page = int(tab_value)
    
    if current_page == 1:
        target_path = '/'
    else:
        target_path = f'/page_{current_page}'

    indicator_text = f'Page {current_page} of 5'
    disable_prev = (current_page == 1)
    disable_next = (current_page == 5)
 
    if current_page == 2:
        disable_next = True

    update_tab_value = str(current_page)
    return target_path, current_page, update_tab_value, indicator_text, disable_prev, disable_next, blocked_tabs

@app.callback(
    Output('btn-next', 'disabled', allow_duplicate=True),
    Input('gallery-selection-status', 'data'),
    State('current-page-store', 'data'),
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def update_next_button_from_gallery(gallery_has_selection, current_page):
    if current_page == 2:
        return not gallery_has_selection
    raise PreventUpdate


@app.callback(
    Output('page-tabs', 'style'),
    Input('blocked_tabs', 'data')
)
def handle_visual_tab_lock(blocked_tabs):
    if not blocked_tabs:
        return {
            'pointerEvents': 'none',
            'opacity': '0.75',
            'transition': 'all 0.3s ease'
        }
    return {'pointerEvents': 'auto', 'opacity': '1.0'}


app.clientside_callback(
    '''
    function(pathname, isLoaded) {
        if (!isLoaded && pathname !== '/') {
            // Force the browser window directly to the homepage
            window.location.href = '/';
            return [window.location.pathname, true];
        }
        return [window.dash_clientside.no_update, true];
    }
    ''',
    Output('url', 'pathname'),
    Output('initial-load-detector', 'data'),
    Input('url', 'pathname'),
    State('initial-load-detector', 'data'),
)


@callback(
    Output("custom-dropdown-menu", "style"),
    Input("task-selection-button", "n_clicks"),
    State("custom-dropdown-menu", "style"),
    prevent_initial_call=True
)
def toggle_dropdown(n_clicks, current_style):
    if not current_style or current_style.get("display") == "none":
        return {"display": "block"}
    return {"display": "none"}


@callback(
    Output("dropdown-selection-store", "data"),
    Output("custom-dropdown-menu", "style", allow_duplicate=True),
    Input("btn-opt-a", "n_clicks"),
    Input("btn-opt-b", "n_clicks"),
    Input("btn-opt-c", "n_clicks"),
    Input("btn-opt-d", "n_clicks"),
    prevent_initial_call=True
)
def select_option(btn_a, btn_b, btn_c, btn_d):
    triggered_id = ctx.triggered_id

    if triggered_id == "btn-opt-a":
        selected_value = "btn-opt-a"
    elif triggered_id == "btn-opt-b":
        selected_value = "btn-opt-b"
    elif triggered_id == "btn-opt-c":
        selected_value = "btn-opt-c"
    elif triggered_id == "btn-opt-d":
        selected_value = "btn-opt-d"
    else:
        selected_value = None

    return selected_value, {"display": "none"}


#laden der Task-Images
@callback(
    Output('camera-overlay-image', 'src'),
    Output('camera-overlay-image', 'style'),
    Input('dropdown-selection-store', 'data'),
    prevent_initial_call=False
)
def update_overlay(selected_value):
    base_style = {
        'position': 'absolute', 'top': '0', 'left': '0', 
        'width': '640px', 'height': '480px', 'zIndex': '10', 
        'pointerEvents': 'none', 'display': 'none'
    }
    
    if selected_value == "btn-opt-a":
        base_style['display'] = 'block'
        return '/assets/filter_a.png', base_style
        
    elif selected_value == "btn-opt-b":
        base_style['display'] = 'block'
        return '/assets/filter_b.png', base_style
    
    elif selected_value == "btn-opt-c":
        base_style['display'] = 'block'
        return '/assets/filter_c.png', base_style
    
    elif selected_value == "btn-opt-d":
        base_style['display'] = 'block'
        return '/assets/filter_d.png', base_style
        
    else:
        return '', base_style


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)
