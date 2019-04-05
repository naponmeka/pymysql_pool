# PyMYSQL-pool

PyMySQL connection pool.
Simple mysql pool with minimum refactoring from pymysql. No need to handle cursor and connection with the "python with statement"


* Free software: MIT license


## Installation
--------
```
pip install git+https://github.com/naponmeka/pymysql_pool.git
```
# Usage
Using the library
```
import pymysql_pool

mysql_pool = pymysql_pool.create_pool({
    'host': host,
    'user': user,
    'password': pass,
    'port': port,
    'db': db,
    'charset': 'utf8',
    'cursorclass': pymysql.cursors.DictCursor,
    'autocommit': True
})

with mysql_pool as conn:
    with conn.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()
```
Mocking and testing
```
from unittest.mock import MagicMock, patch, Mock

# Creating mock connection pool
def create_mock_connection_pool(mock_entered_cursor):
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = MagicMock(return_value=mock_entered_cursor)

    mock_entered_connection = MagicMock()
    mock_entered_connection.cursor = MagicMock(return_value=mock_cursor)

    mock_connection = MagicMock()
    mock_connection.__enter__ = MagicMock(return_value=mock_entered_connection)

    mock_connection_pool = MagicMock()
    mock_connection_pool.get = MagicMock(return_value=mock_connection)
    return mock_connection_pool


mock_entered_cursor = MagicMock()
# Depending on the function you use to query the database
mock_entered_cursor.fetchall = MagicMock(return_value=some-mock-result)
mock_connection_pool = create_mock_connection_pool(mock_entered_cursor)



```


