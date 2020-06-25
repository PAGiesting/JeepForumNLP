#!/usr/bin/env python
# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pickle
import numpy as np

# Open pickled model data & model
with open('app_data.pkl','rb') as cellar:
    [topic_scores,norm_probs,x,y,top_docs] = pickle.load(cellar)
# Data for the four components of the dashboard:
# Topic scores (an array)
# Document pseudocounts by topic (an array)
# Words and word scores for each topic (lists of lists)
# Top document for each topic (list of strings, lemmatized post data)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
    'background': '#222222',
    'text': '#874545'
}

app.layout = html.Div(children=[
    html.H1(children='jeepforum.com Post Topic Analytics',
        style={
            'textAlign': 'center',
            'color': colors['text']
        }),

    html.Div(children='''
        Analysis by Paul Giesting.\n
        Using the CorEx library.\n
        Powered by Dash: A web application framework for Python.
    ''', style={
        'textAlign': 'center',
        'color': colors['text']
    }),

    html.Div(children=[
        dcc.Graph(
            id='corr-graph',
            figure={
                'data': [
                    {'x': list(range(20)), 'y': topic_scores, 
                    'marker_color': 'rgb(87,45,45)', 'type': 'bar', 'name': 'TC'},
                ],
                'layout': dict(
                    #title='Total Correlation by Topic',
                    xaxis={'title': 'Topic'},
                    yaxis={'title': 'Total Correlation'},
                    margin={'l': 40, 'b': 40, 't': 40, 'r': 40},
                    legend={'x': 1, 'y': 1},
                    hovermode='closest'
                )
            }
        )
    ],
        style={'width':'50%','display':'inline-block'}
    ),

    html.Div([
        dcc.Graph(id='word-graph'),
        dcc.Slider(
            id='topic-slider',
            min=0,
            max=19,
            value=0,
            marks={str(t): str(t) for t in range(20)},
            step=None
        )],
            style={'width':'47%','display':'inline-block'}
    ),

    html.Div(children=[
        dcc.Graph(
            id='freq-graph',
            figure={
                'data': [
                    {'x': list(range(20)), 'y': norm_probs, 'type': 'bar', 'name': 'TPC'},
                ],
                'layout': dict(
                    #title='Document Pseudocounts by Topic',
                    xaxis={'title': 'Topic'},
                    yaxis={'title': 'Pseudocounts\n(Summed & Normalized Probabilities)'},
                    margin={'l': 80, 'b': 40, 't': 40, 'r': 40},
                    legend={'x': 1, 'y': 1},
                    hovermode='closest'
                )
            }
        )
    ],
        style={'width':'50%','display':'inline-block'}
    ),

    html.Div(children=[
        html.H5(id='top-post-headline',),
        html.Div(id='top-post',)
    ],
        style={'width':'47%','display':'inline-block'}
    )
])

@app.callback(
    [Output('word-graph', 'figure'),
     Output('top-post-headline', 'children'),
     Output('top-post', 'children')],
    [Input('topic-slider', 'value')])

def update_figure(selected_topic):
    trace = [{'x': x[selected_topic], 'y': y[selected_topic],
                'type': 'bar', 'name': 'WS'}]

    return {
        'data': trace,
        'layout': dict(
            #title=('Topic '+str(selected_topic)),
            xaxis={'title': 'Words'},
            yaxis={'title': 'CorEx Score'},
            margin={'l': 40, 'b': 60, 't': 40, 'r': 40},
            legend={'x': 1, 'y': 1},
            hovermode='closest',
            transition = {'duration': 300},
        )
    }, 'Topic '+str(selected_topic)+' Top Post', \
        top_docs[selected_topic][0][0]

if __name__ == '__main__':
    app.run_server(debug=True)