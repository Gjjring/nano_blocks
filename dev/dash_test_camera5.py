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
import shapely
import jcmwave
app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server


server.config["SESSION_TYPE"] = "filesystem"
server.config["SESSION_FILE_DIR"] = "./sessions"
server.config["SESSION_PERMANENT"] = False
server.config["SESSION_USE_SIGNER"] = True
server.config["SECRET_KEY"] = "CHANGE_THIS"

Session(server)    # enable server-side sessions

# tab2_content =  [dbc.Row([
#                    dbc.Col([                        
#                        dcc.Graph(id = 'raw-camera')
#                    ],
#                    width=8,
#                    )                                
#                 ],
#                 justify="center"),
#                 dbc.Row([
#                    dbc.Col([            
#                        html.Button('', id='temporary_color_output',
#                                    disabled=True,
#                                    style={'textAlign':'center', 'width':"50px", "height":"50px", "background-color":"white"}
#                                    ),
#                        ],
#                        width =1,
#                    ),
#                    dbc.Col([
#                        html.Button('', id='color_output',
#                                    disabled=True,
#                                    style={'textAlign':'center', 'width':"50px", "height":"50px", "background-color":"white"}
#                                    ),
#                        ],
#                        width =1,
#                    ),
#                    dbc.Col([
#                        dbc.InputGroup([
#                            dbc.InputGroupText("Red"),
#                            dcc.Input(id='red_input', type='number', min=0, max=255, step=1, placeholder="255"),
#                            ]),                   
#                        ],
#                        width=2
#                    ),
#                    dbc.Col([
#                        dbc.InputGroup([
#                            dbc.InputGroupText("Green"),
#                            dcc.Input(id='green_input', type='number', min=0, max=255, step=1, placeholder="255"),
#                            ]),
#                        ],
#                        width=2
#                    ),
#                    dbc.Col([
#                        dbc.InputGroup([
#                            dbc.InputGroupText("Blue"),
#                            dcc.Input(id='blue_input', type='number', min=0, max=255, step=1, placeholder="255"),
#                            ]),                                              
#                        ],
#                        width=2,
#                    )                                
#                 ],
#                 justify="center"),
#                 dbc.Row([
#                    dbc.Col([
#                        html.Br(),
#                        dbc.Button("Threshold Image", id="make_threshold_image"),
#                        ],
#                        width=2)
#                 ],
#                 justify="center")
#                 ]


# tab3_content =  [
#                     dbc.Row([
#                         dbc.Col([                        
#                             dcc.Graph(id = 'threshold_image')
#                             ],
#                             width=8,
#                         )                                
#                     ],
#                     justify="center"),
#                     dbc.Row([
#                         dbc.Col([                                 
#                                 dbc.Button("Hue", id="hue_label", disabled=True),
#                             ],
#                             width=1
#                             ),
#                         dbc.Col([
#                                 dcc.RangeSlider(0, 1.0, 0.01, value=[0.4, 0.5], marks=None, allowCross=False, id='hue_slider')
#                                 ],
#                             width=7
#                             ),
#                         ],
#                         justify="center"
#                     ),
#                     dbc.Row([
#                         dbc.Col([                                 
#                                 dbc.Button("Saturation", id="saturation_label", disabled=True),
#                             ],
#                             width=1
#                             ),
#                         dbc.Col([
#                                 dcc.RangeSlider(0, 1.0, 0.01, value=[0.1, 1.0], marks=None, allowCross=False, id='saturation_slider')
#                                 ],
#                             width=7
#                             ),
#                         ],
#                         justify="center"
#                     ),
#                     dbc.Row([
#                         dbc.Col([                                 
#                                 dbc.Button(" Value ", id="value_label", disabled=True),
#                             ],
#                             width=1
#                             ),
#                         dbc.Col([
#                                 dcc.RangeSlider(0, 1.0, 0.01, value=[0.1, 1.0], marks=None, allowCross=False, id='value_slider')
#                                 ],
#                             width=7
#                             ),
#                         ],
#                         justify="center"
#                     )
#                 ]  

# --- Layout ---
app.layout = html.Div([
    dcc.Store(id='raw_image_data'),
    dcc.Store(id='threshold_color'),
    #dcc.Store(id='threshold_data'),
    dcc.Tabs(id="tabs", value="home", children=[
        dcc.Tab(label="Home", value="home", children=[
            html.H1("Home tab"),
            html.P("ich bin das neue Element auf der Homeseite")
        ]),
        dcc.Tab(label="Camera", value="camera", children=[
            html.H3("Camera Stream"),

            # Video element that clientside JS will attach to
            html.Video(id="video", width="640", height="480", autoPlay=True,
                       style={"border": "1px solid black"}),

            html.Br(),
            #dcc.Input(id="username", placeholder="enter username", type="text"),
            
            
            html.Button("Capture", id="capture-btn", n_clicks=0),
            
            # html.Hr(),
            # html.H3("Capture Preview"),
            
            # html.Div(id="latest-capture-preview"),

            html.Hr(),
            html.H3("Gallery"),

            html.Div(id="gallery"),
            html.Br(),

            html.Button("Delete Selected Images", id="delete-selected-btn", n_clicks=0),
            html.Button("Select for Processing", id="image-processing-select-btn", n_clicks=0),
            dcc.ConfirmDialog(
                id='single-selection-message',
                message='You may only select one image at a time for processing',
            ),
            html.Div(id='output-provider'),

            # invisible div used only as clientside callback Output target
            html.Div(id="camera-start-dummy", style={"display": "none"}),
            html.Div(id="capture-dummy", style={"display": "none"}),
            
            html.Hr(),
            
            dcc.Graph(id = 'raw-camera'),

            html.Hr(),
            
            dbc.Row([
                dbc.Col([
                    html.Button(
                        '', id='temporary_color_output',
                        disabled=True,
                        style={'textAlign':'center', 'width':"50px", "height":"50px", "background-color":"white"}
                    ),
                    
                    html.Button('', id='color_output',
                                disabled=True,
                                style={'textAlign':'center', 'width':"50px", "height":"50px", "background-color":"white"}
                                ),
                ]),
                dbc.Col([
                    dbc.InputGroup([
                        dbc.InputGroupText("Red"),
                        dcc.Input(id='red_input', type='number', min=0, max=255, step=1, placeholder="255"),
                        ]),                   
                    dbc.InputGroup([
                        dbc.InputGroupText("Green"),
                        dcc.Input(id='green_input', type='number', min=0, max=255, step=1, placeholder="255"),
                        ]),

                    dbc.InputGroup([
                        dbc.InputGroupText("Blue"),
                        dcc.Input(id='blue_input', type='number', min=0, max=255, step=1, placeholder="255"),
                        ]),                                              
                ]),
            ]),

            dbc.Button("Threshold Image", id="make_threshold_image"),
            html.Hr(),

            dcc.Graph(id = 'threshold_image'),

            dbc.Row([
                dbc.Col([                                 
                        dbc.Button("Hue", id="hue_label", disabled=True),
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
                        dbc.Button("Saturation", id="saturation_label", disabled=True),
                    ],
                    width=1
                    ),
                dbc.Col([
                        dcc.RangeSlider(0, 1.0, 0.01, value=[0.1, 1.0], marks=None, allowCross=False, id='saturation_slider')
                        ],
                    width=7
                    ),
                ],
                justify="center"
            ),
            dbc.Row([
                dbc.Col([                                 
                        dbc.Button(" Value ", id="value_label", disabled=True),
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

            dbc.Button("Simulate", id="make_jcm_suite_simulation"),

            html.Hr(),

            dcc.Graph(id = 'jcm_output'),

   
                             
        ]),
        # dcc.Tab(label="Color Thresholding", value="processing", children=[
        #     tab2_content
            
        # ]),
        # dcc.Tab(label="Processing", value="processing", children=[
        #     tab3_content
        # ]),
    ])
])



# --------------------
# Clientside callback 1:
# Start camera when the Camera tab becomes active.
#
# Input: tabs.value
# Output: camera-start-dummy.children (unused; just to satisfy Dash)
# --------------------
app.clientside_callback(
    """
    function(tab_value) {
        // only run when camera tab is active
        if (tab_value !== 'camera') {
            return '';
        }

        // If the video is already streaming, do nothing
        const vid = document.getElementById('video');
        if (!vid) {
            return '';
        }
        if (vid.srcObject && vid.srcObject.getTracks && vid.srcObject.getTracks().length > 0) {
            return '';
        }

        // request camera
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function(stream) {
                const video = document.getElementById('video');
                if (!video) return;
                video.srcObject = stream;
                video.onloadedmetadata = function() { video.play(); };
            })
            .catch(function(err) {
                // log error to console (user can open DevTools)
                console.error('getUserMedia error:', err);
                // optionally inform user via alert:
                // alert('Camera error: ' + err.message);
            });

        return '';
    }
    """,
    Output("camera-start-dummy", "children"),
    Input("tabs", "value")
)

# --------------------
# Clientside callback 2:
# Capture image when the Capture button is clicked.
#
# Inputs: capture-btn.n_clicks, username value
# Output: capture-dummy.children (unused)
# --------------------
# app.clientside_callback(
#     """
#     function(n_clicks) {
#         if (!n_clicks) {
#             return 0;
#         }

#         const video = document.getElementById('video');
#         if (!video || !video.videoWidth) {
#             return 0;
#         }

#         const canvas = document.createElement('canvas');
#         canvas.width = video.videoWidth;
#         canvas.height = video.videoHeight;
#         const ctx = canvas.getContext('2d');
#         ctx.drawImage(video, 0, 0);

#         const dataUrl = canvas.toDataURL('image/png');

#         fetch("/upload_image", {
#             method: "POST",
#             headers: {"Content-Type": "application/json"},
#             body: JSON.stringify({ image: dataUrl })
#         });
        
        

#         return (new Date()).getTime();
#     }
#     """,
#     Output("capture-dummy", "children"),
#     Input("capture-btn", "n_clicks")
# )

app.clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks) return 0;

        const video = document.getElementById('video');
        if (!video || !video.videoWidth) {
            return 0;
        }

        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);

        const dataUrl = canvas.toDataURL('image/png');

        // --- IMPORTANT ---
        // Return a Promise so Dash waits for upload to finish
        return fetch("/upload_image", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ image: dataUrl })
        })
        .then(resp => {
            if (!resp.ok) {
                console.error("Upload failed");
                return 0;
            }
            // Only AFTER server saves image → update gallery
            return (new Date()).getTime();
        })
        .catch(err => {
            console.error("Error sending image", err);
            return 0;
        });
    }
    """,
    Output("capture-dummy", "children"),
    Input("capture-btn", "n_clicks")
)


# --------------------
# Server route: save uploaded image
# --------------------
SAVE_DIR = "saved_images"
os.makedirs(SAVE_DIR, exist_ok=True)

@server.route("/upload_image", methods=["POST"])
def upload_image():
    data = request.get_json(force=True)
    #username = data.get("username", "unknown_user")
    #userid
    image_data = data.get("image")
    
    if not image_data:
        return jsonify({"message": "No image provided"}), 400

    try:
        header, encoded = image_data.split(",", 1)
    except Exception:
        return jsonify({"message": "Bad image data"}), 400

    current_time = datetime.now()
    id_val = current_time.strftime("%Y%m%d%H%M%S%f")
    try:
        stored = session.get("saved_images", [])
        stored.append({
            "id": id_val,
            "image": image_data, 
            "timestamp": current_time.isoformat()
        })
        session["saved_images"] = stored
        session.modified = True       # VERY important: tells Flask the session changed
    except Exception as exp:
        print(str(exp))
        return jsonify({"message": f"{str(exp)}"}), 400
    
    # decoded = base64.b64decode(encoded)
    # filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    # path = os.path.join(SAVE_DIR, filename)
    # with open(path, "wb") as f:
    #     f.write(decoded)
    stored = session.get("saved_images", [])
    print(f"N stored images: {len(stored)}")
    return jsonify({"message": f"Image saved as {id_val}"})
    #return jsonify({"message": "Image saved as in session"})

@app.callback(
    Output("gallery", "children", allow_duplicate=True),
    Input("capture-dummy", "children"),
    Input("delete-selected-btn", "n_clicks"),
    State({"type":"img-select","index":dash.ALL}, "value"),
    #allow_duplicate=True,
    prevent_initial_call=True,
)
def update_gallery(_, __, selections):
    triggered_id = ctx.triggered_id
    print(triggered_id)
    
    
    def render_tile(img):        
        return html.Div([
            html.Img(src=img["image"], style={
                "width": "200px",
                "height": "150px",
                "objectFit": "cover",
                "display": "block",
                "border": "1px solid #999"
            }),
            dcc.Checklist(
                id={"type": "img-select", "index": img["id"]},
                options=[{"label": "Select", "value": img["id"]}],
                value=[],
                style={"textAlign": "center"}
            )
        ], style={
            "display": "inline-block",
            "margin": "10px",
            "textAlign": "center"
        })
            
    def delete_selected(selections):
        if not selections:
            return ""

        # flatten selected ids
        selected_ids = {v[0] for v in selections if v}
        
        imgs = session.get("saved_images", [])
        print(f"len imgs: {len(imgs)}")
        imgs = [img for img in imgs if img["id"] not in selected_ids]
        print(f"len imgs: {len(imgs)}")
        session["saved_images"] = imgs
        session.modified = True
        # return imgs

    if triggered_id == 'delete-selected-btn':
        delete_selected(selections)
    
    images = session.get("saved_images", [])
    print(f"rendering {len(images)} images")
        
    return [render_tile(img) for img in images]

# @app.callback(
#     Output("gallery", "children", allow_duplicate=True),
#     Input("delete-selected-btn", "n_clicks"),
#     State({"type":"img-select","index":dash.ALL}, "value"),
#     prevent_initial_call=True,    
#     #allow_duplicate=True,
# )
# def delete_selected(_, selections):    
#     if not selections:
#         return ""

#     # flatten selected ids
#     selected_ids = {v[0] for v in selections if v}
    
#     imgs = session.get("saved_images", [])
#     print(f"len imgs: {len(imgs)}")
#     imgs = [img for img in imgs if img["id"] not in selected_ids]
#     print(f"len imgs: {len(imgs)}")
#     session["saved_images"] = imgs
#     session.modified = True

#     return ""

# @callback(Output('single-selection-message', 'displayed'),
#               Input('dropdown-danger', 'value'))
# def display_confirm(value):
#     if value == 'Danger!!':
#         return True
#     return False

def make_color(r=0,g=0,b=0):
    color_str = "rgb({}, {}, {})".format(r,g,b)
    return color_str

@app.callback(Output(component_id='raw-camera', component_property= 'figure'),
              Output('single-selection-message', 'displayed'),
              Input('image-processing-select-btn', 'n_clicks'),
              State({"type":"img-select","index":dash.ALL}, "value"))
def plot_raw_camera_image(n_clicks, selections):
    #print("calling plot_raw-camera_image, data is none: {}".format(raw_image_data == None))
    current_raw_image = session.get("current_raw_image", None)
    
    def plot_raw_data(image_data):
        fig = px.imshow(image_data)
        # else:
        
        #fig = go.Figure()
        #print("figure type: {}".format(type(fig)))
        fig.update_layout(coloraxis_showscale=False)
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)
        return fig
    
    if not selections:
        if current_raw_image is not None:
            fig = plot_raw_data(current_raw_image)
            print(f"returning: {fig}, {False}")
            return (fig, False)
        else:
            print(f"returning: {None}, {False}")
            return (None, False)
    else:
        selected_ids = [v[0] for v in selections if v]        
        if len(selected_ids) > 1:
            return (None, True)
        imgs = session.get("saved_images", [])
        selected_id = selected_ids[0]
        for img in imgs:
            if img['id'] == selected_id:
                str_image = img['image']    
        
        png_base64 = str_image.strip().replace("data:image/png;base64,", "")
    
        # Base64 → bytes
        image_bytes = base64.b64decode(png_base64)
        
        # Load the PNG
        img = Image.open(BytesIO(image_bytes))
        
        # Convert to pixel array
        #raw_image = np.array(img)
        
        #img = [img for img in imgs if img["id"] not in selected_ids]
        # if raw_image_data is not None:
        
        raw_image_data = np.array(img, dtype=np.uint8)
        session["current_raw_image"] = raw_image_data
        session.modified = True
        fig = plot_raw_data(raw_image_data)
        
        return (fig, False)

@app.callback(Output(component_id='temporary_color_output', component_property= 'style'),
              [dash.dependencies.Input('raw-camera', 'hoverData')])
def update_temporary_color_state(hover_data):
    if hover_data is None:
        raise PreventUpdate()
    else:
        color = hover_data['points'][0]['color']
        red = color['0']
        green = color['1']
        blue = color['2']
        color = make_color(red, green, blue)
        style = {'textAlign':'center', 'width':"50px", "height":"50px", "background-color":color}
        return style

@app.callback(Output(component_id='color_output', component_property= 'style'),
              Output(component_id='threshold_color', component_property= 'data'),
              [Input(component_id='red_input', component_property= 'value'),
                Input(component_id='green_input', component_property= 'value'),
                Input(component_id='blue_input', component_property= 'value')])
def color_box_update(red, green, blue):
    color = make_color(red, green, blue)
    print(color)
    style = {'textAlign':'center', 'width':"50px", "height":"50px", "background-color":color}
    data = [red, green, blue]
    return style, data


@app.callback(dash.dependencies.Output('red_input', 'value'),
              dash.dependencies.Output('green_input', 'value'),
              dash.dependencies.Output('blue_input', 'value'),
              [dash.dependencies.Input('raw-camera', 'clickData')])
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

@app.callback(Output(component_id='hue_slider', component_property= 'value'),
              Input('threshold_color','data'))
def update_hue_threshold(target_color):
    if target_color is None:
        raise PreventUpdate()
    if len(target_color) == 0:
        raise PreventUpdate()
    hsv_target_color = ski.color.rgb2hsv(np.array(target_color, dtype=np.uint8))
    lower_hue_bound = np.clip(hsv_target_color[0]-0.15, 0.0, 1.0)
    upper_hue_bound = np.clip(hsv_target_color[0]+0.15, 0.0, 1.0)
    return lower_hue_bound, upper_hue_bound



@app.callback([Output(component_id='threshold_image', component_property= 'figure'),
              ],
              [Input('make_threshold_image', 'n_clicks'),
                Input('hue_slider', 'value'),
                Input('saturation_slider', 'value'),
                Input('value_slider', 'value')]
                )
def make_threshold_image(n_clicks, hue_range, saturation_range,
                          value_range):
    if n_clicks is None:
        raise PreventUpdate()
    else:
        try:
            img_data = session["current_raw_image"]
        except:
            raise PreventUpdate()
        
            
        print("img data shape: {}".format(img_data.shape))
        for ii in range(4):
            print(ii, np.min(img_data[..., ii]), np.max(img_data[..., ii]))
        np_data = np.array(img_data[..., :3], dtype=np.uint8)

        hsv_lower = np.array([hue_range[0], saturation_range[0], value_range[0]])
        hsv_higher = np.array([hue_range[1], saturation_range[1], value_range[1]])
        print("np data shape: {}".format(np_data.shape))
        blurred_image = ski.filters.gaussian(np_data, sigma=1.0)
        print("blurred image shape: {}".format(blurred_image.shape))
        hsv_image = ski.color.rgb2hsv(blurred_image)

        binary_mask = cv2.inRange(hsv_image, hsv_lower, hsv_higher)

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
    return [fig]

def order_lexicographically(points, start=0.0, return_sort_indices=False):
    angle = np.angle( (points[:,0]+1j*points[:,1])*np.exp(1j*(np.pi+1e-3+start)))
    angle = np.round(angle, 3)
    radius = np.linalg.norm(points, axis=1)
    angle[np.isclose(radius, 0.)] = -np.pi
    sort_indices = np.lexsort((radius, angle))
    #sort_indices = np.argsort(angle)
    all_data = np.round(np.vstack([points.T, angle, radius]).T, 3)
    #pp = pprint.PrettyPrinter(indent=4, width=120)
    #pp.pprint("x, y, z, angle, radius")
    #pp.pprint(all_data)
    #pp.pprint("x, y, z, angle, radius")
    #pp.pprint(all_data[sort_indices, :])
    if return_sort_indices:
        return points[sort_indices, :], sort_indices
    else:
        return points[sort_indices, :]

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
            #patch1 = PolygonPatch(p, fc=BLUE, ec=BLUE, alpha=0.5, zorder=2)
            #ax.add_patch(patch1)
            #plot_polygon(ax, p)
            
            p2 = p.simplify(10.)            
            #p2 = p
            c = np.array(p2.exterior.coords)
            c = c[:-1, :]            
            c[:, 1] = keys['cd_height']-c[:, 1]
            mid_point = np.tile(np.mean(c, axis=0), c.shape[0]).reshape(c.shape)            
            #c -= mid_point 
            #c = order_lexicographically(c)
            #c += mid_point
            
            keys['polygons'].append(c)
    
    #jcmwave.jcmt2jcm("layout.jcmt", keys=keys)
    #jcmwave.geo(".")
    results = jcmwave.solve("project.jcmpt", keys=keys)
    cart_field = results[1]

    e_field = np.linalg.norm(np.abs(cart_field['field'][0]), axis=2)**2

    return e_field


@app.callback([Output(component_id='jcm_output', component_property= 'figure'),
              ],
              [Input('make_jcm_suite_simulation', 'n_clicks'),
                ])
def make_jcmwave_simulation(n_clicks):
    if n_clicks is None:
        raise PreventUpdate()
    else:
        try:
            threshold_data = session["current_threshold_image"]
        except:
            raise PreventUpdate()
        
            
        print("img data shape: {}".format(threshold_data.shape))
        for ii in range(1):
            print(ii, np.min(threshold_data), np.max(threshold_data))
        
        field_data = run_jcmwave_simulation(threshold_data)
        # for ip, poly in enumerate(field_data['polygons']):            
        #     if ip == 0:
        #         fig = px.line(x=poly[:, 0], y=poly[:, 1])
        fig = px.imshow(field_data.T, origin="lower")

    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)
    return [fig]


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)
