import sqlite3
from collections import OrderedDict


class Persistence:
    def __init__(self, path, log):
        self.path = path
        self.log = log

    def init_db(self):
        db_conn, db_client = self.create_connection()
        try:
            db_client.execute('''CREATE TABLE IF NOT EXISTS contribution
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         title TEXT,
                         url TEXT,
                         'text' TEXT,
                         time TIMESTAMP
                         )''')
            db_conn.commit()
        except Exception as e:
            self.close_connection(db_conn)
            raise e
        self.close_connection(db_conn)

    def create_connection(self):
        try:
            db_conn = sqlite3.connect(self.path)
            db_client = db_conn.cursor()
            return db_conn, db_client
        except Exception as ex:
            self.log.error('Error connecting with the SQLite DB. Exception: ' + str(ex))
            raise ex

    def close_connection(self, db_conn):
        try:
            db_conn.close()
            return db_conn
        except Exception as ex:
            self.log.error('Error closing the connection with the SQLite DB. Exception: ' + str(ex))
            raise ex
