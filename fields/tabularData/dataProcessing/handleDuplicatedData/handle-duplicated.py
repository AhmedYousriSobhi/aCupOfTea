"""
    Author: Ahmed Yousri Sobhi (ahmedyousrisobhi@gmail.com)
    Created_at: 7th Sep 2023
    Objective: Handling duplicated data in Dataset.
"""

import os
import pandas as pd, numpy as np
from tqdm import tqdm

def filter_duplicated_records(df:pd.DataFrame, target_col:str, dependant_cols=dict)-> pd.DataFrame:
    """
        Used to filter out records of certain input target column, based on specific values in dependant columns.

        PARAMETERS
            df: pandas dataframe, input dataset.
            target_col: str, Target column which required to drop duplicated from.
            dependant_cols: dict, describe the dependant columns and their aggeration function.

        RETURN 
            pandas DataFrame after dropping the duplicated values.
    """

    # Create a copy of input dataframe
    df_copy = df.copy()

    # Select unique ids, where time_to_delivery is maximum, and down_payment is minimum
    df_unique = (
        df_copy.groupby(target_col, as_index=False)
        .agg(dependant_cols)
    )

    dependant_cols_lst = list(dependant_cols.keys())

    # append target_col
    dependant_cols_lst.append(target_col)

    df_copy = df_copy.merge(
        df_unique,
        how='inner',
        on=dependant_cols_lst,
        )

    # Final filter step, drop out whole duplicated rows
    df_copy.drop_duplicates(subset=[target_col], inplace=True)

    # Return modified dataframe
    return df_copy