"""
    This script contains all the required functions for data cleaning required for this project
"""
# Importing nessecary libararies and packages
import pandas as pd
import numpy as np

# Main function: data_cleaning
def data_preprocess(_df:pd.DataFrame)->pd.DataFrame:
    """
        Used to create all defined possible cleaning steps in the data.

        PARAMETERS
            _df: pandas dataframe, input dataframe.

        RETURN
            pandas DataFrame with created features.
    """

    # Create a copy of input dataframe
    df = _df.copy()

    # Drop missing values from column 'Income'
    df.dropna(subset='Income', axis=0, inplace=True)

    # Handling Outliers
    # From RAW EDA analysis
    outliers_cols= [
        'Income',
        'MntWines', 
        'MntFishProducts', 
        'MntSweetProducts', 
        'MntGoldProds', 
        "NumDealsPurchases", 
        "NumCatalogPurchases", 
        "NumWebVisitsMonth"
    ]

    outliers_selected_cols = extract_outliers_cols(df[outliers_cols])

    cols_to_drop = list(set(df.columns.tolist()) - set(outliers_selected_cols))
    
    dependant_cols = ['Marital_Status']
    df = remove_outlier(df, cols_to_drop, dependant_cols)
    
    return df


def extract_outliers_cols(_df:pd.DataFrame, thr:int=None)->list:
    """
        Used to extract cols with outliers with low records percentage in the dataset

        PARAMETERS
            _df: pandas dataframe, input dataframe.
             thr: int, therould of outliers records percentage.

        RETURN
            list of outliers cols.
    """

    # Create a copy of input dataframe
    df = _df.copy()

    # Calculate the records percentage of the outliers data in each feature
    iqr = df.quantile(0.75) - df.quantile(0.25)
    higher = df.quantile(0.75) + iqr * 1.5

    df_dict = {}
    for col in df.columns:
        df_dict[col] = 100*df[df[col]> higher[col]].shape[0]/df.shape[0]

    # Convert to dataframe
    df_outlier_percentage = pd.DataFrame(df_dict.items() , columns=['feature', 'percentage'])

    outliers_cols_selected = (
        df_outlier_percentage[df_outlier_percentage.percentage <= thr]
        ['feature'].tolist()
    )

    return outliers_cols_selected



# Function to handle outliers
def remove_outlier_iqr(_df:pd.DataFrame, features_lst:list, target_col:str)->pd.DataFrame:
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

    # Create empty list for records storing, to be converted into dataframe later.
    Q1 = df_copy.groupby(features_lst)[target_col].transform('quantile', 0.25)
    Q3 = df_copy.groupby(features_lst)[target_col].transform('quantile', 0.75)

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
    for col in numeric_cols:

        # Using Iqr to remove outliers
        df_copy = remove_outlier_iqr(df_copy, dependant_cols, col)

    # It is a nesessary step to reset_index
    df_copy.reset_index(drop=True, inplace=True)

    return df_copy
