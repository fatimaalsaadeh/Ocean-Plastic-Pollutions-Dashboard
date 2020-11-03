"""
Runs the backend for the website.

To run this script, add the hostname as the first argument. For example,
    python app.py 0.0.0.0 
"""
import io
import json
import math

import pandas as pd
import plotly
import plotly.express as px
import sqlite3
import re
import plotly.graph_objects as go
import geocoder as geocoder

from flask import Flask, render_template, request, send_file
from sys import argv

from organize import *

# title = ""
# with sqlite3.connect('ocean_plastic.db') as con:
#     try:
#         all_data = pd.read_sql('select * from plastic_all_data', con)
#         top_10 = pd.read_sql('select * from plastic_top_10', con)
#         entangled  = pd.read_sql('select * from entangled_animals', con)
#     except pd.io.sql.DatabaseError:
#         entangled = pd.read_csv("EntangledAnimals.csv")
#         entangled.to_sql('entangled_animals', con)
#         all_data = pd.read_csv("all-cleanups.csv")
#         all_data.to_sql('plastic_all_data', con)
#         print('Added', len(all_data), 'rows to all_data table')
#         top_10 = pd.read_csv("https://opendata.arcgis.com/datasets/7afcc89e5a0f4c339ddf7b4bf6fabe3d_0.csv")
#         top_10.to_sql('plastic_top_10', con)
#         print('Added', len(top_10), 'rows to plastic_top_10 table')

try:
    hostname = argv[1]
except:
    hostname = '0.0.0.0'

app = Flask(__name__)
city_l = ""
country_l = ""

@app.route('/')
def index():
    # entanglements = entanglement()
    bar = g_bar
    scatter = g_scatter
    mapp = g_mapp
    stats = g_stats
    years = g_years
    locations = g_locations
    title = g_title
    top_organization = g_top_organization
    organizations = g_organizations
    return render_template('index.html',
                           params=[[bar, mapp, scatter], stats, years, locations, title, top_organization, city_l,
                                   country_l, organizations])


@app.route('/organize')
def organizef():
    stats = org_stats
    mapp = org_mapp
    scatter = org_scatter
    years = org_years
    locations = org_locations
    title = org_title
    top_organization = org_top_organization
    organizations = org_organizations
    return render_template('organize.html',
                           params=[[None, mapp, scatter], stats, years, locations, title, top_organization, city_l,
                                   country_l])


@app.route('/references')
def references():
    return render_template('references.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/get_title', methods=['GET', 'POST'])
def title_formatting(params=None):
    if params is None:
        params = params_pre_check()
    title = ""
    if params['by_location']:
        title = params["location"].split(',')[0].replace("'", "") + ','
    title += params["city"].replace("'", "") + ", " if params["city"] else ""
    title += params["country_code"].replace("'", "") if params["country_code"] else ""

    return json.dumps([title, params["location"], params["city"], params["country_code"]])


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
    if month is not None:
        month.replace("'", "")
    if year is not None:
        year.replace("'", "")
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


@app.route('/create_scatter', methods=['GET', 'POST'])
def create_scatter_plot():
    width = 542
    height = 334
    params = params_pre_check()
    query = 'SELECT Totalltems_EventRecord as TotalItemsRecorded, DateOriginal   FROM plastic_all_data '
    condition = ' and DateOriginal IS Not null and Totalltems_EventRecord  IS Not null'
    if params["month"]:
        # condition = condition + ' and DateOriginal > \'2017-09-01 00:00:00.0000000\' and DateOriginal < \'2018-09-30 00:00:00.0000000\'  ORDER by DateOriginal desc'
        datelimit = params["month"].replace("'", "") + "/%/" + params["year"].replace("'", "")
        condition = condition + ' and DateOriginal like \'' + datelimit + '\' ORDER by DateOriginal desc'
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            if params["by_location"]:
                plastic_all_data = pd.read_sql(query + 'Where Location=' + params["location"] + condition, con)
            elif params["city"] is not None:
                plastic_all_data = pd.read_sql(query + 'Where Name=' + params["city"] + condition, con)
                if len(plastic_all_data) == 0 and params["country_code"] is not None:
                    plastic_all_data = pd.read_sql(query + 'Where ISO_CC=' + params["country_code"] + condition, con)
            if params["org"]:
                plastic_all_data = pd.read_sql(query + 'Where Organization = \'' + params["org"] + "\'" + condition,
                                               con)

            plastic_all_data['DateOriginal'] = pd.to_datetime(plastic_all_data['DateOriginal'])
            if params["start_year"] and params["end_year"]:
                startyear = params["start_year"]
                endyear = params["end_year"]
                plastic_all_data = plastic_all_data[
                    plastic_all_data["DateOriginal"].isin(pd.date_range('1/1/' + startyear, '30/12/' + endyear))]
            plastic_all_data.groupby(plastic_all_data['DateOriginal'].dt.date).sum()
            plastic_all_data = plastic_all_data.set_index('DateOriginal')
            if not params["month"] and not params["year"]:
                plastic_all_data = plastic_all_data.resample('MS').mean()
                plastic_all_data.dropna()
                labels = []
                for l in plastic_all_data.index:
                    labels.append(l.strftime('%y-%m'))
                fig = px.line(plastic_all_data, x=plastic_all_data.index, y=plastic_all_data['TotalItemsRecorded'],
                              width=width, height=height,
                              labels={
                                  "DateOriginal": "Events Date",
                                  "TotalItemsRecorded": "Total Collected Items"
                              })
                fig.update_layout(
                    legend=dict(font=dict(size=11)), margin={"r": 0, "t": 25, "l": 0, "b": 0}
                )
                fig.data[0].update(mode='markers+lines')
                fig['data'][0]['line']['color'] = "#ffb3b3"
            else:
                fig = px.scatter(plastic_all_data, x=plastic_all_data.index, y=plastic_all_data['TotalItemsRecorded'],
                                 width=width, height=height, trendline="lowess")
                fig.update_layout(
                    plot_bgcolor='rgba(0, 0, 0, 0)',
                    paper_bgcolor='rgba(0, 0, 0, 0)',
                    legend=dict(font=dict(size=11)), margin={"r": 0, "t": 25, "l": 0, "b": 0})

            graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            global scatter_data
            scatter_data = plastic_all_data
            return graph_json
        except pd.io.sql.DatabaseError as e:
            app.logger.error(e)


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
            app.logger.error(e)


def get_locations():
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            locations = pd.read_sql(
                'SELECT [Location]  FROM plastic_all_data  where [Location] IS NOT NULL'
                , con)
            locations = locations['Location'].unique()
            return locations.tolist()
        except pd.io.sql.DatabaseError as e:
            app.logger.error(e)


@app.route('/get_orgs', methods=['GET', 'POST'])
def get_organizations():
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            organizations = pd.read_sql(
                'SELECT [Organization]  FROM plastic_all_data  where [Organization] IS NOT NULL'
                , con)
            organizations = organizations['Organization'].unique()
            return organizations.tolist()
        except pd.io.sql.DatabaseError as e:
            print(e)


@app.route('/get_top_orgs', methods=['GET', 'POST'])
def get_top_organization():
    params = params_pre_check()
    global city_l
    city_l = params['city']
    global country_l
    country_l = params['country_code']
    city = params['city']
    location = params['location']
    query = 'SELECT Organization, count(*) countOrganization From plastic_all_data'
    if city:
        condition = ' Where [Name]=' + city + ' and Organization is not null'
    if location:
        condition = ' Where [Location]=' + location + ' and Organization is not null'
    if params["start_year"] and params["end_year"]:
        startyear = params["start_year"]
        endyear = params["end_year"]
        datelimit1 = '\'%/' + startyear + '%\''
        datelimit2 = '\'%/' + endyear + "%\'"
        condition += ' and DateOriginal like ' + datelimit1
        condition += ' or DateOriginal like ' + datelimit2
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            condition += ' Group By Organization order by countOrganization desc'
            if params['by_location']:
                orgs = pd.read_sql(query + condition, con)
            else:
                orgs = pd.read_sql(query + condition, con)
            orgs = orgs.dropna()
            if len(orgs.Organization.values) > 0:
                return orgs.Organization.values[0]
            else:
                return ""
        except pd.io.sql.DatabaseError as e:
            print(e)
            return ""
    return ""


@app.route('/get_stats', methods=['GET', 'POST'])
def get_stats():
    params = params_pre_check()
    query = 'SELECT SUM([TotalVolunteers]) as totalVolunteers, count(*) as countAll, sum(Totalltems_EventRecord)as TotalltemsEventsRecorded, Avg(TotalLength_m)  as totalArea FROM plastic_all_data '
    condition = ''
    if params["month"]:
        # condition = condition + ' and DateOriginal > \'2017-09-01 00:00:00.0000000\' and DateOriginal < \'2018-09-30 00:00:00.0000000\'  ORDER by DateOriginal desc'
        datelimit = params["month"].replace("'", "") + "/%/" + params["year"].replace("'", "")
        condition = ' and DateOriginal like \'' + datelimit + '\''
    if params["start_year"] and params["end_year"]:
        startyear = params["start_year"]
        endyear = params["end_year"]
        datelimit1 = '\'%/' + startyear + '%\''
        datelimit2 = '\'%/' + endyear + "%\'"
        condition += ' and DateOriginal like ' + datelimit1
        condition += ' or DateOriginal like ' + datelimit2
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            condition += 'ORDER by DateOriginal desc'
            if params['by_location']:
                stat = pd.read_sql(query + 'Where [Location] =' + params["location"] + condition, con)
            elif params["city"]:
                stat = pd.read_sql(query + 'Where [Name] =' + params["city"] + condition, con)
            elif params["org"]:
                stat = pd.read_sql(query + 'Where [Organization] = \'' + params["org"] + "\'" + condition, con)
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
            app.logger.error(e)
            return json.dumps([0, 0, 0, 0])
        return json.dumps([0, 0, 0, 0])


@app.route('/info_box', methods=['GET', 'POST'])
def get_info_box():
    params = params_pre_check()
    organization = description = event_type = total_length = total_items_events_recorded = beachlocation = x = y = ""
    date_event = request.args.get('date').replace("'", "")
    total_items = request.args.get('totalItems')
    location = params["location"].replace("'", "")
    query = 'SELECT DateOriginal, Totalltems_EventRecord, Organization,EventType,TotalLength_m,DebrisDescription, [Location] as beachlocation, X,Y FROM plastic_all_data'
    condition = ''
    if params['by_location']:
        condition += ' Where [Location] like \'' + location + '\''
    else:
        condition += ' Where [Name] =' + params["city"]
    condition += ' AND [DateOriginal] like \'%' + date_event + '%\' And [Totalltems_EventRecord]=' + total_items
    organization = description = event_type = total_length = total_items_events_recorded = ""
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            stat = pd.read_sql(query + condition, con)
            if len(stat) > 0:
                if stat.Organization.values[0] is not None:
                    organization = str(stat.Organization.values[0])
                if stat.DebrisDescription.values[0] is not None:
                    description = str(stat.DebrisDescription.values[0])
                if stat.EventType.values[0] is not None:
                    event_type = str(stat.EventType.values[0])
                if stat.TotalLength_m.values[0] is not None:
                    total_length = str(int(stat.TotalLength_m.values[0]))
                if stat.Totalltems_EventRecord.values[0] is not None:
                    total_items_events_recorded = str(int(stat.Totalltems_EventRecord.values[0]))
                if stat.beachlocation.values[0] is not None:
                    beachlocation = str(stat.beachlocation.values[0])
                if stat.X.values[0] is not None:
                    x = str(stat.X.values[0])
                if stat.Y.values[0] is not None:
                    y = str(stat.Y.values[0])
            return json.dumps(
                [organization, description, event_type, total_length, total_items_events_recorded, beachlocation, x, y])
        except pd.io.sql.DatabaseError as e:
            print(e)
            return json.dumps(
                [organization, description, event_type, total_length, total_items_events_recorded, beachlocation, x, y])
        return json.dumps(
            [organization, description, event_type, total_length, total_items_events_recorded, beachlocation, x, y])


def get_plastic_top_ten_location(location):
    params = params_pre_check()
    condition = ""
    if params["month"]:
        # condition = condition + ' and DateOriginal > \'2017-09-01 00:00:00.0000000\' and DateOriginal < \'2018-09-30 00:00:00.0000000\'  ORDER by DateOriginal desc'
        datelimit = params["month"].replace("'", "") + "/%/" + params["year"].replace("'", "")
        condition += ' and DateOriginal like \'' + datelimit + '\''
    if params["start_year"] and params["end_year"]:
        startyear = params["start_year"]
        endyear = params["end_year"]
        datelimit1 = '\'%/' + startyear + '%\''
        datelimit2 = '\'%/' + endyear + "%\'"
        condition += ' and DateOriginal like ' + datelimit1
        condition += ' or DateOriginal like ' + datelimit2
    if params["org"]:
        condition += ' and Organization = \'' + params["org"] + "\'"
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
            Where [Location] LIKE """ + location + condition + " GROUP by [Location]", con)
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
            app.logger.error(e)
            return pd.DataFrame()


def get_plastic_top_ten_city(city, country_code):
    if country_code:
        country_code = country_code.replace(' ', '')
    params = params_pre_check()
    condition = ""
    query = """SELECT
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
            FROM plastic_all_data """
    if params["start_year"] and params["end_year"]:
        startyear = params["start_year"]
        endyear = params["end_year"]
        datelimit1 = '\'%/' + startyear + '%\''
        datelimit2 = '\'%/' + endyear + "%\'"
        condition += ' DateOriginal like ' + datelimit1
        condition += ' or DateOriginal like ' + datelimit2

    if params["month"]:
        # condition = condition + ' and DateOriginal > \'2017-09-01 00:00:00.0000000\' and DateOriginal < \'2018-09-30 00:00:00.0000000\'  ORDER by DateOriginal desc'
        datelimit = params["month"].replace("'", "") + "/%/" + params["year"].replace("'", "")
        condition = ' and DateOriginal like \'' + datelimit + '\' ORDER by DateOriginal desc'
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            print(city)
            if len(condition) > 0:
                condition = "AND " + condition
            if city:
                name_top_10 = pd.read_sql(query + ' WHERE [Name]=' + city + condition, con)
            if country_code and len(name_top_10) == 0:
                name_top_10 = pd.read_sql(
                    query + ' WHERE [ISO_2DIGIT]=' + country_code + ' OR [ISO_3DIGIT] =' + country_code + condition,
                    con)
            elif params["org"]:
                name_top_10 = pd.read_sql(query + ' WHERE [Organization]= \'' + params["org"] + "\'" + condition, con)
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
            app.logger.error(e)
            return pd.DataFrame()


@app.route('/create_plot', methods=['GET', 'POST'])
def create_bar_plot():
    params = params_pre_check()
    if params["by_location"]:
        df = get_plastic_top_ten_location(params["location"])
    else:
        print(params["city"])
        df = get_plastic_top_ten_city(params["city"], params["country_code"])

    title = json.loads(title_formatting(params))[0]
    fig = px.pie(df, values='Percentage', names='Category', color_discrete_sequence=px.colors.qualitative.Set3,
                 title='Top 10 most common plastics in ' + title,
                 width=500, height=334)
    fig.update_layout(
        legend=dict(font=dict(size=11)), xaxis=dict(
            autorange=True,
            showgrid=False,
            ticks='',
            showticklabels=False
        ), margin={"r": 0, "t": 25, "l": 0, "b": 0})
    data = fig
    global bar_data
    bar_data = df
    graph_json = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
    return graph_json


@app.route('/create_map', methods=['GET', 'POST'])
def create_map():
    global all_data
    params = params_pre_check()
    query = '''select DateOriginal, Latitude1,Longitude1,Location,NAME,COUNTRY,ISO_CC,sum(TotalVolunteers) TotalVolunteers,EventType, sum(Totalltems_EventRecord) Totalltems_EventRecord
            FROM plastic_all_data
            Where Latitude1 IS Not NULL and  Longitude1 IS Not NULL and DateOriginal IS Not NULL and Location IS Not NULL
            '''
    condition = ""
    if params["month"]:
        datelimit = params["month"].replace("'", "") + "/%/" + params["year"].replace("'", "")
        condition = condition + ' and DateOriginal like \'' + datelimit + '\''
        if params["org"]:
            condition += ' and Organization = \'' + params["org"] + "\'"
        if params["by_location"] and params["location"]:
            condition += ' and Location like \'%' + params["location"].replace("'", "") + "%\'"
    elif params["org"]:
        condition += ' and Organization = \'' + params["org"] + "\'"
        if params["by_location"] and params["location"]:
            condition += ' and  Location like \'%' + params["location"].replace("'", "") + "%\'"
    elif params["by_location"] and params["location"]:
        condition += ' and Location like \'%' + params["location"].replace("'", "") + "%\'"
    condition += ''' group by Latitude1, Longitude1,Location,NAME,COUNTRY,ISO_CC,EventType, DateOriginal
    order by sum(Totalltems_EventRecord), DateOriginal desc'''
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            all_data = pd.read_sql(query + condition, con)
        except pd.io.sql.DatabaseError:
            print(query + condition)
            print("Error")
    if len(all_data) > 5:
        all_data = all_data.dropna()
        all_data['DateOriginal'] = pd.to_datetime(all_data['DateOriginal'])
        if params["start_year"] and params["end_year"]:
            startyear = params["start_year"]
            endyear = params["end_year"]
            all_data = all_data[all_data["DateOriginal"].isin(pd.date_range('1/1/' + startyear, '30/12/' + endyear))]
    all_data['Year'] = pd.DatetimeIndex(all_data['DateOriginal']).year
    all_data.sort_values(by='Year')
    all_data['Year'] = (all_data['Year']).astype('str')
    if len(all_data) > 1 and params["by_location"]:
        lat = all_data.Latitude1[0]
        lon = all_data.Longitude1[0]
    else:
        lat = 39.1176
        lon = -123.7096
    px.set_mapbox_access_token(open(".mapbox_token").read())
    if params["mapby"]:
        fig = px.scatter_mapbox(all_data, lat="Latitude1", lon="Longitude1", hover_name="Location",
                                hover_data=["NAME", "COUNTRY", "ISO_CC", "TotalVolunteers", "EventType", "Location"],
                                color='Year', size="Totalltems_EventRecord",
                                color_discrete_sequence=px.colors.qualitative.Bold,
                                zoom=1, width=667, height=334,
                                category_orders={"Year": ["2015", "2016", "2017", "2018", "2019", "2020"]})
    else:
        fig = px.scatter_mapbox(all_data, lat="Latitude1", lon="Longitude1", hover_name="Location",
                                hover_data=["NAME", "COUNTRY", "ISO_CC", "TotalVolunteers", "EventType", "Location"],
                                color='Year',
                                color_discrete_sequence=px.colors.qualitative.Bold,
                                zoom=1, width=667, height=334,
                                category_orders={"Year": ["2015", "2016", "2017", "2018", "2019", "2020"]})
    fig.update_traces(
        hovertemplate=None
    )
    fig.update_layout(mapbox_style="mapbox://styles/falsaadeh/ckf7f7mx70d6d19qkal4k4u99",
                      mapbox=dict(
                          accesstoken=open(".mapbox_token").read(),
                          center=go.layout.mapbox.Center(
                              lat=lat,
                              lon=lon
                          ),
                          pitch=0,
                          zoom=9
                      ),
                      legend=dict(
                          traceorder='normal',
                          orientation="h",
                          yanchor="bottom",
                          y=1.02,
                          xanchor="right",
                          x=1
                      ),
                      margin={"r": 0, "t": 0, "l": 0, "b": 0},
                      )

    data = fig
    global map_data
    map_data = all_data
    graph_json = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
    return graph_json


@app.route('/near_me', methods=['GET', 'POST'])
def find_nearest_beach():
    g = geocoder.ip('me')
    g1 = g.latlng
    city = g.current_result.province
    country_code = g.current_result.country

    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            con.create_function("power", 2, lambda x, y: x ** y)
            con.create_function("sqrt", 1, lambda x: x ** (1 / 2))
            con.create_function("cos", 1, lambda x: math.cos(x))
            query = '''
                SELECT X, Y, location, Totalltems_EventRecord, DateOriginal, sqrt(
                power(69.1 * (X - ''' + str(g1[1]) + '''), 2) +
                power(69.1 * (''' + str(g1[0]) + ''' - Y) * cos(X / 57.3), 2)) as distance
                FROM plastic_all_data
                where location is not null
                ORDER BY distance ASC LIMIT 10
            '''
            nearest_locations = pd.read_sql(query, con)
            nearest_locations['Year'] = pd.DatetimeIndex(nearest_locations['DateOriginal']).year
            nearest_locations.sort_values(by='Year')
            nearest_locations['Year'] = (nearest_locations['Year']).astype('str')
            nearest_locations.dropna()
            loc = nearest_locations.iloc[0].Location
            # nearest_locations.append({'X': g1[1], 'Y': g1[0], 'Locationa': g.current_result.address}, ignore_index=True)
            px.set_mapbox_access_token(open(".mapbox_token").read())

            fig = px.scatter_mapbox(nearest_locations, lat="Y", lon="X", hover_name="Location", color='Year',
                                    color_discrete_sequence=px.colors.qualitative.Bold,
                                    zoom=10, width=667, height=334,
                                    category_orders={"Year": ["2015", "2016", "2017", "2018", "2019", "2020"]})
            fig.update_traces(
                hovertemplate=None
            )
            fig.update_layout(mapbox_style="mapbox://styles/falsaadeh/ckf7f7mx70d6d19qkal4k4u99",
                              mapbox=dict(
                                  accesstoken=open(".mapbox_token").read(),
                                  center=go.layout.mapbox.Center(
                                      lat=g1[0],
                                      lon=g1[1]
                                  ),
                                  pitch=0,
                                  zoom=10
                              ),
                              legend=dict(
                                  traceorder='normal',
                                  orientation="h",
                                  yanchor="bottom",
                                  y=1.02,
                                  xanchor="right",
                                  x=1
                              ),
                              margin={"r": 0, "t": 0, "l": 0, "b": 0},
                              )

            data = fig
            graph_json = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
            overall = {
                'graph': graph_json,
                'city': city,
                'country_code': country_code,
                'first_loc': loc,
            }
            return json.dumps(overall)
        except pd.io.sql.DatabaseError as e:
            print(e)
            return json.dumps([])


from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt


def entanglement():
    query = '''select * from entangled_animals '''
    condition = ""
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            num = pd.read_sql('''select Animal
                                      from entangled_animals
                                      where COUNTRY = 'United States' and Animal NOT LIKE '%unknown%'
                                      group by Animal
                                      ''', con)
            num["Animal"] = num["Animal"].str.lower()
            num["Animal"] = num["Animal"].str.replace('\d+', '')
            num["Animal"] = num["Animal"].str.replace('\([^)]*\)', '')
            num = num[~num['Animal'].isin(
                ["name", "unknown", "unnknown", "test", "dtype", "two", "tree", "Name", "Length", "id"])]
            text = num["Animal"]
            wordcloud = WordCloud(
                width=8000,
                height=2000,
                background_color='white',
                stopwords=STOPWORDS).generate(str(text))
            fig = plt.figure(
                figsize=(80, 30),
                facecolor='k',
                edgecolor='k')
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.tight_layout(pad=0)
            plt.savefig('new_plot.png')
            return ""
        except pd.io.sql.DatabaseError as e:
            print(query + condition)
            print(e)


@app.route('/predScatter', methods=['GET', 'POST'])
def organize_scatter():
    return create_organize_scatter()


@app.route('/predStats', methods=['GET', 'POST'])
def predictStat():
    return predictStats()


@app.route('/saveEvent', methods=['GET', 'POST'])
def saveEvent():
    conn = sqlite3.connect('ocean_plastic.db')
    event_date = request.args.get('event_date')
    event_location = request.args.get('event_location')
    event_organization = request.args.get('event_organization')
    invitation = request.args.get('invitation')
    item = [event_date, event_location, event_organization, invitation]
    c = conn.cursor()
    c.execute('insert into planned_events (event_date, event_location, organization, invitation) values (?,?,?,?)',
              item)
    conn.commit()
    index = pd.read_sql('select *  from planned_events', conn)
    print(index)
    return "sucess"


@app.route('/getData', methods=['GET', 'POST'])
def getData():
    data_type = request.args.get('data_type')
    data_type = str(data_type.replace("'", ""))
    if data_type == 'map':
        csv = map_data.to_csv()
        buf_str = io.StringIO(csv)
        # Create a bytes buffer from the string buffer
        buf_byt = io.BytesIO(buf_str.read().encode("utf-8"))
        # Return the CSV data as an attachment
        return send_file(buf_byt,
                         mimetype="text/csv",
                         as_attachment=True,
                         attachment_filename="mapData.csv")
    elif data_type == 'scatter':
        csv = scatter_data.to_csv()
        buf_str = io.StringIO(csv)
        # Create a bytes buffer from the string buffer
        buf_byt = io.BytesIO(buf_str.read().encode("utf-8"))
        # Return the CSV data as an attachment
        return send_file(buf_byt,
                         mimetype="text/csv",
                         as_attachment=True,
                         attachment_filename="scatterData.csv")
    elif data_type == 'bar':
        csv = bar_data.to_csv()
        buf_str = io.StringIO(csv)
        # Create a bytes buffer from the string buffer
        buf_byt = io.BytesIO(buf_str.read().encode("utf-8"))
        # Return the CSV data as an attachment
        return send_file(buf_byt,
                         mimetype="text/csv",
                         as_attachment=True,
                         attachment_filename="barData.csv")
    else:
        return orgGetData(data_type)


if __name__ == '__main__':
    global g_bar
    g_bar = create_bar_plot()
    global g_scatter
    g_scatter = create_scatter_plot()
    global g_mapp
    g_mapp = create_map()
    global g_stats
    g_stats = eval(get_stats())
    global g_years
    g_years = get_years()
    global g_locations
    g_locations = get_locations()
    global g_title
    g_title = title_formatting()
    global g_top_organization
    g_top_organization = get_top_organization()
    global g_organizations
    g_organizations = get_organizations()
    global org_stats
    org_stats = eval(predictStats())
    global org_mapp
    org_mapp = create_organize_map()
    global org_scatter
    org_scatter = create_organize_scatter()
    global org_years
    org_years = get_years()
    global org_locations
    org_locations = get_locations()
    global org_title
    org_title = title_formatting()
    global org_top_organization
    org_top_organization = get_top_organization()
    global org_organizations
    org_organizations = get_organizations()

    app.run(host=hostname)
