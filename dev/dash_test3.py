import dash
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

import plotly.graph_objects as go
import plotly.express as px

import numpy as np
from fibre.optics import *
from fibre.ray import RaySimulation




def plot_arc(figure, center, radius, start_angle, end_angle, color, name):
    phi = np.linspace(start_angle, end_angle, 100)
    r = np.ones(phi.shape)*radius
    x = r*np.cos(phi) + center[0]
    y = r*np.sin(phi) + center[1]

    figure.add_trace(go.Scatter(x=x, y=y,
                                mode='lines',
                                name=name + " {:.0f}".format(np.degrees(end_angle-start_angle)),
                                line=dict(color='rgba({}, {})'.format(color, 1.0), width=10., dash='dot'),
                                ))


app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

#df = px.data.stocks()

"""
app.layout = html.Div(id = 'parent',
    children = [
    html.H1(id = 'H1', children = 'Reflection and Transmission at an Interface', style = {'textAlign':'center',\
                                            'marginTop':40,'marginBottom':40}),

        dcc.Slider(min=0, max=85, step=5,
                   value = 45,
                   id = 'inc_angle'),
        dcc.Graph(id = 'air_glass_interface',
                  style={'width':"50%"})
    ])
"""

app.layout = html.Div(
    [
        dbc.Row(
            dbc.Col(children = [
                html.H1(id = 'H1',
                        children = 'Guiding Light in Fibre Optic',
                        style = {'textAlign':'center', 'marginTop':40, 'marginBottom':40})],
                width="auto",
                style={"border":"0px black solid"}),
                justify='center'),
        dbc.Row(
            [
                dbc.Col(dbc.ListGroup([
                            dbc.ListGroupItem("Mirror Reflection"),
                            dbc.ListGroupItem("Air - Glass Reflection"),
                            dbc.ListGroupItem("Glass - Air Reflection "),
                            dbc.ListGroupItem("Glass Fibre"),
                        ])
                        ,width=2,style={"border":"0px black solid"}),
                dbc.Col(
                    html.Div(children=[
                        dcc.Slider(min=0, max=89., step=1.,
                                  value = 45,
                                  marks=None,
                                  tooltip={"placement": "bottom", "always_visible": True},
                                  id = 'inc_angle1',
                                  ),
                        dcc.Dropdown(['Core', 'Core-Oil', 'Core-Cladding-Oil'], 'Core', id='geometry_selector'),
                        dcc.Graph(id = 'fibre_optic_sim',
                                  style={'width':"1200px", "height":"300px"}),
                            ]),
                    width=12,
                    style={"border":"0px black solid"}),
            ],
        justify='center'
        ),
    ],
    className = 'container')

@app.callback(Output(component_id='fibre_optic_sim', component_property= 'figure'),
              [Input(component_id='inc_angle1', component_property= 'value'),
               Input(component_id='geometry_selector', component_property= 'value')])
def graph_update(inc_angle1, geometry_selector):
    #inc_angle = 45.
    if np.isclose(inc_angle1,90.0):
        inc_angle1 = 89.0

    return fibre_optic_graph(inc_angle1, geometry_selector)


def plot_segments(fig, obj):
    #for p0, p1 in pairwise(obj.exterior.coords):
    x, y = obj.exterior.xy
    fig.add_trace(go.Scatter(x=np.array(x), y=np.array(y),
                            mode='lines',
                            line=dict(color='black', width=1.),showlegend=False))

def plot_ray(fig, ray, color):
    x = (ray.origin[0], ray.end_point[0])
    y = (ray.origin[1], ray.end_point[1])
    fig.add_trace(go.Scatter(x=x, y=y,
                            mode='lines',
                            line=dict(color='rgba({}, {:.2f})'.format(color, ray.intensity), width=2.),showlegend=False))

def fibre_optic_graph(inc_angle, geometry_selector):
    sim = RaySimulation()
    sim.init_ray(np.radians(inc_angle))
    sim.init_background()
    if geometry_selector == 'Core-Oil':
        sim.add_oil(0.4, 0.7, 20., 0.1, 2)
    elif geometry_selector == 'Core-Cladding-Oil':
        sim.add_cladding(0.4, 0.5, 20.)
        sim.add_oil(0.5, 0.8, 20., 0.1, 2)
    #sim.add_oil(0.5, 0.8, 20., 0.1, 2)
    #sim.add_cladding(0.5, 0.8, 20.)
    fig = go.Figure()
    for obj in sim.objects:
        plot_segments(fig, obj)
    #sim.find_intersection(sim.rays[0])
    sim.main()

    color1 = make_color(127, 201, 127)
    color2 = make_color(190,174,212)
    color3 = make_color(253,192,134)

    fig.update_layout(xaxis_showgrid=True, yaxis_showgrid=False, plot_bgcolor='white',
                     xaxis_showticklabels=False, yaxis_showticklabels=False)

    fig.update_xaxes(range=[-0.5, 7.5], autorange=False)
    fig.update_yaxes(range=[-1., 1.], autorange=False)

    for ray in sim.finished_rays:
        plot_ray(fig, ray, color1)
    return fig
    sim.plot_rays(ax)



    alpha1 = 1.
    alpha2 = R
    alpha3 = T


    fig.add_trace(go.Scatter(x=x_inc, y=y_inc,
                        mode='lines',
                         line=dict(color='rgba({}, {})'.format(color1, alpha1),
                                  width=10.),
                        name='Incident'))

    fig.add_trace(go.Scatter(x=x_ref, y=y_ref,
                        mode='lines',
                             line=dict(color='rgba({}, {})'.format(color2, alpha2),
                                       width=10.),
                        name='Reflected: {:.2f}%'.format(alpha2*100)))
    if np.imag(n_trans) == 0:
        fig.add_trace(go.Scatter(x=x_trn, y=y_trn,
                            mode='lines',
                             line=dict(color='rgba({}, {})'.format(color3, alpha3),
                                  width=10.),
                            name='Transmitted: {:.2f}%'.format(alpha3*100)))

    fig.add_shape(type='line',
                    yref="y",
                    xref="x",
                    x0=0.,
                    y0=-2.,
                    x1=0.,
                    y1=2.,
                    line=dict(color='black', width=3))

    fig.add_shape(type='line',
                    yref="y",
                    xref="x",
                    x0=-2.,
                    y0=0.,
                    x1=2.,
                    y1=0.,
                    line=dict(color='black', width=3, dash='dash'))

    plot_arc(fig, (0,0), 0.5, np.pi, np.pi+inc_angle, color1, "Angle Inc.")
    plot_arc(fig, (0,0), 0.5, np.pi-inc_angle, np.pi, color2, "Angle Ref.")
    if np.imag(n_trans) == 0.:
        plot_arc(fig, (0,0), 0.5, 0., np.real(trans_angle), color3, "Angle Trans.")


    return fig



if __name__ == '__main__':
    app.run_server()
