from distutils.log import INFO
from dash import Dash, html, dcc
import dash
import dash_bootstrap_components as dbc
import LoraLogger
from json import dumps

logger = LoraLogger.logger(__name__, INFO)

app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.DARKLY])

app.layout = html.Div([
    html.H1(
        children='Sector Search',
        style={
            'textAlign': 'center',
        }
    ),

    html.Div(
        [
            html.Div(
                dcc.Link(
                    f"{page['name']} - {page['path']}", href=page["relative_path"],
                    style={
                        'margin-left': '100px'
                    }
                )

            )
            for page in dash.page_registry.values()
        ]
    ),

    dash.page_container
])

if __name__ == '__main__':
    app.run_server(host="0.0.0.0", port=8051)
