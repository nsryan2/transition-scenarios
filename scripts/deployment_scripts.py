# These functions outline different reactor deployment algorithms, and metrics for analyzing the final product.

import pandas as pd
import numpy as np
import math  # for rounding ceiling and floor
from datetime import datetime  # for random seed generation




# # # # # # # # # # # # Constituent Functions # # # # # # # # # # #

def direct_decom(df, ar_dict):
    """
    This function assumes that every time a reactor model is decommissioned it
    is replaced by a new version of itself.

    Parameters
    ----------
    df: pandas dataframe
        The dataframe of capacity information
    ar_dict: dictionary
        A dictionary of reactors with information of the form:
        {reactor: [Power (MWe), capacity_factor (%), lifetime (yr)]}
    """

    # now we are going to note when reactors are decommissioned
    for reactor in ar_dict.keys():
        # create a decommissioning column
        df[f'{reactor}Decom'] = 0
        for year in range(len(df['Year'])):
            decom_year = year + ar_dict[reactor][2]
            if decom_year >= len(df['Year']):
                pass
            else:
                # tracks the number of decommissioned reactors
                df.loc[decom_year, f'{reactor}Decom'] += df.loc[year, f'num_{reactor}']

                # construct new reactors to replace the decommissioned ones
                df.loc[decom_year, f'num_{reactor}'] += df.loc[year, f'num_{reactor}']

    return df


def num_react_to_cap(df, ar_dict):
    """
    This function takes in a dataframe and the dictionary of reactors,
    and converts the number of reactors columns to a capacity from each reactor
    and a total capacity column.

    Parameters
    ----------
    df: pandas dataframe
        The dataframe of capacity information
    ar_dict: dictionary
        A dictionary of reactors with information of the form:
        {reactor: [Power (MWe), capacity_factor (%), lifetime (yr)]}
    """

    if 'total_cap' not in df:
        df[f'total_cap'] = 0
    else:
        pass

    for reactor in ar_dict.keys():
        df[f'{reactor}_cap'] = df[f'num_{reactor}'] * ar_dict[f'{reactor}'][0]
        df['total_cap'] += df[f'{reactor}_cap']

    return df


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
