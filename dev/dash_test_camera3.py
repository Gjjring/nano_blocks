import dash
import numpy as np
from dash import html
import plotly.graph_objects as go
from dash import dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import skimage as ski
import time
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import cv2
from flask import Flask, Response, request, make_response

from PIL import Image
import requests
from io import BytesIO
import os
#import joblib
from tempfile import mkdtemp
#savedir = mkdtemp()
#feed_file = os.path.join(savedir, 'feed.joblib')
#cache_file = os.path.join(savedir, 'cache.joblib')




def make_color(r=0,g=0,b=0):
    color_str = "rgb({}, {}, {})".format(r,g,b)
    return color_str


class VideoCamera(object):
    def __init__(self):        
        self.video = cv2.VideoCapture(1)        

    def __del__(self):
        self.video.release()

    def get_frame(self):
        frameId = int(round(self.video.get(1)))
        success, image = self.video.read()
        fps = self.video.get(cv2.CAP_PROP_FPS)               
        # if success and frameId % fps == 0:
        #     joblib.dump(image, feed_file)
        #     #path = os.path.join("test", "video_feed")
            #ext ="jpg"
            #cv2.imwrite('{}.{}'.format(path, ext), image)
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

# def pattern_data(data):
#     return (b'--frame\r\n'
#         b'Content-Type: image/jpeg\r\n\r\n' + data + b'\r\n\r\n')

def gen(camera):
    while True:        
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        

server = Flask(__name__)

app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP],
                suppress_callback_exceptions=True)



@server.route('/video_feed')
def video_feed():
    try:
        feed = gen(VideoCamera())
        return Response(feed,
                    mimetype='multipart/x-mixed-replace; boundary=frame')
    except:    
        return Response("feed stopped", mimetype="text/html")    





    

@app.callback(Output(component_id='raw_camera', component_property= 'figure'),
              [Input('raw_image_data', 'data')])
def plot_raw_camera_image(raw_image_data):
    print("calling plot_raw_camera_image, data is none: {}".format(raw_image_data == None))
    if raw_image_data is not None:
        raw_image_data = np.array(raw_image_data, dtype=np.uint8)            
        fig = px.imshow(raw_image_data)
    else:
        fig = go.Figure()
    print("figure type: {}".format(type(fig)))
    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)
    return fig


@app.callback([Output(component_id='tabs_feed', component_property= 'value'),
                Output('raw_image_data', 'data')],
              [Input('capture_image', 'n_clicks'),
                Input('raw_image_data', 'data')])
def grab_camera_frame(n_clicks, raw_image_data):
    print("grab_camera_frame called with n_clicks: {}".format(n_clicks))
    print("raw image data is none: {}".format(raw_image_data is None))
    if n_clicks is None:
        if raw_image_data is None or len(raw_image_data) == 0:
            raise PreventUpdate()
        else:
            raw_image_data = np.array(raw_image_data, dtype=np.uint8)
            print("raw image data shape: {}".format(raw_image_data.shape))
            
    else:
        
        # raw_image_data = joblib.load(feed_file)
        # joblib.dump(raw_image_data, cache_file)
        #stream_url = "http://localhost:5000/video_feed"
        # stream_url = "http://127.0.0.1:8050/video_feed"
        # cap = cv2.VideoCapture(stream_url)
        # ret, frame = cap.read()
        # if ret:
        #     raw_image_data = frame
        #     print("raw image data shape: {}".format(raw_image_data.shape))
        # else:
        #     print("image could not be captured")
        #     raise PreventUpdate()
        
                
    
    return "tab_2", raw_image_data

@app.callback(Output(component_id='color_output', component_property= 'style'),
              Output(component_id='threshold_color', component_property= 'data'),
              [Input(component_id='red_input', component_property= 'value'),
                Input(component_id='green_input', component_property= 'value'),
                Input(component_id='blue_input', component_property= 'value')])
def color_box_update(red, green, blue):
    color = make_color(red, green, blue)
    style = {'textAlign':'center', 'width':"50px", "height":"50px", "background-color":color}
    data = [red, green, blue]
    return style, data

@app.callback(Output(component_id='temporary_color_output', component_property= 'style'),
              [dash.dependencies.Input('raw_camera', 'hoverData')])
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

@app.callback(dash.dependencies.Output('red_input', 'value'),
              dash.dependencies.Output('green_input', 'value'),
              dash.dependencies.Output('blue_input', 'value'),
              [dash.dependencies.Input('raw_camera', 'clickData')])
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
              Output(component_id='threshold_data', component_property= 'data')],
              [Input('make_threshold_image', 'n_clicks'),
                Input('hue_slider', 'value'),
                Input('saturation_slider', 'value'),
                Input('value_slider', 'value'),
                Input('raw_image_data', 'data')])
def make_threshold_image(n_clicks, hue_range, saturation_range,
                          value_range, img_data):
    if n_clicks is None:
        raise PreventUpdate()
    else:
        if len(img_data) == 0:
            raise PreventUpdate()
        else:
            np_data = np.array(img_data, dtype=np.uint8)




            hsv_lower = np.array([hue_range[0], saturation_range[0], value_range[0]])
            hsv_higher = np.array([hue_range[1], saturation_range[1], value_range[1]])

            blurred_image = ski.filters.gaussian(np_data, sigma=1.0)
            hsv_image = ski.color.rgb2hsv(blurred_image)

            binary_mask = cv2.inRange(hsv_image, hsv_lower, hsv_higher)

            binary_mask = ski.filters.gaussian(binary_mask, sigma=3.0)
            edge = 20
            half_edge = int(edge/2)
            ix, iy = binary_mask.shape
            new_mask = np.zeros((ix+edge, iy+edge), dtype=np.bool_)
            new_mask[half_edge:-half_edge, half_edge:-half_edge] = binary_mask


            fig = px.imshow(new_mask)


    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)
    return fig, new_mask






# @app.callback(Output('tabs_feed_content', 'children'),
#               Input('tabs_feed', 'value'))
# def render_content(tab):
#     if tab == 'tab_1_live_feed':
#         FEED_ON = True
#         return tab1
#     elif tab == 'tab_2_snapshot':
#         FEED_ON = False
#         return tab2

#
#raw_camera_output = dbc.Col(dcc.Graph(id = 'raw_camera', style={'width':"600px", "height":"600px"}))
#capture_image_button = 
#live_feed = dbc.Col(html.Img(src="/video_feed"))

tab1_content =  dbc.Row([
                    dbc.Col(
                        dbc.Card([
                            dbc.CardImg(src="/video_feed", top=True),
                            dbc.CardBody([
                                dbc.Button("Capture Image", id="capture_image"),
                            ])
                        ]),
                        width=8
                    )],
                    justify="center",
                )            

tab2_content =  [dbc.Row([
                   dbc.Col([                        
                       dcc.Graph(id = 'raw_camera')
                   ],
                   width=8,
                   )                                
                ],
                justify="center"),
                dbc.Row([
                   dbc.Col([            
                       html.Button('', id='temporary_color_output',
                                   disabled=True,
                                   style={'textAlign':'center', 'width':"50px", "height":"50px", "background-color":"white"}
                                   ),
                       ],
                       width =1,
                   ),
                   dbc.Col([
                       html.Button('', id='color_output',
                                   disabled=True,
                                   style={'textAlign':'center', 'width':"50px", "height":"50px", "background-color":"white"}
                                   ),
                       ],
                       width =1,
                   ),
                   dbc.Col([
                       dbc.InputGroup([
                           dbc.InputGroupText("Red"),
                           dcc.Input(id='red_input', type='number', min=0, max=255, step=1, placeholder="255"),
                           ]),                   
                       ],
                       width=2
                   ),
                   dbc.Col([
                       dbc.InputGroup([
                           dbc.InputGroupText("Green"),
                           dcc.Input(id='green_input', type='number', min=0, max=255, step=1, placeholder="255"),
                           ]),
                       ],
                       width=2
                   ),
                   dbc.Col([
                       dbc.InputGroup([
                           dbc.InputGroupText("Blue"),
                           dcc.Input(id='blue_input', type='number', min=0, max=255, step=1, placeholder="255"),
                           ]),                                              
                       ],
                       width=2,
                   )                                
                ],
                justify="center"),
                dbc.Row([
                   dbc.Col([
                       html.Br(),
                       dbc.Button("Threshold Image", id="make_threshold_image"),
                       ],
                       width=2)
                ],
                justify="center")
                ]
                

tab3_content =  [
                    dbc.Row([
                        dbc.Col([                        
                            dcc.Graph(id = 'threshold_image')
                            ],
                            width=8,
                        )                                
                    ],
                    justify="center"),
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
                    )
                ]                                
                    


#     dcc.RangeSlider(0, 1.0, 0.01, value=[0.1, 1.0], marks=None, allowCross=False, id='saturation_slider'),
#     dcc.RangeSlider(0, 1.0, 0.01, value=[0.1, 1.0], marks=None, allowCross=False, id='value_slider'),

# @app.callback(Output('tabs_content', 'children'),
#               Input('tabs_feed', 'value'))
# def render_content(tab):
#     if tab == 'tab_1':
#         global FEED_ON
#         FEED_ON = True
#         return tab1_content
#     elif tab == 'tab_2':
#         return tab2_content
#     elif tab == 'tab_3':
#         return tab3_content

app.layout = dbc.Container(
    [dcc.Store(id='raw_image_data'),
     dcc.Store(id='threshold_color'),
     dcc.Store(id='threshold_data'),
        dbc.Row(children=[
                    html.H1(id = 'H1',
                            children = 'Creating a Mesh from an Image', 
                            style = {'textAlign':'center', 'marginTop':40, 'marginBottom':40})
            ]),
        dbc.Row(children=[
                    dcc.Tabs(id="tabs_feed",  value="tab_1", children=[
                        # dcc.Tab(tab1_content, label='Live Feed', id="tab_1", value="tab_1"),
                        # dcc.Tab(tab2_content, label='Captured Image', id="tab_2", value="tab_2"),
                        # dcc.Tab(tab3_content, label='Threshold Image', id="tab_3", value="tab_3")
                        dcc.Tab(tab1_content, label='Live Feed', id="tab_1", value="tab_1"),
                        dcc.Tab(tab2_content, label='Captured Image', id="tab_2", value="tab_2"),
                        dcc.Tab(tab3_content, label='Threshold Image', id="tab_3", value="tab_3")
                    ]
                    ),
                    html.Div(id='tabs_content'),
            ]
        ),        
    ],
    className = 'container')


if __name__ == '__main__':
    app.run_server(debug=True)
