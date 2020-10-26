"""
Predict the number of cleanups using an ARIMA model
"""

import itertools
import matplotlib.pyplot as plt
import pandas as pd
import sqlite3
import statsmodels.api as sm
import warnings

from pylab import rcParams
from sys import argv, stderr

warnings.filterwarnings("ignore")
plt.style.use('fivethirtyeight')

try:
    cleanups_datafile = argv[1]
except IndexError:
    cleanups_datafile = 'data/cleanups.csv'

with sqlite3.connect('ocean_plastic.db') as con:
    try:
        all_data = pd.read_sql('select * from plastic_all_data', con)
        top_10 = pd.read_sql('select * from plastic_top_10', con)
    except pd.io.sql.DatabaseError:
        all_data = pd.read_csv(cleanups_datafile)
        all_data.to_sql('plastic_all_data', con)
        print('Added', len(all_data), 'rows to all_data table', file=stderr)
        top_10 = pd.read_csv("https://opendata.arcgis.com/datasets/7afcc89e5a0f4c339ddf7b4bf6fabe3d_0.csv")
        top_10.to_sql('plastic_top_10', con)
        print('Added', len(top_10), 'rows to plastic_top_10 table', file=stderr)


def dataPreProcessing():
    global all_data
    # convert the DateOriginal to datetime
    all_data['DateOriginal'] = pd.to_datetime(all_data['DateOriginal'])
    # print date time range we have: 2015-01-01 00:00:00 2020-09-29 00:00:00
    dropThis = pd.date_range('2020-01-01', '2020-09-29')

    all_data = all_data[~all_data['DateOriginal'].isin(dropThis)]

    print(all_data['DateOriginal'].min(), all_data['DateOriginal'].max(), file=stderr)
    # sort the data by date
    all_data = all_data.sort_values('DateOriginal')
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
    num_events_per_date_df.plot(figsize=(18, 6))
    plt.show()

    # we are using here time series decomposition as an additive model in order to be able to visualize data
    # decomposed into three components seasonal, trend, and resid(noise) attributes
    # additive model is = trend + seasonal+ noise
    # the figure shows upward trend of our data through the years, seasonal trend
    # in the middle of the year and noise  around the beginning and end of the year
    # sm.tsa.seasonal_decompose is Seasonal decomposition using moving averages.
    # Time series decomposition using moving averages is a fast
    # way to view seasonal and overall trends in time series data.
    rcParams['figure.figsize'] = 18, 6
    decomposition = sm.tsa.seasonal_decompose(num_events_per_date_df, freq=30, model='additive')
    fig = decomposition.plot()
    plt.show()

    # return our dataframe to pass it to the model
    return num_events_per_date_df


# ARIMA: Autoregressive Integrated Moving Average.
# regression analysis that finds the strength of one dependent variable relative to other changing variables.
# the model goal is to predict future number of events that will occur
# by finding the differences between the values in the time series instead of through the actual valuse

def validating_model():
    return


def arima_model_forcasting(events_per_date_df):
    perc = int(len(events_per_date_df) * .6)
    # 2015-01-01 - 2015-01-01
    data_train = events_per_date_df[:perc]
    print(data_train, file=stderr)
    perc2 = int(len(events_per_date_df) * .2)
    # 2018-06-01 - 2020-09-01
    data_validate = events_per_date_df[perc:]
    print(data_validate, file=stderr)
    perc3 = int(len(events_per_date_df) * .2)
    # 2015-01-01 - 2018-06-01
    data_test = events_per_date_df[perc:]
    print(data_test, file=stderr)

    # p: is the number of lag observation in the model "lag order"
    # d: the number of tomes that the raw observations are differences "degree of differencing:
    # q: the size of the moving average window: "the order of moving avergae"
    p = d = q = range(0, 2)
    # generate all the combination of p,d,q
    pdq = list(itertools.product(p, d, q))

    # generate all the combinations of the triplets
    seasonal_pdq = [(x[0], x[1], x[2], 12) for x in list(itertools.product(p, d, q))]
    print(seasonal_pdq, file=stderr)

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
    arima_model = sm.tsa.statespace.SARIMAX(events_per_date_df,
                                            order=(1, 1, 1),
                                            seasonal_order=(1, 1, 1, 12),
                                            enforce_stationarity=False,
                                            enforce_invertibility=False)
    # from the resulted summary after fitting our model we chose the table of coefficients
    # The resulted p>|Z| are all lower than 0.05 so we consider all features
    results = arima_model.fit()
    print(results.summary().tables[1])
    results.plot_diagnostics(figsize=(16, 8))
    plt.show()

    pred = results.get_prediction(start='2018-06-01', dynamic=False)
    pred_ci = pred.conf_int()
    ax = events_per_date_df['2015':].plot(label='observed')
    pred.predicted_mean.plot(ax=ax, label='One-step ahead Forecast', alpha=.7, figsize=(14, 7))
    ax.fill_between(pred_ci.index,
                    pred_ci.iloc[:, 0],
                    pred_ci.iloc[:, 1], color='k', alpha=.2)
    ax.set_xlabel('Date')
    ax.set_ylabel('Number of events')
    plt.legend()
    plt.show()

    y_forecasted = pred.predicted_mean
    y_truth = events_per_date_df['2018-06-01':]
    mse = ((y_forecasted.values - y_truth['numEvents'].values) ** 2).mean()
    print('The Mean Squared Error of our forecasts is {}'.format(round(mse, 2)))
    pred_uc = results.get_forecast(steps=100)
    pred_ci = pred_uc.conf_int()
    ax = events_per_date_df.plot(label='observed', figsize=(14, 7))
    pred_uc.predicted_mean.plot(ax=ax, label='Forecast')
    ax.fill_between(pred_ci.index,
                    pred_ci.iloc[:, 0],
                    pred_ci.iloc[:, 1], color='k', alpha=.25)
    ax.set_xlabel('Date')
    ax.set_ylabel('Events')
    plt.legend()
    plt.show()


events_per_date_df = dataPreProcessing()
arima_model_forcasting(events_per_date_df)
