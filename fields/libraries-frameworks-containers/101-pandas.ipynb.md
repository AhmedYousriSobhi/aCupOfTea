# 101-pandas.ipynb

<div class="code-file">

Notebook from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/libraries-frameworks-containers/101-pandas.ipynb)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/fields/libraries-frameworks-containers/101-pandas.ipynb)  ·  [Open in Colab](https://colab.research.google.com/github/AhmedYousriSobhi/aCupOfTea/blob/main/fields/libraries-frameworks-containers/101-pandas.ipynb)

</div>


```python
import pandas as pd
import numpy as np
```

```python
# Creating a dictionary with different data types
data = {
    'int_column': [1, 2, 3, 4],
    'float_column': [1.5, 2.5, 3.5, 4.5],
    'str_column': ['a', 'b', 'c', 'd'],
    'bool_column': [True, False, True, False],
    'date_column': pd.date_range('2023-01-01', periods=4),
    'category_column': pd.Categorical(['x', 'y', 'z', 'x']),
    'object_column': [object(), object(), object(), object()],
    'nullable_column': [1.5, np.nan, 3.5, 4.5]
}

# Creating the DataFrame
df = pd.DataFrame(data)

# Displaying the DataFrame
df.head()
```

<div class="nb-output">

<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>int_column</th>
      <th>float_column</th>
      <th>str_column</th>
      <th>bool_column</th>
      <th>date_column</th>
      <th>category_column</th>
      <th>object_column</th>
      <th>nullable_column</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1</td>
      <td>1.5</td>
      <td>a</td>
      <td>True</td>
      <td>2023-01-01</td>
      <td>x</td>
      <td>&lt;object object at 0x7f124fba8b20&gt;</td>
      <td>1.5</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2</td>
      <td>2.5</td>
      <td>b</td>
      <td>False</td>
      <td>2023-01-02</td>
      <td>y</td>
      <td>&lt;object object at 0x7f124fba8af0&gt;</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>2</th>
      <td>3</td>
      <td>3.5</td>
      <td>c</td>
      <td>True</td>
      <td>2023-01-03</td>
      <td>z</td>
      <td>&lt;object object at 0x7f124fba8b30&gt;</td>
      <td>3.5</td>
    </tr>
    <tr>
      <th>3</th>
      <td>4</td>
      <td>4.5</td>
      <td>d</td>
      <td>False</td>
      <td>2023-01-04</td>
      <td>x</td>
      <td>&lt;object object at 0x7f124fba8ac0&gt;</td>
      <td>4.5</td>
    </tr>
  </tbody>
</table>
</div>

</div>

```python
df.to_csv('dummy_data.csv', index=False)
```

```python
df.info()
```

```output
<class 'pandas.core.frame.DataFrame'>
RangeIndex: 4 entries, 0 to 3
Data columns (total 8 columns):
 #   Column           Non-Null Count  Dtype         
---  ------           --------------  -----         
 0   int_column       4 non-null      int64         
 1   float_column     4 non-null      float64       
 2   str_column       4 non-null      object        
 3   bool_column      4 non-null      bool          
 4   date_column      4 non-null      datetime64[ns]
 5   category_column  4 non-null      category      
 6   object_column    4 non-null      object        
 7   nullable_column  3 non-null      float64       
dtypes: bool(1), category(1), datetime64[ns](1), float64(2), int64(1), object(2)
memory usage: 464.0+ bytes
```

```python
import numpy as np

# Creating a DataFrame from a NumPy array
data = np.array([[1, 'A'], [2, 'B'], [3, 'C']])
df = pd.DataFrame(data, columns=['Column1', 'Column2'])
df
```

<div class="nb-output">

<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Column1</th>
      <th>Column2</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1</td>
      <td>A</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2</td>
      <td>B</td>
    </tr>
    <tr>
      <th>2</th>
      <td>3</td>
      <td>C</td>
    </tr>
  </tbody>
</table>
</div>

</div>

```python
# Creating a DataFrame from pandas Series
series1 = pd.Series([1, 2, 3])
series2 = pd.Series(['A', 'B', 'C'])
df = pd.DataFrame({'Column1': series1, 'Column2': series2})
df
```

<div class="nb-output">

<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Column1</th>
      <th>Column2</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1</td>
      <td>A</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2</td>
      <td>B</td>
    </tr>
    <tr>
      <th>2</th>
      <td>3</td>
      <td>C</td>
    </tr>
  </tbody>
</table>
</div>

</div>

```python
# Creating a DataFrame from a list of dictionaries
data = [{'Column1': 1, 'Column2': 'A'},
        {'Column1': 2, 'Column2': 'B'},
        {'Column1': 3, 'Column2': 'C'}]
df = pd.DataFrame(data)
df
```

<div class="nb-output">

<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Column1</th>
      <th>Column2</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1</td>
      <td>A</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2</td>
      <td>B</td>
    </tr>
    <tr>
      <th>2</th>
      <td>3</td>
      <td>C</td>
    </tr>
  </tbody>
</table>
</div>

</div>

```python
# Creating a DataFrame from a dictionary
data = {'Column1': [1, 2, 3], 'Column2': ['A', 'B', 'C']}
df = pd.DataFrame.from_dict(data)
df
```

<div class="nb-output">

<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Column1</th>
      <th>Column2</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1</td>
      <td>A</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2</td>
      <td>B</td>
    </tr>
    <tr>
      <th>2</th>
      <td>3</td>
      <td>C</td>
    </tr>
  </tbody>
</table>
</div>

</div>

```python
# Creating a DataFrame from a list of tuples
data = [(1, 'A'), (2, 'B'), (3, 'C')]
df = pd.DataFrame(data, columns=['Column1', 'Column2'])
df
```

<div class="nb-output">

<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Column1</th>
      <th>Column2</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1</td>
      <td>A</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2</td>
      <td>B</td>
    </tr>
    <tr>
      <th>2</th>
      <td>3</td>
      <td>C</td>
    </tr>
  </tbody>
</table>
</div>

</div>

```python
pd.DataFrame(columns=['Column1', 'Column2'])
```

<div class="nb-output">

<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Column1</th>
      <th>Column2</th>
    </tr>
  </thead>
  <tbody>
  </tbody>
</table>
</div>

</div>

```python
# Creating a DataFrame from a 2D NumPy array
data = np.array([[1, 2, 3], [4, 5, 6]])
df = pd.DataFrame(data, columns=['A', 'B', 'C'])
df
```

<div class="nb-output">

<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>A</th>
      <th>B</th>
      <th>C</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1</td>
      <td>2</td>
      <td>3</td>
    </tr>
    <tr>
      <th>1</th>
      <td>4</td>
      <td>5</td>
      <td>6</td>
    </tr>
  </tbody>
</table>
</div>

</div>

```python
data = [(1, 'A'), (2, 'B'), (3, 'C')]
df = pd.DataFrame(data, columns=['Column1', 'Column2'])
df
```

<div class="nb-output">

<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Column1</th>
      <th>Column2</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1</td>
      <td>A</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2</td>
      <td>B</td>
    </tr>
    <tr>
      <th>2</th>
      <td>3</td>
      <td>C</td>
    </tr>
  </tbody>
</table>
</div>

</div>
