# solution.ipynb

<div class="code-file">

Notebook from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/problems/interview-assessment-problems/question-job-counter-using-pyspark/solution.ipynb)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/problems/interview-assessment-problems/question-job-counter-using-pyspark/solution.ipynb)  ·  [Open in Colab](https://colab.research.google.com/github/AhmedYousriSobhi/aCupOfTea/blob/main/problems/interview-assessment-problems/question-job-counter-using-pyspark/solution.ipynb)

</div>


## Question

Group & sort data using PySpark.

Requirements

You are given a path to a file of comma-seperated values (CSV), jobs.csv, which contains people's names and job titles, such as Dancer, Nurse, Pilot, etc. The dataset has two columns: 'name' (a string data type) and 'job' (also a string data type).

|name|job|
|--|--|
|Tony Sullivan|Office Manager|
|Mary Henry| Film Editor|
|...|...|
|Tiffany Young|Dancer|

Implement a group_sort(input_path) method that reads data from the jobs.csv file and returns a dictionary in which the keys are jobs and the values are counts of how many times each job appears within the dataset. The dictionaty should be ordered by count (in ascending order), then job (in ascending order from A to Z).
The group_sort(input_path) method takes one argument:</br>
input_path - a path to the CSV file containing the data.|

```python
!pip install pyspark
```

```output
Defaulting to user installation because normal site-packages is not writeable
Looking in indexes: https://pypi.org/simple, https://pypi.ngc.nvidia.com
Collecting pyspark
  Downloading pyspark-3.4.1.tar.gz (310.8 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 310.8/310.8 MB 3.6 MB/s eta 0:00:0000:0100:03
  Preparing metadata (setup.py) ... done
Collecting py4j==0.10.9.7
  Downloading py4j-0.10.9.7-py2.py3-none-any.whl (200 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 200.5/200.5 KB 933.4 kB/s eta 0:00:00a 0:00:01
Building wheels for collected packages: pyspark
  Building wheel for pyspark (setup.py) ... done
  Created wheel for pyspark: filename=pyspark-3.4.1-py2.py3-none-any.whl size=311285409 sha256=f35dac4a8a44260b92e260a9ac4c1aa523c81f9c33c8db2d9b759a5669929c1e
  Stored in directory: /tmp/pip-ephem-wheel-cache-40rodamk/wheels/0d/77/a3/ff2f74cc9ab41f8f594dabf0579c2a7c6de920d584206e0834
Successfully built pyspark
Installing collected packages: py4j, pyspark
Successfully installed py4j-0.10.9.7 pyspark-3.4.1
```

```python
!pip install pandas
```

```output
Defaulting to user installation because normal site-packages is not writeable
Looking in indexes: https://pypi.org/simple, https://pypi.ngc.nvidia.com
Collecting pandas
  Downloading pandas-2.0.3-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (12.3 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 12.3/12.3 MB 2.2 MB/s eta 0:00:0000:0100:01
Requirement already satisfied: pytz>=2020.1 in /usr/lib/python3/dist-packages (from pandas) (2022.1)
Requirement already satisfied: numpy>=1.21.0 in /usr/lib/python3/dist-packages (from pandas) (1.21.5)
Requirement already satisfied: python-dateutil>=2.8.2 in /home/yousri/.local/lib/python3.10/site-packages (from pandas) (2.8.2)
Collecting tzdata>=2022.1
  Downloading tzdata-2023.3-py2.py3-none-any.whl (341 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 341.8/341.8 KB 3.0 MB/s eta 0:00:00a 0:00:01
Requirement already satisfied: six>=1.5 in /usr/lib/python3/dist-packages (from python-dateutil>=2.8.2->pandas) (1.16.0)
Installing collected packages: tzdata, pandas
Successfully installed pandas-2.0.3 tzdata-2023.3
```

```python
import pandas as pd, numpy as np
from pyspark.sql import SparkSession
```

```python
data = pd.DataFrame({
    'name':['Mido', 'Noura', 'AHmed', 'Nadine', 'Yasmen'],
    'job':['car', 'doctor', 'car', 'nurse', 'nurse']
})
```

```python
data.to_csv('data.csv', index = False)
```

```python
data_path = 'jobs.csv'


class SparkTask:
    def __init__(self, spark_session):
        self.job_counts_dict = None
        self.sc = spark_session.sparkContext
        self.spark = spark_session

    def group_sort(self, input_path):
    
        # Read the CSV file into a DataFrame
        df = self.spark.read.csv(input_path, header=True, inferSchema=True)

        # Group by the second column and count the occurrences
        count_df = df.groupBy(df.columns[1]).count()

        # Convert the DataFrame
        result_dict = dict(count_df.collect())

        # Sort the dictionary
        result_dict = sorted(result_dict.items(), key=lambda item: (item[1], item[0]))

        self.job_counts_dict = result_dict

        return self.job_counts_dict
```

```python
# Create a SparkSession
spark = SparkSession.builder.appName("CountDuplicates").getOrCreate()

s = SparkTask(spark)
```

```output
23/08/02 15:44:24 WARN Utils: Your hostname, yousri-Lenovo-Legion-5-15IMH05H resolves to a loopback address: 127.0.1.1; using 192.168.1.112 instead (on interface wlp0s20f3)
23/08/02 15:44:24 WARN Utils: Set SPARK_LOCAL_IP if you need to bind to another address
Setting default log level to "WARN".
To adjust logging level use sc.setLogLevel(newLevel). For SparkR, use setLogLevel(newLevel).
23/08/02 15:44:24 WARN NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
```

```python
s.group_sort()
```

```output
---------------------------------------------------------------------------
TypeError                                 Traceback (most recent call last)
/tmp/ipykernel_40674/3758704783.py in <module>
----> 1 s.group_sort()

TypeError: SparkTask.group_sort() missing 1 required positional argument: 'input_path'
```
