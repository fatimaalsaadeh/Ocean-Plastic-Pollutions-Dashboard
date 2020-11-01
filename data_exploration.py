import pandas as pd
import plotly
import plotly.express as px
import sqlite3
import re
from django.contrib.admin.utils import flatten
import seaborn
import seaborn as sn
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import geocoder as geocoder
import numpy as np
from matplotlib.dates import DateFormatter
from pandas.plotting import scatter_matrix
from scipy.stats import norm
import matplotlib.pyplot as plt
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

def num_events_per_country():
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            num = pd.read_sql('''select CONTINENT, DateOriginal as Year , count(CONTINENT) NumEvents
                                      from plastic_all_data
                                      where CONTINENT is not null
                                      group by CONTINENT, DateOriginal''', con)
            num['Year'] = pd.to_datetime(num['Year'])
            num = num.pivot(index='Year', columns='CONTINENT', values='NumEvents')
            print(num)
            fig = px.line(num, x="Year", y="NumEvents", color="CONTINENT",
                          line_group="CONTINENT", hover_name="CONTINENT")

            fig.show()
        except pd.io.sql.DatabaseError:
            print("error")
def num_events_country():
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            num = pd.read_sql('''select Name , count(COUNTRY) NumEvents
                                      from plastic_all_data
                                      where Name is not null and COUNTRY = 'United States'
                                      group by Name''', con)
            avg = num["NumEvents"].mean()
            print(avg)
            print(len(num))
            avg_df = num[num['NumEvents'] > avg]
            avg_df.sort_values(by=['NumEvents'], inplace=True)
            print(avg_df)
            fig = px.pie(avg_df, values='NumEvents', names='NAME',color_discrete_sequence=px.colors.qualitative.Set1, width=1000)


            fig.show()
        except pd.io.sql.DatabaseError as e:
            print(e)
def box_plot_num_volunteers():
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            num = pd.read_sql('''     select  DateOriginal, Totalltems_EventRecord
                                      from plastic_all_data
                                      where Name =\'Florida\' and DateOriginal like '%2019%'
                                      ''', con)
            fig = px.box(num, y="Totalltems_EventRecord", width=550)
            fig.show()
        except pd.io.sql.DatabaseError as e:
            print(e)


def top_ten_plastic():
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
            Where [Name] LIKE \'Florida\' GROUP by [Name]""", con)
            print(name_top_10)
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
            fig = px.pie(df, values='Percentage', names='Category',color_discrete_sequence=px.colors.qualitative.Set1, width=1000)
            fig.show()
        except pd.io.sql.DatabaseError as e:
            print(e)

def correlation_find():
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            num = pd.read_sql('''     select TotalVolunteers volunteers, TotalClassifiedItems_EC2020 Classified, Totalltems_EventRecord collected, TotalLength_m AreaCovered_sqm
                                      from plastic_all_data
                                      where Country = "United States" and Name is not Null
                                      ''', con)
            scatter_matrix(num)
            plt.show()
        except pd.io.sql.DatabaseError as e:
            print(e)

def create_scatter_plot():
    width = 372
    height = 334
    query = 'SELECT Country, DateOriginal as EventDate FROM plastic_all_data '
    condition = ' and DateOriginal IS Not null'
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            plastic_all_data = pd.read_sql(query + 'Where Country like \'%United States%\'' + condition, con)
            print(plastic_all_data)
            plastic_all_data['EventDate'] = pd.to_datetime(plastic_all_data['EventDate'])
            plastic_all_data = plastic_all_data[plastic_all_data["EventDate"].isin(pd.date_range('2018-06-01','2018-12-30'))]
            plastic_all_data = plastic_all_data.groupby(plastic_all_data.EventDate)['COUNTRY'].count()
            plastic_all_data = pd.DataFrame({'EventDate': plastic_all_data.index, 'numEvents':plastic_all_data.values})
            plastic_all_data = plastic_all_data.drop(plastic_all_data[plastic_all_data.numEvents == 3408].index)
            print(plastic_all_data)
            #plastic_all_data = plastic_all_data[plastic_all_data["TotalItemsRecorded"] > plastic_all_data["TotalItemsRecorded"].mean()]
            # Fit a normal distribution to the data:
            seaborn.distplot(plastic_all_data['numEvents'])
            mu, std = norm.fit(plastic_all_data['numEvents'])
            print(mu)
            print(std)
            #
            # # Plot the histogram.
            # plt.hist(plastic_all_data, bins=25, density=True, alpha=0.6, color='g')
            #
            # # Plot the PDF.
            # xmin, xmax = plt.xlim()
            # x = np.linspace(xmin, xmax, 100)
            # p = norm.pdf(x, mu, std)
            # plt.plot(x, p, 'k', linewidth=2)
            # title = "Fit results: mu = %.2f,  std = %.2f" % (mu, std)
            # plt.title(title)

            plt.show()







            # fig = px.bar(plastic_all_data, y="numEvents", x="EventDate", text="numEvents",
            #             color="numEvents",
            #              color_discrete_sequence=px.colors.qualitative.Antique)
            # fig.show()
        except pd.io.sql.DatabaseError as e:
            print(e)

def all_daa_map():
    px.set_mapbox_access_token(open(".mapbox_token").read())
    fig = px.scatter_mapbox(all_data, lat="Latitude1", lon="Longitude1", hover_name="Location",
                            hover_data=["NAME", "COUNTRY", "ISO_CC", "TotalVolunteers", "EventType", "Location"],
                            color_discrete_sequence=["#9AD1FF"],
                            zoom=1)
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
    fig.show()
def test ():
    query = 'SELECT DateOriginal, Totalltems_EventRecord as Total_Items_Recorded FROM plastic_all_data '
    condition = ' and DateOriginal IS Not null'
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            plastic_all_data = pd.read_sql(query + 'Where Country like \'%United States%\' or Country like \'%Canada%\'' + condition, con)
            plastic_all_data['DateOriginal'] = pd.to_datetime(plastic_all_data['DateOriginal'])
            plastic_all_data.groupby(plastic_all_data['DateOriginal'].dt.date)
            plastic_all_data = plastic_all_data.set_index('DateOriginal')
            plastic_all_data = plastic_all_data.resample('MS').mean()
            plastic_all_data.dropna()
            labels = []
            s = plastic_all_data.index[0].strftime('%y')
            for l in plastic_all_data.index:
                labels.append(l.strftime('%y-%m'))
            print(labels)
            # ax=plastic_all_data.plot( figsize=(18, 6))
            # ax.set_xticklabels(labels)
            # plt.show()
            # fig = px.line(plastic_all_data, x=plastic_all_data.index, y=plastic_all_data['Total_Items_Recorded'])
            # fig.update_layout(
            #     xaxis = dict(
            #         tickmode = 'array',
            #         tickvals = labels,
            #         ticktext = labels
            #     )
            # )
            trace = plotly.graph_objs.Scatter(
                x=plastic_all_data.index,
                y=plastic_all_data['Total_Items_Recorded'],
                mode='lines+markers'
            )
            fig = go.Figure(
                data=trace
            )
            fig.show()
        except pd.io.sql.DatabaseError as e:
            print(e)
def test2 ():
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
    print(all_data)

    px.set_mapbox_access_token(open(".mapbox_token").read())
    df = px.data.carshare()
    fig = px.scatter_mapbox(all_data, lat="Latitude1", lon="Longitude1", size="Totalltems_EventRecord", color="month-year", size_max=15, zoom=10)
    fig.show()
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
def test3():
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
            num = num[~num['Animal'].isin(["name" , "unknown","unnknown", "test", "dtype", "two", "tree", "Name" , "Length", "id"])]
            text = num["Animal"]
            wordcloud = WordCloud(
                width = 8000,
                height = 2000,
                background_color = 'white',
                stopwords = STOPWORDS).generate(str(text))
            fig = plt.figure(
                figsize = (80, 30))
            plt.imshow(wordcloud, interpolation = 'bilinear')
            plt.axis('off')
            plt.tight_layout(pad=0)
            plt.savefig('new_plot.png')
        except pd.io.sql.DatabaseError as e:
            print(query + condition)
            print(e)

test2()