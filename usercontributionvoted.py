class UserContributionVoted:

    def __init__(self, user, contribution):
        self.user = user
        self.contribution = contribution

    def save(self, repository):
        sql_script = '''INSERT INTO user_contribution_voted (\'user\', contribution) VALUES (:user, :contribution)'''
        user_contribution_voted = {'user': self.user, 'contribution': self.contribution}
        repository.insert(sql_script, user_contribution_voted)

    @staticmethod
    def get_table_creation():
        return '''CREATE TABLE IF NOT EXISTS user_contribution_voted
                             ('user' TEXT,
                             contribution INTEGER,
                             PRIMARY KEY('user', contribution),
                             FOREIGN KEY('user') REFERENCES 'user' (email),
                             FOREIGN KEY('contribution') REFERENCES 'contribution' (id)
                             )'''

    @staticmethod
    def get_voted(repository, username):
        return repository.list('SELECT contribution AS contribution_id FROM user_contribution_voted WHERE user = \'' + username + '\'')

    def delete(self, repository):
        repository.delete('DELETE FROM user_contribution_voted WHERE user = \'' + self.user + '\' AND  contribution = \'' + self.contribution + '\'')

    @staticmethod
    def exists(repository, contribution_id, username):
        return repository.exists('SELECT * FROM user_contribution_voted WHERE contribution = \'' + contribution_id + '\' AND user = \'' + username + '\'')