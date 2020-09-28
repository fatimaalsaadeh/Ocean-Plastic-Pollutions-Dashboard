"""
Runs the backend for the website.

To run this script, add the hostname as the first argument. For example,
    python app.py 0.0.0.0
"""

import json
import pandas as pd
import plotly
import plotly.express as px
import sqlite3
import re

from flask import Flask, render_template, request
from sys import argv

with sqlite3.connect('ocean_plastic.db') as con:
    try:
        all_data = pd.read_sql('select * from plastic_all_data', con)
        top_10 = pd.read_sql('select * from plastic_top_10', con)
    except pd.io.sql.DatabaseError:
        all_data = pd.read_csv("https://opendata.arcgis.com/datasets/98631dc5bb9a4ea5a8f9c0b4ec433290_0.csv")
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


@app.route('/')
def index():
    bar = create_bar_plot()
    scatter = create_scatter_plot()
    mapp = create_map()
    stats = eval(get_stats())
    years = get_years()
    locations = get_locations()
    return render_template('index.html', params=[[bar, mapp, scatter], stats, years, locations])


def title_formatting(params):
    title = ""
    if params['by_location']:
        title = params["location"].split(',')[0].replace("'", "") + ','
    title += params["city"].replace("'", "") + ", " if params["city"] else ""
    title += params["country_code"].replace("'", "") if params["country_code"] else ""

    return title


def params_pre_check():
    country_code = request.args.get('country_code')
    city = request.args.get('city')
    location = request.args.get('location')
    month_year = request.args.get('month_year')
    if month_year is not None:
        month_year.replace("'", "")
    by_location = True if request.args.get('byLocation') == "true" else False
    if city is None and country_code is None and location is None:
        country_code = '\'US\''
        city = '\'California\''
        location = '\'Blackpoint Beach, Sonoma, CA, United States\''
    return {"country_code": country_code, "city": city, "location": location, "by_location": by_location,
            "month_year": month_year}


@app.route('/create_scatter', methods=['GET', 'POST'])
def create_scatter_plot():
    width = 372
    height = 334
    params = params_pre_check()
    query = 'SELECT Totalltems_EventRecord as TotalItemsRecorded, DateOriginal as EventDate FROM plastic_all_data '
    condition = ' and DateOriginal IS Not null and Totalltems_EventRecord  IS Not null'
    if params["month_year"]:
        # condition = condition + ' and DateOriginal > \'2017-09-01 00:00:00.0000000\' and DateOriginal < \'2018-09-30 00:00:00.0000000\'  ORDER by DateOriginal desc'
        startDate = params["month_year"].replace("'", "") + '/01 00:00:00'
        endDate = params["month_year"].replace("'", "") + '/30 00:00:00'
        condition = condition + ' and DateOriginal >= \'' + startDate + '\' and DateOriginal <= \'' + endDate + '\' ORDER by DateOriginal desc'
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            if params["by_location"]:
                plastic_all_data = pd.read_sql(query + 'Where Location=' + params["location"] + condition, con)
            elif params["city"] is not None:
                plastic_all_data = pd.read_sql(query + 'Where Name=' + params["city"] + condition, con)
            if len(plastic_all_data) == 0 and params["country_code"] is not None:
                plastic_all_data = pd.read_sql(query + 'Where ISO_CC=' + params["country_code"] + condition, con)
            plastic_all_data['EventDate'] = plastic_all_data['EventDate'].str.replace('00:00:00', '')

            fig = px.scatter(plastic_all_data, x="EventDate", y="TotalItemsRecorded",
                             color="TotalItemsRecorded", width=width, height=height,
                             color_discrete_sequence=px.colors.qualitative.Set1)
            fig.update_layout(
                coloraxis_showscale=False,
                plot_bgcolor='rgba(0, 0, 0, 0)',
                paper_bgcolor='rgba(0, 0, 0, 0)',
                legend=dict(font=dict(size=11)), margin={"r": 0, "t": 25, "l": 0, "b": 0})
            graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            return graph_json
        except pd.io.sql.DatabaseError as e:
            print(e)


def get_years():
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            years = pd.read_sql(
                'SELECT [DateOriginal] as years  '
                'FROM plastic_all_data '
                'where [DateOriginal] is not NULL'
                ' group by [DateOriginal] '
                , con)
            years = pd.to_datetime(years['years']).dt.year.unique()
            return years
        except pd.io.sql.DatabaseError as e:
            print(e)


def get_locations():
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            locations = pd.read_sql(
                'SELECT [Location]  FROM plastic_all_data  where [Location] IS NOT NULL'
                , con)
            locations = locations['Location'].unique()
            return locations.tolist()
        except pd.io.sql.DatabaseError as e:
            print(e)


@app.route('/get_stats', methods=['GET', 'POST'])
def get_stats():
    params = params_pre_check()
    query = 'SELECT SUM([TotalVolunteers]) as totalVolunteers, count(*) as countAll, sum(Totalltems_EventRecord)as TotalltemsEventsRecorded, Avg(TotalLength_m)  as totalArea FROM plastic_all_data '
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            if params['by_location']:
                stat = pd.read_sql(query + 'Where [Location] =' + params["location"], con)
            else:
                stat = pd.read_sql(query + 'Where [Name] =' + params["city"], con)
            total_volunteers = count_all = total_items_events_recorded = ""
            if stat.totalVolunteers.values[0] is not None:
                total_volunteers = str(int(stat.totalVolunteers.values[0]))
            if stat.countAll.values[0] is not None:
                count_all = str(int(stat.countAll.values[0]))
            if stat.TotalltemsEventsRecorded.values[0] is not None:
                total_items_events_recorded = str(int(stat.TotalltemsEventsRecorded.values[0]))
            if stat.totalArea.values[0] is not None:
                total_area = str(int(stat.totalArea.values[0]))
            return json.dumps([total_volunteers, count_all, total_items_events_recorded, total_area])
        except pd.io.sql.DatabaseError as e:
            print(e)
            return json.dumps([0, 0, 0, 0])
        return json.dumps([0, 0, 0, 0])


def get_plastic_top_ten_location(location):
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            name_top_10 = pd.read_sql("""SELECT
                 SUM([Totalltems_EventRecord]) total
                ,SUM([TotalClassifiedItems_EC2020]) classified
                ,SUM([SUM_Hard_PlasticBeverageBottle] ) PlasticBeverageBottle
                ,SUM([SUM_Hard_OtherPlasticBottle]) OtherPlasticBottle
                ,SUM([SUM_HardOrSoft_PlasticBottleCap]) PlasticBottleCap
                ,SUM([SUM_PlasticOrFoamFoodContainer]) FoodContainer
                ,SUM([SUM_Hard_BucketOrCrate]) BucketOrCrate
                ,SUM([SUM_Hard_Lighter]) HardLighter
                ,SUM([SUM_OtherHardPlastic]) OtherHardPlastic
                ,SUM([SUM_PlasticOrFoamPlatesBowlsCup]) FoamPlatesBowlsCup
                ,SUM([SUM_HardSoft_PersonalCareProduc]) PersonalCareProduc
                ,SUM([SUM_HardSoftLollipopStick_EarBu]) SoftLollipopStick
                ,SUM([SUM_Soft_Bag]) SoftBag
                ,SUM([SUM_Soft_WrapperOrLabel]) WrapperOrLabel
                ,SUM([SUM_Soft_Straw]) Straw
                ,SUM([SUM_Soft_OtherPlastic]) OtherSoftPlastic
                ,SUM([SUM_Soft_CigaretteButts]) CigaretteButts
                ,SUM([SUM_FishingLineLureRope]) FishingLineLureRope
                ,SUM([SUM_OtherPlasticDebris]) OtherPlasticDebris
            FROM plastic_all_data
            Where [Location] LIKE """ + location + " GROUP by [Location]", con)
            if len(name_top_10) > 0:
                columns = list(name_top_10)
                pct = []
                name = []
                for i in columns:
                    if i != "total" and i != "classified":
                        if name_top_10[i][0] is not None:
                            pct.append(round((name_top_10[i][0] / name_top_10["classified"][0]) * 100, 2))
                        else:
                            pct.append(0)
                        name.append(re.sub('([A-Z])', r' \1', i))
                df = pd.DataFrame({'Category': name, 'Percentage': pct})
                df.sort_values(by='Percentage', inplace=True, ascending=False)
                df = df.head(10)
                return df
            return pd.DataFrame()
        except pd.io.sql.DatabaseError as e:
            print(e)
            return pd.DataFrame()


def get_plastic_top_ten_city(city, country_code):
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            name_top_10 = pd.read_sql('select * from plastic_top_10 WHERE [Name]=' + city, con)
            if len(name_top_10) == 0:
                name_top_10 = pd.read_sql('select * from plastic_top_10 WHERE [ISO_2DIGIT]=' + country_code, con)
            if len(name_top_10) > 0:
                columns = list(name_top_10)
                pct = []
                name = []
                for i in columns:
                    if re.match("Top[0-9]_PCT", i):
                        pct.append(name_top_10[i][0])
                    if re.match("Top[0-9]_Name", i):
                        name.append(name_top_10[i][0].replace("Plastic/Foam", ""))
                df = pd.DataFrame({'Category': name, 'Percentage': pct})
                return df
            return pd.DataFrame()
        except pd.io.sql.DatabaseError as e:
            print(e)
            return pd.DataFrame()


@app.route('/create_plot', methods=['GET', 'POST'])
def create_bar_plot():
    params = params_pre_check()
    if params["by_location"]:
        df = get_plastic_top_ten_location(params["location"])
    else:
        df = get_plastic_top_ten_city(params["city"], params["country_code"])

    title = title_formatting(params)
    fig = px.bar(df, y="Category", x="Percentage", text="Percentage",
                 title='Top 10 most common plastics in ' + title,
                 width=667, height=334, orientation='h', color="Category",
                 color_discrete_sequence=px.colors.qualitative.Antique)
    fig.update_layout(
        legend=dict(font=dict(size=11)), xaxis=dict(
            autorange=True,
            showgrid=False,
            ticks='',
            showticklabels=False
        ), margin={"r": 0, "t": 25, "l": 0, "b": 0})
    data = fig
    graph_json = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
    return graph_json


def create_map():
    px.set_mapbox_access_token(open(".mapbox_token").read())
    fig = px.scatter_mapbox(all_data, lat="Latitude1", lon="Longitude1", hover_name="Location",
                            hover_data=["NAME", "COUNTRY", "ISO_CC", "TotalVolunteers", "EventType", "Location"],
                            color_discrete_sequence=["#9AD1FF"],
                            zoom=1, width=667, height=334)
    fig.update_traces(
        hovertemplate=None
    )
    fig.update_layout(mapbox_style="mapbox://styles/falsaadeh/ckf7f7mx70d6d19qkal4k4u99",
                      mapbox_accesstoken=open(".mapbox_token").read(),
                      margin={"r": 0, "t": 0, "l": 0, "b": 0})

    data = fig
    graph_json = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
    return graph_json


if __name__ == '__main__':
    app.run(host=hostname)
