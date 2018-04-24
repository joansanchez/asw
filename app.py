import datetime
import os
import time
from logging import basicConfig, INFO

from flask import Flask, logging, render_template, request, redirect, url_for, make_response

from contribution import Contribution, ContributionTypes
from google_login import validate_token
from persistence import Persistence
from user import User
from usercontributionvoted import UserContributionVoted

app = Flask(__name__, static_folder='./static')


@app.route('/')
def home():
    contributions = Contribution.get_news_home(repository)
    username = request.cookies.get('user')
    if username is not None and username:
        user = User.get(repository, username)
        return render_template('home.html', contributions=contributions, user=user)
    return render_template('home.html', contributions=contributions)


@app.route('/login', methods=['POST'])
def login():
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
    resp = make_response(redirect(''))
    resp.set_cookie('user', email)
    return resp

@app.route('/user', methods=['GET'])
def user():
    user_to_show = request.args.get('user', '')
    user = User.get(repository, user_to_show)
    return render_template('profile.html', user=user)

@app.route('/logout', methods=['POST'])
def logout():
    resp = make_response(redirect(''))
    resp.set_cookie('user', '', expires=(datetime.datetime.now()))
    return resp


@app.route('/submit')
def submit():
    username = request.cookies.get('user')
    if username is not None and username:
        user = User.get(repository, username)
        return render_template('submit.html', user=user)
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
    return redirect('')


@app.route('/ask')
def ask():
    asks = Contribution.get_asks(repository)
    username = request.cookies.get('user')
    if username is not None and username:
        user = User.get(repository, username)
        return render_template('ask.html', contributions=asks, user=user)
    return render_template('ask.html', asks=asks)


@app.route('/new')
def new():
    contributions = Contribution.get_contributions_new(repository)
    username = request.cookies.get('user')
    if username is not None and username:
        user = User.get(repository, username)
        return render_template('home.html', contributions=contributions, user=user)
    return render_template('home.html', contributions=contributions)


@app.template_filter('strftime')
def _jinja2_filter_datetime(date):
    return date
    now_date = ((time.mktime(datetime.datetime.now().timetuple())) - date)
    strftime = datetime.datetime.fromtimestamp(now_date).strftime('%M')
    time_ago = int(strftime)
    if time_ago < 60:
        return str(time_ago) + " minutes"

    elif time_ago/60 < 24:
        time_ago /= 60
        return str(time_ago) + " hours"

    elif time_ago/24 < 12:
        time_ago /=24
        return str(time_ago) + " months"

    else:
        return str(time_ago/12) + " years"


if __name__ == '__main__':
    repository = Persistence(os.environ['DB_PATH'], logging.getLogger(__name__))
    repository.init_db(
        [User.get_table_creation(), Contribution.get_table_creation(), UserContributionVoted.get_table_creation()])

    basicConfig(filename=os.environ['LOG'], level=INFO)

    app.config.update(TEMPLATES_AUTO_RELOAD=True)
    app.run(host=str(os.environ['HOST']), port=int(os.environ['PORT']))
