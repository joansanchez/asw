import sqlite3


class Persistence:
    def __init__(self, path, log):
        self.path = path
        self.log = log

    def init_db(self, tables):
        db_conn, db_client = self.create_connection()
        try:
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
