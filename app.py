from flask import Flask, jsonify
from flask import render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import *

app = Flask(__name__)

APP_NAME = 'Global Launchpad Initiative'

# Database Engine
engine = create_engine('postgresql://glpi:safekeep@localhost:5432/glpidb')
Base.metadata.create_all(engine)

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/get/posts')
def get_all_posts():
    posts = session.query(Content).all()
    return render_template('temp.html', posts=posts)


@app.route('/get/categories')
def get_all_categories():
    categories = session.query(Category).all()
    return jsonify(Categories=[cat.serialize for cat in categories])


if __name__ == '__main__':
    app.secret_key = 'SSHH_Do_not_tell'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
