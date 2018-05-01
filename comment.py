class Comment:

    def __init__(self, username, time, text, contribution_id, parent_id, comment_id=None):
        self.id = comment_id
        self.username = username
        self.time = time
        self.text = text
        self.contribution_id = contribution_id
        self.parent_id = parent_id

    def save(self, repository):
        sql_script = '''INSERT INTO comment (\'user\', time, \'text\', contribution_id, parent_id) 
                        VALUES (:username, :time, :text, :contribution_id, :parent_id)'''
        comment = {'username': self.username, 'time': self.time, 'text': self.text,
                   'contribution_id': self.contribution_id, 'parent_id': self.parent_id}
        self.id = repository.insert(sql_script, comment)

    @staticmethod
    def get_table_creation():
        return '''CREATE TABLE IF NOT EXISTS comment
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                            'user' TEXT NOT NULL,
                            time TIMESTAMP,
                            'text' TEXT,
                            contribution_id INTEGER NOT NULL,
                            parent_id INTEGER,
                            FOREIGN KEY('parent_id') REFERENCES 'id' (comment),
                            FOREIGN KEY('contribution_id') REFERENCES 'id' (contribution)
                            )'''

    @staticmethod
    def get_comments_by_contribution(repository, contribution_id):
        return repository.list(
            'SELECT * FROM comment WHERE contribution_id = \'' + contribution_id + '\' ORDER BY time DESC')

    @staticmethod
    def get_number_comments_by_contribution(repository, contribution_id):
        return repository.list(
            'SELECT count(*) AS n_comments FROM comment WHERE contribution_id = \'' + contribution_id + '\' ORDER BY time DESC')

    @staticmethod
    def get_comments_by_user(repository, username):
        result = repository.list(
            'SELECT *, c.text as \'text\' FROM comment c LEFT JOIN contribution co ON c.contribution_id = co.id WHERE c.user = \'' + username + '\' ORDER BY c.time DESC')
        comments = []
        for r in result:
            comment = Comment(r['user'], r['time'], r['text'], r['contribution_id'], r['parent_id'], r['id'])
            comment.contribution_title = r['title']
            comments.append(comment)
        return comments

    @staticmethod
    def get_replies_by_comment(repository, comment_id):
        return repository.list('SELECT * FROM comment WHERE parent_id = \'' + comment_id + '\' ORDER BY time DESC')

    @staticmethod
    def get_comments(repository):
        return repository.list('SELECT * FROM comment ORDER BY time DESC')
