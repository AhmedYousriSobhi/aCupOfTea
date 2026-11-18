"""
    This script contains all the required functions for feature engineering required for this project
"""

# Importing nessecary libararies and packages
import pandas as pd
import numpy as np
import webcolors

# Main function: Feature Engineer
def feature_engineereing(_df:pd.DataFrame)->pd.DataFrame:
    """
        Used to create all defined possible engineering steps in the data.

        PARAMETERS
            _df: pandas dataframe, input dataframe.

        RETURN
            pandas DataFrame with created features.
    """

    # Create a copy of input dataframe
    df = _df.copy()

    # Feature: Discount
    df = calculate_discount(df, 'ratio')

    # Feature: Closest color to RGB values
    df = extract_closest_color(df)

    # Feature: Time based features
    df = extract_time_based_features(df, 'retailweek')

    return df

def calculate_discount(data:pd.DataFrame, target_col:str)->pd.DataFrame:
    """
        Used to calculate discount feature from ratio column.

        PARAMETERS
            data: pandas dataframe, input dataframe.
            target_col: str, target ratio column.
        
        OUTPUT
            pandas DataFrame with extracted features
    """

    # Make a copy of input dataset
    df_copy = data.copy()

    df_copy['discount'] = 1- df_copy['ratio']

    # Drop unnessary column
    df_copy.drop('ratio', axis=1, inplace=True)

    return df_copy
    
def closest_colour(requested_colour:tuple)->str:
    """
        Used to calculate the closest color based on RGB values.

        PARAMETERS
            requested_colour: tuple, values of RGB.
        
        OUTPUT
            str, the closest color name
    """
    min_colours = {}
    for key, name in webcolors.CSS3_HEX_TO_NAMES.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = (r_c - requested_colour[0]) ** 2
        gd = (g_c - requested_colour[1]) ** 2
        bd = (b_c - requested_colour[2]) ** 2
        min_colours[(rd + gd + bd)] = name
    return min_colours[min(min_colours.keys())]


def get_colour_name(requested_colour):
    """
        Used to calculate the actual and closest color based on RGB values.

        PARAMETERS
            requested_colour: tuple, values of RGB.
        
        OUTPUT
            list of strings, the actual and closest color name
    """
    try:
        closest_name = actual_name = webcolors.rgb_to_name(requested_colour)
    except ValueError:
        closest_name = closest_colour(requested_colour)
        actual_name = None
    return actual_name, closest_name


def extract_closest_color(data:pd.DataFrame)->pd.DataFrame:
    """
        Used to extract closest color names based on RGB values.

        PARAMETERS
            data: pandas dataframe, input dataframe.
        
        OUTPUT
            pandas DataFrame with extracted colors
    """
    
    # Create a copy of color name
    df_copy = data.copy()

    # Define main/secondary colours
    main_color_cols = ['rgb_r_main_col', 'rgb_g_main_col', 'rgb_b_main_col'] 
    sec_color_cols = ['rgb_r_sec_col', 'rgb_g_sec_col', 'rgb_b_sec_col']

    # Calculate the closest color
    df_copy['main_closest_color'] = (
        df_copy[main_color_cols].apply(lambda row: tuple(row), axis=1)
        .apply(get_colour_name)
        .apply(lambda row: row[1])
    )

    df_copy['sec_closest_color'] = (
        df_copy[sec_color_cols].apply(lambda row: tuple(row), axis=1)
        .apply(get_colour_name)
        .apply(lambda row: row[1])
    )

    # Drop unnessary columns
    df_copy.drop(main_color_cols, axis=1, inplace=True)
    df_copy.drop(sec_color_cols, axis=1, inplace=True)

    return df_copy


def extract_time_based_features(data:pd.DataFrame, ts_col:str)->pd.DataFrame:
    """
        Used to extract time based features from time series column.

        PARAMETERS
            data: pandas dataframe, input dataframe.
            ts_col: str, target time series column.
        
        OUTPUT
            pandas DataFrame with extracted features
    """
    
    # make a copy of input dataframe
    df_copy = data.copy()

    # Make sure the target column is datetime format
    df_copy[ts_col] = pd.to_datetime(df_copy[ts_col])

    # Extract time based features
    df_copy['year'] = df_copy[ts_col].dt.year
    df_copy['month'] = df_copy[ts_col].dt.month
    df_copy['day'] = df_copy[ts_col].dt.day
    df_copy['dayofweek'] = df_copy[ts_col].dt.day_of_week

    # drop timeseries column
    df_copy.drop(ts_col, axis=1, inplace=True)

    return df_copy