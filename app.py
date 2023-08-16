import os

from flask import Flask, render_template, request, flash, redirect, session, g, url_for
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from errors import generate_api_response, isolate_errors_from_api_response, add_errors_to_db, generate_grammar_errors_html, grammar_error_descriptions, apply_all_corrections, add_errors_to_db, generate_spelling_errors_html, add_text_to_db, order_error_types_by_frequency, create_show_all_grammar_errors_objects, get_misspelled_word_counts, create_spelling_error_html_objects

from forms import SignupForm, LoginForm, SubmitTextForm
from models import db, connect_db, User, Text

import pdb
import bcrypt

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

        return redirect("/")

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
            # TODO change redirect
            return redirect("/")

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
        return redirect("/")
    
    if form.is_submitted() and form.validate():

        user = g.user
        
        text_to_submit = form.text.data

        api_response = generate_api_response(text_to_submit)

        grammar_errors_list = isolate_errors_from_api_response(api_response, 'grammar')
        spelling_errors_list = isolate_errors_from_api_response(api_response, 'spelling')

        corrected_text = apply_all_corrections(text_to_submit, grammar_errors_list, spelling_errors_list)

        new_text = add_text_to_db(user.id, text_to_submit, corrected_text)

        add_errors_to_db(grammar_errors_list, spelling_errors_list, user.id, new_text.id)

        html_grammar_errors = generate_grammar_errors_html(grammar_errors_list, grammar_error_descriptions)
        html_spelling_errors = generate_spelling_errors_html(spelling_errors_list)

        db.session.add(new_text)
        db.session.commit()

        flash("Text submitted successfully!", "success")

        return render_template('review_text_submission.html', text=new_text, html_grammar_errors=html_grammar_errors,html_spelling_errors=html_spelling_errors) 

    return render_template('submit_text.html', form=form)


@app.route('/show_all_grammar_errors', methods=["GET", "POST"])
def show_all_grammar_errors():

    user = g.user

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/signup")

    error_types_ordered_by_frequency = order_error_types_by_frequency(user.id)

    show_all_errors_objects = create_show_all_grammar_errors_objects(error_types_ordered_by_frequency)

    return render_template('all_grammar_errors.html', all_grammar_errors=show_all_errors_objects, grammar_error_descriptions=grammar_error_descriptions)


@app.route('/show_all_spelling_errors', methods=["GET", "POST"])
def show_all_spelling_errors():

    user = g.user

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/signup")

    word_counts = get_misspelled_word_counts(user.id)

    spelling_error_html_objects = create_spelling_error_html_objects(word_counts, user.id)

    return render_template('all_spelling_errors.html', all_spelling_errors=spelling_error_html_objects)





