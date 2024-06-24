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


# # # # # # # # # # # # Deployment Functions # # # # # # # # # # #
# 1. Greedy Algorithm: deploy the largest reactor first at each time step, fill in the remaining capacity with the next smallest, and so on.
# 2. Pre-determined distributions: one or more reactors have a preset distribution, and a smaller capacity model fills in the gaps.
# 3. Deployment Cap: there is a single-number capacity for one or more of the reactor models.
# 4. Random Deployment: uses a date and hour as seed to randomly sample the reactors list.
# 5. Initially Random, Greedy: randomly deploys reactors until a reactor bigger than the remaining capacity is proposed for each year, then fills remaining capacity with a greedy algorithm.

def greedy_deployment(df, base_col, ar_dict):
    """
    In this greedy deployment, we will deploy the largest capacity reactor first until another deployment will exceed the desired capacity then the next largest capacity reactor is deployed and so on.

    Parameters
    ----------
    df: pandas dataframe
        The dataframe of capacity information
    base_col: str
        The string name corresponding to the column of capacity that the algorithm is deploying reactors to meet
    ar_dict: dictionary
        A dictionary of reactors with information of the form:
        {reactor: [Power (MWe), capacity_factor (%), lifetime (yr)]}
    """

    for reactor in ar_dict.keys():
        if f'num_{reactor}' not in df:
            df[f'num_{reactor}'] = 0
        else:
            pass

    for year in range(len(df[base_col])):
        remaining_cap = df[base_col][year].copy()
        for reactor in ar_dict.keys():
            if ar_dict[reactor][0] > df[base_col][year]:
                reactor_div = 0
            else:
                # find out how many of this reactor to deploy
                reactor_div = math.floor(remaining_cap / ar_dict[reactor][0])
                # remaining capacity to meet
                remaining_cap = df[base_col][year] - reactor_div * ar_dict[reactor][0]
            df.loc[year, f'num_{reactor}'] += reactor_div

    # account for decommissioning with a direct replacement
    df = direct_decom(df, ar_dict)

    df  = num_react_to_cap(df, ar_dict)

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
