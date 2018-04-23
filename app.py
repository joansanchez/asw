import datetime
import os
from logging import basicConfig, INFO

from flask import Flask, logging, render_template, request, redirect, url_for, make_response
from google.auth.transport import requests
from google.oauth2 import id_token

from contribution import Contribution, ContributionTypes
from persistence import Persistence
from user import User
from usercontributionvoted import UserContributionVoted

app = Flask(__name__, static_folder='./static')


@app.route('/')
def home():
    contributions = Contribution.get_news_home(repository)
    return render_template('home.html', contributions=contributions, user= User.get(repository, 'jsanchezgarcia13@gmail.com'))


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
    user = User.get(repository, email)
    resp = make_response(render_template('home.html', user=user))
    resp.set_cookie('user', user.email)
    return resp


def validate_token(username_token):
    # Specify the CLIENT_ID of the app that accesses the backend:
    client_id = '443234130566-cba0cgt2np2alo9e3jhpb7au9hmeptoh.apps.googleusercontent.com'
    id_info = id_token.verify_oauth2_token(username_token, requests.Request(), client_id)

    if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
        raise ValueError('Wrong issuer.')

    # ID token is valid. Get the user's Google Account ID from the decoded token.
    user_id = id_info['sub']
    return user_id


@app.route('/submit')
def submit():
    return render_template('submit.html')


@app.route('/newpost', methods=['POST'])
def new_post():
    title = request.form["title"]
    url = request.form["url"]
    text = request.form["text"]
    time = datetime.datetime.now()
    user = request.cookies.get('user')
    if url != '' and text == '':
        contribution = Contribution(title, url, text, time, user, ContributionTypes.NEW.value, 0)
    elif text != '' and url == '':
        contribution = Contribution(title, url, text, time, user, ContributionTypes.ASK.value, 0)
    else:
        return redirect(url_for('submit'))
    contribution.save(repository)
    return redirect(url_for(''))


@app.route('/ask')
def ask():
    asks = Contribution.get_asks(repository)
    return render_template('ask.html', asks=asks)


@app.route('/new')
def new():
    contributions = Contribution.get_news(repository)
    return render_template('home.html', contributions=contributions)


if __name__ == '__main__':
    repository = Persistence(os.environ['DB_PATH'], logging.getLogger(__name__))
    repository.init_db(
        [User.get_table_creation(), Contribution.get_table_creation(), UserContributionVoted.get_table_creation()])

    basicConfig(filename=os.environ['LOG'], level=INFO)

    app.run(host=str(os.environ['HOST']), port=int(os.environ['PORT']))
