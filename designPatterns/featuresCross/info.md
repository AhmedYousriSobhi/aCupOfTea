# Design Pattern - #3 - Feature Cross

## Abstract
In Machine Learning, Feature engineering is the process of using domain knowledge to create new features that aid the machine learning process and increase the predictive power of our model. One commonly used feature engineering technique is creting a feature cross.

The Feature Cross design pattern helps the models learn relationships between inputs faster by explicitly making each combination of input values a seperate feature.


## Definition
A feature cross is a synthetic feature formed by concatenating two or more categorical features in order to capture the interaction between them.

## Importants
By joining two features in this way, it is possible to encode nonlinearity into the model, which can allow for predictive abilities beyond what each of the features would have been able to provide individually.

Feature Crossess provide a way to have the ML model learn relationships between the features faster. While in complex models like neaural networks and trees can learn feature crosses on their own, using feature crossess explicitly can allow us to get away with training just a linear model. Consequently, feature crosses can speed up model training (less expensive) and reduce model complexity (less data is needed).

## Credits
- This Previous illustration is summerized from Chapter-2, From Book: __Machine Learning Design Patterns - Solutions to Common challenges in Data Preparation, Model Building, and MLOps__