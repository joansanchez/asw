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
        result = repository.list(
            'SELECT *, c.text AS \'text\', c.user AS \'user\', c.id AS id FROM comment c WHERE c.contribution_id = \'' + contribution_id + '\' ORDER BY c.time DESC')
        comments = []
        for r in result:
            comment = Comment(r['user'], r['time'], r['text'], r['contribution_id'], r['parent_id'], r['id'])
            comments.append(comment)
        return comments

    @staticmethod
    def get_number_comments_by_contribution(repository, contribution_id):
        return repository.list(
            'SELECT count(*) AS n_comments FROM comment WHERE contribution_id = \'' + contribution_id + '\' ORDER BY time DESC')

    @staticmethod
    def get_comments_by_user(repository, username):
        result = repository.list(
            'SELECT *, c.text AS \'text\', c.user AS \'user\', c.id AS id, c.time AS \'time\' FROM comment c LEFT JOIN contribution co ON c.contribution_id = co.id WHERE c.user = \'' + username + '\' ORDER BY c.time DESC')
        comments = []
        for r in result:
            comment = Comment(r['user'], r['time'], r['text'], r['contribution_id'], r['parent_id'], r['id'])
            comment.contribution_title = r['title']
            comments.append(comment)
        return comments

    @staticmethod
    def get_comment(repository, comment_id):
        sql_script = 'SELECT * FROM comment c JOIN contribution co ON c.contribution_id = co.id WHERE c.id = \'' + comment_id + '\''
        result = repository.get(sql_script)
        comment = Comment(result[1], result[2], result[3], result[4], result[5], comment_id=result[0])
        comment.contribution_title = result[7]
        return comment

    @staticmethod
    def get_comments_by_parent(repository, parent_id):
        sql_script = 'SELECT *, c.id AS id, c.text AS \'text\', c.time AS \'time\', c.user AS \'user\' FROM comment c JOIN contribution co ON c.contribution_id = co.id WHERE c.parent_id = ' + str(
            parent_id)
        results = repository.list(sql_script)
        if results:
            comments = []
            for result in results:
                comment = Comment(result['user'], result['time'], result['text'], result['contribution_id'],
                                  result['parent_id'], comment_id=result['id'])
                comment.contribution_title = result['title']
                children = Comment.get_comments_by_parent(repository, comment.id)
                comment.children = children
                comments.append(comment)
            return comments
        else:
            return []
