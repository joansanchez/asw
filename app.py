import datetime
import os
from logging import basicConfig, INFO

from flask import Flask, logging, render_template, request, redirect, url_for, make_response, jsonify, json, Response
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from yaml import Loader, load

from comment import Comment
from contribution import Contribution, ContributionTypes
from google_login import validate_token
from persistence import Persistence
from token_generator import encode_auth_token, decode_auth_token
from user import User
from usercommentvoted import UserCommentVoted
from usercontributionvoted import UserContributionVoted

app = Flask(__name__, static_folder='./static')
CORS(app)

SWAGGER_URL = '/api/docs'
swagger_path = os.environ['SWAGGER']

swagger_yml = load(open(swagger_path, 'r'), Loader=Loader)

blueprint = get_swaggerui_blueprint(SWAGGER_URL, swagger_path, config={'spec': swagger_yml})

app.register_blueprint(blueprint, url_prefix=SWAGGER_URL)


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
        return jsonify('Forbidden'), 403

    exists = User.exists(repository, email)
    if not exists:
        user = User(email)
        user.save(repository)
    resp = make_response(redirect(''))
    resp.set_cookie('token', encode_auth_token(email))
    return resp


@app.route('/api/users', methods=['POST'])
def create_user():
    json = request.get_json()
    token = json['token']
    email = json['email']
    try:
        validate_token(token)
    except ValueError:
        return jsonify('Forbidden'), 403

    exists = User.exists(repository, email)
    if not exists:
        User(email).save(repository)
    json = User.get(repository, email).toJSON()
    json['token'] = encode_auth_token(email).decode("utf-8")
    return jsonify(json)


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
    resp = make_response(redirect(request.form['view']))
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
    resp = make_response(redirect(request.form['view']))
    return resp


@app.route('/submit')
def submit():
    username = decode_auth_token(request.cookies.get('token'))
    error = request.args.get('error')
    if username is not None:
        user = User.get(repository, username)
        if error is not None:
            return render_template('submit.html', user=user, error=error)
        elif error is None:
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
        if comment.id not in [c.id for c in all_children]:
            parents_comments.append(comment)
    if username is not None:
        user = User.get(repository, username)
        contributions_voted = UserContributionVoted.get_voted(repository, username)
        voted = contribution.id in [cv['contribution_id'] for cv in contributions_voted]
        return render_template('contribution.html', contribution=contribution, comments=parents_comments, user=user,
                               voted=voted)
    return render_template('contribution.html', contribution=contribution, comments=parents_comments)


@app.route('/deleteCom', methods=['POST'])
def delete_comment():
    comment_id = request.form['com_id']
    contribution_id = request.form['con_id']
    Comment.delete_comment(repository, comment_id)
    return redirect("contribution?id={0}".format(contribution_id))


@app.route('/deleteCon', methods=['POST'])
def delete_contribution():
    contribution_id = request.form['con_id']
    Comment.delete_comments_from_contribution(repository, contribution_id)
    Contribution.delete_contribution(repository, contribution_id)
    return redirect('')


@app.route('/newPost', methods=['POST'])
def new_post():
    title = request.form["title"]
    url = request.form["url"]
    text = request.form["text"]
    time = datetime.datetime.now()
    user = decode_auth_token(request.cookies.get('token'))
    if user is None:
        error = "ERROR: You must be logged to make a new post"
        return redirect("submit?error={0}".format(error))
    elif url != '' and text == '' and title != '' and not Contribution.exists(repository, url):
        contribution = Contribution(title, url, None, time, user, ContributionTypes.NEW.value, 0)
    elif text != '' and url == '' and title != '':
        contribution = Contribution(title, None, text, time, user, ContributionTypes.ASK.value, 0)
    elif text != '' and url != '':
        error = "ERROR: You can only fill URL or Text but not both"
        return redirect("submit?error={0}".format(error))
    elif url != '' and text == '' and Contribution.exists(repository, url):
        contribution_id = Contribution.get_contribution_id_by_URL(repository, url)
        return redirect("contribution?id={0}".format(contribution_id))
    elif text == '' and url == '' and title != '':
        error = "ERROR: You have to fill either URL or Text"
        return redirect("submit?error={0}".format(error))
    else:
        error = "ERROR: You must fill title"
        return redirect("submit?error={0}".format(error))
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
            comment = Comment(user, time, text, contribution, None)
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
        aux = UserContributionVoted.get_votes_contribution(repository, str(c['id']))
        contribution_votes = []
        for aux_v in aux:
            contribution_votes.append(aux_v['username'])
        c['contribution_votes'] = contribution_votes
        new_attributes = {
            "id": c['id'],
            "title": c['title'],
            "text": c['text'],
            "time": c['time'],
            "user": c['user'],
            "n_votes": c['n_votes'],
            "n_comments": c['n_comments'],
            "contribution_votes": c['contribution_votes']
        }
        news_to_show.append(new_attributes)
    return Response(json.dumps(news_to_show), mimetype='application/json')


@app.route('/api/asks', methods=['POST'])
def create_new_ask():
    if 'Authorization' not in request.headers:
        return jsonify(''), 401
    username = decode_auth_token(request.headers['Authorization'])
    if username is None:
        return jsonify(''), 401
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
        aux = UserContributionVoted.get_votes_contribution(repository, str(c['id']))
        contribution_votes = []
        for aux_v in aux:
            contribution_votes.append(aux_v['username'])
        c['contribution_votes'] = contribution_votes
        new_attributes = {
            "id": c['id'],
            "title": c['title'],
            "url": c['url'],
            "time": c['time'],
            "user": c['user'],
            "n_votes": c['n_votes'],
            "n_comments": c['n_comments'],
            "contribution_votes": c['contribution_votes']
        }
        news_to_show.append(new_attributes)
    return Response(json.dumps(news_to_show), mimetype='application/json')


@app.route('/api/users/<username>/threads')
def return_threads(username):
    user = User.get(repository, username)
    if user is None:
        return jsonify('Not Found'), 404
    if user is not None:
        comments = get_user_comments(username)
        return jsonify(comments)


@app.route('/api/news', methods=['POST'])
def create_new_new():
    if 'Authorization' not in request.headers:
        return jsonify('Unauthorized'), 401
    username = decode_auth_token(request.headers['Authorization'])
    if username is None:
        return jsonify(''), 401
    json = request.get_json()
    new = Contribution(title=json['title'], url=json['url'], text=None, time=datetime.datetime.now(),
                       username=username, kind=ContributionTypes.NEW.value)
    if Contribution.exists(repository, new.url):
        new = Contribution.get_contribution_by_url(repository, new.url)
        return jsonify(new.toJSON()), 409
    new.save(repository)
    return jsonify(new.toJSON())


@app.route('/api/newest')
def return_newest_contributions():
    contributions = Contribution.get_contributions_new(repository)
    for c in contributions:
        aux = Comment.get_number_comments_by_contribution(repository, str(c['id']))
        c['n_comments'] = aux[0]['n_comments']
        aux = UserContributionVoted.get_votes_contribution(repository, str(c['id']))
        contribution_votes = []
        for aux_v in aux:
            contribution_votes.append(aux_v['username'])
        c['contribution_votes'] = contribution_votes
    return Response(json.dumps(contributions), mimetype='application/json')


@app.route('/api/users/<user>', methods=['GET'])
def return_asked_user(user):
    user_to_show = User.get(repository, user)
    if user_to_show is None:
        return jsonify('Not Found'), 404
    return jsonify(user_to_show.toJSON())


@app.route('/api/contributions/<contribution_id>', methods=['GET'])
def return_asked_contribution(contribution_id):
    if not Contribution.exists_contribution(repository, contribution_id):
        return jsonify('Not Found'), 404
    contribution_to_show = Contribution.get_contribution(repository, contribution_id)
    contribution = {
        "id": contribution_to_show.id,
        "title": contribution_to_show.title,
        "url": contribution_to_show.url,
        "text": contribution_to_show.text,
        "time": contribution_to_show.time,
        "user": contribution_to_show.username,
        "kind": contribution_to_show.kind,
        "n_votes": contribution_to_show.n_votes,
        "comments": get_contribution_comments(contribution_id)
    }
    votes = UserContributionVoted.get_votes_contribution(repository, contribution_id)
    contribution_votes = []
    for vote in votes:
        contribution_votes.append(vote['username'])
    contribution['contribution_votes'] = contribution_votes
    contribution['n_comments'] = Comment.get_number_comments_by_contribution(repository, contribution_id)[0][
        'n_comments']
    return jsonify(contribution)

@app.route('/api/comments/<comment_id>', methods=['GET'])
def return_asked_comment(comment_id):
    if not Comment.exists_comment(repository, comment_id):
        return jsonify('Not Found'), 404
    comment_to_show = Comment.get_comment(repository, comment_id)
    contribution = {
        "id": comment_to_show.id,
        "username": comment_to_show.username,
        "time": comment_to_show.time,
        "text": comment_to_show.text,
        "contribution_id": comment_to_show.contribution_id,
        "parent_id": comment_to_show.parent_id,
        #"n_votes": comment_to_show.n_votes
    }
    return jsonify(contribution)

def parse_comment(comment):
    children = Comment.get_comments_by_parent(repository, comment.id)
    parsed_children = []
    for child in children:
        votes = UserCommentVoted.get_votes_of_a_comment(child.id, repository)
        child.votes = votes
        parsed_child = parse_comment(child)
        parsed_children.append(parsed_child)
    parsed_comment = {
        "id": comment.id,
        "username": comment.username,
        "time": comment.time,
        "text": comment.text,
        "contribution_id": comment.contribution_id,
        "parent_id": comment.parent_id,
        "children": parsed_children,
        "n_votes": comment.n_votes,
        "votes": comment.votes
    }
    if hasattr(comment, 'contribution_title'):
        parsed_comment['contribution_title'] = comment.contribution_title
    return parsed_comment


def get_contribution_comments(contribution_id):
    comments = Comment.get_comments_by_contribution(repository, contribution_id)
    results = []
    for comment in comments:
        votes = UserCommentVoted.get_votes_of_a_comment(comment.id, repository)
        comment.votes = votes
        if comment.parent_id is None:
            result = parse_comment(comment)
            results.append(result)
    return results


def get_user_comments(user):
    comments = Comment.get_comments_by_user(repository, user)
    results = []
    for comment in comments:
        votes = UserCommentVoted.get_votes_of_a_comment(comment.id, repository)
        comment.votes = votes
        result = parse_comment(comment)
        results.append(result)
    return results


@app.route('/api/contributions/<contribution_id>', methods=['DELETE'])
def delete_contribution_api(contribution_id):
    if 'Authorization' not in request.headers:
        return jsonify('Unauthorized'), 401
    username = decode_auth_token(request.headers['Authorization'])
    if username is None:
        return jsonify('Unauthorized'), 401
    if not Contribution.exists_contribution(repository, contribution_id):
        return jsonify('Not Found'), 404
    contribution = Contribution.get_contribution(repository, contribution_id)
    if contribution.username != username:
        return jsonify('Forbidden'), 403
    Comment.delete_comments_from_contribution(repository, contribution_id)
    Contribution.delete_contribution(repository, contribution_id)
    return jsonify('Successful delete'), 204


@app.route('/api/comments/<comment_id>', methods=['DELETE'])
def delete_comment_api(comment_id):
    if 'Authorization' not in request.headers:
        return jsonify('Unauthorized'), 401
    username = decode_auth_token(request.headers['Authorization'])
    if username is None:
        return jsonify('Unauthorized'), 401
    if not Comment.exists_comment(repository, comment_id):
        return jsonify('Not Found'), 404
    comment = Comment.get_comment(repository, comment_id)
    if comment.username != username:
        return jsonify('Forbidden'), 403
    Comment.delete_comment(repository, comment_id)
    return jsonify('Successful delete'), 204


@app.route('/api/contributions/<contribution_id>/vote', methods=['POST', 'DELETE'])
def vote_contribution_api(contribution_id):
    if 'Authorization' not in request.headers:
        return jsonify('Unauthorized'), 401
    username = decode_auth_token(request.headers['Authorization'])
    if username is None:
        return jsonify('Unauthorized'), 401
    if not Contribution.exists_contribution(repository, contribution_id):
        return jsonify('Not Found'), 404
    contribution = Contribution.get_contribution(repository, contribution_id)
    if contribution.username == username:
        return jsonify('Forbidden'), 403
    contribution_voted = UserContributionVoted(username, contribution_id)
    if request.method == 'POST':
        if UserContributionVoted.exists(repository, contribution_id, username):
            return jsonify('Conflict'), 409
        contribution_voted.save(repository)
    elif request.method == 'DELETE':
        if not UserContributionVoted.exists(repository, contribution_id, username):
            return jsonify('Not Found'), 404
        contribution_voted.delete(repository)
    return return_asked_contribution(contribution_id)


@app.route('/api/contributions/<contribution_id>/comments', methods=['POST'])
def create_new_comment(contribution_id):
    if 'Authorization' not in request.headers:
        return jsonify('Unauthorized'), 401
    username = decode_auth_token(request.headers['Authorization'])
    if username is None:
        return jsonify('Unauthorized'), 401
    if not Contribution.exists_contribution(repository, contribution_id):
        return jsonify('Not Found'), 404
    json = request.get_json()
    comment = Comment(username, datetime.datetime.now(), json['text'], contribution_id, None)
    comment.save(repository)
    return jsonify(comment.toJSON())


@app.route('/api/comments/<parent_id>/replies', methods=['POST'])
def create_new_reply(parent_id):
    if 'Authorization' not in request.headers:
        return jsonify('Unauthorized'), 401
    username = decode_auth_token(request.headers['Authorization'])
    if username is None:
        return jsonify('Unauthorized'), 401
    if not Comment.exists_comment(repository, parent_id):
        return jsonify('Not Found'), 404
    json = request.get_json()
    parent_comment = Comment.get_comment(repository, parent_id)
    comment = Comment(username, datetime.datetime.now(), json['text'], parent_comment.contribution_id, parent_id)
    comment.save(repository)
    return jsonify(comment.toJSON())


@app.route('/api/comments/<comment_id>/vote', methods=['POST', 'DELETE'])
def vote_comment_api(comment_id):
    if 'Authorization' not in request.headers:
        return jsonify('Unauthorized'), 401
    username = decode_auth_token(request.headers['Authorization'])
    if username is None:
        return jsonify('Unauthorized'), 401
    if not Comment.exists_comment(repository, comment_id):
        return jsonify('Not Found'), 404
    comment = Comment.get_comment(repository, comment_id)
    if comment.username == username:
        return jsonify('Forbidden'), 403
    comment_voted = UserCommentVoted(username, comment_id)
    if request.method == 'POST':
        if UserCommentVoted.exists(repository, comment_id, username):
            return jsonify('Conflict'), 409
        comment_voted.save(repository)
    elif request.method == 'DELETE':
        if not UserCommentVoted.exists(repository, comment_id, username):
            return jsonify('Not Found'), 404
        comment_voted.delete(repository)
    return return_asked_contribution(str(comment.contribution_id))


@app.route('/api/users/<userput>', methods=['PUT'])
def return_updated_user(userput):
    if 'Authorization' not in request.headers:
        return jsonify('Unauthorized'), 401
    username = decode_auth_token(request.headers['Authorization'])
    if username is None:
        return jsonify('Unauthorized'), 401
    if username != userput:
        return jsonify('Forbidden'), 403
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
    app.run(host=str(os.environ['HOST']), port=int(os.environ['PORT']), threaded=True)
