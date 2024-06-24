# These functions outline different reactor deployment algorithms, and metrics for analyzing the final product.

import pandas as pd
import numpy as np
import math  # for rounding ceiling and floor
from datetime import datetime  # for random seed generation


# # # # # # # # # # # # Analysis Functions # # # # # # # # # # # #
# analyze how well each method did with the amount and percent of over/
# under-prediction.

def simple_diff(df, base, proj):
    """
    Calculate the difference between the projected and base capacities.

    Parameters
    ----------
    df: pd.DataFrame
        The output pandas DataFrame from the deployment functions.
    base: str
        The name of the base capacity column in the DataFrame.
    proj: str
        The name of the projected capacity column in the DataFrame.
    """
    return df[proj] - df[base]



def calc_percentage(df, base):
    """
    Calculate the percentage difference between proj and base.

    Parameters
    ----------
    df: pd.DataFrame
        The output pandas DataFrame from the deployment functions.
    base: str
        The name of the base capacity column in the DataFrame.
    """
    return (df['difference'] / df[base]) * 100



def analyze_algorithm(df, base, proj, ar_dict):
    """
    This function takes in a DataFrame output of the deployment functions
    above, and returns a series of metrics so you can compare different
    deployments.

    Parameters
    ----------
    df: pd.DataFrame
        The output pandas DataFrame from the deployment functions.
    base: str
        The name of the base capacity column in the DataFrame.
    proj: str
        The name of the projected capacity column in the DataFrame.
    ar_dict: dictionary
        A dictionary of reactors with information of the form:
        {reactor: [Power (MWe), capacity_factor (%), lifetime (yr),
        [distribution]]}.

    Returns
    -------
    above_count: int
        The number of times the deployed capacity exceeds the desired capacity.
    below_count: int
        The number of times the deployed capacity is below the desired capacity.
    equal_count: int
        The number of times the deployed capacity equals the desired capacity.
    above_percentage: float
        The percent of times the deployed capacity exceeds the desired capacity.
    below_percentage: float
        The percent of times the deployed capacity is below the desired
        capacity.
    total_above: int
        The excess of deployed capacity.
    total_below: int
        The dearth of deployed capacity.
    percent_provided: dict
        The percent of the deployed capacity that comes from each reactor.
    """

    df['difference'] = df.apply(simple_diff, base=base, proj=proj, axis=1)
    df['percentage'] = df.apply(calc_percentage, base=base, axis=1)

    above_count = (df['difference'] > 0).sum()
    below_count = (df['difference'] < 0).sum()
    equal_count = (df['difference'] == 0).sum()

    above_percentage = (above_count / len(df)) * 100
    below_percentage = (below_count / len(df)) * 100

    total_above = df['difference'][df['difference'] > 0].sum()
    total_below = df['difference'][df['difference'] < 0].sum()

    # Now we will calculate the percent of the total capacity coming from each
    # reactor.
    percent_provided = {}

    total_cap_sum = df['total_cap'].sum()
    for reactor in ar_dict.keys():
        total_reactor_cap = df[f'{reactor}_cap'].sum()
        percent_reactor_cap = (1 - (total_cap_sum - total_reactor_cap)/total_cap_sum) * 100
        percent_provided[reactor] = percent_reactor_cap

    results = {
        'above_count': above_count,
        'below_count': below_count,
        'equal_count': equal_count,
        'above_percentage': above_percentage,
        'below_percentage': below_percentage,
        'total_above': total_above,
        'total_below': total_below,
        'percent_provided': percent_provided
    }

    return results
