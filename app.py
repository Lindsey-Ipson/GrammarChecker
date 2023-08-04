import os

from flask import Flask, render_template, request, flash, redirect, session, g, url_for
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import SignupForm, LoginForm, SubmitTextForm
from models import db, connect_db, User

import pdb
import bcrypt

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql://kksluwoo:k-o2ThSbwF-GIbqCJKw7iQ9hnSv0Xd7X@mahmud.db.elephantsql.com/kksluwoo'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
# app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")

app.config['DEBUG'] = True

toolbar = DebugToolbarExtension(app)

connect_db(app)


# JUST ADDED
with app.app_context():
    db.drop_all()
    db.create_all()

    # Commit the changes to the database
    db.session.commit()


##############################################################################
# User signup/login/logout

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    print('starting logout')
    print('do_logout session[CURR_USER_KEY]', session[CURR_USER_KEY])

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/')
def redirect_from_root():
    """Show signup/login page if not logged in, otherwise show submit_text.html"""

    if not g.user:
        return redirect('/signup')
    else:
        return render_template('hello.html')


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.
    Create new user and add to DB. Redirect to home page.
    If form not valid, present form.
    If there already is a user with that username: flash message
    and re-present form.
    """

    form = SignupForm()

    if form.is_submitted() and form.validate():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.is_submitted() and form.validate():

        print('form.username.data', form.username.data)
        print('form.password.data', form.password.data)

        user = User.authenticate(form.username.data,
                                 form.password.data)
        
        print('Login route user', user)

        if user:
            print('BREAK222222222222222222>>>>>>>>>>>>>>>>>>')
            do_login(user)
            print('BREAK33333333333333333>>>>>>>>>>>>>>>>>>>>>>')
            flash(f"Hello, {user.username}!", "success")
            # TODO change redirect
            return redirect("/")

        print('BREAK4444444444444444444>>>>>>>>>>>>>>>>>>>>>>>>')
        flash("Invalid credentials.", 'danger')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()
    print('just did do_logout')
    # print('session[CURR_USER_KEY]', session[CURR_USER_KEY])
    flash("You've been logged out.")
    return redirect('/login')


# Grammar Routes

@app.route('/submit_text', methods=["GET", "POST"])
def submit_text():
    """Show form to submit text and handle submission"""

    form = SubmitTextForm()

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    if form.is_submitted() and form.validate():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        # if user:
        #     text = Text(

        #     )
        return

    return render_template('submit_text.html')
