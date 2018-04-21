import os
from logging import basicConfig, INFO

from flask import Flask, logging, render_template, request

from contribution import Contribution
from persistence import Persistence
from user import User

app = Flask(__name__, static_folder='./static')


@app.route('/')
def home():
    contributions = Contribution.get_news(repository)
    return render_template('home.html', contributions=contributions)


@app.route('/users', methods=['POST'])
def users():
    username_id = request.form['id']
    print(username_id)
    return '', 204


@app.route('/submit')
def submit():
    return render_template('submit.html')


@app.route('/ask')
def ask():
    asks = Contribution.get_asks(repository)
    return render_template('ask.html', asks=asks)


@app.route('/new')
def new():
    contributions = Contribution.get_news(repository)
    return render_template('new.html', contributions=contributions)


if __name__ == '__main__':
    repository = Persistence(os.environ['DB_PATH'], logging.getLogger(__name__))
    repository.init_db([User.get_table_creation(), Contribution.get_table_creation()])

    basicConfig(filename=os.environ['LOG'], level=INFO)

    app.run(host=str(os.environ['HOST']), port=int(os.environ['PORT']))
