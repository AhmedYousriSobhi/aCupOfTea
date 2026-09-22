"""
    Author: Ahmed Yousri Sobhi (ahmedyousrisobhi@gmail.com)
    Created_at: 7th Sep 2023
    Objective: Handling Missing Data in Dataset.
"""
import os
import pandas as pd, numpy as np
from tqdm import tqdm

# Function to handle missing values
def fill_missing_values(df:pd.DataFrame, nan_col:str, feature_depend:list, method:str)->pd.DataFrame:
    """
        Used to fill missing values in certain column,
        based on selected metric, calculated according to certain features.

        PARAMETERS
            df: pandas DataFrame, input dataset.
            nan_col: str, input column with required to fill missing values in.
            feature_depend: str, feature which we will calculate the filling values based on.
            method:str, selected aggregation function, [mean, mode]

        RETURN
            pandas Series of filled column.
    """

    # Create a copy of input dataFrame 
    df_copy = df.copy()

    # Calculate the average value for nan_col based on each feature_col.
    df_fill_value = (
        df_copy.groupby(feature_depend, as_index=False)
        .agg({nan_col:method})
        .round()
    )
    
    # Merge with actually dataFrame
    df_copy = df_copy.merge(
        df_fill_value,
        on=feature_depend,
        how='left',
        suffixes=('','_fill')
        )

    # Fill missing values
    df_copy.loc[df_copy[nan_col].isna(), nan_col] = df_copy.loc[df_copy[nan_col].isna(), nan_col+'_fill']

    return df_copy.drop(nan_col+'_fill', axis=1)


def fill_missing_columns(df:pd.DataFrame, dependant_cols:list, fill_value_dict:dict)->pd.DataFrame:
    """
       Given input dataset, and required to fill all missing values in all columns,
       Talking into consideration whether that column is numerical or categorical, 
       and fill its missing values based on filling aggeration function required, of certain input dependant cols.

       PARAMETERS
            df: pandas DataFrame, input dataset with missing values.
            dependant_cols: list, features which target missing columns depends on during the filling.
            fill_value_dict: dictionary, describe each method used for filling value in case of numerical and categorical.

       RETURN
            pandas DataFrame with missing values filled.
    """
    # Create a copy of input dataframe
    df_copy = df.copy()

    # Extract columns with nans values
    cols_with_nans = df_copy.columns[df_copy.isna().sum()>0].tolist()
    
    # Extract numeric & catetorical cols
    numeric_cols = df_copy.select_dtypes('number').columns.tolist()

    category_cols = df_copy.select_dtypes('object').columns.tolist()

    # Iterate over each column with nan values
    for col in tqdm(cols_with_nans, total=len(cols_with_nans)):
        
        # Check if column is numerical or categorical
        if col in numeric_cols:
            df_copy =  fill_missing_values(df_copy, col, dependant_cols, fill_value_dict['numeric'])
        
        elif col in category_cols:
            df_copy.fillna({col: fill_value_dict['category']}, inplace=True)

        else:
            # Skip these column, will be handled later
            continue

    return df_copy