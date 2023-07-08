
from scipy import stats
from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd
import numpy as np


class SkewnessTransformer(BaseEstimator, TransformerMixin):

    def __init__(self, skew_limit=0.8):
        self.skew_limit = skew_limit
        self.method_dict = {}

    def fit(self, X, y=None):
        if isinstance(X, pd.DataFrame):
            X= X.to_numpy()
        self.method_dict = self.extracrt_recommeneded_features(X)
        return self

    def transform(self, X):
        if isinstance(X, pd.DataFrame):
            X= X.to_numpy()
        X_transformed = X.copy()
        for method, features in self.method_dict.items():

            if method == 'log':
                # Apply log transformation to the specified features
                X_transformed[:, features] = np.log1p(X_transformed[:, features])
            elif method == 'sqrt':
                # Apply square root transformation to the specified features
                X_transformed[:, features] = np.sqrt(X_transformed[:, features])
            elif method == 'boxcox':
                # Apply Box-Cox transformation to the specified features
                for feature in features:
                    X_transformed[:, feature], _ = stats.boxcox(X_transformed[:, feature])
            elif method == 'yeojohnson':
                for feature in features:
                    X_transformed[:, feature], _ = stats.yeojohnson(X_transformed[:, feature])
            elif method == 'cube':
                # Apply Cube transformation to the specified features
                X_transformed[:, features] = np.cbrt(X_transformed[:, features])

        return X_transformed

    def extracrt_recommeneded_features(self, X):
        skew_vals = np.abs(stats.skew(X, axis=0))
        skew_col_indices = np.where(skew_vals > self.skew_limit)[0]
        method_dict = {}

        for feature_idx in skew_col_indices:
            feature = X[:, feature_idx]

            method = self.recommend_skewness_reduction_method(feature)
            if method not in method_dict:
                method_dict[method] = [feature_idx]
            else:
                method_dict[method].append(feature_idx)

        print(method_dict)
        return method_dict

    def recommend_skewness_reduction_method(self, feature: pd.Series, forced_fix= False) -> str:

        skewness_dict = {}
        all= {}

        transformed_log = np.log1p(feature)
        _, p_value = stats.normaltest(transformed_log)

        # The p-value is a measure of the evidence against the null hypothesis of normality. 
        # A low p-value (typically less than 0.05) suggests that the data is significantly different from a normal distribution, 
        # indicating that the fix for skewness was not successful in achieving normality.
        if p_value > 0.05:
            skewness_dict['log'] = p_value
        else:
            all['log']= p_value

        transformed_sqrt = np.sqrt(feature)
        _, p_value = stats.normaltest(transformed_sqrt)
        if p_value > 0.05:
            skewness_dict['sqrt'] = p_value
        else:
            all['sqrt']= p_value

        if (feature < 0).any() or (feature == 0).any():
            transformed_yeojohnson, _ = stats.yeojohnson(feature)
            _, p_value = stats.normaltest(transformed_yeojohnson)
            if p_value > 0.05:
                skewness_dict['yeojohnson'] = p_value
            else:
                all['yeojohnson']= p_value

        else:
            transformed_boxcox, _ = stats.boxcox(feature + 0.0001)
            _, p_value = stats.normaltest(transformed_boxcox)
            if p_value > 0.05:
                skewness_dict['boxcox'] = p_value
            else:
                all['boxcox']= p_value

        transformed_cbrt = np.cbrt(feature)
        _, p_value = stats.normaltest(transformed_cbrt)
        if p_value > 0.05:
            skewness_dict['cube'] = p_value
        else:
            all['cube']= p_value

        if len(skewness_dict) > 0:
            return max(skewness_dict, key=lambda y: abs(skewness_dict[y]))
        else:
            if forced_fix:
                print('No Fix, using best transformers')
                return max(all, key=lambda y: abs(all[y]))
            else:
                return 'No Fix'