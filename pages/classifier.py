from datetime import datetime
from distutils.log import INFO
from dash import Dash, html, dcc, Input, Output, State, callback
import dash
import plotly.express as px
import pandas as pd
import utils.vote as vote
import LoraLogger
import utils.recorder as recorder
from json import dumps

logger = LoraLogger.logger(__name__, INFO)

dash.register_page(__name__)


layout = html.Div(children=[
    html.H1(
        children='Query Classifier',
        style={
            'textAlign': 'center',
        }
    ),

    html.Div(children='What are the sectors related to your input ?', style={
        'textAlign': 'center',
    }),

    html.Div(
        children=[
            dcc.Input(
                id="input_{}".format('q'),
                # value='semiconductor',
                placeholder='your query',
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
                value=6,
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

    html.Div(style={'textAlign': 'center'}, id='charts'),
])


@callback(
    Output("charts", "children"),
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
        return chart_render(q, n, dev)
    elif (nc == 'I AM SUPERHOT'):
        dev = True
        return chart_render(q, n, dev)
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


def chart_render(q, n, dev):

    if (q and n):
        input_constructed = []
        output_raw = []
        output = []
        constructed, result_raw, results = vote.get_voting_result(
            q, get_code=False, topn=n)

        results = list(results.items())
        request_time = (datetime.utcnow() -
                        datetime.utcfromtimestamp(0)).total_seconds() * 1000.0
        if bool(results):
            charts = []
            for result in results:
                logger.info(result)
                output.append({
                    'description': 'code ' + result[0],
                    'content': dumps(result[1])
                })
                df = pd.DataFrame({
                    "Sector": [x[0] for x in result[1].items()],
                    "Scores": [x[1] for x in result[1].items()]
                })
                fig = px.pie(df, values='Scores', names='Sector',
                             title=f"Name {result[0]} Distribution").update_layout(template="plotly_dark")
                charts.append(dcc.Graph(
                    id=f"pie{result[0]}",
                    figure=fig,
                    style={'display': 'inline-block'}
                ))
            log = {
                # "input_constructed": input_constructed,
                "input": q,
                "topn": n,
                "output": output,
                "dev": dev,
                "request_time": request_time,
                # "output_raw": output_raw
            }
            resp = recorder.send(log, 'user-query-log-stocksearch')
            logger.debug(resp)
            return charts
        else:
            empty = html.H2(
                children='No corresponding stocks!',
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
            resp = recorder.send(log, 'user-query-log-stocksearch')
            logger.debug(resp)
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
