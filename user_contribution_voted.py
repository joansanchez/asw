class User_Contribution_voted:

    def __init__(self, username, contribution_id):
        self.username = username
        self.contribution_id = contribution_id

    def save(self, repository):
        sql_script = '''INSERT INTO \'user\' (\'user\', contribution_id) VALUES (:username, :contribution_id)'''
        user_contribution_id = {'username': self.username, 'contribution_id': self.contribution_id}
        self.id = repository.insert(sql_script, user_contribution_id)

    @staticmethod
    def get_table_creation():
        return '''CREATE TABLE IF NOT EXISTS user_contribution_id
                             (id INTEGER,
                             'user' TEXT,
                             PRIMARY KEY(id, 'user')
                             FOREIGN KEY('user') REFERENCES 'user' (username)
                             )'''