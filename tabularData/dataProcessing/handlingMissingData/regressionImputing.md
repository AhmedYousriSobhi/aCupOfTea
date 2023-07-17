# Missing Data - Regression Imputing

It is recommened to read __determineMissingValues__ before starting.

## Methods for Handling Missing Values: __Regression Imputing__
From [kaggle notebook](https://www.kaggle.com/code/shashankasubrahmanya/missing-data-imputation-using-regression), the author tried to explain how to use the regression imputing method for missing values.

The Reason for not just imputing the missing values by the __Measure of centeral tendency__, as this would lead to over(under)estimate, which means we add some bias in our estimation.
  
    For example, a person who earns just enough to meet his daily needs might not be comfortable in mentioning his salary, and thus the value for the variable salary would be missing for such a person. However, if we impute it with the mean value of the variable, we are overestimating that person's salary and thus introducing bias in our analysis.

So an interesting method to use is __Regression Imputing__ which we estimate the missing values by Regression using other variables as parameters.

Continuting the __determineMissingValues__ markdown file, we saw that, there were around 5 features with missing values in the diabetes dataset, so we can't just directly use Regression Imputation to impute one of them as the predictors contain missing data themselves.

This is called __Catch-22__ a problematic situation for which the only solution is denied by a circumstance inherent in the problem or by a rule. It was taken from the show-business catch-22 "no work unless you have an agent, no agent unless you've worked Mary Murphy. also : the circumstance or rule that denies a solution."

```python
missing_columns = ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]
```
 
We can avoid this Catch-22 situation by initially imputing all the variables with missing values using some trivial methods like Simple Random Imputation (we impute the missing data with random observed values of the variable) which is later followed by Regression Imputation of each of the variables iteratively.

```python
def random_imputation(df, feature):

    number_missing = df[feature].isnull().sum()
    
    observed_values = df.loc[df[feature].notnull(), feature]
    
    df.loc[df[feature].isnull(), feature + '_imp'] = np.random.choice(observed_values, number_missing, replace = True)
    
    return df
```

Then we apply this function on each of column of the columns which contains missing values.

```python
for feature in missing_columns:
    df[feature + '_imp'] = df[feature]
    df = random_imputation(df, feature)
```

Now we have none missing columns, which will help us use the regression imputing on each target missing column, based on other features.

```python
deter_data = pd.DataFrame(columns = ["Det" + name for name in missing_columns])

for feature in missing_columns:
        
    deter_data["Det" + feature] = df[feature + "_imp"]
    
    parameters = list(set(df.columns) - set(missing_columns) - {feature + '_imp'})
    
    #Create a Linear Regression model to estimate the missing data
    model = linear_model.LinearRegression()
   
    model.fit(X = df[parameters], y = df[feature + '_imp'])
    
    #observe that I preserve the index of the missing data from the original dataframe
    deter_data.loc[df[feature].isnull(), "Det" + feature] = model.predict(df[parameters])[df[feature].isnull()]

    mno.matrix(deter_data, figsize = (20,5))
```
### Disadvantage
A major disadvantage in this method is that we reduce the inherent variability in the imputed variable. In other words, since we substitute the missing data with regression outputs, the predicted values lie along the regression hyperplane where the variable would have actually contained some noise/bias.

Another point:

When we compare both complete data with the incomplete data:
- the complete data has a lesser standard deviation (thus lesser variability) than the incomplete data.
```python
pd.concat([df[["Insulin", "SkinThickness"]], deter_data[["DetInsulin", "DetSkinThickness"]]], axis = 1).describe().T
```

### Conclusion
Regression Imputation might not serve as the best method when a variable is missing majority of it's data, as in case of insulin. In these cases we have to use more powerful approaches as __Maximum Likelihood Imputation__ and __Multple Imputaton__.