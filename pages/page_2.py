import dash
from dash import Dash, html, dcc, Input, Output, State, ctx, MATCH, ALL
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from flask import session
import base64
from io import BytesIO
from PIL import Image
import numpy as np

dash.register_page(__name__, path='/page_2')
app = dash.get_app()
server = app.server

layout = html.Div([
    html.Div(id='gallery'),
    dcc.Store(id='gallery-selection-status', data=False),

    html.Button('Delete Selected Images', id='delete-selected-btn', n_clicks=0),
    dcc.ConfirmDialog(
        id='single-selection-message',
        message='You may only select one image at a time for processing',
    ),
])


def render_tile(img):        
    return html.Div([
        dcc.Store(id='click-state', data=False),
        html.Div([
            html.Img(src=img['image'], id={'type': 'clickable-image', 'index': img['id']}, n_clicks=0, style={
                'width': '200px',
                'height': '150px',
                'objectFit': 'cover',
                'display': 'block',
                'border': '1px solid Black'
            }),
            html.P(id={'type': 'img-select', 'index': img['id']}, children='Select')
        ]),
    ], style={
        'display': 'inline-block',
        'margin': '10px',
        'textAlign': 'center'
    })


@app.callback(
    Output({'type': 'clickable-image', 'index': ALL}, 'style'),
    Output({'type': 'clickable-image', 'index': ALL}, 'n_clicks'),
    Output({'type': 'img-select', 'index': ALL}, 'children'),
    Output('gallery-selection-status', 'data', allow_duplicate=True),
    Input('gallery', 'children'), 
    Input({'type': 'clickable-image', 'index': ALL}, 'n_clicks'),
    State({'type': 'clickable-image', 'index': ALL}, 'id'),
    prevent_initial_call=True
)   
def mutually_exclusive_selection(gallery_children, all_n_clicks, all_ids):
    if not all_ids:
        raise PreventUpdate
    
    triggered_id = ctx.triggered_id
    
    if isinstance(triggered_id, dict) and triggered_id.get('type') == 'clickable-image':
        target_index = triggered_id['index']
        
        imgs = session.get('saved_images', [])
        clicked_img = next((img for img in imgs if img['id'] == target_index), None)
        if clicked_img:
            png_base64 = clicked_img['image'].strip().replace('data:image/png;base64,', '')
            image_bytes = base64.b64decode(png_base64)
            img_file = Image.open(BytesIO(image_bytes))
            
            session['active_image_id'] = target_index
            session['current_raw_image'] = np.array(img_file, dtype=np.uint8)
            session.modified = True
    else:
        target_index = session.get('active_image_id', None)

    new_styles = []
    new_clicks = []
    new_texts = []

    active_style = {
        'width': '195px', 'height': '145px', 'objectFit': 'cover', 'display': 'block',
        'border': '5px solid black', 'transform': 'scale(0.95)', 'cursor': 'pointer',
        'transition': 'all 0.3s ease'
    }
    normal_style = {
        'width': '200px', 'height': '150px', 'objectFit': 'cover', 'display': 'block',
        'border': '1px solid black', 'transition': 'all 0.3s ease'
    }

    has_selection = False
    for comp_id in all_ids:
        current_index = comp_id['index']

        if current_index == target_index:
            new_styles.append(active_style)
            new_clicks.append(1)
            new_texts.append('Selected')
            has_selection = True
        else:
            new_styles.append(normal_style)
            new_clicks.append(0)
            new_texts.append('Select')
            
    return new_styles, new_clicks, new_texts, has_selection


@app.callback(
    Output('gallery', 'children'),
    Output('gallery-selection-status', 'data'),
    Input('capture-dummy', 'children'),
    Input('gallery', 'id'),
    Input('delete-selected-btn', 'n_clicks'),
    State({'type': 'clickable-image', 'index': ALL}, 'n_clicks'),
    State({'type': 'clickable-image', 'index': ALL}, 'id'),
    prevent_initial_call=False
)
def manage_gallery(capture_trigger, gallery_init, delete_clicks, all_n_clicks, all_ids):
    triggered_id = ctx.triggered_id
    print(f'Triggered by: {triggered_id}')

    current_active = session.get('active_image_id', None)
    selection_status = True if current_active is not None else False

    if triggered_id == 'delete-selected-btn':
        if all_n_clicks and all_ids:
            selected_ids = [
                comp_id['index'] 
                for clicks, comp_id in zip(all_n_clicks, all_ids) 
                if clicks and clicks % 2 == 1
            ]
            
            if selected_ids:
                deleted_id = selected_ids[0]
                imgs = session.get('saved_images', [])
                
                deleted_index = next((i for i, img in enumerate(imgs) if img['id'] == deleted_id), -1)
                
                imgs = [img for img in imgs if img['id'] != deleted_id]
                session['saved_images'] = imgs

                if imgs and deleted_index != -1:
                    if deleted_index >= len(imgs):
                        next_selected_index = len(imgs) - 1
                    else:
                        next_selected_index = deleted_index
                    
                    next_image = imgs[next_selected_index]
                    
                    png_base64 = next_image['image'].strip().replace('data:image/png;base64,', '')
                    image_bytes = base64.b64decode(png_base64)
                    img_file = Image.open(BytesIO(image_bytes))
                    
                    session['active_image_id'] = next_image['id']
                    session['current_raw_image'] = np.array(img_file, dtype=np.uint8)
                    selection_status = True
                else:
                    session.pop('active_image_id', None)
                    session.pop('current_raw_image', None)
                    selection_status = False
                
                session.modified = True

    elif triggered_id == 'gallery' or triggered_id is None:
        session.pop('active_image_id', None)
        session.pop('current_raw_image', None)
        session.modified = True
        selection_status = False

    images = session.get('saved_images', [])
    return [render_tile(img) for img in images], selection_status
