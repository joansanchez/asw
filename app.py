import datetime
import os
from logging import basicConfig, INFO

from flask import Flask, logging, render_template, request, redirect, url_for, make_response, jsonify, json, Response

from comment import Comment
from contribution import Contribution, ContributionTypes
from google_login import validate_token
from persistence import Persistence
from token_generator import encode_auth_token, decode_auth_token
from user import User
from usercommentvoted import UserCommentVoted
from usercontributionvoted import UserContributionVoted

app = Flask(__name__, static_folder='./static')


@app.route('/')
def home():
    contributions = Contribution.get_news_home(repository)
    username = decode_auth_token(request.cookies.get('token'))
    if username is not None:
        contributions_voted = UserContributionVoted.get_voted(repository, username)
        for c in contributions:
            c.voted = c['id'] in [cv['contribution_id'] for cv in contributions_voted]
            aux = Comment.get_number_comments_by_contribution(repository, str(c['id']))
            c['n_comments'] = aux[0]['n_comments']
        user = User.get(repository, username)
        return render_template('home.html', contributions=contributions, user=user)
    else:
        for c in contributions:
            aux = Comment.get_number_comments_by_contribution(repository, str(c['id']))
            c.n_comments = aux[0]['n_comments']
        return render_template('home.html', contributions=contributions)


@app.route('/threads')
def threads():
    username = decode_auth_token(request.cookies.get('token'))
    email = request.args.get('id', default=username)
    if username is not None:
        user = User.get(repository, username)
        comments = Comment.get_comments_by_user(repository, email)
        all_children = []
        for comment in comments:
            children = Comment.get_comments_by_parent(repository, comment.id)
            all_children.extend(children)
            comment.children = children
        first_level_comments = []
        for comment in comments:
            if not comment.id in [c.id for c in all_children]:
                first_level_comments.append(comment)
        return render_template('threads.html', comments=first_level_comments, user=user)
    return redirect('')


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
    username = decode_auth_token(request.cookies.get('token'))
    user_to_show = User.get(repository, request.args.get('user'))
    if username is not None:
        user = User.get(repository, username)
        return render_template('profile.html', user_to_show=user_to_show, user=user)
    return render_template('profile.html', user_to_show=user_to_show)


@app.route('/logout', methods=['POST'])
def logout():
    resp = make_response(redirect(''))
    resp.set_cookie('token', '', expires=(datetime.datetime.now()))
    return resp


@app.route('/voteContribution', methods=['POST'])
def voteContribution():
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


@app.route('/voteComment', methods=['POST'])
def voteComment():
    username = decode_auth_token(request.cookies.get('token'))
    if username is not None:
        comment_id = request.form['comment']
        action = request.form['action']
        comment_voted = UserCommentVoted(username, comment_id)
        if action == 'vote':
            comment_voted.save(repository)
        elif action == 'unvote':
            comment_voted.delete(repository)
    resp = make_response(redirect(''))
    return resp


@app.route('/submit')
def submit():
    username = decode_auth_token(request.cookies.get('token'))
    if username is not None:
        user = User.get(repository, username)
        return render_template('submit.html', user=user)
    return redirect('')


@app.route('/contribution')
def get_contribution():
    contribution_id = request.args.get('id')
    contribution = Contribution.get_contribution(repository, contribution_id)
    comments = Comment.get_comments_by_contribution(repository, contribution_id)
    contribution.n_comments = len(comments)
    username = decode_auth_token(request.cookies.get('token'))
    all_children = []
    comments_voted = []
    if username is not None:
        comments_voted = UserCommentVoted.get_voted(repository, username)
    for comment in comments:
        comment.voted = comment.id in [cv['comment_id'] for cv in comments_voted]
        children = Comment.get_comments_by_parent(repository, comment.id)
        all_children.extend(children)
        comment.children = children
    for child in all_children:
        child.voted = child.id in [cv['comment_id'] for cv in comments_voted]
        # TODO: Falta votar ultim child
    parents_comments = []
    for comment in comments:
        if not comment.id in [c.id for c in all_children]:
            parents_comments.append(comment)
    if username is not None:
        user = User.get(repository, username)
        contributions_voted = UserContributionVoted.get_voted(repository, username)
        voted = contribution.id in [cv['contribution_id'] for cv in contributions_voted]
        return render_template('contribution.html', contribution=contribution, comments=parents_comments, user=user,
                               voted=voted)
    return render_template('contribution.html', contribution=contribution, comments=parents_comments)


@app.route('/newPost', methods=['POST'])
def new_post():
    title = request.form["title"]
    url = request.form["url"]
    text = request.form["text"]
    time = datetime.datetime.now()
    user = decode_auth_token(request.cookies.get('token'))

    if url != '' and text == '' and not Contribution.exists(repository, url):
        contribution = Contribution(title, url, text, time, user, ContributionTypes.NEW.value, 0)
    elif text != '' and url == '':
        contribution = Contribution(title, url, text, time, user, ContributionTypes.ASK.value, 0)
    elif text != '' and url != '':
        return redirect(url_for('submit'))
    else:
        return redirect(url_for('submit'))
    contribution.save(repository)
    return redirect('')


@app.route('/doComment', methods=['POST'])
def new_comment():
    user = decode_auth_token(request.cookies.get('token'))
    time = datetime.datetime.now()
    contribution = request.form["contribution"]
    text = request.form["text"]
    if user is not None and text:
        if text != '':
            comment = Comment(user, time, text, contribution, 0)
        else:
            return redirect(url_for('get_contribution', id=contribution))
        comment.save(repository)
    return redirect(url_for('get_contribution', id=contribution))


@app.route('/ask')
def ask():
    contributions = Contribution.get_asks(repository)
    username = decode_auth_token(request.cookies.get('token'))
    if username is not None:
        contributions_voted = UserContributionVoted.get_voted(repository, username)
        for c in contributions:
            c.voted = c['id'] in [cv['contribution_id'] for cv in contributions_voted]
            aux = Comment.get_number_comments_by_contribution(repository, str(c['id']))
            c['n_comments'] = aux[0]['n_comments']
        user = User.get(repository, username)
        return render_template('home.html', contributions=contributions, user=user)
    else:
        for c in contributions:
            aux = Comment.get_number_comments_by_contribution(repository, str(c['id']))
            c.n_comments = aux[0]['n_comments']
        return render_template('home.html', contributions=contributions)


@app.route('/new')
def new():
    contributions = Contribution.get_contributions_new(repository)
    username = decode_auth_token(request.cookies.get('token'))
    for c in contributions:
        aux = Comment.get_number_comments_by_contribution(repository, str(c['id']))
        c['n_comments'] = aux[0]['n_comments']
    if username is not None:
        user = User.get(repository, username)
        contributions_voted = UserContributionVoted.get_voted(repository, username)
        for c in contributions:
            c.voted = c['id'] in [cv['contribution_id'] for cv in contributions_voted]
        return render_template('home.html', contributions=contributions, user=user)
    return render_template('home.html', contributions=contributions)


@app.route('/editProfile')
def edit_profile():
    username = decode_auth_token(request.cookies.get('token'))
    token_user = request.cookies.get('token')
    if username is not None:
        user = User.get(repository, username)
        return render_template('editProfile.html', user=user, token=token_user)
    return redirect('')


@app.route('/updateUser', methods=['POST'])
def update_profile():
    username = decode_auth_token(request.cookies.get('token'))
    if username is not None:
        user = User.get(repository, username)
        user.update(repository, request.form["about"])
        return render_template('editProfile.html', user=user)
    return redirect('')


@app.route('/reply')
def reply():
    username = decode_auth_token(request.cookies.get('token'))
    comment_id = request.args.get('id')
    if username is not None:
        user = User.get(repository, username)
        comment = Comment.get_comment(repository, comment_id)
        return render_template('reply.html', user=user, comment=comment)
    return redirect('')


@app.route('/newReply', methods=['POST'])
def new_reply():
    username = decode_auth_token(request.cookies.get('token'))
    text = request.form["text"]
    contribution = request.form["contribution"]
    if username is not None and text:
        parent = request.form["parent"]
        comment = Comment(username, datetime.datetime.now(), text, contribution, parent)
        comment.save(repository)
    return redirect('contribution?id=' + contribution)


@app.route('/api/asks')
def return_asks():
    contributions = Contribution.get_asks(repository)
    news_to_show = []
    for c in contributions:
        aux = Comment.get_number_comments_by_contribution(repository, str(c['id']))
        c['n_comments'] = aux[0]['n_comments']
        new_attributes = {
            "id": c['id'],
            "title": c['title'],
            "text": c['text'],
            "time": c['time'],
            "user": c['user'],
            "n_votes": c['n_votes'],
            "n_comments": c['n_comments']
        }
        news_to_show.append(new_attributes)
    return Response(json.dumps(news_to_show), mimetype='application/json')


@app.route('/api/asks', methods=['POST'])
def create_new_ask():
    if 'Authorization' not in request.headers:
        return '', 401
    username = decode_auth_token(request.headers['Authorization'])
    if username is None:
        return '', 401
    json = request.get_json()
    ask = Contribution(title=json['title'], url=None, text=json['text'], time=datetime.datetime.now(),
                       username=username, kind=ContributionTypes.ASK.value)
    ask.save(repository)

    return jsonify(ask.toJSON())


@app.route('/api/news')
def return_news():
    contributions = Contribution.get_news_home(repository)
    news_to_show = []
    for c in contributions:
        aux = Comment.get_number_comments_by_contribution(repository, str(c['id']))
        c['n_comments'] = aux[0]['n_comments']
        new_attributes = {
            "id": c['id'],
            "title": c['title'],
            "url": c['url'],
            "time": c['time'],
            "user": c['user'],
            "n_votes": c['n_votes'],
            "n_comments": c['n_comments']
        }
        news_to_show.append(new_attributes)
    return Response(json.dumps(news_to_show), mimetype='application/json')


@app.route('/api/newest')
def return_newest_contributions():
    contributions = Contribution.get_contributions_new(repository)
    for c in contributions:
        aux = Comment.get_number_comments_by_contribution(repository, str(c['id']))
        c['n_comments'] = aux[0]['n_comments']
    return Response(json.dumps(contributions), mimetype='application/json')


@app.route('/api/users/<user>', methods=['GET'])
def return_asked_user(user):
    user_to_show = User.get(repository, user)
    if user_to_show is None:
        return '', 404
    return jsonify(user_to_show.toJSON())


@app.route('/api/contributions/<contribution>', methods=['GET'])
def return_asked_contribution(contribution):
    contribution_to_show = Contribution.get_contribution(repository, contribution)
    if contribution_to_show is None:
        return '', 404
    return jsonify(contribution_to_show.toJSON())


@app.route('/api/contributions/<contribution_id>/vote', methods=['POST', 'DELETE'])
def vote_contribution_api(contribution_id):
    if 'Authorization' not in request.headers:
        return '', 401
    username = decode_auth_token(request.headers['Authorization'])
    if username is None:
        return '', 401
    contribution = Contribution.get_contribution(repository, contribution_id)
    if contribution is None:
        return '', 404
    if contribution.username == username:
        return '', 403
    contribution_voted = UserContributionVoted(username, contribution_id)
    if request.method == 'POST':
        if UserContributionVoted.exists(repository, contribution_id, username):
            return '', 409
        contribution_voted.save(repository)
    elif request.method == 'DELETE':
        if not UserContributionVoted.exists(repository, contribution_id, username):
            return '', 404
        contribution_voted.delete(repository)
    return return_asked_contribution(contribution_id)


@app.route('/api/comments/<comment_id>/vote', methods=['POST', 'DELETE'])
def vote_comment_api(comment_id):
    if 'Authorization' not in request.headers:
        return '', 401
    username = decode_auth_token(request.headers['Authorization'])
    if username is None:
        return '', 401
    comment = Comment.get_comment(repository, comment_id)
    if comment is None:
        return '', 404
    if comment.username == username:
        return '', 403
    comment_voted = UserCommentVoted(username, comment_id)
    if request.method == 'POST':
        if UserCommentVoted.exists(repository, comment_id, username):
            return '', 409
        comment_voted.save(repository)
    elif request.method == 'DELETE':
        if not UserCommentVoted.exists(repository, comment_id, username):
            return '', 404
        comment_voted.delete(repository)
    return '', 200


@app.route('/api/users/<userput>', methods=['PUT'])
def return_updated_user(userput):
    if 'Authorization' not in request.headers:
        return '', 401
    username = decode_auth_token(request.headers['Authorization'])
    if username is None:
        return '', 401
    if username != userput:
        return '', 403
    json = request.get_json()
    user_to_return = User.get(repository, username)
    user_to_return.update(repository, json['about'])
    return jsonify(user_to_return.toJSON())


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
         Comment.get_table_creation(), UserCommentVoted.get_table_creation()])

    basicConfig(filename=os.environ['LOG'], level=INFO)

    app.config.update(TEMPLATES_AUTO_RELOAD=True)
    app.run(host=str(os.environ['HOST']), port=int(os.environ['PORT']))
