"""
    Author: Ahmed Yousri Sobhi (ahmedyousrisobhi@gmail.com)
    Created_at: 7th Sep 2023
    Objective: Handling Outliers in Dataset.
"""

import os
import pandas as pd, numpy as np
from tqdm import tqdm

# Function to handle outliers
def remove_outlier_iqr(_df:pd.DataFrame, features_lst:list=None, target_col:str='')->pd.DataFrame:
    """
        Used to remove outliers based on input selected features in the dataframe.
        Outlier removal method is IQR

        PARAMETERS
            df: pandas DataFrame, describe input dataframe which require outliers removal
            features_lst: list, describe the input columns features list.
            target_col: str, describe the target column which we need to remove outlier from.

        RETURN
            Pandas DataFrame, after removing outliers
    """

    # Make a copy of input dataframe
    df_copy = _df.copy()

    if features_lst is not None:
        # Create empty list for records storing, to be converted into dataframe later.
        Q1 = df_copy.groupby(features_lst)[target_col].transform('quantile', 0.25)
        Q3 = df_copy.groupby(features_lst)[target_col].transform('quantile', 0.75)

    else:
        # Create empty list for records storing, to be converted into dataframe later.
        Q1 = df_copy[target_col].quantile(0.25)
        Q3 = df_copy[target_col].quantile(0.75)
        
    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR

    upper_bound = Q3 + 1.5 * IQR

    return df_copy[df_copy[target_col].between(lower_bound, upper_bound, inclusive='both')]



def remove_outlier(df:pd.DataFrame, neglected_cols:list, dependant_cols:list)->pd.DataFrame:
    """
        Used to extract numerical columns and drop used input neglected columns,
        Then remove outliers from these columns based on selected dependant features
        using IQR

        PARAMETERS
            df: pandas DataFrame, user input dataframe.
            neglected_cols: list, numerical columns to drop and not interested in removing outliers for.
            dependant_cols: lst, columns to remove ouliters based on them.

        RETURN
            pandas DataFrame after removing outliers.    
    """

    # Create a copy of input dataset
    df_copy = df.copy()

    # Select numerical columns
    numeric_cols = df_copy.select_dtypes('number').columns.tolist()

    # Remove neglected columns
    for col in neglected_cols:
        if col in numeric_cols:
            numeric_cols.remove(col)   

    # Iterate over each numerical col and remove ouliers
    for col in tqdm(numeric_cols, total=len(numeric_cols)):

        # Using Iqr to remove outliers
        df_copy = remove_outlier_iqr(df_copy, dependant_cols, col)

    # It is a nesessary step to reset_index
    df_copy.reset_index(drop=True, inplace=True)

    return df_copy