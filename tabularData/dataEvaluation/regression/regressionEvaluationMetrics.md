# Regression Evalulation Metrics

## Table of Content
- [Regression Evalulation Metrics](#regression-evalulation-metrics)
  - [Table of Content](#table-of-content)
  - [Abstract](#abstract)
  - [MSE - Mean Squared Error](#mse---mean-squared-error)
  - [RMSE - Root Mean Squared Error](#rmse---root-mean-squared-error)
  - [Mean absolute error (MAE)](#mean-absolute-error-mae)
  - [R-squared (R^2)](#r-squared-r2)
  - [Adjusted R^2](#adjusted-r2)
  - [Mean absolute percentage error (MAPE)](#mean-absolute-percentage-error-mape)
  - [Root mean squared logarithmic error (RMSLE)](#root-mean-squared-logarithmic-error-rmsle)
  - [Median absolute error (MedAE)](#median-absolute-error-medae)
  - [Explained variance score (EVS)](#explained-variance-score-evs)
  - [AIC (Akaike information criterion)](#aic-akaike-information-criterion)
  - [BIC (Bayesian information criterion)](#bic-bayesian-information-criterion)
  - [A Good Tip](#a-good-tip)
  - [Accuracy Metric in Regression Problem](#accuracy-metric-in-regression-problem)

## Abstract
For a regression problem, the output is a continous number from the infinite values in the number world, unlike the classification problem, where the output should belong to either a binary value like [0, 1], or a multiclass output.

In this markdown, we will highlight some of the most common used evaluation metrics, how to calculate them, and when to use them.

## MSE - Mean Squared Error
This is the most common evaluation metric for regression problems. It measures the average squared difference between the predicted and actual values. MSE is sensitive to outliers, so it is not always the best metric to use if the data contains a lot of outliers.

Formula:
```
MSE = Σ(y_i - y_hat_i)^2 / n
```

## RMSE - Root Mean Squared Error
This is the square root of MSE. It has the same units as the target variable, so it is easier to interpret than MSE. RMSE is also less sensitive to outliers than MSE.

Formula:
```
RMSE = √(MSE)
```

## Mean absolute error (MAE)
This metric measures the average absolute difference between the predicted and actual values. MAE is less sensitive to outliers than MSE, but it is not as easy to interpret as RMSE.

Formula:
```
MAE = Σ|y_i - y_hat_i| / n
```

## R-squared (R^2)
This metric measures the proportion of variance in the target variable that is explained by the model. R^2 can range from 0 to 1, where 0 means that the model does not explain any variance in the target variable and 1 means that the model perfectly explains all of the variance in the target variable.

Formula:
```
R^2 = 1 - Σ(y_i - y_hat_i)^2 / Σ(y_i - y_bar)^2
    = 1 - RSS/TSS
```
Where:
- RSS: Sum of squares of residuals.
- TSS: Total sum of squares.

## Adjusted R^2
This metric is similar to R^2, but it adjusts for the number of features in the model. Adjusted R^2 can be lower than R^2 if the model has too many features.

Formula:
```
Adjusted R^2 = 1 - (n - 1) * MSE / (TSS - MSE)
```

## Mean absolute percentage error (MAPE)
This metric measures the average percentage error between the predicted and actual values. MAPE is expressed as a percentage, so it is easy to understand and interpret. However, MAPE is sensitive to outliers, so it is not always the best metric to use.

Formula:
```
MAPE = Σ|(y_i - y_hat_i) / y_i| * 100 / n
```

## Root mean squared logarithmic error (RMSLE)
This metric is similar to RMSE, but it takes into account the fact that the target variable is often skewed. RMSLE is less sensitive to outliers than RMSE, and it is more appropriate for predicting skewed target variables.

Formula:
```
RMSLE = √(Σ(log(y_i + 1) - log(y_hat_i + 1))^2 / n)
```

## Median absolute error (MedAE)
This metric is similar to MAE, but it uses the median instead of the mean. MedAE is less sensitive to outliers than MAE, and it is more robust to changes in the distribution of the target variable.

Formula:
```
MedAE = median(|y_i - y_hat_i|)
```

## Explained variance score (EVS)
This metric measures the proportion of variance in the target variable that is explained by the model. EVS is similar to R^2, but it is not affected by the number of features in the model.

Formula:
```
EVS = 1 - (TSS - RSS) / TSS
```
Note: It can be misleading if the target variable is not normally distributed. Additionally, EVS can be sensitive to outliers.

## AIC (Akaike information criterion)
This metric measures the information loss associated with a model. AIC is a penalized likelihood metric, which means that it penalizes models with more parameters. AIC can be used to compare different models and select the model with the best trade-off between goodness of fit and complexity.

Formula:
```
AIC = 2 * K - 2 * log(L)
```

where:
- K is the number of parameters in the model
- L is the log-likelihood of the model

The log-likelihood of a model is a measure of how well the model fits the data. It is calculated by taking the natural logarithm of the likelihood of the model. The likelihood of a model is a probability distribution that describes how likely the observed data is under the assumption that the model is correct.
- The formula for the log-likelihood function is:
  - log(L) = Σ(ln(p(x_i | θ))) </br>
    where:</br>
        L is the log-likelihood function</br>
        p(x_i | θ) is the probability of observing the data point x_i under the assumption that the model parameters are θ</br>
        Σ is the sum over all data points
- The log-likelihood function is a logarithmic transformation of the likelihood function, which makes it easier to work with mathematically. The log-likelihood function is also a more stable measure of fit than the likelihood function, because it is less sensitive to small changes in the data.
- A higher log-likelihood value indicates a better-fitting model. This is because a higher log-likelihood value means that the model is more likely to have generated the observed data.

The penalty term in AIC is 2 * K. This penalty term penalizes models with more parameters. The reason for this is that models with more parameters are more likely to overfit the data. Overfitting occurs when a model learns the noise in the data instead of the underlying relationships between the variables.

A lower AIC value indicates a better-fitting model. This is because a lower AIC value means that the model has a higher log-likelihood and a smaller penalty term.

For example, let's say that we have two models that we are trying to compare. The first model has 2 parameters, and the second model has 3 parameters. The log-likelihood of the first model is 100, and the log-likelihood of the second model is 90. The AIC of the first model is 40, and the AIC of the second model is 50.

In this case, the first model would be considered to be a better-fitting model because it has a lower AIC value. This is because the first model has a higher log-likelihood and a smaller penalty term.

AIC is a useful metric for evaluating the fit of a statistical model to a set of data. It is a simple metric to understand and interpret, and it can be used to compare models with different numbers of parameters.

## BIC (Bayesian information criterion)
This metric is similar to AIC, but it uses a different penalty term. BIC is also a penalized likelihood metric, but it penalizes models with more parameters more heavily than AIC. BIC can be used to compare different models and select the model with the best trade-off between goodness of fit and complexity.

Formula:
```
BIC = K * log(n) - 2 * log(L)
```

## A Good Tip
The best evaluation metric to use for a regression problem depends on the specific problem and the desired outcome. For example, if the goal is to minimize the error, then MSE or RMSE might be the best metrics to use. If the goal is to understand the relationship between the features and the target variable, then R^2 or adjusted R^2 might be the best metrics to use.

## Accuracy Metric in Regression Problem
There is no accuracy metric for a regression problem, although the business always ask for a accuracy metric to evaulate the model that a data science build.

One of the best approaches, is to define a threshould, so if the output predicted lies between this margain of +- threshould, then we can classify this prediction to be a 1, otherwise it is classified to be a zero.

Advanced estimation to define the acceptable margain, is that, it could depend on other features, depending on the use case we have, and its related features.
