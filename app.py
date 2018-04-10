import os

from flask import Flask, logging

from contribution import Contribution
from persistence import Persistence

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    repository = Persistence(os.environ['DB_PATH'], logging.getLogger(__name__))
    repository.init_db([Contribution.get_table_creation()])
    app.run()
