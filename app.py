import datetime
import os
from logging import basicConfig, INFO

from flask import Flask, logging, render_template, request, redirect, url_for, make_response

from comment import Comment
from contribution import Contribution, ContributionTypes
from google_login import validate_token
from persistence import Persistence
from token_generator import encode_auth_token, decode_auth_token
from user import User
from usercontributionvoted import UserContributionVoted

app = Flask(__name__, static_folder='./static')


@app.route('/')
def home():
    contributions = Contribution.get_news_home(repository)
    username = decode_auth_token(request.cookies.get('token'))
    if username is not None:
        user = User.get(repository, username)
        contributions_voted = UserContributionVoted.get_voted(repository, username)
        for c in contributions:
            c.voted = c['id'] in [cv['contribution_id'] for cv in contributions_voted]
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
    resp.set_cookie('token', encode_auth_token(email))
    return resp


@app.route('/user', methods=['GET'])
def user():
    user_to_show = request.args.get('user', '')
    user = User.get(repository, user_to_show)
    return render_template('profile.html', user=user)


@app.route('/logout', methods=['POST'])
def logout():
    resp = make_response(redirect(''))
    resp.set_cookie('token', '', expires=(datetime.datetime.now()))
    return resp


@app.route('/vote', methods=['POST'])
def vote():
    username = decode_auth_token(request.cookies.get('token'))
    if username is not None:
        contribution_id = request.form['contribution']
        action = request.form['action']
        contribution_voted = UserContributionVoted(username, contribution_id)
        if action == 'vote':
            contribution_voted.save(repository)
        elif action == 'unvote':
            contribution_voted.delete(repository)
    resp = make_response(redirect(''))
    return resp


@app.route('/submit')
def submit():
    username = decode_auth_token(request.cookies.get('token'))
    if username is not None:
        user = User.get(repository, username)
        return render_template('submit.html', user=user)
    return render_template('submit.html')


@app.route('/contribution', methods=['GET'])
def get_contribution():
    contribution_id = request.args.get('id', '')
    contribution = Contribution.get_contribution(repository, contribution_id)
    comments = Comment.get_comments_by_contribution(repository, contribution_id)
    user = decode_auth_token(request.cookies.get('token'))
    if user is not None:
        user = User.get(repository, user)
        return render_template('contribution.html', contribution=contribution, comments=comments, user=user)
    return render_template('contribution.html', contribution=contribution, comments=comments)


@app.route('/newPost', methods=['POST'])
def new_post():
    title = request.form["title"]
    url = request.form["url"]
    text = request.form["text"]
    time = datetime.datetime.now()
    user = decode_auth_token(request.cookies.get('token'))
    if url != '' and text == '':
        contribution = Contribution(title, url, text, time, user, ContributionTypes.NEW.value, 0)
    elif text != '' and url == '':
        contribution = Contribution(title, url, text, time, user, ContributionTypes.ASK.value, 0)
    else:
        return redirect(url_for('submit'))
    contribution.save(repository)
    return redirect('')


@app.route('/doComment', methods=['POST'])
def new_comment():
    user = decode_auth_token(request.cookies.get('token'))
    time = datetime.datetime.now()
    text = request.form["text"]
    contribution = request.form["contribution"]
    if user is not None:
        if text != '':
            comment = Comment(user, time, text, contribution, 0)
        else:
            return redirect(url_for('get_contribution'))
        comment.save(repository)
    return redirect('contribution?id=' + contribution)


@app.route('/ask')
def ask():
    contributions = Contribution.get_asks(repository)
    username = decode_auth_token(request.cookies.get('token'))
    if username is not None:
        user1: User = User.get(repository, username)
        contributions_voted = UserContributionVoted.get_voted(repository, username)
        for c in contributions:
            c.voted = c['id'] in [cv['contribution_id'] for cv in contributions_voted]
        return render_template('home.html', contributions=contributions, user=user1)
    return render_template('home.html', contributions=contributions)


@app.route('/new')
def new():
    contributions = Contribution.get_contributions_new(repository)
    username = decode_auth_token(request.cookies.get('token'))
    if username is not None:
        user1: User = User.get(repository, username)
        contributions_voted = UserContributionVoted.get_voted(repository, username)
        for c in contributions:
            c.voted = c['id'] in [cv['contribution_id'] for cv in contributions_voted]
        return render_template('home.html', contributions=contributions, user=user1)
    return render_template('home.html', contributions=contributions)


@app.route('/editProfile')
def edit_profile():
    username = decode_auth_token(request.cookies.get('token'))
    if username is not None:
        user = User.get(repository, username)
        return render_template('editProfile.html', user=user)
    return redirect('')


@app.route('/updateUser', methods=['POST'])
def update_profile():
    username = decode_auth_token(request.cookies.get('token'))
    if username is not None:
        user = User.get(repository, username)
        user.update(repository, request.form["about"])
        return render_template('editProfile.html', user=user)
    return redirect('')


@app.template_filter('time_ago')
def _time_ago_filter(date):
    date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
    now = datetime.datetime.now()
    time_ago = now - date
    time_ago = time_ago.seconds

    if time_ago < 60:
        return str(int(round(time_ago))) + " seconds"

    time_ago = time_ago / 60
    if time_ago < 60:
        return str(int(round(time_ago))) + " minutes"

    time_ago = time_ago / 60
    if time_ago / 60 < 24:
        return str(int(round(time_ago))) + " hours"

    time_ago = time_ago / 24
    if time_ago < 12:
        return str(int(round(time_ago))) + " months"

    time_ago = time_ago / 12
    return str(int(round(time_ago))) + " years"


if __name__ == '__main__':
    repository = Persistence(os.environ['DB_PATH'], logging.getLogger(__name__))
    repository.init_db(
        [User.get_table_creation(), Contribution.get_table_creation(), UserContributionVoted.get_table_creation(),
         Comment.get_table_creation()])

    basicConfig(filename=os.environ['LOG'], level=INFO)

    app.config.update(TEMPLATES_AUTO_RELOAD=True)
    app.run(host=str(os.environ['HOST']), port=int(os.environ['PORT']))
