To use mysql inPython on macos you need use following command: 
`pip install mysqlclient` (mix os/ python 3)

To init database run command (not necessary):
`sqlite3 <path to db file>`

To create tables first import db:
`from <name main file app> import <name of db instance>`
`<name of db instance>.create_all()`

SQLite version 3.19.3 2017-06-27 16:48:08
Enter ".help" for usage hints.
sqlite> `.tables`
sqlite> `.exit`

after that in python:

>>> `from app import db`
>>> `db.create_all()`