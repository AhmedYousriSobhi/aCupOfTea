# solution.ipynb

<div class="code-file">

Notebook from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/problems/interview-assessment-problems/question-cheapest-flats-per-city-using-sql/solution.ipynb)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/problems/interview-assessment-problems/question-cheapest-flats-per-city-using-sql/solution.ipynb)  ·  [Open in Colab](https://colab.research.google.com/github/AhmedYousriSobhi/aCupOfTea/blob/main/problems/interview-assessment-problems/question-cheapest-flats-per-city-using-sql/solution.ipynb)

</div>


## Question :

You are given a table of flats with the following structure: </br>
create table flats(</br>
    id integer primary key,</br>
    city varchar(40) not null,</br>
    price integer not null</br>
)</br>
Each row of table flats represents a flat located in acity available for sale for a given price.

Write a SQL query that, for each city finds the three cheapest flats located in that city. In case of a tie, the query may return any three flats with the cheapest prices.

The result table should contain three columns: id, city, and price and should be sorted by id column. If the city has less than three flats for sale, the result table should contain all of them.

Please use an OVER clause to simplify your solution.

Example:</br>
1.Given:</br>
|id|city|price|
|--|--|--|
|25|London|200000|
|5|Cairo|90000|
|7|London|200000|
|18|Warsaw|150000|
|2|London|170000|
|3|Cairo|300000|
|21|London|500000|
|9|London|500000|

One of the possible outputs is:</br>
|id|city|price|
|--|--|--|
|2|London|170000|
|3|Cairo|300000|
|5|Cairo|90000|
|7|London|200000|
|9|London|200000|
|18|Warsaw|150000|

There are only two flats available in Warsaw and on in Cairo, sothery are all selected. The cheapest flat in London has ID 2, then there are three flats with the same price (with IDs: 7, 9, 25). Any two of them may be selected.

Assume that:
- The flast table has at most 100 rows.
- Price column can only contains from 1000 to 100000000 inclusive.

```python
!pip install pandasql
```

```output
Defaulting to user installation because normal site-packages is not writeable
Looking in indexes: https://pypi.org/simple, https://pypi.ngc.nvidia.com
Collecting pandasql
  Downloading pandasql-0.7.3.tar.gz (26 kB)
  Preparing metadata (setup.py) ... done
Requirement already satisfied: numpy in /usr/lib/python3/dist-packages (from pandasql) (1.21.5)
Requirement already satisfied: pandas in /home/yousri/.local/lib/python3.10/site-packages (from pandasql) (2.0.3)
Collecting sqlalchemy
  Downloading SQLAlchemy-2.0.19-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.7 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.7/2.7 MB 2.9 MB/s eta 0:00:00a 0:00:01
Requirement already satisfied: pytz>=2020.1 in /usr/lib/python3/dist-packages (from pandas->pandasql) (2022.1)
Requirement already satisfied: tzdata>=2022.1 in /home/yousri/.local/lib/python3.10/site-packages (from pandas->pandasql) (2023.3)
Requirement already satisfied: python-dateutil>=2.8.2 in /home/yousri/.local/lib/python3.10/site-packages (from pandas->pandasql) (2.8.2)
Requirement already satisfied: typing-extensions>=4.2.0 in /home/yousri/.local/lib/python3.10/site-packages (from sqlalchemy->pandasql) (4.6.3)
Collecting greenlet!=0.4.17
  Downloading greenlet-2.0.2-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (613 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 613.7/613.7 KB 4.1 MB/s eta 0:00:00a 0:00:01
Requirement already satisfied: six>=1.5 in /usr/lib/python3/dist-packages (from python-dateutil>=2.8.2->pandas->pandasql) (1.16.0)
Building wheels for collected packages: pandasql
  Building wheel for pandasql (setup.py) ... done
  Created wheel for pandasql: filename=pandasql-0.7.3-py3-none-any.whl size=26784 sha256=2310de03dced71c94d9850f7cb8dcebea4c148a4a2cbd4e8c06108ac9d12da43
  Stored in directory: /tmp/pip-ephem-wheel-cache-9zq4tsdp/wheels/e9/bc/3a/8434bdcccf5779e72894a9b24fecbdcaf97940607eaf4bcdf9
Successfully built pandasql
Installing collected packages: greenlet, sqlalchemy, pandasql
Successfully installed greenlet-2.0.2 pandasql-0.7.3 sqlalchemy-2.0.19
```

```python
import pandas as pd
from pandasql import sqldf
```

```python
# Data for the flats table
data = {
    'id': [25, 5, 7, 18, 2, 3, 21, 9],
    'city': ['London', 'Cairo', 'London', 'Warsaw', 'London', 'Cairo', 'London', 'London'],
    'price': [200000, 90000, 200000, 150000, 178000, 300000, 500000, 200000]
}

# Create a DataFrame with the flats data
flats_df = pd.DataFrame(data)

flats_df
```

<div class="nb-output">

<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>id</th>
      <th>city</th>
      <th>price</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>25</td>
      <td>London</td>
      <td>200000</td>
    </tr>
    <tr>
      <th>1</th>
      <td>5</td>
      <td>Cairo</td>
      <td>90000</td>
    </tr>
    <tr>
      <th>2</th>
      <td>7</td>
      <td>London</td>
      <td>200000</td>
    </tr>
    <tr>
      <th>3</th>
      <td>18</td>
      <td>Warsaw</td>
      <td>150000</td>
    </tr>
    <tr>
      <th>4</th>
      <td>2</td>
      <td>London</td>
      <td>178000</td>
    </tr>
    <tr>
      <th>5</th>
      <td>3</td>
      <td>Cairo</td>
      <td>300000</td>
    </tr>
    <tr>
      <th>6</th>
      <td>21</td>
      <td>London</td>
      <td>500000</td>
    </tr>
    <tr>
      <th>7</th>
      <td>9</td>
      <td>London</td>
      <td>200000</td>
    </tr>
  </tbody>
</table>
</div>

</div>

```python
# Define the SQL query
query = """
    -- Implement your solution here
WITH ranked_flats AS (
    SELECT
        id,
        city,
        price,
        DENSE_RANK() OVER (PARTITION BY city ORDER BY price, id) AS rank
    FROM
        flats
)
SELECT
    id,
    city,
    price
FROM
    ranked_flats
WHERE
    rank <= 3
ORDER BY id, price;

"""

# Execute the SQL query using pandasql
result = sqldf(query, env={'flats': flats_df})

# Print the result DataFrame
print(result)
```

```output
   id    city   price
0   2  London  178000
1   3   Cairo  300000
2   5   Cairo   90000
3   7  London  200000
4   9  London  200000
5  18  Warsaw  150000
```
