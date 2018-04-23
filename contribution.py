from enum import Enum


class ContributionTypes(Enum):
    ASK = 'ask'
    NEW = 'new'


class Contribution:

    def __init__(self, title, url, text, time, username, kind, n_votes, contribution_id=None):
        self.id = contribution_id
        self.title = title
        self.url = url
        self.text = text
        self.time = time
        self.username = username
        self.kind = kind
        self.n_votes = n_votes

    def save(self, repository):
        sql_script = '''INSERT INTO contribution (title, url, \'text\', time, \'user\', kind, n_votes) 
                        VALUES (:title, :url, :text, :time, :username, :kind, :n_votes)'''
        contribution = {'title': self.title, 'url': self.url, 'text': self.text, 'time': self.time,
                        'username': self.username, 'kind': self.kind.value, 'n_votes': self.n_votes}
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
                         'kind' TEXT,
                         n_votes INTEGER,
                         FOREIGN KEY('user') REFERENCES 'user' (email)
                         )'''

    @staticmethod
    def get_contributions(repository):
        return repository.list('SELECT * FROM contribution')

    @staticmethod
    def get_news(repository):
        return repository.list('SELECT * FROM contribution WHERE kind = \'' + ContributionTypes.NEW.value + '\'')

    @staticmethod
    def get_news_home(repository):
        return repository.list(
            'SELECT * FROM contribution WHERE kind = \'' + ContributionTypes.NEW.value + '\' ORDER BY n_votes DESC')

    @staticmethod
    def get_asks(repository):
        return repository.list('SELECT * FROM contribution WHERE kind = \'' + ContributionTypes.ASK.value + '\'')
