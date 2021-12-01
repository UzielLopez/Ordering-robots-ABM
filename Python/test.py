from flask import Flask
from flask_restful import Api
from flask.json import jsonify


def test_connection(self):
    app = Flask(__name__)
    with app.app_context():
        #test code
        test = {"Robots": [1, 2], "Boxes": [3, 4], "Shelves": [5, 6, 7]}
        print(jsonify(test))
        app.run()


