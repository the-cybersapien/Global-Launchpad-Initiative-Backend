import calendar
import json
import random
import string
from datetime import datetime

import httplib2
import requests
from flask import Flask, jsonify
from flask import flash
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import session as login_session

from oauth2client.client import FlowExchangeError
from oauth2client.client import flow_from_clientsecrets
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from database import *

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secret.json', 'r').read())['web']['client_id']
APP_NAME = 'Global Launchpad Initiative'

# Database Engine
engine = create_engine('postgresql://glpi:safekeep@localhost:5432/glpidb')
Base.metadata.create_all(engine)

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Helpers to create Users
def create_user(login_session):
    new_user = User(name=login_session['username'], email=login_session['email'], photo=login_session['photo'])
    session.add(new_user)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def get_user(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def get_user_id(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except NoResultFound:
        return None


def make_res(message, errorCode=401):
    response = make_response(json.dumps(message), errorCode)
    response.headers['Content-Type'] = 'application/json'
    return response


def get_current_epoch():
    d = datetime.utcnow()
    unix_time = calendar.timegm(d.utctimetuple())
    return unix_time


# Google Connect Method
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Verify the login state token
    if request.args.get('state') != login_session['state']:
        return make_res('Invalid Login attempt!')
    code = request.data

    try:
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code=code)

        # Check the validity of access token
        access_token = credentials.access_token
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
        h = httplib2.Http()
        res = str(h.request(url, 'GET')[1], encoding='utf-8')
        res.replace('\n', '')
        result = json.loads(res)

        if result.get('error') is not None:
            # Error verifying server side token
            return make_res(json.dumps(result.get('error')), 500)

        gplus_id = credentials.id_token['sub']
        if result['user_id'] != gplus_id:
            # Access Token not for intended user
            return make_res(json.dumps('Token is not for intended User'))

        if result['issued_to'] != CLIENT_ID:
            # Token invalid for our app
            return make_res(json.dumps("Client ID does not match!"))

        stored_credentials = login_session.get('credentials')
        stored_gplus_id = login_session.get('gplus_id')

        if stored_credentials is not None and gplus_id == stored_gplus_id:
            # User already connected
            return make_res(json.dumps('Current User Already Connected!'), 200)

        # Store the credentials for future use
        login_session['credentials'] = credentials.access_token
        login_session['gplus_id'] = gplus_id

        # Get User Info
        userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
        params = {'access_token': credentials.access_token, 'alt': 'json'}
        answer = requests.get(userinfo_url, params=params)

        data = answer.json()

        login_session['username'] = data['name']
        login_session['photo'] = data['picture']
        login_session['email'] = data['email']

        user_id = get_user_id(login_session['email'])

        if not user_id:
            user_id = create_user(login_session)

        login_session['user_id'] = user_id

        output = 'Login Successful!'
        flash("Logged in successfully!")
        return make_res(output, 200)

    except FlowExchangeError:
        return make_res('Failed to upgrade auth code.')


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('credentials')
    if access_token is None:
        return make_res('Current User not connected!')

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    res = h.request(url, method='GET')[0]
    if res['status'] == '200':
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['photo']
        del login_session['email']
        flash('Successfully logged out!')
        return redirect(url_for('home'))
    else:
        make_res(jsonify(str(res)), 200)


@app.route('/login')
def show_login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    categories = session.query(Category).all()
    login_session['state'] = state
    return render_template('login.html', login_session=login_session, STATE=state, categories=categories)


@app.route('/')
def home():
    categories = session.query(Category).all()
    posts = session.query(Content).all()
    return render_template('index.html', login_session=login_session, categories=categories, posts=posts)


@app.route('/get/<int:cat_id>/posts')
def get_posts(cat_id):
    categories = session.query(Category).all()
    posts = session.query(Content).filter_by(category_id=cat_id).all()
    return render_template('index.html', login_session=login_session, categories=categories, posts=posts)


@app.route('/new/post', methods=['GET', 'POST'])
@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id=-1):
    print(request.form)
    if 'username' not in login_session:
        flash('You need to login to make changes!')
        return redirect(url_for('show_login'))
    if request.method == 'POST':
        form = request.form
        try:
            post = session.query(Content).filter_by(id=post_id).one()
            post.title = form['post_title'],
            post.description = form['post_description'],
            post.date = form['post_date'],
            post.url = form['post_url'],
            post.timeAdded = get_current_epoch(),
            post.author_id = login_session['user_id'],
            post.category_id = form['cat_id']
        except NoResultFound:
            post = Content(
                title=form['post_title'],
                description=form['post_description'],
                date=form['post_date'],
                url=form['post_url'],
                timeAdded=get_current_epoch(),
                author_id=login_session['user_id'],
                category_id=form['cat_id']
            )
        session.add(post)
        session.commit()
        if post_id == -1:
            flash('Added Successfully!')
        else:
            flash('Update Successful!')
        return redirect(url_for('home'))
    else:
        try:
            post = session.query(Content).filter_by(id=post_id).one()
        except NoResultFound:
            post = None
        categories = session.query(Category).all()

        return render_template('post_editor.html', login_session=login_session, categories=categories, post=post)


@app.route('/api/get/posts')
def get_posts_json():
    posts = session.query(Content).all()
    return jsonify([post.serialize for post in posts])


@app.route('/api/get/<int:cat_id>/posts')
def get_cat_posts_json(cat_id):
    posts = session.query(Content).filter_by(category_id=cat_id).all()
    return jsonify([post.serialize for post in posts])


@app.route('/api/get/categories')
def get_all_categories():
    categories = session.query(Category).all()
    return jsonify([cat.serialize for cat in categories])


@app.route('/new/category', methods=['GET', 'POST'])
@app.route('/cat/<int:cat_id>/edit', methods=['GET', 'POST'])
def edit_cat(cat_id=-1):
    if 'username' not in login_session:
        flash("You need to login to make changes!")
        return redirect(url_for('show_login'))
    if request.method == 'POST':
        try:
            category = session.query(Category).filter_by(id=cat_id).one()
            category.name = request.form['cat_name']
        except NoResultFound:
            # Will enter here if category doesn't already exists
            category = Category(name=request.form['cat_name'])
        session.add(category)
        session.commit()
        if cat_id == -1:
            flash('Category Added Successfully!')
        else:
            flash('Category %s updated' % category.name)
        return redirect(url_for('home'))
    else:
        try:
            category = session.query(Category).filter_by(id=cat_id).one()
        except NoResultFound:
            category = None
        categories = session.query(Category).all()
        return render_template('cat_editor.html', login_session=login_session, category=category, categories=categories)


if __name__ == '__main__':
    app.secret_key = 'SSHH_Do_not_tell'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
