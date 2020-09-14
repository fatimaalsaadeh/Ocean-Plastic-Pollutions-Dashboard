from flask import Flask, render_template, request
import plotly
import plotly.graph_objs as go

import pandas as pd
import numpy as np
import json

us_cities = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/us-cities-top-1k.csv")

import plotly.express as px

app = Flask(__name__)


@app.route('/')
def index():
    bar = create_bar_plot()
    scatter = create_scatter_plot()
    map = create_map()
    return render_template('index.html', plot=[bar, map, scatter])


def create_scatter_plot():
    width = 667
    height = 334
    df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv')
    data = [go.Scatter(x=df['Date'], y=df['AAPL.High'])]
    layout = go.Layout(
        autosize=False,
        width=width,
        height=height,
        margin=go.layout.Margin(
            l=25,  # left margin
            r=0,  # right margin
            b=20,  # bottom margin
            t=0  # top margin
        )
    )
    fig = dict(data=data, layout=layout)
    data = fig
    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON


@app.route('/create_plot', methods=['GET', 'POST'])
def create_bar_plot(count=40):
    N = count
    width = 390
    height = 318
    x = np.linspace(0, 1, N)
    y = np.random.randn(N)
    df = pd.DataFrame({'x': x, 'y': y})  # creating a sample dataframe
    data = [
        go.Bar(
            x=df['x'],  # assign x as the dataframe column 'x'
            y=df['y']
        )
    ]
    layout = go.Layout(
        autosize=False,
        width=width,
        height=height,
        margin=go.layout.Margin(
            l=25,  # left margin
            r=0,  # right margin
            b=20,  # bottom margin
            t=0  # top margin
        )
    )
    fig = dict(data=data, layout=layout)
    data = fig
    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON


def create_map():
    fig = px.scatter_mapbox(us_cities, lat="lat", lon="lon", hover_name="City", hover_data=["State", "Population"],
                            color_discrete_sequence=["#1F77B4"], zoom=3, width=650, height=318)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    data = fig
    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON


if __name__ == '__main__':
    app.run()
