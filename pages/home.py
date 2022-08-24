import dash
from dash import html, dcc

dash.register_page(__name__, path='/')

layout = html.Div(children=[
    html.H1(children='This is Sector Search Home page',
            style={
                'textAlign': 'center',
            }
            ),

    html.H2(children='''
        Please pick a function above
    ''',
            style={
                'textAlign': 'center',
            }),

])
