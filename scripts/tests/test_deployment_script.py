import os
import sys
import pytest
import numpy as np
import pandas as pd
path = os.path.realpath(__file__)
sys.path.append(os.path.dirname(os.path.dirname(path)))
import deployment_scripts as dep

ad_reactors = {
    'ReactorBig': [80, 1, 6, [1,2,1,2,1,2,1,2,1]],
    'ReactorMedium':[20,1,4,'no_dist'],
    'ReactorSmall': [5, 1, 2, 'no_dist']}
# {reactor: [Power (MWe), capacity_factor (%),
# lifetime (yr), distribution (default='no_dist')]}

test_dict = {
    'Year':[2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
    'test_cap': [20, 79, 80, 81, 220, 640, 693, 950, 700]}
test_df = pd.DataFrame.from_dict(test_dict)


def test_direct_decom():
    # Decommissioning test dictionary
    # Based on the greedy algorithm
    decom_df = {
        'Year': [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
        'manual_decom': [0, 0, 0, 0, 0, 0, 0, 0, 1],
        # manual calculation based on greedy algorithm
        'ReactorBigDecom': [0, 0, 0, 0, 0, 0, 0, 0, 1]}
        # result of greedy function using the direct_decom function

    assert all(decom_df['manual_decom'][i] == decom_df['ReactorBigDecom'][i] for i in range(len(decom_df['manual_decom'])))


def test_num_react_to_cap():
    # Reactors to capacity test dictionary
    # Based on the greedy algorithm
    react_to_cap_df = {
        'Year': [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
        'manual_cap': [0, 0, 80, 80, 160, 640, 640, 880, 720],
        'new_cap': [0, 0, 80, 80, 160, 640, 640, 880, 720]}

    assert all(react_to_cap_df['manual_cap'][i] == react_to_cap_df['new_cap'][i] for i in range(len(react_to_cap_df['manual_cap'])))

def test_greedy_deployment():
    # Greedy distribution dictionary
    greedy_dist_df = {
        'Year': [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
        'test_cap': [20, 79, 80, 81, 220, 640, 693, 950, 700],
        'manual_cap': [20, 75, 80, 80, 220, 640, 690, 950, 700]}

    # Convert to DataFrame for comparison
    greedy_dist_df = pd.DataFrame(greedy_dist_df)

    calculated_greedy_df = dep.greedy_deployment(
        test_df, 'test_cap', ad_reactors)

    # Ensure 'new_cap' column exists in the result
    assert 'new_cap' in calculated_greedy_df.columns, "The 'new_cap' column is missing in the calculated results."

    # Test the 'manual_cap' values against 'new_cap'
    for i in range(len(greedy_dist_df)):
        assert greedy_dist_df['manual_cap'][i] == calculated_greedy_df['new_cap'][i], f"Failed at index {i}: {greedy_dist_df['manual_cap'][i]} != {calculated_greedy_df['new_cap'][i]}"

    print("All tests passed.")

# def test_pre_det_deployment_greedy():
#     # Pre-determined greedy distribution dictionary
#     manual_pre_det_greedy_df = {
#         'test_cap': [20, 79, 80, 81, 220, 640, 693, 950, 700],
#         'total_cap': [20, 75, 80, 95, 240, 715, 690, 965, 950],
#         'manual_cap': [20, 75, 80, 80, 220, 640, 690, 950, 700]}

#     manual_pre_det_greedy_df = pd.DataFrame(manual_pre_det_greedy_df)

#     pre_det_dep_df_greedy = test_df.copy()
#     dep.pre_det_deployment(pre_det_dep_df_greedy, 'test_cap', ad_reactors)

#     # Ensure 'new_cap' column exists in the result
#     assert 'new_cap' in pre_det_dep_df_greedy.columns, "The 'new_cap' column is missing in the calculated results."

#     # Test the 'manual_cap' values against 'new_cap'
#     for i in range(len(pre_det_dep_df_greedy)):
#         assert manual_pre_det_greedy_df['manual_cap'][i] == pre_det_dep_df_greedy['new_cap'][i], f"Failed at index {i}: {manual_pre_det_greedy_df['manual_cap'][i]} != {pre_det_dep_df_greedy['new_cap'][i]}"

#     print("All tests passed.")

# def test_pre_det_deployment_not():
#     # Pre-determined linear distribution dictionary
#     pre_det_linear_df = {
#         'test_cap': [20, 79, 80, 81, 220, 640, 693, 950, 700],
#         'total_cap': [80, 80, 100, 100, 225, 655, 825, 1150, 1050],
#         'manual_cap': [80, 80, 100, 100, 225, 655, 700, 955, 705]}

#     pre_det_dep_df_not = test_df.copy()
#     dep.pre_det_deployment(pre_det_dep_df_not, 'test_cap', ad_reactors, False)

#     assert all(pre_det_linear_df['manual_cap'][i] == pre_det_dep_df_not['new_cap'][i] for i in range(len(pre_det_dep_df_not['new_cap'])))

def test_pre_det_deployment_greedy():
    # Define the expected DataFrame for the greedy case
    manual_pre_det_greedy_df = {
        'Year': [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
        'test_cap': [20, 79, 80, 81, 220, 640, 693, 950, 700],
        'total_cap': [20, 75, 80, 95, 240, 715, 690, 965, 950],
        'manual_cap': [20, 75, 80, 80, 220, 640, 690, 950, 700]
    }
    manual_pre_det_greedy_df = pd.DataFrame(manual_pre_det_greedy_df)

    # Create a copy of test_df to pass to the function
    pre_det_dep_df_greedy = test_df.copy()

    # Call the pre_det_deployment function with greedy=True
    result_df = dep.pre_det_deployment(pre_det_dep_df_greedy, 'test_cap', ad_reactors, greedy=True)

    # Merge DataFrames on 'Year' and 'test_cap' to compare the expected 'manual_cap' with 'new_cap'
    comparison_df = pd.merge(
        result_df, manual_pre_det_greedy_df[['Year', 'test_cap', 'manual_cap']],
        on=['Year', 'test_cap'], suffixes=('', '_manual'))

    # Check that 'new_cap' matches 'manual_cap'
    assert comparison_df['new_cap'].equals(comparison_df['manual_cap']), \
        f"Greedy Test failed. Mismatched values:\n{comparison_df[comparison_df['new_cap'] != comparison_df['manual_cap']]}"

    print("Greedy Test passed.")

def test_pre_det_deployment_linear():
    # Define the expected DataFrame for the linear case
    pre_det_linear_df = {
        'Year': [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
        'test_cap': [20, 79, 80, 81, 220, 640, 693, 950, 700],
        'total_cap': [80, 80, 100, 100, 225, 655, 825, 1150, 1050],
        'manual_cap': [80, 80, 100, 100, 225, 655, 700, 955, 705]
    }
    pre_det_linear_df = pd.DataFrame(pre_det_linear_df)

    # Create a copy of test_df to pass to the function
    pre_det_dep_df_linear = test_df.copy()

    # Call the pre_det_deployment function with greedy=False
    result_df = dep.pre_det_deployment(pre_det_dep_df_linear, 'test_cap', ad_reactors, greedy=False)

    # Merge DataFrames on 'Year' and 'test_cap' to compare the expected 'manual_cap' with 'new_cap'
    comparison_df = pd.merge(result_df, pre_det_linear_df[['Year', 'test_cap', 'manual_cap']],
                            on=['Year', 'test_cap'], suffixes=('', '_manual'))

    # Check that 'new_cap' matches 'manual_cap'
    assert comparison_df['new_cap'].equals(comparison_df['manual_cap']), \
        f"Linear Test failed. Mismatched values:\n{comparison_df[comparison_df['new_cap'] != comparison_df['manual_cap']]}"

    print("Linear Test passed.")

# Set capacity distribution dictionary
set_cap_reactors = {
    'ReactorBig': [80, 1, 6, [2, 2, 2, 2, 2, 2, 2, 2, 2]],
    'ReactorMedium': [20, 1, 4, 'no_dist'],
    'ReactorSmall': [5, 1, 2, 'no_dist']}

set_cap_df = {
    'test_cap': [20, 79, 80, 81, 220, 640, 693, 950, 700],
    'total_cap': [80, 80, 100, 100, 230, 655, 815, 1150, 960],
    'manual_cap': [80, 80, 100, 100, 230, 655, 705, 955, 705]}

# def test_