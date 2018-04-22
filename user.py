class User:

    def __init__(self, email, karma=None, about=None):
        self.email = email
        self.karma = karma
        self.about = about

    @staticmethod
    def get_table_creation():
        return '''CREATE TABLE IF NOT EXISTS 'user'
                            (email TEXT PRIMARY KEY,
                            karma INTEGER DEFAULT 0,
                            about TEXT
                            )'''

    def save(self, repository):
        sql_script = 'INSERT INTO \'user\' (email, karma, about) VALUES (:email, :karma, :about)'
        user = {'email': self.email, 'karma': self.karma, 'about': self.about}
        self.id = repository.insert(sql_script, user)

    @staticmethod
    def exists(repository, email):
        sql_script = 'SELECT * FROM \'user\' WHERE email = \'' + email + '\''
        return repository.exists(sql_script)
