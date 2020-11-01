import sqlite3
import warnings
import itertools
import matplotlib.pyplot as plt
import plotly
warnings.filterwarnings("ignore")
plt.style.use('fivethirtyeight')
import pandas as pd
import statsmodels.api as sm
from pylab import rcParams
import numpy as np
with sqlite3.connect('ocean_plastic.db') as con:
    try:
        #all_data = pd.read_sql('select * from plastic_all_data', con)
        all_data = pd.read_sql('select * from plastic_all_data where Name=\'California\'', con)
        print(all_data)
        #all_data = pd.read_sql('select * from plastic_all_data where name = \'California\'', con)
        #top_10 = pd.read_sql('select * from plastic_top_10', con)
    except pd.io.sql.DatabaseError:
        all_data = pd.read_csv("all-cleanups.csv")
        all_data.to_sql('plastic_all_data', con)
        print('Added', len(all_data), 'rows to all_data table')
        top_10 = pd.read_csv("https://opendata.arcgis.com/datasets/7afcc89e5a0f4c339ddf7b4bf6fabe3d_0.csv")
        top_10.to_sql('plastic_top_10', con)
        print('Added', len(top_10), 'rows to plastic_top_10 table')
def dataPreProcessing(all_data):
    # convert the DateOriginal to datetime
    all_data['DateOriginal'] = pd.to_datetime(all_data['DateOriginal'])
    # print date time range we have: 2015-01-01 00:00:00 2020-09-29 00:00:00
    #dropThis = pd.date_range('2020-01-01', '2020-09-29')

    #all_data = all_data[~all_data['DateOriginal'].isin(dropThis)]

    #print(all_data['DateOriginal'].min(), all_data['DateOriginal'].max())
    # sort the data by date
    all_data.sort_values('DateOriginal')
    print(all_data)

    # generate number of events per date column
    num_events_per_date = all_data.groupby(all_data['DateOriginal'])['DateOriginal'].count()
    # convert the result to dateframe of EventDate, and NumEvents columns
    num_events_per_date_df = pd.DataFrame(
        {'EventDate': num_events_per_date.index, 'numEvents': num_events_per_date.values})
    # indexing the dataframe with respect to the time series "EventDate" column
    num_events_per_date_df = num_events_per_date_df.set_index('EventDate')
    # reprocess the data by using the average daily events value per month, and then use
    # the start of each month as the timestamp.
    num_events_per_date_df = num_events_per_date_df.resample('MS').mean()
    # plot the average number of events with respect to the event date
    # from the plot we can find a pattern at the middle of each year the number of events peek,
    # and that's reasonable as at this time of the year its summer, more people plan beach events
    num_events_per_date_df.dropna()

    num_events_per_date_df['numEvents_diff'] = num_events_per_date_df['numEvents'] - num_events_per_date_df['numEvents'].shift(1)
    num_events_per_date_df['numEvents_diff'] = num_events_per_date_df['numEvents_diff'].dropna()

    num_events_per_date_df = num_events_per_date_df.dropna()
    X = num_events_per_date_df['numEvents_diff'].values


    # we are using here time series decomposition as an additive model in order to be able to visualize data
    # decomposed into three components seasonal, trend, and resid(noise) attributes
    # additive model is = trend + seasonal+ noise
    # the figure shows upward trend of our data through the years, seasonal trend
    # in the middle of the year and noise  around the beginning and end of the year
    # sm.tsa.seasonal_decompose is Seasonal decomposition using moving averages.
    # Time series decomposition using moving averages is a fast
    # way to view seasonal and overall trends in time series data.
    #     rcParams['figure.figsize'] = 18, 6
    #     decomposition = sm.tsa.seasonal_decompose(num_events_per_date_df, freq=12, model='additive')
    #     fig = decomposition.plot()
    #     plt.savefig('decompose.png', transparent=True)
    #     plt.show()

    del num_events_per_date_df['numEvents_diff']
    #num_events_per_date_df.rename(columns={'EventDate': 'EventDate', 'numEvents_diff': 'numEvents'}, inplace=True)
    # return our dataframe to pass it to the model
    return num_events_per_date_df
# ARIMA: Autoregressive Integrated Moving Average.
# regression analysis that finds the strength of one dependent variable relative to other changing variables.
# the model goal is to predict future number of events that will occur
# by finding the differences between the values in the time series instead of through the actual valuse
global a
import plotly.express as px
def arima_model_forcasting(events_per_date_df):
    # p: is the number of lag observation in the model "lag order"
    # d: the number of tomes that the raw observations are differences "degree of differencing:
    # q: the size of the moving average window: "the order of moving avergae"
    data_train = events_per_date_df[:'2019']
    data_test = events_per_date_df['2020':]
    print(data_test)
    p = d = q = range(0, 2)
    # generate all the combination of p,d,q
    pdq = list(itertools.product(p, d, q))
    # generate all the combinations of the triplets
    seasonal_pdq = [(x[0], x[1], x[2], 12) for x in list(itertools.product(p, d, q))]
    print(seasonal_pdq)

    # iterate over all the combinations using SARIMAX function to fit the arima model
    # after fitting the model on each combination the AIC will be calculated "Akaike information Criterion"
    # which calculates how will the model fits the data and we pick the AIC with lowest AIC value
    warnings.filterwarnings("ignore")  # specify to ignore warning messages
    parameters = []
    for param in pdq:
        for param_seasonal in seasonal_pdq:
            try:
                arima_model = sm.tsa.statespace.SARIMAX(events_per_date_df,
                                                        order=param,
                                                        seasonal_order=param_seasonal,
                                                        enforce_stationarity=False,
                                                        enforce_invertibility=False)
                results = arima_model.fit()
            except:
                continue
            aic = results.aic
            parameters.append([param, param_seasonal, aic])
    result_table = pd.DataFrame(parameters)
    result_table.columns = ['parameters', 'parameters_seasonal', 'aic']
    # sorting in ascending order, the lower AIC is - the better
    result_table = result_table.sort_values(by='aic', ascending=True).reset_index(drop=True)
    print(result_table)

    # after running the above we found the lowest AIC ARIMA(0, 1, 1)x(1, 1, 1, 12)21 - AIC:404.319224
    # we use this combination to fir our variables
    #1, 1, 1)       (1, 1, 0, 12
    arima_model = sm.tsa.statespace.SARIMAX(events_per_date_df,
                                            order=result_table.iloc[0].parameters,
                                            seasonal_order=result_table.iloc[0].parameters_seasonal,
                                            enforce_stationarity=False,
                                            enforce_invertibility=False)
    # from the resulted summary after fitting our model we chose the table of coefficients
    # The resulted p>|Z| are all lower than 0.05 so we consider all features
    results = arima_model.fit()
    print(results.summary().tables[1])
    results.plot_diagnostics(figsize=(16, 8))
    plt.savefig('diag.png', transparent=True)

    plt.show()

    pred = results.get_prediction(start='2020-01-01', dynamic=False)
    pred_ci = pred.conf_int()
    ax = events_per_date_df['2015':].plot(label='observed')
    plota = pred.predicted_mean.plot(ax=ax, label='One-step ahead Forecast', alpha=.7, figsize=(14, 7))
    ax.fill_between(pred_ci.index,
                    pred_ci.iloc[:, 0],
                    pred_ci.iloc[:, 1], color='k', alpha=.2)
    print("Fat Here")
    print(pred_ci.index)
    print(pred_ci.iloc[:, 0])
    print(pred_ci.iloc[:, 1])
    ax.set_xlabel('Date')
    ax.set_ylabel('Number of events')
    ax.set_title("ARIMA prediction: United States")
    plt.legend()
    plt.savefig('test.png', transparent=True)
    plt.show()

    y_forecasted = pred.predicted_mean
    y_truth = events_per_date_df['2020-01-01':]
    mse = ((y_forecasted.values - y_truth['numEvents'].values) ** 2).mean()
    print('The Mean Squared Error of our forecasts is {}'.format(round(mse, 2)))
    mase = ((y_forecasted.values - y_truth['numEvents'].values) / y_truth['numEvents']).abs().mean()
    print('The accuracy of our forecasts (using the 1-MASE metric) is {}%'.format(int(100*(1-mase))))
    pred_uc = results.get_forecast(steps=30)
    pred_ci = pred_uc.conf_int()
    ax = events_per_date_df.plot(label='observed', figsize=(14, 7))
    pred_uc.predicted_mean.plot(ax=ax, label='Forecast')
    print(pred_uc.predicted_mean)
    ax.fill_between(pred_ci.index,
                    pred_ci.iloc[:, 0],
                    pred_ci.iloc[:, 1], color='k', alpha=.25)
    print("Fat Here2")

    observ = pd.DataFrame(
        {'type':'observed','EventDate': events_per_date_df.index, 'numEvents': np.array(events_per_date_df.values).flatten()})

    mean_fore = pd.DataFrame(
        {'type':'Forecast','EventDate': pred_uc.predicted_mean.index, 'numEvents': pred_uc.predicted_mean.values})
    test3 = pd.concat([observ,mean_fore])
    lower = pd.DataFrame(
        {'type':'Forecast','EventDate': pred_ci.index, 'numEvents': pred_ci.iloc[:, 0]})
    upper = pd.DataFrame(
        {'type':'Forecast','EventDate': pred_ci.index, 'numEvents': pred_ci.iloc[:, 1]})
    print(pred_ci.iloc[:, 0])
    print(pred_ci.iloc[:, 1])
    fig = px.line(test3, x="EventDate", y="numEvents", color="type",
                  line_group="type", hover_name="numEvents")
    fig.show()
    import plotly.graph_objects as go
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=observ.EventDate, y=observ.numEvents,
        fill=None,
        line_color='blue',
        hoverinfo='x+y',
        mode='lines'
    ))
    fig.add_trace(go.Scatter(
        x=upper.EventDate, y=upper.numEvents,
        hoverinfo='x+y',
        mode='lines',
        line=dict(width=0.5, color='rgb(220, 220, 220)'),
    ))
    fig.add_trace(go.Scatter(
        x=mean_fore.EventDate, y=mean_fore.numEvents,
        hoverinfo='x+y',
        mode='lines',
        line_color = 'red',
        line=dict(width=0.5, color='rgb(220, 220, 220)'),
        fill = 'tonexty'

    ))
    fig.add_trace(go.Scatter(
        x=lower.EventDate, y=lower.numEvents,
        hoverinfo='x+y',
        mode='lines',
        line=dict(width=0.5, color='rgb(220, 220, 220)'),
        fill='tonexty'

    ))


    fig.update_layout(yaxis_range=(0, 100))
    fig.show()
    ax.set_xlabel('Date')
    ax.set_ylabel('Events')
    ax.set_title("ARIMA Forecast: United States")
    plt.legend()
    plt.savefig('predict.png', transparent=True)
    plt.show()
def test():
    with sqlite3.connect('ocean_plastic.db') as con:
        try:
            #all_data = pd.read_sql('select * from plastic_all_data', con)
            t = pd.read_sql('select DISTINCT Name from plastic_all_data where country=\'United States\'', con)
            print(t)
            df = pd.DataFrame(columns=['name', 'parameters', 'parameters_seasonal'])
            for index, row in t.iterrows():
                if row['NAME'] is not None:
                    try:
                        all_data = pd.read_sql('select * from plastic_all_data where Name=\''+row['NAME']+'\'', con)
                        events_per_date_df = dataPreProcessing(all_data)
                        t1,t2 = arima_model_forcasting(events_per_date_df)
                        df = df.append(pd.DataFrame([[row['NAME'], t1, t2]], columns=df.columns))
                    except pd.io.sql.DatabaseError as e:
                        print(e)
            df.to_csv("test.csv", index=False)
            #all_data = pd.read_sql('select * from plastic_all_data where name = \'California\'', con)
            #top_10 = pd.read_sql('select * from plastic_top_10', con)
        except pd.io.sql.DatabaseError as e:
            print(e)
#est()
events_per_date_df = dataPreProcessing(all_data)
arima_model_forcasting(events_per_date_df)