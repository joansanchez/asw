import os

from flask import Flask, logging, render_template

from contribution import Contribution
from persistence import Persistence
from user import User

app = Flask(__name__, static_folder='./static')


@app.route('/')
def home():
    contributions = Contribution.get_news(repository)
    return render_template('home.html', contributions=contributions)


if __name__ == '__main__':
    repository = Persistence(os.environ['DB_PATH'], logging.getLogger(__name__))
    repository.init_db([User.get_table_creation(), Contribution.get_table_creation()])
    app.run()
