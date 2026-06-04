from pathlib import Path

import dash
from dash import Dash, html, dcc, Input, Output, State, ctx, MATCH, ALL
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
import hashlib
import jcmwave

dash.register_page(__name__, path = '/page_5')
app = dash.get_app()
server = app.server

layout = html.Div([
    html.Hr(),

    dcc.Dropdown(
        options=['Simulation Mesh', 'Intensity'],
        value='Simulation Mesh',
        id='plot-type-dropdown',
        style={'width': '300px', 'margin': '0 auto'}
    ),
    html.Div(id='result-box', children=[
        dcc.Loading(
            type='circle',
            children=[
                dcc.Graph(id = 'jcm_mesh_output', className='output', style={"height": "480px", "width": "640px", "display": "block"}, config={'displayModeBar': False}),
                dcc.Graph(id = 'jcm_intensity_output', className='output', style={"height": "480px", "width": "640px", "display": "none"}, config={'displayModeBar': False}),
            ]
        ),
    ])
])

def order_lexicographically(points, start=0.0, return_sort_indices=False):
    angle = np.angle( (points[:,0]+1j*points[:,1])*np.exp(1j*(np.pi+1e-3+start)))
    angle = np.round(angle, 3)
    radius = np.linalg.norm(points, axis=1)
    angle[np.isclose(radius, 0.)] = -np.pi
    sort_indices = np.lexsort((radius, angle))
    #sort_indices = np.argsort(angle)
    all_data = np.round(np.vstack([points.T, angle, radius]).T, 3)
    if return_sort_indices:
        return points[sort_indices, :], sort_indices
    else:
        return points[sort_indices, :]


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

def run_jcmwave_simulation(threshold_data, project):
    keys = {}

    keys['cd_width'] = 6
    keys['cd_height'] = 4.5
    keys['user_area_width'] = keys['cd_width'] - 2
    keys['user_area_height'] = keys['cd_height'] - 1.5
    keys['wg_width'] = 0.3
    keys['wg_displacement_left'] = -1
    keys['wg_displacement_right'] = 1
    keys['wg_stub_length'] = 0.75
    keys['boundary_id'] = 1
    keys['air_slc'] = 0.25
    keys['dielectric_slc'] = 0.5/3.5
    keys['vacuum_wavelength'] = 500e-9
    project_path = Path(project)
    first_dir = project_path.parts[0]
    keys['in_port_fields_path'] = os.path.abspath(os.path.join(first_dir, '1D', 'project_results', 'fieldbag.jcm'))

    image_width = threshold_data.shape[1]
    image_height = threshold_data.shape[0]
    image_buffer  = 20
    half_buffer = int(image_buffer / 2)
    image_width_without_buffer = image_width - image_buffer
    image_height_without_buffer = image_height - image_buffer
    keys['polygons'] = []
    print('image shape: {}'.format(threshold_data.shape))
    print('image dimensions: {} x {}'.format(image_width, image_height))
    print('image width without buffer: {}, image height without buffer: {}'.format(image_width_without_buffer, image_height_without_buffer))
    contours = ski.measure.find_contours(threshold_data.T, 0.5)
    for contour in contours:
        p = shapely.Polygon(contour)
        if p.area > 10:
            p2 = p.simplify(1)
            keys['polygons'].append(p2)

    # determine nesting level which will be used to set polygon domain Id in jcm file.
    nesting_levels = {}
    for i, poly in enumerate(keys['polygons']):
        nesting_levels[i] = 0
        for j, other_poly in enumerate(keys['polygons']):
            if i != j and poly.within(other_poly):
                nesting_levels[i] += 1

    # convert to numpy arrays and flip y axis to match jcmwave coordinate system where y increases upwards
    np_polys = []
    for i, poly in enumerate(keys['polygons']):
        c = np.array(poly.exterior.coords)
        c = c[:-1, :]
        c[:, 1] = image_height-c[:, 1]
        np_polys.append(np.ceil(c))
    keys['polygons'] = np_polys

    # order the vertices in couterclockwise order starting from the point with the smallest angle to the x-axis
    for i, poly in enumerate(keys['polygons']):
        orientation = polygon_orientation(poly)
        if orientation == "CW":
            poly = poly[::-1]
        keys['polygons'][i] = poly

    # now convert the coordinates from pixel coordinates to physical coordinates in micrometers.
    for polygon in keys['polygons']:
        print('polygon ymin: {}, ymax: {}, x min: {}, x max: {}'.format(np.min(polygon[:, 1]), np.max(polygon[:, 1]), np.min(polygon[:, 0]), np.max(polygon[:, 0])))
        polygon[:, 0] = (polygon[:, 0]- (half_buffer+1) )/ (image_width_without_buffer-1) * keys['user_area_width'] + 1 - keys['cd_width']/2
        #polygon[:, 0] = (polygon[:, 0]- half_buffer )/ image_width_without_buffer * keys['user_area_width'] + 1 - keys['cd_width']/2
        polygon[:, 1] = (polygon[:, 1]- (half_buffer+1) )/ (image_height_without_buffer-1) * keys['user_area_height'] + 0.75 - keys['cd_height']/2

    keys['polygons'] = list(zip(keys['polygons'], nesting_levels.values()))
    jcmwave.jcmt2jcm(os.path.join(project, 'layout.jcmt'), keys=keys)
    print("checking hash value in : ", os.path.join(project, 'layout.jcm'))
    with open(os.path.join(project, 'layout.jcm'), encoding='utf-8') as f:
        text = f.read()
    hash_value = hashlib.sha256(text.encode('utf-8')).hexdigest()

    #jcmwave.geo('.')

    if 'simulation_hash' in session and hash_value == session['simulation_hash']:
        cart_field = jcmwave.loadcartesianfields(
            os.path.join(project, 'project_results', 'field.jcm')
        )
        grid_tables = jcmwave.loadtable(os.path.join(project, 'grid_table.jcm'))
        is_updated = False
    else:
        jcmwave.geo(os.path.join(project), keys=keys)
        if not project == "jcmwave":
            jcmwave.solve(os.path.join(first_dir, '1D','project.jcmpt'), keys=keys)
        results = jcmwave.solve(os.path.join(project, 'project.jcmpt'), keys=keys)
        session['simulation_hash'] = hash_value
        cart_field = results[1]
        grid_tables = results[2]
        is_updated = True

    e_field = np.linalg.norm(np.abs(cart_field['field'][0]), axis=2)**2

    return e_field, grid_tables, is_updated

def make_field_data_plot(field_data):
    zmax = np.max([np.max(field_data)*0.9, 1.0])
    fig = px.imshow(field_data.T, origin='lower',
                    zmin=0., zmax=zmax,
                    color_continuous_scale="turbo")

    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)

    fig.update_layout(
        height=480,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    return fig

def make_grid_plot(grid_tables):
    vertices = grid_tables[0]['Points'][:, :2] #2D points

    triangles = np.zeros((grid_tables[1]['Points'][0].size, 3), dtype=np.int64)
    triangles[:, 0] = grid_tables[1]['Points'][0]
    triangles[:, 1] = grid_tables[1]['Points'][1]
    triangles[:, 2] = grid_tables[1]['Points'][2]
    triangles -= 1
    color_index = grid_tables[1]['DomainId']

    palette = qualitative.Plotly

    unique_colors = np.unique(color_index)

    color_map = {
        c: palette[i % len(palette)]
        for i, c in enumerate(unique_colors)
    }

    fig = go.Figure()

    # for tri, c in zip(triangles, color_index):
    #     pts = vertices[tri]

    #     fig.add_trace(
    #         go.Scatter(
    #             x=np.r_[pts[:, 0], pts[0, 0]],
    #             y=np.r_[pts[:, 1], pts[0, 1]],
    #             fill='toself',
    #             mode='lines',
    #             line=dict(color='black'),
    #             fillcolor=palette[c % len(palette)],
    #             showlegend=False
    #         )
    #     )

    for color_id in np.unique(color_index):
        xs = []
        ys = []

        for tri in triangles[color_index == color_id]:
            pts = vertices[tri]

            xs.extend([pts[0,0], pts[1,0], pts[2,0], pts[0,0], None])
            ys.extend([pts[0,1], pts[1,1], pts[2,1], pts[0,1], None])

        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode='lines',
                fill='toself',
                fillcolor=color_map[color_id],
                line=dict(width=1),
                showlegend=False
            )
        )

    edge_x = []
    edge_y = []

    for tri in triangles:
        pts = vertices[tri]

        edge_x.extend([
            pts[0, 0], pts[1, 0],
            None,
            pts[1, 0], pts[2, 0],
            None,
            pts[2, 0], pts[0, 0],
            None
        ])

        edge_y.extend([
            pts[0, 1], pts[1, 1],
            None,
            pts[1, 1], pts[2, 1],
            None,
            pts[2, 1], pts[0, 1],
            None
        ])

    fig.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode='lines',
            line=dict(color='black', width=0.5),
            showlegend=False,
            hoverinfo='skip',
        )
    )

    xmin, ymin = vertices.min(axis=0)
    xmax, ymax = vertices.max(axis=0)

    # optional small padding
    #pad = 0.02 * max(xmax - xmin, ymax - ymin)
    pad = 0.

    fig.update_xaxes(range=[xmin - pad, xmax + pad])
    fig.update_yaxes(range=[ymin - pad, ymax + pad])

    # keep aspect ratio
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    #fig.update_yaxes(scaleanchor="x", scaleratio=1)

    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)

    fig.update_layout(
        height=480,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)

    return fig


@app.callback([Output(component_id='jcm_mesh_output', component_property= 'style'),
               Output(component_id='jcm_intensity_output', component_property= 'style')
              ],
              [Input("plot-type-dropdown", "value"),
                ])
def swap_displayed_data(plot_type):
    if plot_type == "Simulation Mesh":
        return {"height": "480px", "width": "640px", "display": "block"}, {"height": "480px", "width": "640px", "display": "none"}
    elif plot_type == "Intensity":
        return {"height": "480px", "width": "640px", "display": "none"}, {"height": "480px", "width": "640px", "display": "block"}
    else:
        raise PreventUpdate()

@app.callback([Output(component_id='jcm_mesh_output', component_property= 'figure'),
               Output(component_id='jcm_intensity_output', component_property= 'figure')
              ],
              [Input('current-page-store', 'data'),
               Input('plot-type-dropdown', 'value'),
               Input('dropdown-selection-store', 'data')
                ])
def make_jcmwave_simulation(data, plot_type, selected_option):
    print("selected option: ", selected_option)
    print('make_jcmwave_simulation was called')
    print('Value of data: ', data, type(data))
    if data is None:
        raise PreventUpdate()
    elif not data == 5:
        raise PreventUpdate()
    else:
        try:
            threshold_data = session['current_threshold_image']
            print('Reached')
        except:
            raise PreventUpdate()


        print('img data shape: {}'.format(threshold_data.shape))
        for ii in range(1):
            print(ii, np.min(threshold_data), np.max(threshold_data))

        match selected_option:
            case "btn-opt-a":
                project = "jcmwave"
            case "btn-opt-b":
                project = os.path.join('jcmwave2', '2D')
        field_data, grid_tables, is_updated = run_jcmwave_simulation(threshold_data, project)
        if is_updated:
            fig1 = make_grid_plot(grid_tables)
            fig2 = make_field_data_plot(field_data)
        else:
            raise PreventUpdate()


    return [fig1, fig2]
