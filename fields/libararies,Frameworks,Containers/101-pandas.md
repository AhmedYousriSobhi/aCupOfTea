# 101 - Pandas
# Table of Content
- [101 - Pandas](#101---pandas)
- [Table of Content](#table-of-content)
- [Pandas Basics](#pandas-basics)
  - [Concepts and Definitions](#concepts-and-definitions)
    - [DataFrame](#dataframe)
  - [Setting Display Options](#setting-display-options)
  - [Methods to Create a DataFrame](#methods-to-create-a-dataframe)
    - [from Lists or Arrays](#from-lists-or-arrays)
    - [from List of Dictionaries](#from-list-of-dictionaries)
    - [from a Numpy Array](#from-a-numpy-array)
    - [from a Series or Dictionary of Series](#from-a-series-or-dictionary-of-series)
    - [from a List of Tuples](#from-a-list-of-tuples)
  - [Reading a CSV file](#reading-a-csv-file)
    - [To Read Data from CSV File](#to-read-data-from-csv-file)
    - [To Read CSV File from URL](#to-read-csv-file-from-url)
    - [pd.read\_csv Method](#pdread_csv-method)
    - [Assign Operations while reading a CSV File](#assign-operations-while-reading-a-csv-file)
  - [Saving DataFrame as CSV File](#saving-dataframe-as-csv-file)
  - [Data Exploring: Retrieving rows from a dataframe](#data-exploring-retrieving-rows-from-a-dataframe)
  - [Data Exploring: DataFrame Schema](#data-exploring-dataframe-schema)
- [Reference](#reference)

# Pandas Basics
## Concepts and Definitions
### DataFrame
A DataFrame is a two-dimensional, size-mutable, and potentially heterogeneous tabular data structure.

Key features of a DataFrame:
|Feature|Description|
|-|-|
Tabular Data Structure| It represents data in a table format with rows and columns, much like a spreadsheet or SQL table.
Two-Dimensional| Data is arranged in rows and columns. Each row typically represents an observation or an individual data point, while each column represents a different variable or feature.
Size-Mutable| The DataFrame object's size can be modified after creation, meaning rows and columns can be added, removed, or modified.
Heterogeneous Data Types| Unlike arrays or lists in Python, a DataFrame can contain different data types (e.g., integers, floats, strings, etc.) within the same DataFrame.
Labels and Indexing| Each row and column in a DataFrame has a label or index associated with it, allowing for easy data retrieval, manipulation, and alignment.

The pandas DataFrame is a fundamental data structure used extensively for data cleaning, data analysis, manipulation, transformation, and computation in various fields, including data science, machine learning, finance, and more.

Creating a DataFrame usually involves importing the pandas library and constructing it from various data sources, such as lists, dictionaries, NumPy arrays, or reading data from CSV files, databases, Excel files, etc. Pandas provides a wide range of functionalities to handle, analyze, and process data stored in DataFrames efficiently.

## Setting Display Options
When exploring the dataframe, it will be displayed like a table with rows and columns. By default pandas displays a default number of rows=15 and columns=15, so some times our data are much bigger, so the  inbetween rows and columns will be trimmed from the display.

In case you need to fully visualize a specific number of rows and columns, we can do that by setting the options for that!:
```python
# we can set numbers for how many rows and columns will be displayed
pd.set_option('display.min_rows', 10) #default will be 10 
pd.set_option('display.max_columns', 20)
```

Refer to pandas documents to know more about [options and settings](https://pandas.pydata.org/docs/user_guide/options.html)

## Methods to Create a DataFrame
In pandas there are various methods to create a dataframe depending on the shape of the data you have.

### from Lists or Arrays
```python
# Creating a DataFrame from lists
data = {'Column1': [1, 2, 3], 'Column2': ['A', 'B', 'C']}
df = pd.DataFrame(data)

# Output:
#   Column1	Column2
# 0	1	A
# 1	2	B
# 2	3	C
```
### from List of Dictionaries
```python
# Creating a DataFrame from a list of dictionaries
data = [{'Column1': 1, 'Column2': 'A'},
        {'Column1': 2, 'Column2': 'B'},
        {'Column1': 3, 'Column2': 'C'}]
df = pd.DataFrame(data)

# Output:
#   Column1	Column2
# 0	1	A
# 1	2	B
# 2	3	C
```
### from a Numpy Array
```python
import numpy as np

# Creating a DataFrame from a NumPy array
data = np.array([[1, 'A'], [2, 'B'], [3, 'C']])
df = pd.DataFrame(data, columns=['Column1', 'Column2'])

# Output:
#   Column1	Column2
# 0	1	A
# 1	2	B
# 2	3	C
```
### from a Series or Dictionary of Series
```python
# Creating a DataFrame from pandas Series
series1 = pd.Series([1, 2, 3])
series2 = pd.Series(['A', 'B', 'C'])
df = pd.DataFrame({'Column1': series1, 'Column2': series2})

# Output:
#   Column1	Column2
# 0	1	A
# 1	2	B
# 2	3	C
```
### from a List of Tuples
```python
# Creating a DataFrame from a list of tuples
data = [(1, 'A'), (2, 'B'), (3, 'C')]
df = pd.DataFrame(data, columns=['Column1', 'Column2'])

# Output:
#   Column1	Column2
# 0	1	A
# 1	2	B
# 2	3	C
```

## Reading a CSV file
As a Data Scientist, most of our works depends on data, these data are mostly stored as a CSV "Comma Seperated Values" files. The data are called a tabular data as they are have a tabular structure represents a data in a table format with raw and columns. In most common practice, we usually call the data in CSV a **DataFrame**.

### To Read Data from CSV File
```python
# Importing pandas libarary
import pandas as pd

# Load the data into a varaible called df "dataframe"
df = pd.read_csv('data.csv')
```
### To Read CSV File from URL
```python
url = "https://Some.url-to/file.csv"
df_url = pd.read_csv(url)
```
### pd.read_csv Method
According to the [documentation](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html), there are multiple provided parameters regarding the reading of the CSV file which pandas support. Let's talk about the most common used ones.

|Paramter|Details|
|-|-|
File Path or URL| Provide the file path or URL correctly as the first argument. This can be a local file path or a URL pointing to the CSV file.
Header| Specify whether the CSV file contains a header row. Use the **header** parameter (default is infer) to indicate whether the first row should be used as column names (header=0) or not (header=None).
Index Column| Define which column(s) to use as the DataFrame index. Use the **index_col** parameter to specify the column number or name to set as the index. For multiple indices, pass a list of column names/numbers.
Specify Columns| Use the **usecols** parameter to select specific columns from the CSV file. This can be a list of column names or indices to include in the DataFrame.
Data Types| Use the **dtype** parameter to specify the data types of columns explicitly. This can be a dictionary where keys are column names and values are the desired data types.
Parsing Dates| If the CSV contains date/time data, use the **parse_dates** parameter to specify which columns to parse as dates. Pass either a list of column names or indices.
Missing Values Handling| Use the **na_values** parameter to define the values considered as missing (NaN) during parsing. It can be a string, list, or dictionary of columns and their respective missing values.
Skip Rows| To skip initial rows in the CSV file (e.g., for skipping headers or metadata), use the **skiprows** parameter.
Handling Quotes| If the CSV file uses quotes to enclose fields, use the **quotechar** parameter to specify the quote character.
Chunking and Memory Optimization| For large datasets, consider using **chunksize** to read the file in smaller chunks, allowing for efficient memory usage when processing large files.
Encoding| Use the **encoding** parameter to specify the character encoding of the CSV file, especially if it's not in UTF-8 format (encoding='utf-8').
Custom Delimiter| Use the **delimiter** or **sep** parameter to specify a custom delimiter if the CSV file is not comma-separated (e.g., tab-separated: delimiter='\t').

```python
import pandas as pd

# Reading CSV file with specific options
data = pd.read_csv('file.csv', 
                   header=0,
                   index_col='ID',
                   usecols=['ID', 'Name', 'Age'],
                   dtype={'ID': int, 'Age': float},
                   parse_dates=['Date'],
                   na_values={'Age': -1},
                   encoding='utf-8')
```
### Assign Operations while reading a CSV File
In some cases, during the reading process, we need to perform an operation on a specific column in our data, like for example; let's assume we have a datetime column (which values represent dates/timestamps), these values are by default stored as an **object** (Strings) datatype, so we need to convert them to the correct datatype again.

```python
# Using pandas method .assign, to apply a certain function to each raw of a column.
# It takes a lambda expression to apply a certain function on the target column.
df = pd.read_csv('data.csv').assign(date_col = lambda x: pd.to_datetime(x.date_col))
```
Let's assume another case, where we want to rename some columns to a different naming:
```python
# Using pandas method .rename, to change the name of columns by giving a dictionary to where the keys are the original column name, and the values are the target new names.
df = pd.read_csv('data.csv').rename(columns={'data_col':'Date'})
```

Now, let's warp these two methods together into a single line of command:
```python
# Using () enclosure to be able to split the code line into several lines
df = (
    pd.read_csv("data.csv")
    .assign(
        data_col = lambda x: pd.to_datetime(x.data_col)
    )
    .rename(
        columns={'date_col':'Date'}
    )
)
```

A note here, in the .assign method, you can simply create a new column by setting is name as you like instead of **data_col**, like: **my_data = lambda x: pd.to_datetime(x.data_col)**, so this will create a new column called my_data, and the old column data_col still exists in our data. But it has no benefit to have a two columns, and one of them (the Object datatype one) will not be used in this string format.

## Saving DataFrame as CSV File
After working on your project, some times we may clean, process, or even feature engineer our data, so we have to be able to store these new modified/created dataframe in a CSV file, so we could simply load that data to continue work on it.
```python
# Save dataframe as csv format
df.to_csv("/Path/to/save/df.csv", index=False)

# Adding parameter: as_index and assign a False value to it, so this will not create an index for these dataframe while storing.
```
## Data Exploring: Retrieving rows from a dataframe
After we load the dataframe, we need to take a look to check our data, even this look is a glance look, but it is a catchy one, which helps us to make sure that everything is loaded correctly so far.

To do this, we simply could use **.head**/**.tail** method to display the first/last n number of rows
```python
# display first 3 rows
df.head(3)

# int_column	float_column	str_column	bool_column	date_column	category_column	object_column	nullable_column
# 0	1	1.5	a	True	2023-01-01	x	<object object at 0x7f12538191d0>	1.5
# 1	2	2.5	b	False	2023-01-02	y	<object object at 0x7f1253819230>	NaN

# display the last 6 rows
df.tail(6)
```

## Data Exploring: DataFrame Schema
To know the schema about the dataframe, we could use **.info** method:
```python
df.info()

# <class 'pandas.core.frame.DataFrame'>
# RangeIndex: 4 entries, 0 to 3
# Data columns (total 8 columns):
#  #   Column           Non-Null Count  Dtype         
# ---  ------           --------------  -----         
#  0   int_column       4 non-null      int64         
#  1   float_column     4 non-null      float64       
#  2   str_column       4 non-null      object        
#  3   bool_column      4 non-null      bool          
#  4   date_column      4 non-null      datetime64[ns]
#  5   category_column  4 non-null      category      
#  6   object_column    4 non-null      object        
#  7   nullable_column  3 non-null      float64       
# dtypes: bool(1), category(1), datetime64[ns](1), float64(2), int64(1), object(2)
# memory usage: 464.0+ bytes
```

# Reference
- Pandas Docs - Cummunity Tutorials: [link](https://pandas.pydata.org/pandas-docs/stable/getting_started/tutorials.html)
- Towardsai-Pandas Complete Tutprial for Data Science in 2022: [link](https://towardsai.net/p/data-science/pandas-complete-tutorial-for-data-science-in-2022)
- kdnuggets - 5 Advanced Features Pandas: [link](https://www.kdnuggets.com/2019/10/5-advanced-features-pandas.html)
- bitbucket - learn pandas: [link](https://bitbucket.org/hrojas/learn-pandas/src/master/)
- Github - pandas cookbook: [link](https://github.com/jvns/pandas-cookbook)
  