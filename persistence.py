import sqlite3
from collections import OrderedDict


class Persistence:
    def __init__(self, path, log):
        self.path = path
        self.log = log

    def init_db(self, tables):
        db_conn, db_client = self.create_connection()
        try:
            db_client.execute('PRAGMA foreign_keys = ON;')
            for table in tables:
                db_client.execute(table)
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

    def insert(self, sql_script, element):
        db_conn, db_client = self.create_connection()
        try:
            cursor = db_conn.cursor()
            cursor.execute(sql_script, element)
            element_id = cursor.lastrowid
            db_conn.commit()
            self.close_connection(db_conn)
            return element_id
        except Exception as ex:
            self.log.error('Error executing a query in the SQLite DB. Exception: ' + str(ex))
            if db_conn:
                self.close_connection(db_conn)
            raise ex

    def list(self, sql_script):
        db_conn, db_client = self.create_connection()
        try:
            db_client.execute(sql_script)
            keys = [description[0] for description in db_client.description]
            rows = db_client.fetchall()
            element_list = []
            for row in rows:
                element_list.append(OrderedDict(zip(keys, row)))
            self.close_connection(db_conn)
            return element_list
        except Exception as ex:
            self.log.error('Error executing a query in the SQLite DB. Exception: ' + str(ex))
            if db_conn:
                self.close_connection(db_conn)
            raise ex

    def exists(self, sql_script):
        db_conn, db_client = self.create_connection()
        try:
            db_client.execute(sql_script)
            row = db_client.fetchone()
            self.close_connection(db_conn)
            return row is not None
        except Exception as ex:
            self.log.error('Error executing a query in the SQLite DB. Exception: ' + str(ex))
            if db_conn:
                self.close_connection(db_conn)
            raise ex