from datetime import datetime
from distutils.log import INFO
from dash import Dash, html, dcc, Input, Output, State, dash_table, callback
import dash
import plotly.express as px
import pandas as pd
import utils.vote as vote
import LoraLogger
import utils.recorder as recorder
import utils.get_tickers as get_tickers
import dash_bootstrap_components as dbc

logger = LoraLogger.logger(__name__, INFO)

dash.register_page(__name__)

layout = html.Div(children=[
    html.H1(
        children='Get Stocks Based on Industries',
        style={
            'textAlign': 'center',
        }
    ),
    html.Div(children='What are the stocks for to your industry input ?', style={
        'textAlign': 'center',
    }),
    html.Div(
        children=[
            dcc.Input(
                id="input_{}".format('q'),
                # value='semiconductor',
                placeholder='what industry are you looking for?',
                type='text',
                debounce=True,
                style={
                    'display': 'inline-block',
                    'width': '35%',
                    'margin': 'auto',
                    'margin-right': '1px'
                }
            ),
            dcc.Input(
                id="input_{}".format('n'),
                value=20,
                placeholder='top n',
                min=1,
                step=1,
                type='number',
                debounce=True,
                style={
                    'display': 'inline-block',
                    'width': '10%',
                    'margin': 'auto',
                    'margin-right': '2px'
                }
            ),
            html.Button('Submit', id='submit-val',
                        n_clicks=0, style={'width': '70px'}),
            dcc.Input(
                id="input_nc",
                value='DO NOT CHANGE THIS FIELD',
                placeholder='DO NOT CHANGE',
                type='text',
                debounce=True,
                style={
                    'display': 'inline-block',
                    'width': '225px',
                    'margin': 'auto',
                    'margin-left': '1px'
                }
            ),
        ], style={'textAlign': 'center'}
    ),


    # dash_table.DataTable(id='scharts', columns=[
    #     {'name': 'symbol', 'id': 'symbol'},
    #     {'name': 'name_es', 'id': 'name_es'},
    #     {'name': 'name_zh_hant', 'id': 'name_zh_hant'},
    #     {'name': 'sector_score', 'id': 'sector_score'},
    #     {'name': 'mkt_cap', 'id': 'mkt_cap'},
    # ]),
    html.Div(id='scharts',
             style={'width': '75%', 'textAlign': 'center',
                    'margin': 'auto', 'margin-top': '30px'}
             ),
])


@callback(
    Output(component_id="scharts", component_property="children"),
    Input("submit-val", "n_clicks"),
    State("input_q", "value"),
    State("input_n", "value"),
    State("input_nc", "value"),
)
def update_output(x, q, n, nc):
    return chart_render_check(q, n, nc)


def chart_render_check(q, n, nc):
    dev = True
    if (nc == 'DO NOT CHANGE THIS FIELD'):
        dev = False
        return stock_chart_render(q, n, dev)
    elif (nc == 'I AM SUPERHOT'):
        dev = True
        return stock_chart_render(q, n, dev)
    else:
        empty = html.H2(
            children=["I told you NOT to change that FIELD!",
                      "Now change to 'DO NOT CHANGE THIS FIELD' to continue."],
            style={
                'textAlign': 'center',
                'margin-top': '100px',
            }
        )
        return empty


def stock_chart_render(q, n, dev):

    if (q):
        _, _, results = vote.get_voting_result(q, get_code=True, topn=6)

        request_time = (datetime.utcnow() -
                        datetime.utcfromtimestamp(0)).total_seconds() * 1000.0

        if bool(results['4']):
            df = get_tickers.get_stock_list_with_ind(results, topn=n)

            # columns = [{'name': i, 'id': i} for i in df.columns]
            # data = df.to_dict(orient='records')
            # chart = dash_table.DataTable(data, columns)
            chart = dbc.Table.from_dataframe(df, bordered=True, hover=True)

            log = {
                "input": q,
                "topn": n,
                "dev": dev,
                "request_time": request_time
            }
            resp = recorder.send(log, 'user-query-log-sectorsearch-gettickers')
            logger.debug(resp)
            return chart
        else:
            empty = html.H2(
                children='No corresponding industry!',
                style={
                    'textAlign': 'center',
                    'margin-top': '100px',
                }
            )
            log = {
                # "input_constructed": input_constructed,
                "input": q,
                "dev": dev,
                "topn": n,
                "output": {'description': 'empty output', 'content': ''},
                "request_time": request_time,
                # "output_raw": output_raw
            }
            # resp = recorder.send(log, 'user-query-log-sectorsearch-gettickers')
            # logger.debug(resp)
            return empty

    else:
        empty = html.H2(
            children="Enter query and hit 'Submit' to get started.",
            style={
                'textAlign': 'center',
                'margin-top': '100px',
            }
        )
        return empty
