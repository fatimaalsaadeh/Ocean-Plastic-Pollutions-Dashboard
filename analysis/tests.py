import pandas as pd
import sqlite3
import matplotlib.pyplot as plt

from scipy.stats import norm
from scipy.stats import t

old = pd.read_csv('../data/cleanups.csv')[['Year', 'TotalVolunteers', 'COUNTRY']]
new = pd.read_csv('../data/new-cleanups.csv')
new = pd.DataFrame({'Year': pd.to_datetime(new['Cleanup Date']).dt.year, 'COUNTRY': new['Country'], 'TotalVolunteers': new['People']})
cleanups = pd.concat([new, old]).reset_index().drop(columns=['index'])
cleanups = cleanups.rename(columns={'COUNTRY': 'Country', 'TotalVolunteers': 'Volunteers'})

def statistical_difference_in_number_of_volunteers(country_1: str, year_1: int, country_2: str, year_2: int, alpha: float = 0.05) -> (bool, int):
    '''
    Answers the question: is there a statistically-significant difference between the number of volunteers per event in countries 1 and 2 in years 1 and 2?
    Note that we compare the number of volunteers per event in (country 1, year 1) and (country 2, year 2).
    We can set a threshold using alpha.
    
    This runs a Z-test if each of the two samples has at least 30 events and a t-test if one has fewer than 30.
    If one of the the samples has 0 events, then it returns (False, float('nan')).
    
    It returns (boolean which is True if the difference is statistically significant, probability given from the test).
    '''
    sample_1 = cleanups[(cleanups['Country'] == country_1) & (cleanups['Year'] == year_1)]
    sample_2 = cleanups[(cleanups['Country'] == country_2) & (cleanups['Year'] == year_2)]
    
    X_1 = sample_1['Volunteers'].mean()
    X_2 = sample_2['Volunteers'].mean()
    
    S_1 = sample_1['Volunteers'].std()
    S_2 = sample_2['Volunteers'].std()
    
    N_1 = sample_1['Volunteers'].count()
    N_2 = sample_2['Volunteers'].count()
    
    if N_1 == 0 or N_2 == 0:
        return False, float('nan')
    
    if N_1 >= 30 and N_2 >= 30:
        Z = abs(X_1 - X_2) / (S_1 ** 2 / N_1 + S_2 ** 2 / N_2) ** 0.5
        p = norm.cdf(Z)
    else:
        S = ((N_1 - 1) * S_1 ** 2 + (N_2 - 1) * S_2 ** 2) / (N_1 + N_2 - 2)
        t_value = (X_1 - X_2) / (S ** 2 * (1 / N_1 + 1 / N_2)) ** 0.5
        df = N_1 + N_2 - 2
        p = t.cdf(t_value, df)
    
    return p > 1 - alpha, p