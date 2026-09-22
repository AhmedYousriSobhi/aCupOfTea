# Question - Machine Learning Classifier

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