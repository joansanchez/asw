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
            comment = {'username': self.username, 'time': self.time, 'text': self.text, 'contribution_id': self.contribution_id,
                       'parent_id': self.parent_id}
            self.id = repository.insert(sql_script, comment)

        @staticmethod
        def get_table_creation():
            return '''CREATE TABLE IF NOT EXISTS comment
                                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                'user' TEXT NOT NULL,
                                time TIMESTAMP,
                                'text' TEXT,
                                FOREIGN KEY('parent_id') REFERENCES 'id' (comment)
                                FOREIGN KEY('contribution_id') REFERENCES 'id' (contribution)
                                )'''
