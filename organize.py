"""
Runs the backend for the website.

To run this script, add the hostname as the first argument. For example,
    python app.py 0.0.0.0
"""
import io
import json
import numpy as np
import plotly
import plotly.express as px
from datetime import date
import plotly.graph_objects as go
import math
from flask import Flask, render_template, request, send_file
from sys import argv
from sklearn.linear_model import LinearRegression
import sqlite3
import warnings

warnings.filterwarnings("ignore")
import pandas as pd
import statsmodels.api as sm

title = ""
with sqlite3.connect('ocean_plastic.db') as con:
    try:
        all_data = pd.read_sql('select * from plastic_all_data', con)
        top_10 = pd.read_sql('select * from plastic_top_10', con)
    except pd.io.sql.DatabaseError:
        test = pd.read_csv("test.csv")
        test.to_sql('forecast_params', con)
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


def params_pre_check():
    if request:
        start_year = request.args.get('start_year')
        end_year = request.args.get('end_year')
        country_code = request.args.get('country_code')
        city = request.args.get('city')
        location = request.args.get('location')
        month = request.args.get('month')
        year = request.args.get('year')
        org = request.args.get('org')
        mapby = request.args.get('mapby')
        by_location = True if request.args.get('byLocation') == "true" else False
    else:
        start_year = None
        end_year = None
        country_code = None
        city = None
        location = None
        month = None
        year = None
        org = None
        mapby = None
        by_location = False
    if (city is None or city == "") and (country_code is None or country_code == "") and (
            location is None or location == ""):
        country_code = '\'US\''
        city = '\'California\''
        location = '\'Blackpoint Beach, Sonoma, CA, United States\''
    else:
        if country_code:
            country_code.replace("'", "")
        if city:
            city.replace("'", "")
    return {"country_code": country_code, "city": city, "location": location, "by_location": by_location,
            "month": month, "year": year, "start_year": start_year, "end_year": end_year, "org": org, "mapby": mapby}


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
    all_data = all_data[all_data["DateOriginal"].isin(pd.date_range('5/1/2020', '8/30/2020'))]
    all_data["month-year"] = all_data['DateOriginal'].dt.to_period('M')
    px.set_mapbox_access_token(open(".mapbox_token").read())
    fig = px.scatter_mapbox(all_data, lat="Latitude1", lon="Longitude1", hover_name="Location",
                            hover_data=["NAME", "COUNTRY", "ISO_CC", "TotalVolunteers", "EventType", "Location"],
                            size="Totalltems_EventRecord", color="month-year",
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
    global orgmap
    orgmap = all_data
    data = fig
    graph_json = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
    return graph_json


@app.route('/predStats', methods=['GET', 'POST'])
def predictStats():
    stats = ['TotalVolunteers', 'Totalltems_EventRecord', 'TotalLength_m']
    res = []
    params = params_pre_check()
    for i in stats:
        with sqlite3.connect('ocean_plastic.db') as con:
            try:
                locate = params['location'].replace("'", "")
                query = 'select DateOriginal,' + i + ' from plastic_all_data'
                condition = ' Where [location] like \'' + locate + '\''
                numVolunteers = pd.read_sql(query + condition, con)
                numVolunteers['DateOriginal'] = pd.to_datetime(numVolunteers['DateOriginal'])
                dropThis = pd.date_range('2020-01-01', '2020-09-29')
                numVolunteers = numVolunteers[~numVolunteers['DateOriginal'].isin(dropThis)]
                numVolunteers['date_delta'] = (numVolunteers['DateOriginal'] - numVolunteers[
                    'DateOriginal'].min()) / np.timedelta64(1, 'D')
                # Is this correct?
                model = LinearRegression()
                X = numVolunteers[['date_delta']]
                y = numVolunteers[i]
                model.fit(X, y)
                model.score(X, y)
                today = date.today()
                d1 = today.strftime("%Y-%m-%d")
                new = pd.DataFrame([[d1]], columns=['Date'])
                new['Date'] = pd.to_datetime(new['Date'])
                new['date_delta'] = (new['Date'] - numVolunteers['DateOriginal'].min()) / np.timedelta64(1, 'D')
                new_X = new[['date_delta']]
                pred = model.predict(new_X)
                if (math.ceil(pred[0]) < 0):
                    res.append("No Predicted Value")
                else:
                    res.append(math.ceil(pred[0]))
            except pd.io.sql.DatabaseError as e:
                print(e)
    return json.dumps(res)


def dataPreProcessing(params, drop=True):
    query = 'select * from plastic_all_data'
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            if params and params['city']:
                query += ' where Name = ' + params['city']
            elif params and params['country']:
                query += ' where Country = ' + params['country']
            all_data = pd.read_sql(query, con)
        except pd.io.sql.DatabaseError as e:
            print(e)
    all_data['DateOriginal'] = pd.to_datetime(all_data['DateOriginal'])
    if drop:
        dropThis = pd.date_range('2020-01-01', '2020-09-29')
        all_data = all_data[~all_data['DateOriginal'].isin(dropThis)]
    all_data.sort_values('DateOriginal')
    num_events_per_date = all_data.groupby(all_data['DateOriginal'])['DateOriginal'].count()
    num_events_per_date_df = pd.DataFrame(
        {'EventDate': num_events_per_date.index, 'numEvents': num_events_per_date.values})
    num_events_per_date_df = num_events_per_date_df.set_index('EventDate')
    num_events_per_date_df = num_events_per_date_df.resample('MS').mean()
    num_events_per_date_df = num_events_per_date_df.dropna()
    return num_events_per_date_df


@app.route('/predScatter', methods=['GET', 'POST'])
def create_organize_scatter():
    params = params_pre_check()
    print(params['city'])
    events_per_date_df = dataPreProcessing(params)
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            if params and params['city']:
                query = 'select * from forecast_params where name = ' + params['city']
            ml_params = pd.read_sql(query, con)
        except pd.io.sql.DatabaseError as e:
            print(e)
    if len(ml_params) > 0:
        arima_model = sm.tsa.statespace.SARIMAX(events_per_date_df,
                                                order=eval(ml_params.parameters[0]),
                                                seasonal_order=eval(ml_params.parameters_seasonal[0]),
                                                enforce_stationarity=False,
                                                enforce_invertibility=False)
        results = arima_model.fit()
        pred_uc = results.get_forecast(steps=30)
        pred_ci = pred_uc.conf_int()
        date = pd.date_range(str(events_per_date_df.tail(1).index[0]).split(" ")[0], periods=30, freq='MS')
        observ = pd.DataFrame(
            {'type': 'observed', 'EventDate': events_per_date_df.index,
             'numEvents': np.array(events_per_date_df.values).flatten()})
        mean_fore = pd.DataFrame(
            {'type': 'Forecast', 'EventDate': date, 'numEvents': pred_uc.predicted_mean.values})
        lower = pd.DataFrame(
            {'type': 'Forecast', 'EventDate': date, 'numEvents': pred_ci.iloc[:, 0]})
        upper = pd.DataFrame(
            {'type': 'Forecast', 'EventDate': date, 'numEvents': pred_ci.iloc[:, 1]})
        global orgscatter
        orgscatter = pd.concat([observ, lower, mean_fore, upper])
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=observ.EventDate, y=observ.numEvents,
            fill=None,
            line_color='blue',
            hoverinfo='x+y',
            mode='lines',
            name="observed"
        ))
        fig.add_trace(go.Scatter(
            x=upper.EventDate, y=upper.numEvents,
            hoverinfo='x+y',
            mode='lines',
            line=dict(width=0.5, color='rgb(105,105,105)'),
            name="upper limit forecast"
        ))
        fig.add_trace(go.Scatter(
            x=mean_fore.EventDate, y=mean_fore.numEvents,
            hoverinfo='x+y',
            mode='lines',
            line_color='red',
            line=dict(width=0.5, color='rgb(105,105,105)'),
            fill='tonexty',
            name="forecast"

        ))
        fig.add_trace(go.Scatter(
            x=lower.EventDate, y=lower.numEvents,
            hoverinfo='x+y',
            mode='lines',
            line=dict(width=0.5, color='rgb(105,105,105)'),
            fill='tonexty',
            name="lower limit forecast"

        ))
        t = "Number of Events History and Predictions In " + params['city'].replace("'", "")
        fig.update_layout(yaxis_range=(0, 100),
                          width=1000, height=334,
                          legend=dict(
                              orientation="h",
                              xanchor="center",
                              x=0.5
                          ),
                          title=t,
                          margin={"r": 0, "t": 25, "l": 0, "b": 0})
        data = fig
        graph_json = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
        return graph_json
    else:
        events_per_date_df = dataPreProcessing(params, drop=False)
        observ = pd.DataFrame(
            {'type': 'observed', 'EventDate': events_per_date_df.index,
             'numEvents': np.array(events_per_date_df.values).flatten()})
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=observ.EventDate, y=observ.numEvents,
            fill=None,
            line_color='blue',
            hoverinfo='x+y',
            mode='lines'
        ))
        fig.update_layout(yaxis_range=(0, 100),
                          width=1000, height=334,
                          legend=dict(
                              orientation="h",
                              yanchor="bottom",
                              y=1.02,
                              xanchor="right",
                              x=1
                          ),
                          title="Number of events history in " + params['city'],
                          margin={"r": 0, "t": 25, "l": 0, "b": 0})
        data = fig
        graph_json = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
        return graph_json


@app.route('/getData', methods=['GET', 'POST'])
def orgGetData(data_type):
    if data_type == 'orgscatter':
        csv = orgscatter.to_csv()
        buf_str = io.StringIO(csv)
        # Create a bytes buffer from the string buffer
        buf_byt = io.BytesIO(buf_str.read().encode("utf-8"))
        # Return the CSV data as an attachment
        return send_file(buf_byt,
                         mimetype="text/csv",
                         as_attachment=True,
                         attachment_filename="scatterData.csv")
    elif data_type == 'orgmap':
        csv = orgmap.to_csv()
        buf_str = io.StringIO(csv)
        # Create a bytes buffer from the string buffer
        buf_byt = io.BytesIO(buf_str.read().encode("utf-8"))
        # Return the CSV data as an attachment
        return send_file(buf_byt,
                         mimetype="text/csv",
                         as_attachment=True,
                         attachment_filename="mapData.csv")


if __name__ == '__main__':
    app.run(host=hostname)
