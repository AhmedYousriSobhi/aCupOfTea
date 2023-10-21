## Question - Cheapest Flats per city using SQL

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