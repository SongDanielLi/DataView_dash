import base64
import datetime
import io
import math

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table

import pandas as pd
import plotly.express as px

"""
References:
https://dash.plotly.com/datatable/callbacks
https://dash.plotly.com/datatable/editable
"""

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
PAGE_TABLE_SIZE = 50

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}
PAGE_SIZE = 10

app.layout = html.Div(children=[
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px',
        },
        # Allow multiple files to be uploaded
        # multiple=True
    ),
    dcc.Graph(id='DataGraph'),

    html.Br(),
    html.H5("Updated Table"),
    dash_table.DataTable(id = 'datatable-upload-container', 
        page_current=0, page_size=PAGE_SIZE, page_action='custom',
        sort_action='custom', sort_mode='single', sort_by=[]
    )
])

def parse_data(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = None
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
    return df


"""
Args:
    page_current : current page of dash_table
    page_size : page size of one page of dash_table
    contents : contents from upload file
    filename : uploaded filename

Returns:
    data : data for dash_table
    columns : columns of data
    page_count : total page count
"""
@app.callback([Output('datatable-upload-container', 'data'),
               Output('datatable-upload-container', 'columns'),
               Output('datatable-upload-container', 'page_count')],
              [Input('datatable-upload-container', "page_current"),
              Input('datatable-upload-container', "page_size"),
              Input('datatable-upload-container', 'sort_by'),
              Input('upload-data', 'contents'),],
              [State('upload-data', 'filename')])
def update_table(page_current, page_size, sort_by, contents, filename):
    if contents is None:
        return [{}], [], None

    df = parse_data(contents, filename)
    if df is None:
        return [{}], [], None
    
    # Sort values
    if(len(sort_by)):
        df.sort_values(sort_by[0]['column_id'],
            ascending=sort_by[0]['direction'] == 'asc',
            inplace=True)
    
    # total page count of table
    page_count = math.ceil(len(df) / page_size)
    df = df.iloc[page_current*page_size:(page_current+ 1)*page_size]

    return df.to_dict('records'), [{"name": i, "id": i} for i in df.columns], page_count

def getErrorFigure():
    return {
        "layout": {
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
            "annotations": [
                {
                    "text": "No matching data found",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 28}
                }
            ]
        }
    }

@app.callback(Output('DataGraph', 'figure'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])
def update_graph(contents, filename):
    fig = getErrorFigure()
    if contents is None:
        return fig

    df = parse_data(contents, filename)
    if df is not None:
        fig = px.line(df)
    return fig



if __name__ == '__main__':
    app.run_server(debug=True)