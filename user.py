class User:

    def __init__(self, email, karma=0, about=''):
        self.email = email
        self.karma = karma
        self.about = about

    @staticmethod
    def get_table_creation():
        return '''CREATE TABLE IF NOT EXISTS 'user'
                            (email TEXT PRIMARY KEY,
                            karma INTEGER DEFAULT 0 NOT NULL,
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

    @staticmethod
    def get(repository, email):
        sql_script = 'SELECT * FROM \'user\' WHERE email = \'' + email + '\''
        user = repository.get(sql_script)
        if user is not None:
            return User(user[0], user[1], user[2])
        return None

    def update(self, repository, about):
        sql_script = 'UPDATE \'user\' SET about = \'' + about + '\' WHERE email = \'' + self.email + '\''
        user = {'email': self.email, 'karma': self.karma, 'about': about}
        repository.insert(sql_script, user)
        self.about = about

    def toJSON(self):
        json = {
            "email": self.email,
            "karma": self.karma,
            "about": self.about,
        }
        return json
