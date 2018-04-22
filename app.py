import os
from logging import basicConfig, INFO

from flask import Flask, logging, render_template, request
from google.oauth2 import id_token
from google.auth.transport import requests

from contribution import Contribution
from persistence import Persistence
from user import User

app = Flask(__name__, static_folder='./static')


@app.route('/')
def home():
    contributions = Contribution.get_news_home(repository)
    return render_template('home.html', contributions=contributions)


@app.route('/users', methods=['POST'])
def users():
    token = request.form['token']
    email = request.form['email']
    try:
        validate_token(token)
    except ValueError:
        return '', 403

    exists = User.exists(repository, email)
    if not exists:
        user = User(email)
        user.save(repository)
    return '', 204


def validate_token(username_token):
    # Specify the CLIENT_ID of the app that accesses the backend:
    CLIENT_ID = '443234130566-cba0cgt2np2alo9e3jhpb7au9hmeptoh.apps.googleusercontent.com'
    idinfo = id_token.verify_oauth2_token(username_token, requests.Request(), CLIENT_ID)

    if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
        raise ValueError('Wrong issuer.')

    # ID token is valid. Get the user's Google Account ID from the decoded token.
    userid = idinfo['sub']
    return userid


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
