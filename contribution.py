class Contribution:

    def __init__(self, title, url, text, time, contribution_id=None):
        self.id = contribution_id
        self.title = title
        self.url = url
        self.text = text
        self.time = time

    def save(self, repository):
        sql_script = 'INSERT INTO contribution (title, url, \'text\', time) VALUES (:title, :url, :text, :time)'
        contribution = {'title': self.title, 'url': self.url, 'text': self.text, 'time': self.time}
        self.id = repository.insert(sql_script, contribution)

    @staticmethod
    def get_table_creation():
        return '''CREATE TABLE IF NOT EXISTS contribution
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         title TEXT,
                         url TEXT,
                         'text' TEXT,
                         time TIMESTAMP
                         )'''
