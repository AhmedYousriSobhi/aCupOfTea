<!-- related-block -->
<nav class="crumbs" aria-label="Breadcrumb"><a href="#/fields/">Fields</a> / <a href="#/fields/tabular-data/">Tabular Data</a> / <a href="#/fields/tabular-data/data-processing/">Data Processing</a> / <a href="#/fields/tabular-data/data-processing/handling-missing-data/">Handling Missing Data</a></nav>

# Tabular Data - Data Processing - Handling Missing Data - Mean Imputing

<!-- related-block -->
<div class="reading-time">1 min read · Updated 5 Nov 2026</div>


It is recommend to read __determineMissingValues__ before starting.

## Methods for Handling Missing Values: __Mean Imputing__
The Idea here is to get the average value of certain column to fill the missing values with it.

```python
df['A'] = df.A.fillna(df.A.mean())
```

But In case that, the average value is depending on other certain categorical values, So it is recommended to calculate each mean for each unique categorical value

### Step#1: Calculate the average value per categorical feature
```python
# Calculate the average value for feature numeical_col 'A' based on each categorical_col unique value 'B'.
fill_value = (
    df.groupby('B')
    .agg({'A':'mean'})
    # In case, it's required to have integer values only
    .round()
    # Convert the dataframe into dictionary with list values
    .T.to_dict('list')
)

display(fill_value)
```

The output should be like:
```python
{'Apartment': [965.0],
 'Cabin': [688.0],
 'Chalet': [1207.0],
 'Clinic': [1159.0],
 'Duplex': [1127.0],
 'Family House': [228.0],
 'Office': [1121.0],
 'Penthouse': [989.0],
 'Retail': [1023.0],
 'Serviced Apartment': [823.0],
 'Studio': [887.0],
 'Townhouse': [1201.0],
 'Twinhouse': [1151.0],
 'Villa': [1093.0]}
```

### Step#2: Impute the missing values based on that dictionary
```python
df['A'] = (
    df.A
    .fillna(
        df.B.apply(lambda x: fill_value.get(x)[0])
        )
)
```