# solution.ipynb

<div class="code-file">

Notebook from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/problems/interview-assessment-problems/question-machine-learning-classifier/solution.ipynb)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/problems/interview-assessment-problems/question-machine-learning-classifier/solution.ipynb)  ·  [Open in Colab](https://colab.research.google.com/github/AhmedYousriSobhi/aCupOfTea/blob/main/problems/interview-assessment-problems/question-machine-learning-classifier/solution.ipynb)

</div>


## Question

Implement a function, identify_customers, which will build two classifier models based on financial data. The identify_customers functions accepts two arguments:
- data_train - a Pandas DataFrame consisting of a binary column 'label' (1 means that the client subscribed to a term deposite, 0 otherwise), three integer columns describing the customer, including their age, account (account balance), and duration (time of being a bank customer) and 17 binary columns (with 'yes' and 'no' values) that also describe the customers.
- data_test - a Pandas DataFrame with the same structure as data_train.

In the identify_customers function, you should perform the following steps:
1. Preprate the 17 binary variables in data_train and data_test by replacing 'yes' with 1, and 'no' with 0. Retaion the rest of the variables without any changes. After this step, you will have two new data frames 'onehot_train' and 'onehot_test'.
2. Find the proportion (prep) of clients that have subscribed to a term deposit in onehot_train (use the 'label' variable) and round the value to 3 decimal places. This will be necessary to set weights in the classifier models.
3. build a LogisticRegression Classifier on onehot_train. Set the parameters: class_weight={0:prep, 1:1-prep}, random_state=0, max_inter=50.
4. Build a RandomForest Classifier on onehot_train. Set the parameters: max_depth=10, random_state=0, n_estimators=30, class_weight={0:prep, 1:1-prep}.
5. Do a prediction on onehot_test.

After these steps you should return, in identify_customers, a dictionary with the following keys:
- onehot_train - data_train DataFrame after replacing 'yes' and 'no' values with 1 and 0 (without 'label' column).
- onehot_test - data_test DataFrame after replacing 'yes' and 'no' values with 1 and 0 (without 'label' column).
- prep - propotion from point 2, above.
- negative_impact - list of column names which reduce the probability of subscribing term deposit (when this variables increases). Use properities of the LogisticRegression classifier to obtain this point.
- feature_importance - list of tuples with the five most important varialbes based on feature importances from the RandomForest classifier in the form (column names, feature_importance).
- lr_recall - tupple of recall scores from onehot_train and onehot_test after training with the LogisticRegression Classifier.
- rf_recall - tupple of recall scores from onehot_train and onehot_test after training with the RandomForest Classifier.
- lr_obs - the probabilty of varialbes from LogisticRegression Classifier.
- rf_obs - the probabilty of varialbes from RandomForest Classifier.

```python
!pip install scikit-learn
```

```output
Collecting scikit-learn
  Downloading scikit_learn-1.3.0-cp311-cp311-win_amd64.whl (9.2 MB)
     ---------------------------------------- 9.2/9.2 MB 6.8 MB/s eta 0:00:00
Requirement already satisfied: numpy>=1.17.3 in c:\users\fawzyjr\appdata\local\programs\python\python311\lib\site-packages (from scikit-learn) (1.25.1)
Collecting scipy>=1.5.0
  Downloading scipy-1.11.1-cp311-cp311-win_amd64.whl (44.0 MB)
     ---------------------------------------- 44.0/44.0 MB 5.9 MB/s eta 0:00:00
Collecting joblib>=1.1.1
  Downloading joblib-1.3.1-py3-none-any.whl (301 kB)
     -------------------------------------- 302.0/302.0 kB 3.1 MB/s eta 0:00:00
Collecting threadpoolctl>=2.0.0
  Downloading threadpoolctl-3.2.0-py3-none-any.whl (15 kB)
Installing collected packages: threadpoolctl, scipy, joblib, scikit-learn
Successfully installed joblib-1.3.1 scikit-learn-1.3.0 scipy-1.11.1 threadpoolctl-3.2.0
```

```output

[notice] A new release of pip available: 22.3.1 -> 23.2.1
[notice] To update, run: python.exe -m pip install --upgrade pip
```

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import sklearn.metrics as metrics
import pandas as pd
import numpy as np
```

```python
data_train = pd.read_csv('data/data_train.csv')
data_test = pd.read_csv('data/data_test.csv')
```

```python
data_train.head()
```

<div class="nb-output">

<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>age</th>
      <th>account</th>
      <th>if_marital</th>
      <th>if_default</th>
      <th>if_housing</th>
      <th>if_loan</th>
      <th>if_active_selling</th>
      <th>duration</th>
      <th>label</th>
      <th>occupation_cleaner</th>
      <th>...</th>
      <th>occupation_own-business</th>
      <th>occupation_production</th>
      <th>occupation_retired</th>
      <th>occupation_services</th>
      <th>occupation_student</th>
      <th>occupation_technician</th>
      <th>occupation_unemployed</th>
      <th>education_primary</th>
      <th>education_secondary</th>
      <th>education_unknown</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>41</td>
      <td>2408</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>122</td>
      <td>0</td>
      <td>no</td>
      <td>...</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
    </tr>
    <tr>
      <th>1</th>
      <td>59</td>
      <td>4007</td>
      <td>yes</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>157</td>
      <td>0</td>
      <td>no</td>
      <td>...</td>
      <td>no</td>
      <td>no</td>
      <td>yes</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>yes</td>
      <td>no</td>
      <td>no</td>
    </tr>
    <tr>
      <th>2</th>
      <td>35</td>
      <td>482</td>
      <td>yes</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>129</td>
      <td>0</td>
      <td>no</td>
      <td>...</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
    </tr>
    <tr>
      <th>3</th>
      <td>49</td>
      <td>0</td>
      <td>yes</td>
      <td>no</td>
      <td>yes</td>
      <td>no</td>
      <td>no</td>
      <td>772</td>
      <td>0</td>
      <td>no</td>
      <td>...</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>yes</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
    </tr>
    <tr>
      <th>4</th>
      <td>23</td>
      <td>834</td>
      <td>no</td>
      <td>no</td>
      <td>yes</td>
      <td>no</td>
      <td>no</td>
      <td>283</td>
      <td>0</td>
      <td>no</td>
      <td>...</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>yes</td>
      <td>no</td>
      <td>no</td>
      <td>no</td>
      <td>yes</td>
      <td>no</td>
    </tr>
  </tbody>
</table>
<p>5 rows × 21 columns</p>
</div>

</div>

```python

# you can access datasets by calling:
# data_train = pd.read_csv("data/data_train.csv")
# data_testa = pd.read_csv("data/data_test.csv")

def one_hot_encode(data:pd.DataFrame, mapper:dict)->pd.DataFrame:
    """
        Used to convert categorical binary data to one hot encode values.

        PARAMETERS
            data: pandas dataframe, input data
            mapper: dictionary, to convert from categorical to numerical

        RETURN
            pandas dataframe with one-hot-encoded
    """

    # create a copy of input data
    df = data.copy()

    # Select all categorical values
    categorical_cols = df.select_dtypes('object').columns.tolist()

    # One hot encode categorical values
    df[categorical_cols] = df[categorical_cols].replace(mapper)

    # return modified dataframe
    return df

def get_proba(clf, data):
    
    # Predict probabilities on the test set
    probs = clf.predict_proba(data)

    # If it's a binary classification problem, use the probabilities for class 1 (positive class)
    if len(probs.shape) == 1:
        probabilities = probs
    else:
        probabilities = probs[:, 1]

    # Create a DataFrame with the test indices and corresponding probabilities
    result_df = pd.DataFrame({'index': data.index, 'probability': probabilities})

    # Sort the DataFrame by probabilities in descending order
    sorted_indices = result_df.sort_values(by='probability', ascending=False)['index']

    return sorted_indices


def identify_customers(data_train, data_test):
    
    # Create a copy of input dataframe
    data_train_cp, data_test_cp = data_train.copy(), data_test.copy()

    # Step_0:Define varaibles
    random_seed = 0
    target_col = 'label'

    # Step_1: One hot encode dataframes
    # Define the mapper for one hot encoder
    mapper = {'no':0, 'yes':1}

    # One hot encode the dataframes
    onehot_train = one_hot_encode(data_train_cp, mapper)
    onehot_test = one_hot_encode(data_test_cp, mapper)

    # Step_2: Calculate the prop factor
    prop = round(onehot_train[onehot_train.label==1].shape[0]/onehot_train.shape[0], 3)

    # Define the input, target
    x_train, y_train = onehot_train.drop(target_col, axis=1), onehot_train[target_col]
    x_test, y_test = onehot_test.drop(target_col, axis=1), onehot_test[target_col]

    # Step_3: Logistic Regression
    lr = LogisticRegression(
        class_weight={
            0:prop,
            1:1-prop
        },
        random_state=random_seed,
        max_iter=50
        )

    lr.fit(x_train, y_train)

    lr_pred_train = lr.predict(x_train)
    lr_pred_test = lr.predict(x_test)

    # Step_4: Random Forest Classifier
    rf = RandomForestClassifier(
        max_depth=10,
        random_state=random_seed,
        n_estimators=30,
        class_weight={
            0:prop,
            1:1-prop
        },
    )

    rf.fit(x_train, y_train)

    rf_pred_train = rf.predict(x_train)
    rf_pred_test = rf.predict(x_test)

    # calculate negative impact
    # Get the coefficients of the features
    coefficients = lr.coef_[0]

    # Map the coefficients to the column names
    feature_coefficients = dict(zip(x_train.columns, coefficients))

    # Sort the feature coefficients in ascending order of their absolute values
    sorted_features = sorted(feature_coefficients.items(), key=lambda x: abs(x[1]))

    # Get the list of column names that reduce the probability of subscribing to a term
    n = 3
    negative_impact = [feature[0] for feature in sorted_features[:n]]

    # Get the feature importances
    feature_importances = rf.feature_importances_

    # Map the feature importances to the column names
    feature_importance_dict = dict(zip(x_train.columns, feature_importances))

    # Sort the feature importances in descending order
    sorted_features = sorted(feature_importance_dict.items(), key=lambda x: x[1], reverse=True)

    # Get the list of feature names sorted by their importance
    feature_importance = [feature[0] for feature in sorted_features[:5]]

    # Recall for lr
    lr_recall_train = metrics.recall_score(y_train, lr_pred_train)
    lr_recall_test = metrics.recall_score(y_test, lr_pred_test)
    rf_recall_train = metrics.recall_score(y_train, rf_pred_train)
    rf_recall_test = metrics.recall_score(y_test, rf_pred_test)

    # calculate proba_index
    lr_obs = get_proba(lr, x_test)
    rf_obs = get_proba(rf, x_test)
            
    return {
        'onehot_train': onehot_train,
        'onehot_test': onehot_test,
        'prop': prop,
        'negative_impact': negative_impact,
        'feature_importance': feature_importance,
        'lr_recall': (lr_recall_train, lr_recall_test),
        'rf_recall': (rf_recall_train, rf_recall_train),
        'lr_obs': lr_obs,
        'rf_obs': rf_obs,
    }
```
