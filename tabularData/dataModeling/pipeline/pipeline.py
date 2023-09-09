
import warnings
warnings.filterwarnings('ignore')

import os

import pandas as pd, numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder, RobustScaler
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer, make_column_selector
from sklearn.cluster import KMeans, AgglomerativeClustering

import sys
sys.path.append('../tools/')

import pipelinetransformers

# To save the model locally
import joblib

if __name__ == __main__:
    # Define the preprocessing steps for the entire dataset
    data_preprocessing = Pipeline(
        [
            ('data_cleaning', pipelinetransformers.preprocessTransformer()),  # Custom data cleaning step
            ('feature_engineering', pipelinetransformers.featureEngTransformer()),  # Custom feature engineering step
        ]
    )

    numeric_transformer = Pipeline(
        [
            ('skewness', pipelinetransformers.SkewnessTransformer()),
            ('impute', SimpleImputer(strategy='mean')),
            ('scaler', StandardScaler())
        ]
    )

    categorical_transformer = Pipeline(
        [
            ('impute', SimpleImputer(strategy='most_frequent')),
            ('ohc', OneHotEncoder(handle_unknown='ignore'))
        ]
    )

    """
    By setting remainder='passthrough', you ensure that all columns in the input are included in the output without specifying them by name. 
    This should allow you to use the pipeline with data that might not have column names and resolve the "Specifying the columns using strings" error.
    """

    data_preprocessing.set_output(transform='pandas')

    scalling_transformer = ColumnTransformer(
        [
            ('numericals', numeric_transformer, make_column_selector(dtype_include=np.number)),
            ('Categorical', categorical_transformer, make_column_selector(dtype_include='object'))
        ],
        remainder='drop',
        n_jobs=-1
    )

    model_preprocessor = Pipeline(
        steps=[
            ('data_preprocess', data_preprocessing),
            ('update_feature_lists', pipelinetransformers.updateFeaturesList()),
            ('scaller', scalling_transformer)
        ]
    )

    n_components = 4
    pca_pipeline = Pipeline(
        steps=[
            ('model_preprocessor', model_preprocessor),
            ('PCA', PCA(n_components=n_components))
        ]
    )

    # Define the Agglomerative Clustering step in the pipline
    n_clusters = 4

    agg_clustering = AgglomerativeClustering(n_clusters=n_clusters)
    kmeans_clustering = KMeans(n_clusters=n_clusters)

    cluster_pipeline = Pipeline(
        steps=[
            ('dimentionality_reduction', pca_pipeline),
            ('cluster', kmeans_clustering)
        ]
    )

