"""
Runs the backend for the website.

To run this script, add the hostname as the first argument. For example,
    python app.py 0.0.0.0
"""

import json
import math

import pandas as pd
import plotly
import plotly.express as px
import sqlite3
import re
import plotly.graph_objects as go
import geocoder as geocoder

from flask import Flask, render_template, request
from sys import argv

title = ""
with sqlite3.connect('ocean_plastic.db') as con:
    try:
        all_data = pd.read_sql('select * from plastic_all_data', con)
        top_10 = pd.read_sql('select * from plastic_top_10', con)
    except pd.io.sql.DatabaseError:
        all_data = pd.read_csv("all-cleanups.csv")
        all_data.to_sql('plastic_all_data', con)
        print('Added', len(all_data), 'rows to all_data table')
        top_10 = pd.read_csv("https://opendata.arcgis.com/datasets/7afcc89e5a0f4c339ddf7b4bf6fabe3d_0.csv")
        top_10.to_sql('plastic_top_10', con)
        print('Added', len(top_10), 'rows to plastic_top_10 table')

try:
    hostname = argv[1]
except:
    hostname = '0.0.0.0'
app = Flask(__name__)

city_l = ""
country_l = ""
def get_organizations():
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            organization = pd.read_sql(
                'SELECT [Organization]  FROM plastic_all_data  where [Organization] IS NOT NULL'
                , con)
            organization = organization['Organization'].unique()
            return organization.tolist()
        except pd.io.sql.DatabaseError as e:
            print(e)

def create_organize_map():
    query = '''select DateOriginal, Latitude1,Longitude1,Location,NAME,COUNTRY,ISO_CC,sum(TotalVolunteers) TotalVolunteers,EventType, sum(Totalltems_EventRecord) Totalltems_EventRecord
            FROM plastic_all_data
            group by Latitude1, Longitude1,DateOriginal,Location,NAME,COUNTRY,ISO_CC,EventType
            order by sum(Totalltems_EventRecord) desc'''
    condition = ""
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            all_data = pd.read_sql(query + condition, con)
        except pd.io.sql.DatabaseError as e:
            print(query + condition)
            print(e)
    all_data = all_data.dropna()
    all_data['DateOriginal'] = pd.to_datetime(all_data['DateOriginal'])
    print(all_data['DateOriginal'])
    all_data = all_data[all_data["DateOriginal"].isin(pd.date_range('5/1/2020','8/30/2020'))]
    all_data["month-year"]=all_data['DateOriginal'].dt.to_period('M')
    print(all_data)
    px.set_mapbox_access_token(open(".mapbox_token").read())
    fig = px.scatter_mapbox(all_data, lat="Latitude1", lon="Longitude1", hover_name="Location",
                            hover_data=["NAME", "COUNTRY", "ISO_CC", "TotalVolunteers", "EventType", "Location"], size="Totalltems_EventRecord", color="month-year",
                            color_continuous_scale=px.colors.cyclical.HSV,
                            zoom=1, width=667, height=334)
    fig.update_traces(
        hovertemplate=None
    )
    fig.update_layout(mapbox_style="mapbox://styles/falsaadeh/ckf7f7mx70d6d19qkal4k4u99",
                      mapbox=dict(
                          accesstoken=open(".mapbox_token").read(),
                          center=go.layout.mapbox.Center(
                              lat=39.1176,
                              lon=-123.7096
                          ),
                          pitch=0,
                          zoom=4
                      ),
                      margin={"r": 0, "t": 0, "l": 0, "b": 0},
                      )
    data = fig
    graph_json = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
    return graph_json


if __name__ == '__main__':
    app.run(host=hostname)
