import json
from dash.dependencies import ALL, Input, Output, State
from config.stashprocessor import LISTINGS_DIR, UNIQUES_BLACKLIST
import os
from threads.stashprocessor.stashprocessor import StashProcessor
import dash
import dash_core_components as dcc
import dash_html_components as html
import math
import pandas as pd
import plotly.express as px


data = None

def create_item_selector():
    for _, _, files in os.walk(LISTINGS_DIR):
        item_selector = dcc.Dropdown(
            id='item-selector',
            options=[
                {'label': item_name, 'value': item_name}
            for item_name, _ in map(os.path.splitext, files) if item_name not in UNIQUES_BLACKLIST]
        )
        return item_selector

def create_app():
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
    app.layout = html.Div([
        html.H2('PoE Market Analyser'),
        create_item_selector(),
        html.Div(id='figures-container')
    ])
    return app

def create_stash_processor_thread():
    thread = StashProcessor()
    thread.setDaemon(True)
    thread.start()
    return thread

app = create_app()
server = app.server

def load_data(item_name):
    with open(os.path.join(LISTINGS_DIR, item_name + '.json')) as json_file:
        json_data = json.load(json_file)
        dict_ = {}
        for item in filter(lambda item: not item['corrupted'], json_data.values()):
            if 'price' not in dict_:
                dict_['price'] = []
            dict_['price'].append(item['price'])
            for mod in item['explicitMods'] + item['implicitMods']:
                key, = mod.keys()
                value, = mod.values()
                if key not in dict_:
                    dict_[key] = []
                dict_[key].append(value)
        try:
            df = pd.DataFrame.from_dict(dict_)
        except ValueError:
            print('Inconsistent number of mods!')
            return data
        return df

def create_figures():
    FIGS_PER_ROW = 2
    num_figs = len(data.columns) - 1
    num_rows = math.ceil(num_figs / FIGS_PER_ROW)
    fig_width = math.floor(100 / FIGS_PER_ROW)

    rows = []
    for row_num in range(num_rows):
        row = [
            dcc.Graph(
                id={'type': 'figure', 'index': i + row_num * FIGS_PER_ROW},
                style={'width': f'{fig_width}vw', 'height': '45vh'}
            )
        for i in range(FIGS_PER_ROW) if i + row_num * FIGS_PER_ROW < num_figs]
        rows.append(html.Div(row, style={'display': 'flex'}))
    return rows


@app.callback(
    Output('figures-container', 'children'),
    Input('item-selector', 'value'),
    State('figures-container', 'children'),
)
def item_selected(value, children):
    global data
    print(f'{value} selected')
    if value:
        data = load_data(value)
        figures = create_figures()
        children = figures
    return children

@app.callback(
    Output({'type': 'figure', 'index': ALL}, 'figure'),
    Input({'type': 'figure', 'index': ALL}, 'selectedData')
)
def update_fig(*args):
    def intersect(a, b):
        return [v for v in a if v in b]
    
    def get_figure(df, x_col, y_col, selectedpoints):
        fig = px.scatter(df, x=df[x_col], y=df[y_col], text=df.index)
        fig.update_traces(
            selectedpoints=selectedpoints,
            customdata=df.index,
            mode='markers',
            marker={ 'color': 'rgba(255, 0, 0, 0.7)', 'size': 10 },
            unselected={
                'marker': {
                    'color': 'rgba(0, 116, 217, 0.2)',
                    'size': 7,
                },
            }
        )
        fig.update_layout(dragmode='select')
        return fig

    selected_points = data.index
    for selected_data in args[0]:
        if selected_data and selected_data['points']:
            selected_points = intersect(selected_points, [p['customdata'] for p in selected_data['points']])
    return [
        get_figure(data, data.columns[i], data.columns[0], selected_points)
    for i in range(1, len(data.columns))]

if __name__ == '__main__':
    create_stash_processor_thread()
    app.run_server()
