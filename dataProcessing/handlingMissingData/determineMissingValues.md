# Missing Data

## Determining Missing Data: __Data Exists but Missing__
From [kaggle notebook](https://www.kaggle.com/code/shashankasubrahmanya/missing-data-imputation-using-regression), the author explained important point regarding determining the Missing Data in a dataset even there were no actual missing values in the data.

The dataset the author used was:
    
    Pima Indians Diabetes dataset is used for our analysis. The objective of the dataset is to diagnostically predict whether or not a patient has diabetes, based on certain diagnostic measurements included in the dataset

|Pregnancies| 	Glucose| 	BloodPressure| 	SkinThickness| 	Insulin|	BMI 	|DiabetesPedigreeFunction 	|Age 	|Outcome|
|---|----|----|----|----|----|----|----|----|   
|6| 	148| 	72| 	35| 	0| 	33.6| 	0.627| 	50| 	1|
|1| 	85| 	66| 	29| 	0| 	26.6| 	0.351| 	31| 	0|
|8| 	183| 	64| 	0| 	0| 	23.3| 	0.672| 	32| 	1|

When you check for any Nans values in the dataset, you will find that all values exists and the total missing values are None.

But some data related to diabetes, five number summary would show that some variables have 0.0 as their minimum value which would be meaningless in their case. Plasma glucose concentration, Diastolic blood pressure, Triceps skinfold thickness, 2-Hour serum insulin and Body mass index cannot be zero.

So for feasibility of the analysis, we replace all these 'missing' data with __nan__, and try to impute them again with more appropriate values.
```
df.loc[df["Glucose"] == 0.0, "Glucose"] = np.NAN
df.loc[df["BloodPressure"] == 0.0, "BloodPressure"] = np.NAN
df.loc[df["SkinThickness"] == 0.0, "SkinThickness"] = np.NAN
df.loc[df["Insulin"] == 0.0, "Insulin"] = np.NAN
df.loc[df["BMI"] == 0.0, "BMI"] = np.NAN

# For better visulizing of missing values in each column
# missingno package is used.
import missingno as mno
mno.matrix(df, figsize = (20, 6))
```

Then starting to impute these missing features by any appropriate method.