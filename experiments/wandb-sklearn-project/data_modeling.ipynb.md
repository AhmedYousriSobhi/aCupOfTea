# data_modeling.ipynb

<div class="code-file">

Notebook from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/experiments/wandb-sklearn-project/data_modeling.ipynb)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/experiments/wandb-sklearn-project/data_modeling.ipynb)  ·  [Open in Colab](https://colab.research.google.com/github/AhmedYousriSobhi/aCupOfTea/blob/main/experiments/wandb-sklearn-project/data_modeling.ipynb)

</div>


Author: Ahmed Sobhi

Creation_date: 3th Aug 2023

Objective: Data Modeling Experimental using W&B Tools

# Importing required libararies and packages

```python
import warnings
warnings.filterwarnings('ignore')

import os

import pandas as pd
import numpy as np

# Used for visulization
import matplotlib.pyplot as plt

# For iteration visulization purpose
from tqdm import tqdm

# Import defined tools script
import sys

# adding tools script into system path
# sys.path.insert(0, '')
from tools import featureengineering, datapreprocessing, pipelinetransformers

# Used for datasplitting, modeling
from scipy import stats
from sklearn.impute import SimpleImputer
from sklearn.metrics import confusion_matrix, accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer, make_column_transformer
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier
from sklearn.model_selection import GridSearchCV

# To save the model locally
import joblib

# Import wandb
import wandb
```

# Data loading

```python
# Loading raw dataset
df_raw = pd.read_csv('data/data.csv')

df_raw.head()
```

<div class="nb-output">

<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>country</th>
      <th>article</th>
      <th>sales</th>
      <th>regular_price</th>
      <th>current_price</th>
      <th>ratio</th>
      <th>retailweek</th>
      <th>promo1</th>
      <th>promo2</th>
      <th>customer_id</th>
      <th>...</th>
      <th>style</th>
      <th>sizes</th>
      <th>gender</th>
      <th>rgb_r_main_col</th>
      <th>rgb_g_main_col</th>
      <th>rgb_b_main_col</th>
      <th>rgb_r_sec_col</th>
      <th>rgb_g_sec_col</th>
      <th>rgb_b_sec_col</th>
      <th>label</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Germany</td>
      <td>YN8639</td>
      <td>28</td>
      <td>5.95</td>
      <td>3.95</td>
      <td>0.663866</td>
      <td>2016-03-27</td>
      <td>0</td>
      <td>0</td>
      <td>1003.0</td>
      <td>...</td>
      <td>slim</td>
      <td>xxs,xs,s,m,l,xl,xxl</td>
      <td>women</td>
      <td>205</td>
      <td>104</td>
      <td>57</td>
      <td>255</td>
      <td>187</td>
      <td>255</td>
      <td>0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Germany</td>
      <td>YN8639</td>
      <td>28</td>
      <td>5.95</td>
      <td>3.95</td>
      <td>0.663866</td>
      <td>2016-03-27</td>
      <td>0</td>
      <td>0</td>
      <td>1003.0</td>
      <td>...</td>
      <td>regular</td>
      <td>xxs,xs,s,m,l,xl,xxl</td>
      <td>women</td>
      <td>188</td>
      <td>238</td>
      <td>104</td>
      <td>255</td>
      <td>187</td>
      <td>255</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Germany</td>
      <td>YN8639</td>
      <td>28</td>
      <td>5.95</td>
      <td>3.95</td>
      <td>0.663866</td>
      <td>2016-03-27</td>
      <td>0</td>
      <td>0</td>
      <td>1003.0</td>
      <td>...</td>
      <td>regular</td>
      <td>xxs,xs,s,m,l,xl,xxl</td>
      <td>women</td>
      <td>205</td>
      <td>173</td>
      <td>0</td>
      <td>255</td>
      <td>187</td>
      <td>255</td>
      <td>0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>Germany</td>
      <td>YN8639</td>
      <td>28</td>
      <td>5.95</td>
      <td>3.95</td>
      <td>0.663866</td>
      <td>2016-03-27</td>
      <td>0</td>
      <td>0</td>
      <td>1003.0</td>
      <td>...</td>
      <td>regular</td>
      <td>xxs,xs,s,m,l,xl,xxl</td>
      <td>kids</td>
      <td>205</td>
      <td>140</td>
      <td>149</td>
      <td>164</td>
      <td>211</td>
      <td>238</td>
      <td>0</td>
    </tr>
    <tr>
      <th>4</th>
      <td>Germany</td>
      <td>YN8639</td>
      <td>28</td>
      <td>5.95</td>
      <td>3.95</td>
      <td>0.663866</td>
      <td>2016-03-27</td>
      <td>0</td>
      <td>0</td>
      <td>1003.0</td>
      <td>...</td>
      <td>regular</td>
      <td>xxs,xs,s,m,l,xl,xxl</td>
      <td>women</td>
      <td>138</td>
      <td>43</td>
      <td>226</td>
      <td>164</td>
      <td>211</td>
      <td>238</td>
      <td>0</td>
    </tr>
  </tbody>
</table>
<p>5 rows × 24 columns</p>
</div>

</div>

```python
df_raw.describe().T
```

<div class="nb-output">

<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>count</th>
      <th>mean</th>
      <th>std</th>
      <th>min</th>
      <th>25%</th>
      <th>50%</th>
      <th>75%</th>
      <th>max</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>sales</th>
      <td>9999.0</td>
      <td>57.820882</td>
      <td>89.773730</td>
      <td>1.000000</td>
      <td>10.000000</td>
      <td>26.000000</td>
      <td>62.500000</td>
      <td>789.00</td>
    </tr>
    <tr>
      <th>regular_price</th>
      <td>9999.0</td>
      <td>52.311736</td>
      <td>33.547643</td>
      <td>3.950000</td>
      <td>26.450000</td>
      <td>43.950000</td>
      <td>76.950000</td>
      <td>197.95</td>
    </tr>
    <tr>
      <th>current_price</th>
      <td>9999.0</td>
      <td>28.201225</td>
      <td>21.803522</td>
      <td>1.950000</td>
      <td>12.450000</td>
      <td>22.950000</td>
      <td>36.950000</td>
      <td>140.95</td>
    </tr>
    <tr>
      <th>ratio</th>
      <td>9999.0</td>
      <td>0.545694</td>
      <td>0.191688</td>
      <td>0.298246</td>
      <td>0.354839</td>
      <td>0.532554</td>
      <td>0.694823</td>
      <td>1.00</td>
    </tr>
    <tr>
      <th>promo1</th>
      <td>9999.0</td>
      <td>0.057006</td>
      <td>0.231865</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>1.00</td>
    </tr>
    <tr>
      <th>promo2</th>
      <td>9999.0</td>
      <td>0.006001</td>
      <td>0.077235</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>1.00</td>
    </tr>
    <tr>
      <th>customer_id</th>
      <td>9999.0</td>
      <td>2720.894489</td>
      <td>1941.263157</td>
      <td>3.000000</td>
      <td>1011.500000</td>
      <td>1989.000000</td>
      <td>4618.500000</td>
      <td>5988.00</td>
    </tr>
    <tr>
      <th>cost</th>
      <td>9999.0</td>
      <td>6.516782</td>
      <td>3.915039</td>
      <td>1.290000</td>
      <td>2.290000</td>
      <td>5.200000</td>
      <td>9.600000</td>
      <td>13.29</td>
    </tr>
    <tr>
      <th>rgb_r_main_col</th>
      <td>9999.0</td>
      <td>161.402240</td>
      <td>39.793297</td>
      <td>79.000000</td>
      <td>138.000000</td>
      <td>181.000000</td>
      <td>205.000000</td>
      <td>205.00</td>
    </tr>
    <tr>
      <th>rgb_g_main_col</th>
      <td>9999.0</td>
      <td>139.600260</td>
      <td>63.647856</td>
      <td>26.000000</td>
      <td>104.000000</td>
      <td>148.000000</td>
      <td>181.000000</td>
      <td>238.00</td>
    </tr>
    <tr>
      <th>rgb_b_main_col</th>
      <td>9999.0</td>
      <td>133.499650</td>
      <td>81.156429</td>
      <td>0.000000</td>
      <td>57.000000</td>
      <td>149.000000</td>
      <td>205.000000</td>
      <td>250.00</td>
    </tr>
    <tr>
      <th>rgb_r_sec_col</th>
      <td>9999.0</td>
      <td>207.700270</td>
      <td>35.316550</td>
      <td>164.000000</td>
      <td>164.000000</td>
      <td>205.000000</td>
      <td>255.000000</td>
      <td>255.00</td>
    </tr>
    <tr>
      <th>rgb_g_sec_col</th>
      <td>9999.0</td>
      <td>181.402640</td>
      <td>23.475104</td>
      <td>155.000000</td>
      <td>155.000000</td>
      <td>187.000000</td>
      <td>211.000000</td>
      <td>211.00</td>
    </tr>
    <tr>
      <th>rgb_b_sec_col</th>
      <td>9999.0</td>
      <td>209.905491</td>
      <td>45.307826</td>
      <td>155.000000</td>
      <td>155.000000</td>
      <td>238.000000</td>
      <td>255.000000</td>
      <td>255.00</td>
    </tr>
    <tr>
      <th>label</th>
      <td>9999.0</td>
      <td>0.140614</td>
      <td>0.347640</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>1.00</td>
    </tr>
  </tbody>
</table>
</div>

</div>

# Train Test split

```python
target_col = 'label'
stratify_col = 'country'

# Select features only
df_features = df_raw.drop(target_col, axis=1)

df_y = df_raw[target_col]

x_temp, x_test, y_temp, y_test = train_test_split(
    df_features,
    df_y,
    test_size=0.2,
    random_state=42,
    stratify=df_features[stratify_col]
)

df_temp = pd.concat([x_temp, y_temp], axis=1)

# Apply data preprocessing
df_temp = datapreprocessing.data_preprocess(df_temp)

# Feature engineering
df_temp = featureengineering.feature_engineereing(df_temp)

x_temp = df_temp.drop(target_col, axis=1)
y_temp = df_temp[target_col]

x_train, x_val, y_train, y_val = train_test_split(
    x_temp,
    y_temp,
    test_size=0.2,
    random_state=42,
    stratify=x_temp[stratify_col]
)
```

```python
# Diplay shapes
print('Train set shape:', x_train.shape, y_train.shape)
print('Validation set shape:', x_val.shape, y_val.shape)
print('Test set shape:', x_test.shape, y_test.shape)
```

```output
Train set shape: (5447, 21) (5447,)
Validation set shape: (1362, 21) (1362,)
Test set shape: (2000, 23) (2000,)
```

# Preprocessing and Features Engineering

# Pipeline Steps

```python
# Extract numerical|Categorical features
numeric_features = x_train.select_dtypes('number').columns.tolist()

categorical_features = x_train.select_dtypes('object').columns.tolist()

imputer_numeric = SimpleImputer(strategy='mean')
imputer_categorical = SimpleImputer(strategy='most_frequent')

numeric_transformer = Pipeline(
    [
        ('impute', imputer_numeric),
        ('scaler', StandardScaler())
    ]
)

categorical_transformer = Pipeline(
    [
        ('impute', imputer_categorical),
        ('ohc', OneHotEncoder(handle_unknown='ignore'))
    ]
)

preprocessor = ColumnTransformer(
    [
        ('numericals', numeric_transformer, numeric_features),
        ('Categorical', categorical_transformer, categorical_features)
    ],
    remainder='drop',
    n_jobs=-1
)
```

```python
# # # Testing
# preprocessor.fit(x_train)

# preprocessor.transform(x_train)
```

# Model Pipeline

```python
def train_model(process_pipeline, clf, config):
    "Train a model with given configuration"

    global x_train, y_train, x_val, y_val

    # Start wandb run
    wandb.init(project='sports_store', config=config)

    # Define model
    model = clf(**config)

    # Add to pipeline
    model_pipeline = Pipeline(
        steps=[
            ('col_trans', process_pipeline),
            ('model', model)
        ]
    )

    # Fit the model to training dataset
    model_pipeline.fit(x_train, y_train)
    
    # calculate the accuracy
    pred_train = model_pipeline.predict(x_train)

    pred_val = model_pipeline.predict(x_val)

    acc_train = accuracy_score(y_train, pred_train)
    
    acc_val = accuracy_score(y_val, pred_val)

    conf_matrix_train = confusion_matrix(y_train, pred_train)

    conf_matrix_val = confusion_matrix(y_val, pred_val)
    
    # Log metrices over time to visulaization performance
    wandb.log({
        'train_acc':acc_train,
        'val_acc':acc_val,
        'train_confusion_matrix':conf_matrix_train,
        'val_confusion_matrix':conf_matrix_val
    })

    # Finish wandb
    wandb.finish()
```

```python
wandb.login(anonymous='allow')
```

```output
Failed to detect the name of this notebook, you can set it manually with the WANDB_NOTEBOOK_NAME environment variable to enable code saving.
wandb: Currently logged in as: ahmedyousrisobhi (acupoftea). Use `wandb login --relogin` to force relogin
```

```output
True
```

Try to rerun the following cell, with changing the configuration parameters.

```python
initial_lr = 0.01

config = {
    'objective':'binary:logistic',
    'colsample_bytree':0.5,
    'learning_rate':initial_lr,
    'max_depth':5,
    'min_child_weight':1,
    'n_estimators':1000,
    'subsample':0.99,
    'verbosity':1,
    'n_jobs':-1
    }

train_model(preprocessor, XGBClassifier, config)
```

<div class="nb-output">

Tracking run with wandb version 0.15.8

</div>

<div class="nb-output">

Run data is saved locally in <code>/home/yousri/Workspace/aCupOfTea/generativeAI/evaluation_and_debugging/wandb_sklearnProject/wandb/run-20230803_150849-cd9zv846</code>

</div>

<div class="nb-output">

Syncing run <strong><a href='https://wandb.ai/acupoftea/sports_store/runs/cd9zv846' target="_blank">prime-frog-3</a></strong> to <a href='https://wandb.ai/acupoftea/sports_store' target="_blank">Weights & Biases</a> (<a href='https://wandb.me/run' target="_blank">docs</a>)<br/>

</div>

<div class="nb-output">

View project at <a href='https://wandb.ai/acupoftea/sports_store' target="_blank">https://wandb.ai/acupoftea/sports_store</a>

</div>

<div class="nb-output">

View run at <a href='https://wandb.ai/acupoftea/sports_store/runs/cd9zv846' target="_blank">https://wandb.ai/acupoftea/sports_store/runs/cd9zv846</a>

</div>

<div class="nb-output">

Waiting for W&B process to finish... <strong style="color:green">(success).</strong>

</div>

```output
wandb: WARNING Source type is set to 'repo' but some required information is missing from the environment. A job will not be created from this run. See https://docs.wandb.ai/guides/launch/create-job
```

```output
VBox(children=(Label(value='0.005 MB of 0.011 MB uploaded (0.000 MB deduped)\r'), FloatProgress(value=0.482207…
```

<div class="nb-output">

<div class="wandb-row"><div class="wandb-col"><h3>Run history:</h3><br/><table class="wandb"><tr><td>train_acc</td><td>▁</td></tr><tr><td>val_acc</td><td>▁</td></tr></table><br/></div><div class="wandb-col"><h3>Run summary:</h3><br/><table class="wandb"><tr><td>train_acc</td><td>0.88067</td></tr><tr><td>val_acc</td><td>0.85756</td></tr></table><br/></div></div>

</div>

<div class="nb-output">

View run <strong style="color:#cdcd00">prime-frog-3</strong> at: <a href='https://wandb.ai/acupoftea/sports_store/runs/cd9zv846' target="_blank">https://wandb.ai/acupoftea/sports_store/runs/cd9zv846</a><br/>Synced 5 W&B file(s), 0 media file(s), 0 artifact file(s) and 0 other file(s)

</div>

<div class="nb-output">

Find logs at: <code>./wandb/run-20230803_150849-cd9zv846/logs</code>

</div>

![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/bf290d38-4937-4f8c-9c04-929987ba70d8)



