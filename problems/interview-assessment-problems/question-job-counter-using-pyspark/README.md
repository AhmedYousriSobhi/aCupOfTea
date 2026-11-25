<!-- related-block -->
<nav class="crumbs" aria-label="Breadcrumb"><a href="#/problems/">Problems</a> / <a href="#/problems/interview-assessment-problems/">Interview Assessment Problems</a></nav>

# Question - Job Counter Using PySpark

<!-- related-block -->
<div class="reading-time">1 min read · Updated 5 Nov 2026</div>


> An interview PySpark problem: group and sort data, counting how often each job appears.

Group & sort data using PySpark.

Requirements

You are given a path to a file of comma-separated values (CSV), jobs.csv, which contains people's names and job titles, such as Dancer, Nurse, Pilot, etc. The dataset has two columns: 'name' (a string data type) and 'job' (also a string data type).

|name|job
|--|--
|Tony Sullivan|Office Manager
|Mary Henry| Film Editor
|...|...
|Tiffany Young|Dancer

Implement a group_sort(input_path) method that reads data from the jobs.csv file and returns a dictionary in which the keys are jobs and the values are counts of how many times each job appears within the dataset. The dictionaty should be ordered by count (in ascending order), then job (in ascending order from A to Z).
The group_sort(input_path) method takes one argument:</br>
input_path - a path to the CSV file containing the data.