from enum import Enum


class ContributionTypes(Enum):
    ASK = 'ask'
    NEW = 'new'


class Contribution:

    def __init__(self, title, url, text, time, username, kind, contribution_id=None):
        self.id = contribution_id
        self.title = title
        self.url = url
        self.text = text
        self.time = time
        self.username = username
        self.kind = kind

    def save(self, repository):
        sql_script = '''INSERT INTO contribution (title, url, \'text\', time, \'user\', kind) 
                        VALUES (:title, :url, :text, :time, :username, :kind)'''
        contribution = {'title': self.title, 'url': self.url, 'text': self.text, 'time': self.time,
                        'username': self.username, 'kind': self.kind}
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
                         FOREIGN KEY('user') REFERENCES 'user' (email)
                         )'''

    @staticmethod
    def get_contributions(repository):
        return repository.list('SELECT * FROM contribution')

    @staticmethod
    def get_contributions_urls(repository):
        return repository.list('SELECT url FROM contribution WHERE kind = \'' + ContributionTypes.NEW.value + '\'')

    @staticmethod
    def get_news(repository):
        return repository.list('SELECT * FROM contribution WHERE kind = \'' + ContributionTypes.NEW.value + '\'')

    @staticmethod
    def get_news_home(repository):
        result = repository.list(
            'SELECT c.id, c.title, c.url, c.text, c.time, c.\'user\', c.kind, count(u.\'user\') AS n_votes FROM contribution c LEFT JOIN user_contribution_voted u ON c.id = u.contribution WHERE c.kind = \'' + ContributionTypes.NEW.value + '\' GROUP BY c.id ORDER BY n_votes DESC;')
        contributions = []
        for r in result:
            contribution = Contribution(r['title'], r['url'], r['text'], r['time'], r['user'], r['kind'],
                                        contribution_id=r['id'])
            contribution.n_votes = r['n_votes']
            contributions.append(r)
        return contributions

    @staticmethod
    def get_contributions_new(repository):
        return repository.list(
            'SELECT c.id, c.title, c.url, c.text, c.time, c.\'user\', c.kind, count(u.\'user\') AS n_votes FROM contribution c LEFT JOIN user_contribution_voted u ON c.id = u.contribution GROUP BY c.id ORDER BY time DESC;')

    @staticmethod
    def get_asks(repository):
        return repository.list('SELECT * FROM contribution WHERE kind = \'' + ContributionTypes.ASK.value + '\'')

    @staticmethod
    def get_contribution(repository, contribution_id):
        result = repository.get(
            'SELECT c.id, c.title, c.url, c.text, c.time, c.\'user\', c.kind, count(u.\'user\') AS n_votes FROM contribution c LEFT JOIN user_contribution_voted u ON c.id = u.contribution WHERE c.id = \'' + contribution_id + '\' GROUP BY c.id ORDER BY time DESC;')
        contribution = Contribution(result[1], result[2], result[3], result[4], result[5], result[6],
                                    contribution_id=result[0])
        contribution.n_votes = result[7]
        return contribution

    @staticmethod
    def exists(repository, url):
        return repository.exists('SELECT * FROM contribution WHERE url = \'' + url + '\'')

    @staticmethod
    def get_contribution_id_by_URL(repository, url):
        result = repository.get(
            'SELECT id FROM contribution WHERE url = \'' + url + '\'')
        return result[0]

    def toJSON(self):
        json = {
            "id": self.id,
            "title": self.title,
            "time": self.time,
            "username": self.username,
        }

        if self.kind == ContributionTypes.ASK.value:
            json['text'] = self.text
        elif self.kind == ContributionTypes.NEW.value:
            json['url'] = self.url

        return json
