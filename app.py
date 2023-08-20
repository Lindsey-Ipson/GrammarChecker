import os

from flask import Flask, render_template, request, flash, redirect, session, g, url_for
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from errors import generate_api_response, isolate_errors_from_api_response, add_errors_to_db, apply_all_corrections, add_errors_to_db, add_text_to_db, get_error_type_counts, create_review_text_html_errors, create_show_all_html_errors

from forms import SignupForm, LoginForm, SubmitTextForm
from models import db, connect_db, User, Text

import pdb

CURR_USER_KEY = ""

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or, if not set there, use development local db
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql://kksluwoo:k-o2ThSbwF-GIbqCJKw7iQ9hnSv0Xd7X@mahmud.db.elephantsql.com/kksluwoo'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
# app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
app.config['DEBUG'] = True

toolbar = DebugToolbarExtension(app)

connect_db(app)

with app.app_context():
    # db.drop_all()
    db.create_all()
    db.session.commit()


##############################################################################
# User signup/login/logout routes

@app.before_request
def add_user_to_g():

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):

    session[CURR_USER_KEY] = user.id


def do_logout():

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/')
def redirect_from_root():

    if not g.user:
        return redirect('/signup')
    else:
        return redirect('/submit_text')


@app.route('/signup', methods=["GET", "POST"])
def signup():

    form = SignupForm()

    if form.is_submitted() and form.validate():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data
            )
            db.session.add(user)
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('signup.html', form=form)

        do_login(user)

        return redirect("/submit_text")

    else:
        return render_template('signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():

    form = LoginForm()

    if form.is_submitted() and form.validate():

        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/subit_text")

        flash("Invalid credentials.", 'danger')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():

    do_logout()
    flash("You've been logged out.")
    return redirect('/login')


##############################################################################
# Error Routes

@app.route('/submit_text', methods=["GET", "POST"])
def submit_text():

    form = SubmitTextForm()

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/signup")
    
    if form.is_submitted() and form.validate():

        user = g.user
        
        text_to_submit = form.text.data

        api_response = generate_api_response(text_to_submit)

        grammar_errors_from_api = isolate_errors_from_api_response(api_response, 'Grammar')
 
        spelling_errors_from_api = isolate_errors_from_api_response(api_response, 'Spelling')

        corrected_text = apply_all_corrections(text_to_submit, grammar_errors_from_api, spelling_errors_from_api)

        new_text = add_text_to_db(user.id, text_to_submit, corrected_text)

        add_errors_to_db(grammar_errors_from_api, spelling_errors_from_api, user.id, new_text.id)

        grammar_html_errors = create_review_text_html_errors(grammar_errors_from_api, 'grammar')
        spelling_html_errors = create_review_text_html_errors(spelling_errors_from_api, 'spelling')

        db.session.add(new_text)
        db.session.commit()

        flash("Text submitted successfully!", "success")

        return render_template('review_text_submission.html', text=new_text, grammar_html_errors=grammar_html_errors, spelling_html_errors=spelling_html_errors) 

    return render_template('submit_text.html', form=form)


@app.route('/show_all_grammar_errors', methods=["GET"])
def show_all_grammar_errors():

    user = g.user

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/signup")

    error_type_counts = get_error_type_counts(user.id, 'Grammar')

    html_errors = create_show_all_html_errors(error_type_counts, 3, 'Grammar')

    return render_template('all_grammar_errors.html', all_grammar_errors=html_errors)


@app.route('/show_all_spelling_errors', methods=["GET"])
def show_all_spelling_errors():

    user = g.user

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/signup")

    error_type_counts = get_error_type_counts(user.id, 'Spelling')

    html_errors = create_show_all_html_errors(error_type_counts, 3, 'Spelling')

    return render_template('all_spelling_errors.html', all_spelling_errors=html_errors)





