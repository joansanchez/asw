
import os

from flask import Flask, logging, render_template

from contribution import Contribution
from persistence import Persistence
from user import User

app = Flask(__name__, static_folder='./static')

pageSize = 30

@app.route('/')
def home(p=1):
    contributions = Contribution.get_news(repository)
    offset = pageSize * (p-1)
    contributions = contributions[offset:offset+pageSize]
    p = p+1
    return render_template('home.html', contributions=contributions, p = p)

if __name__ == '__main__':
    repository = Persistence(os.environ['DB_PATH'], logging.getLogger(__name__))
    repository.init_db([User.get_table_creation(), Contribution.get_table_creation()])
    app.run()