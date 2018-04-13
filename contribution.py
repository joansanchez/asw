class Contribution:

    def __init__(self, title, url, text, time, username, contribution_id=None):
        self.id = contribution_id
        self.title = title
        self.url = url
        self.text = text
        self.time = time
        self.username = username

    def save(self, repository):
        sql_script = 'INSERT INTO contribution (title, url, \'text\', time, \'user\') VALUES (:title, :url, :text, :time, :username)'
        contribution = {'title': self.title, 'url': self.url, 'text': self.text, 'time': self.time,
                        'username': self.username}
        self.id = repository.insert(sql_script, contribution)

    @staticmethod
    def get_table_creation():
        return '''CREATE TABLE IF NOT EXISTS contribution
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         title TEXT,
                         url TEXT,
                         'text' TEXT,
                         time TIMESTAMP,
                         'user' TEXT NOT NULL,
                         FOREIGN KEY('user') REFERENCES 'user' (username)
                         )'''

    @staticmethod
    def get_contributions(repository):
        return repository.list('SELECT * FROM contribution')
