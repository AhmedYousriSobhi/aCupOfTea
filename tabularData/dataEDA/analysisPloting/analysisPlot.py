"""
    Author: Ahmed Yousri Sobhi (ahmedyousrisobhi@gmail.com)
    Created_at: 2023-09-05
    Objective: Plotting statistical analysis for features in a dataset.
"""

# Importing required libararies
import os

import pandas as pd
import numpy as np
# for data visualization & ploting
import matplotlib.pyplot as plt
import seaborn as sns

sns.set()
sns.set_style('whitegrid')

## Define functions

def plot_data_frequency(_df: pd.DataFrame, target_col: str, top_index=20, save_plot=True) -> None:
    """
        Used to plot bar plot of top n values in selected target col.
        
        PARAMETERS
            _df: pandas DataFrame, input dataset.
            target_col: str, input target col to plot its unique values count.
            top_index: int, top n index value to plot in the plotting.
            save_plot: boolean, determine whether to save the plot of not.
        
        RETURN
            None
    """
    
    # Setup the figure size
    plt.figure(figsize=(8, 6))

    percentage_counts = (
        _df[target_col]
        .value_counts(normalize=True)
        .rename('percentage')
        .mul(100)
        .reset_index()
        .rename(columns={'index':target_col})
        .sort_values('percentage', ascending=False)
        .iloc[:top_index]
    )

    # seaborn barplot
    sns.barplot(data=percentage_counts, x='percentage', y=target_col)

    # Rotate the x-axis labels
    plt.yticks(rotation=0)

    # Set the titel of the plot.
    plt.title(f'What is the most common used {target_col}?')

    # Save the plot
    if save_plot == True:
        try:
            plt.savefig(f'../report/plots/{target_col}_countplot.jpg', bbox_inches = 'tight')
        except FileNotFoundError:
            print('Wring file or file path')
            print('Creating new directory')
            # Create required directories
            if not os.path.exists('../report/plots'):
                os.makedirs('../report/plots/')
            plt.savefig(f'../report/plots/{target_col}_countplot.jpg', bbox_inches = 'tight')

    # Show the plot
    plt.show()


def plot_numeric_features(df:pd.DataFrame, cols_to_drop:list, plot_type, save_plot:bool) -> None:
    """
        Used to plot numerical featuers based on input selected plot.

        PARAMETERS
            df: pandas DataFrame, input dataframe.
            cols_to_drop: list, list of columns to drop.
            plot_type: function, define the plot type.
            save_plot: boolean, to whether save plot or not.
        
        RETURN
            None
    """

    # Select Numerical columns only
    features_numeric = (
        df.drop(cols_to_drop, axis=1)
        .select_dtypes('number')
        .columns.tolist()
    )

    # Calculate the number of rows and columns for subplots
    num_rows = int(len(features_numeric) / 2) + len(features_numeric) % 2
    num_cols = 2

    # Create subplots
    fig, axes = plt.subplots(nrows=num_rows, ncols=num_cols, figsize=(12, 8))

    # Iterate over features and plot distplot on subplots
    for i, feature in enumerate(features_numeric):
        row = i // num_cols
        col = i % num_cols
        ax = axes[row, col]
        plot_type(df[feature], ax=ax)
        ax.set_title(f'{plot_type.__name__} of {feature.capitalize()}')

    # Remove empty subplots if necessary
    if len(features_numeric) % 2 != 0:
        fig.delaxes(axes[num_rows - 1, num_cols - 1])

    # Set title for the whole plot
    fig.suptitle(f'{plot_type.__name__} Analysis', fontsize=16)
    plt.tight_layout()

    # Save the plot
    if save_plot == True:
        try:
            plt.savefig(f'../report/plots/numerical_{plot_type.__name__}.jpg',bbox_inches = 'tight')
        except FileNotFoundError:
            print('Wring file or file path')
            print('Creating new directory')
            # Create required directories
            if not os.path.exists('../report/plots'):
                os.makedirs('../report/plots/')
            plt.savefig(f'../report/plots/numerical_{plot_type.__name__}.jpg',bbox_inches = 'tight')
        
    plt.show()