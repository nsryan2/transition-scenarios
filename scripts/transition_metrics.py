import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import math

import cymetric as cym
from cymetric import tools
from cymetric import timeseries
from cymetric import filters


def get_metrics(db_file):
    '''
    Opens database using cymetric and evaluates metrics

    Parameters:
    -----------
    db_file: str
        SQLite database from Cyclus

    Returns:
    --------
    metrics_evaler: Evaluator object
        contains all of the metrics of the database
    '''

    db = cym.dbopen(db_file)
    metrics_evaler = cym.Evaluator(db, write=False)
    return metrics_evaler


def add_zeros_columns(df, column_names):
    '''
    Adds a column of a specified name to a given dataframe
    if a column of that name does not exist already. The
    added column is of the length of the entire dataframe
    but consists of only zeros. This function allows for
    greater flexibility in defining prototypes of
    interest across multiple tranistion scenarios

    Parameters:
    -----------
    df: DataFrame
        dataframe to add column to, if the column doesn't exist
        already
    column_names: list of strs
        names to be checked for existence and added if missing

    Returns:
    --------
    df: DataFrame
        dataframe with added column, if column doesn't
        exist anymore
    '''
    for item in column_names:
        if item not in df.columns:
            df[item] = 0.0
    return df


def get_lwr_totals(db_file, non_lwr_prototypes):
    '''
    Creates DataFrame with the number of each prototype
    commissioned or decommissioned at each time step,
    then a column to report the total number of LWR
    prototypes deployed at each time step. The LWR
    prototypes are all of different names, based on
    the unit name, so the aren't easy to total, and
    there are far more LWR prototype names than non-LWR
    prototype names.

    Parameters:
    -----------
    db_file: str
        SQLite database from Cyclus
    non_lwr_prototypes: list of str
        names of non LWR prototypes in the simulation

    Returns:
    --------
    simulation_data: DataFrame
        Contains the number of each prototype commissioned
        and decommissioned at each time step and a column
        for the total number of LWR prototypes at each
        time step.
    '''
    evaler = get_metrics(db_file)
    time = evaler.eval('TimeList')

    commission_df = evaler.eval('BuildSeries')
    decommission_df = evaler.eval('DecommissionSeries')
    commission_df = commission_df.rename(
        index=str, columns={'EnterTime': 'Time'})
    commission_df = tools.add_missing_time_step(commission_df, time)
    commission_by_prototype = pd.pivot_table(
        commission_df,
        values='Count',
        index='Time',
        columns='Prototype',
        fill_value=0)
    commission_by_prototype = add_zeros_columns(
        commission_by_prototype, non_lwr_prototypes)
    commission_by_prototype['lwr'] = commission_by_prototype.drop(
        non_lwr_prototypes, axis=1).sum(axis=1)
    commission_by_prototype = commission_by_prototype.astype('float64')

    if decommission_df is not None:
        negative_count = -decommission_df['Count']
        decommission_df = decommission_df.drop('Count', axis=1)
        decommission_df = pd.concat([decommission_df, negative_count], axis=1)
        decommission_df.rename(columns={'ExitTime': 'Time'}, inplace=True)
        decommission_by_prototype = decommission_df.pivot('Time', 'Prototype')[
            'Count'].reset_index()
        decommission_by_prototype = add_zeros_columns(
            decommission_by_prototype, non_lwr_prototypes)
        decommission_by_prototype = decommission_by_prototype.set_index('Time')
        decommission_by_prototype['lwr'] = decommission_by_prototype.drop(
            non_lwr_prototypes, axis=1).sum(axis=1)
        decommission_by_prototype = decommission_by_prototype.reset_index()
        simulation_data = pd.merge(
            commission_by_prototype,
            decommission_by_prototype,
            left_on='Time',
            right_on='Time',
            how='outer',
            sort=True,
            suffixes=(
                '_enter',
                '_exit')).fillna(0)
    else:
        simulation_data = commission_by_prototype.fillna(0)
        simulation_data = simulation_data.add_suffix('_enter')
        for column in simulation_data.columns:
            simulation_data[(column[:-5] + 'exit')] = 0.0
    simulation_data['lwr_total'] = (
        simulation_data['lwr_enter'] +
        simulation_data['lwr_exit']).cumsum()
    return simulation_data.reset_index()


def get_prototype_totals(db_file, non_lwr_prototypes, prototypes):
    '''
    This function performs the get_lwr_totals
    function on a provided database. Then the total number of
    each prototype deployed at a given time is calculated and
    added to the dataframe. If a prototype
    name is specified but not in the dataframe, then a column
    of zeros is added with the column name reflecting the
    prototype name.

    Parameters:
    -----------
    db_file: str
        name of SQLite database from Cyclus
    non_lwr_prototypes: list of str
        names of non LWR prototypes in the simulation
    prototypes: list of str
        list of names of prototypes to be summed together

    Returns:
    --------
    prototypes_df : DataFrame
        enter, exit, and totals for each type of prototype
        specified. Includes a column totaling all of the
        spcified prototypes, labeled as `advrx_enter`,
        `advrx_exit`, and `advrx_total`, because it is assumed
        that prototypes specified will be the advanced reactors
        of interest for the transition modeled.
    '''
    prototypes_df = get_lwr_totals(db_file, non_lwr_prototypes)
    prototypes_df = add_year(prototypes_df)
    prototypes_df['advrx_enter'] = 0.0
    prototypes_df['advrx_total'] = 0.0
    for prototype in prototypes:
        if prototype in prototypes_df.columns:
            prototypes_df = prototypes_df.rename(
                columns={prototype: prototype + '_enter'})
            prototypes_df[prototype +
                          '_exit'] = np.zeros(len(prototypes_df[prototype + '_enter']))
        prototypes_df[prototype +
                      '_total'] = (prototypes_df[prototype +
                                                 '_enter'] +
                                   prototypes_df[prototype +
                                                 '_exit']).cumsum()
        prototypes_df['advrx_enter'] += prototypes_df[prototype + '_enter']
        prototypes_df['advrx_total'] += prototypes_df[prototype + '_total']

    return prototypes_df


def add_year(df):
    '''
    Adds column of Year, based on the Time colunm

    Parameters:
    -----------
    df: DataFrame
        DataFrame of data to add column to

    Returns:
    --------
    df: DataFrame
        DataFrame with the added column
    '''
    df['Year'] = np.round(df['Time'] / 12 + 1965, 2)
    df['Year'] = df['Year'].fillna(method='ffill')
    return df


def get_transactions(db_file):
    '''
    Gets the TransactionQuantity metric from cymetric,
    sorts by TimeCreated, and renames the TimeCreated
    column

    Parametrs:
    ----------
    db_file: str
        relative path to database

    Returns:
    --------
    transactions: DataFrame
        transaction data with specified modifications
    '''
    evaler = get_metrics(db_file)
    transactions = evaler.eval(
        'TransactionQuantity').sort_values(by='TimeCreated')
    transactions = transactions.rename(columns={'TimeCreated': 'Time'})
    transactions = tools.add_missing_time_step(
        transactions, evaler.eval('TimeList'))
    return transactions


def sum_and_add_missing_time(df):
    '''
    Sums the values of the same time step, and adds any missing time steps
    with 0 for the value

    Parameters:
    -----------
    df: dataframe
        dataframe

    Returns:
    --------
    summed_df: dataframe
        dataframe with the summed values for each time step and inserted
        missing time steps
    '''
    summed_df = df.groupby(['Time']).Quantity.sum().reset_index()
    summed_df = summed_df.set_index('Time').reindex(
        np.arange(0, 1500, 1)).fillna(0).reset_index()
    return summed_df


def find_commodity_transactions(df, commodity):
    '''
    Finds all transactions involving a specified commodity

    Parameters:
    -----------
    df: dataframe
        dataframe of transactions
    commodity: str
        name of commodity to search for

    Returns:
    --------
    commodity_df: dataframe
        contains only transactions involving the specified commodity
    '''
    commodity_df = df.loc[df['Commodity'] == commodity]
    return commodity_df


def find_prototype_transactions(df, prototype):
    '''
    Finds all transactions sent to a specified prototype

    Parameters:
    -----------
    df: dataframe
        dataframe of transactions
    prototype: str
        name of prototype to search for

    Returns:
    --------
    prototype_df: dataframe
        contains only transactions sent to the specified prototype
    '''
    prototype_df = df.loc[df['Prototype'] == prototype]
    return prototype_df


def commodity_mass_traded(transactions_df, commodity):
    '''
    Calculates the total amount of a commodity traded
    at each time step

    Parameters:
    -----------
    transactions: dataframe
        dataframe of transactions of the simulation
    commodity: str
        commodity name

    Returns:
    --------
    total_commodity: DataFrame
        DataFrame of total amount of each
        commodity traded as a function of time
    '''
    transactions = find_commodity_transactions(transactions_df, commodity)
    transactions = sum_and_add_missing_time(transactions)
    total_commodity = add_year(transactions)
    return total_commodity


def add_receiver_prototype(db_file):
    '''
    Creates dataframe of transactions information, and adds in
    the prototype name corresponding to the ReceiverId of the
    transaction. This dataframe is merged with the Agents dataframe, with the
    AgentId column renamed to ReceivedId to assist the merge process. The
    final dataframe is organized by ascending order of Time then TransactionId

    Parameters:
    -----------
    db_file: str
        SQLite database from Cyclus

    Returns:
    --------
    receiver_prototype: dataframe
        contains all of the transactions with the prototype name of the
        receiver included
    '''
    transactions = get_transactions(db_file)
    evaler = get_metrics(db_file)
    agents = evaler.eval('Agents')
    agents = agents.rename(columns={'AgentId': 'ReceiverId'})
    receiver_prototype = pd.merge(
        transactions, agents[['SimId', 'ReceiverId', 'Prototype']], on=[
            'SimId', 'ReceiverId']).sort_values(by=['Time', 'TransactionId']).reset_index(drop=True)
    return receiver_prototype


def commodity_to_prototype(transactions_df, commodity, prototype):
    '''
    Finds the transactions of a specific commodity sent to a single prototype in the simulation,
    modifies the time column, and adds in zeros for any time step without
    a transaction to the specified prototype, and sums all transactions for
    a single time step

    Parameters:
    -----------
    transactions_df: dataframe
        dataframe of transactions with the prototype name
        of the receiver agent added in. use add_receiver_prototype to get this
        dataframe
    commodity: str
        commodity of interest
    prototype: str
        name of prototype transactions are sent to

    Output:
    -------
    prototype_transactions: dataframe
        contains summed transactions at each time step that are sent to
        the specified prototype name.
    '''
    prototype_transactions = find_commodity_transactions(
        transactions_df, commodity)
    prototype_transactions = find_prototype_transactions(
        prototype_transactions, prototype)
    prototype_transactions = sum_and_add_missing_time(prototype_transactions)
    prototype_transactions = add_year(prototype_transactions)
    return prototype_transactions


def commodity_to_LWR(transactions_df, commodity, prototype):
    '''
    Finds the transactions of a specific commodity sent to the LWRs in the
    simulation, modifies the time column, and adds in zeros for any time step
    without a transaction to the LWRs, and sums all transactions for
    a single time step

    Parameters:
    -----------
    transactions_df: dataframe
        dataframe of transactions with the prototype name
        of the receiver agent added in. use add_receiver_prototype to get this
        dataframe
    commodity: str
        commodity of interest
    prototype: str
        name of non-LWR reactor prototype in the simulation

    Output:
    -------
    prototype_transactions: dataframe
        contains summed transactions at each time step that are sent to
        the specified prototype name.
    '''
    prototype_transactions = find_commodity_transactions(
        transactions_df, commodity)
    prototype_transactions = prototype_transactions.loc[
        prototype_transactions['Prototype'] != prototype]
    prototype_transactions = sum_and_add_missing_time(prototype_transactions)
    prototype_transactions = add_year(prototype_transactions)
    return prototype_transactions


def separation_potential(x_i):
    '''
    Calculates Separation Potentail, for use in calculating
    Separative Work Units (SWU) required for enrichment level

    Inputs:
    -------
    x_i: int
        mass fraction of a generic mass stream

    Returns:
    --------
    v: int
        Separation potential
    '''
    v = (2 * x_i - 1) * np.log(x_i / (1 - x_i))
    return v


def calculate_SWU(P, x_p, T, x_t, F, x_f):
    '''
    Calculates Separative Work Units required to produce
    throughput of product given mass of feed and tails and
    assay of each mass stream

    Parameters:
    -----------
    P: int, Series
        mass of product
    x_p: int
        weight percent of U-235 in product
    T: int, Series
        mass of tails
    x_t: int
        weight percent of U-235 in tails
    F: int, Series
        mass of feed
    x_f: int
        weight percent of U-235 in feed

    Returns:
    --------
    SWU: int
        Separative Work units per unit time
    '''
    SWU = P * separation_potential(x_p) + T * separation_potential(x_t) - \
        F * separation_potential(x_f)
    return SWU


def calculate_tails(product, x_p, x_t, x_f):
    '''
    Calculates the mass of tails based on
    a mass of product and the mass fraction
    of the roduct, tails, and feed

    Parameters:
    ----------
    product: int, Series
        mass of product
    x_p: float
        mass fraction of product
    x_t: float
        mass fraction of tails
    x_f: float
        mass fraction of feed

    Returns:
    -------
    tails: int, Series
    '''
    tails = (x_f - x_p) * product / (x_t - x_f)
    return tails


def calculate_feed(product, tails):
    '''
    Calculates the mass of feed material required
    to produce a given amount of product and
    tails

    Parameters:
    ----------
    product: int, Series
        mass of product
    tails: int, Series
        mass of tails

    Returns:
    --------
    feed: int, Series
        mass of feed material
    '''
    feed = product + tails
    return feed


def get_annual_electricity(db_file):
    '''
    Gets the time dependent annual electricity output of reactors
    in the silumation

    Parameters:
    -----------
    db_file: str
        SQLite database from Cyclus

    Returns:
    --------
    electricity_output: DataFrame
        time dependent electricity output, includes
        column for year of time step. The energy column
        is in units of GWe-yr, causing the divide by 1000
        operation.
    '''
    evaler = get_metrics(db_file)
    electricity = evaler.eval('AnnualElectricityGeneratedByAgent')
    electricity['Year'] = electricity['Year'] + 1965
    electricity_output = electricity.groupby(
        ['Year']).Energy.sum().reset_index()
    electricity_output['Energy'] = electricity_output['Energy'] / 1000

    return electricity_output


def get_monthly_electricity(db_file):
    '''
    Gets the time dependent monthy electricity output of reactors
    in the silumation

    Parameters:
    -----------
    db_file: str
        SQLite database from Cyclus

    Returns:
    --------
    electricity_output: DataFrame
        time dependent electricity output, includes
        column for year of time step. The energy column
        is in units of GWe-yr, causing the divide by 1000
        operation.
    '''
    evaler = get_metrics(db_file)
    electricity = evaler.eval('MonthlyElectricityGeneratedByAgent')
    electricity['Year'] = electricity['Month'] / 12 + 1965
    electricity_output = electricity.groupby(
        ['Year']).Energy.sum().reset_index()
    electricity_output['Energy'] = electricity_output['Energy'] / 1000

    return electricity_output


def get_prototype_energy(db_file, advanced_rx):
    '''
    Calculates the annual electricity produced by a given
    prototype name by merging the Agents and AnnualElectricityGeneratedByAgent
    dataframes so that agents can be grouped by prototype name

    Parameters:
    -----------
    db_file: str
        SQLite database from Cyclus
    advanced_rx: str
        name of advanced reactor prototype

    Returns:
    --------
    prototype_energy: dataframe
        dataframe of the year and the total amount of electricity
        generated by all agents of the given prototype name. Values
        are in units of GWe-y, causing the divide by 1000 operation
    '''
    evaler = get_metrics(db_file)
    agents = evaler.eval('Agents')
    energy = evaler.eval('AnnualElectricityGeneratedByAgent')
    merged_df = pd.merge(energy, agents, on=['SimId', 'AgentId'])
    merged_df['Year'] = merged_df['Year'] + 1965
    prototype_energy = merged_df.loc[merged_df['Prototype'] == advanced_rx]
    prototype_energy = prototype_energy.groupby(
        ['Year']).Energy.sum().reset_index()
    prototype_energy = prototype_energy.set_index(
        'Year').reindex(range(1965, 2091)).fillna(0).reset_index()
    prototype_energy['Energy'] = prototype_energy['Energy'] / 1000
    return prototype_energy


def get_lwr_energy(db_file, advanced_rx):
    '''
    Calculates the annual electricity produced by a given
    prototype name by merging the Agents and AnnualElectricityGeneratedByAgent
    dataframes so that agents can be grouped by prototype name

    Parameters:
    -----------
    db_file: str
        SQLite database from Cyclus
    advanced_rx: str
        name of advanced reactor prototype also present in the simulation

    Returns:
    --------
    lwr_energy: dataframe
        dataframe of the year and the total amount of electricity
        generated by all of the LWRs in the simulation. The energy
        column is in units of GWe-y, causing the divide by 1000
        operation.
    '''
    evaler = get_metrics(db_file)
    agents = evaler.eval('Agents')
    energy = evaler.eval('AnnualElectricityGeneratedByAgent')
    merged_df = pd.merge(energy, agents, on=['SimId', 'AgentId'])
    merged_df['Year'] = merged_df['Year'] + 1965
    lwr_energy = merged_df.loc[merged_df['Prototype'] != advanced_rx]
    lwr_energy = lwr_energy.groupby(['Year']).Energy.sum().reset_index()
    lwr_energy = lwr_energy.set_index('Year').reindex(
        range(1965, 2091)).fillna(0).reset_index()
    lwr_energy['Energy'] = lwr_energy['Energy'] / 1000
    return lwr_energy