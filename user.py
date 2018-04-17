class User:

    def __init__(self, username, password):
        self.username = username
        self.password = password

    @staticmethod
    def get_table_creation():
        return '''CREATE TABLE IF NOT EXISTS 'user'
                            (email TEXT PRIMARY KEY,
                            karma INTEGER DEFAULT 0
                            about TEXT
                            )'''

    def save(self, repository):
        sql_script = 'INSERT INTO \'user\' (username, password) VALUES (:username, :password)'
        user = {'username': self.username, 'password': self.password}
        self.id = repository.insert(sql_script, user)