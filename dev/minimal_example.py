import dash
import dash_bootstrap_components as dbc


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                suppress_callback_exceptions=True)

content =  [dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardImg(top=True),                            
                        ]),
                        width=8
                    )],
                    justify="center",
                ),                                
]
                

app.layout = dbc.Container(
    content,
    className = 'container')

if __name__ == '__main__':
    app.run_server(debug=True)
