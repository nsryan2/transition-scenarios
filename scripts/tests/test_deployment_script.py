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


# Greedy distribution dictionary
greedy_dist_df = {
    'Year': [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
    'test_cap': [20, 79, 80, 81, 220, 640, 693, 950, 700],
    'new_cap': [20, 75, 80, 80, 220, 640, 690, 950, 700]}

# Pre-determined greedy distribution dictionary
pre_det_greedy_df = {
    'test_cap': [20, 79, 80, 81, 220, 640, 693, 950, 700],
    'total_cap': [20, 75, 80, 95, 240, 715, 690, 965, 950],
    'new_cap': [20, 75, 80, 80, 220, 640, 690, 950, 700]}

# Pre-determined linear distribution dictionary
pre_det_linear_df = {
    'test_cap': [20, 79, 80, 81, 220, 640, 693, 950, 700],
    'total_cap': [80, 80, 100, 100, 225, 655, 825, 1150, 1050],
    'new_cap': [80, 80, 100, 100, 225, 655, 700, 955, 705]}

# Set capacity distribution dictionary
set_cap_reactors = {
    'ReactorBig': [80, 1, 6, [2, 2, 2, 2, 2, 2, 2, 2, 2]],
    'ReactorMedium': [20, 1, 4, 'no_dist'],
    'ReactorSmall': [5, 1, 2, 'no_dist']}

set_cap_df = {
    'test_cap': [20, 79, 80, 81, 220, 640, 693, 950, 700],
    'total_cap': [80, 80, 100, 100, 230, 655, 815, 1150, 960],
    'new_cap': [80, 80, 100, 100, 230, 655, 705, 955, 705]}
