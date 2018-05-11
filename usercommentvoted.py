class UserCommentVoted:

    def __init__(self, user, comment):
        self.user = user
        self.comment = comment

    def save(self, repository):
        sql_script = '''INSERT INTO user_comment_voted (\'user\', comment) VALUES (:user, :comment)'''
        user_comment_voted = {'user': self.user, 'comment': self.comment}
        repository.insert(sql_script, user_comment_voted)

    @staticmethod
    def get_table_creation():
        return '''CREATE TABLE IF NOT EXISTS user_comment_voted
                             ('user' TEXT,
                             comment INTEGER,
                             PRIMARY KEY('user', comment),
                             FOREIGN KEY('user') REFERENCES 'user' (email),
                             FOREIGN KEY('comment') REFERENCES 'comment' (id)
                             )'''

    @staticmethod
    def get_voted(repository, username):
        return repository.list('SELECT comment AS comment_id FROM user_comment_voted WHERE user = \'' + username + '\'')

    def delete(self, repository):
        repository.delete('DELETE FROM user_comment_voted WHERE user = \'' + self.user + '\' AND  comment = \'' + self.comment+ '\'')

    @staticmethod
    def exists(repository, comment_id, username):
        return repository.exists(
            'SELECT * FROM user_comment_voted WHERE comment = \'' + comment_id + '\' AND user = \'' + username + '\'')