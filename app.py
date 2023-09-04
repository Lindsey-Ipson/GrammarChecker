import os

from flask import Flask, render_template, request, flash, redirect, session, g, url_for, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from errors import generate_api_response, isolate_errors_from_api_response, add_errors_to_db, apply_all_corrections, add_errors_to_db, add_text_to_db, get_error_type_counts, create_review_text_html_errors, create_show_all_html_errors, create_graph_lists, create_errors_graph, parse_error_subcategory, serialize_grammar_error, add_tester_texts_to_db

from forms import SignupForm, LoginForm, SubmitTextForm
from models import db, connect_db, User, Grammar_Error, Spelling_Error

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import pdb

CURR_USER_KEY = ""

app = Flask(__name__)

app.static_folder = 'static'

# Get DB_URI from environ variable (useful for production/testing) or, if not set there, use development local db
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql://kksluwoo:k-o2ThSbwF-GIbqCJKw7iQ9hnSv0Xd7X@mahmud.db.elephantsql.com/kksluwoo'))
# os.environ['DATABASE_URL'] = "postgresql:///capstone1-test"
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
app.config['DEBUG'] = True

toolbar = DebugToolbarExtension(app)

connect_db(app)

# !!! When testing, comment the following lines
# with app.app_context():  
#     db.drop_all()
#     db.create_all()
#     db.session.commit()


##############################################################################
# User signup/login/logout routes

@app.before_request
def add_user_to_g():
    if not request.path.startswith('/static/'):
        if CURR_USER_KEY in session:
            g.user = User.query.get(session[CURR_USER_KEY])
        else:
            g.user = None


def do_login(user):

    session[CURR_USER_KEY] = user.id


def do_logout():

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    form = SignupForm()
    username_taken = False
    email_taken = False
    taken_attribute = ""

    if form.is_submitted() and form.validate():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data
            )
            db.session.add(user)
            db.session.commit()

        except Exception as e:
            if 'duplicate key value violates unique constraint "users_username_key"' in str(e):
                username_taken = True
                taken_attribute = "Username"
            elif 'duplicate key value violates unique constraint "users_email_key"' in str(e):
                email_taken = True
                taken_attribute = "Email"

            flash(f"{taken_attribute} already taken", 'danger')
            db.session.rollback()
            return render_template('signup.html', form=form)

        if not username_taken and not email_taken:
            g.user=user
            do_login(user)

            if user.username.endswith('_tester'):
                return redirect('/set_up_tester')

            return render_template('new_user.html', username=user.username)

    return render_template('signup.html', form=form, username_taken=username_taken, email_taken=email_taken)


@app.route('/set_up_tester', methods=['GET', 'POST'])
def set_up_tester():

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/signup")
    
    user = g.user

    if not user.username.endswith('_tester'):
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    # TODO change to final seed text length
    if len(user.texts) >= 15:
        flash("You've already set up your tester account.", "danger")
        return redirect("/submit_text")

    add_tester_texts_to_db(user)

    # return redirect('submit_text')
    return render_template('new_tester.html', username=user.username)


@app.route('/login', methods=["GET", "POST"])
def login():

    form = LoginForm()

    if form.is_submitted() and form.validate():

        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Welcome back, {user.username}!", "success")
            return redirect("/submit_text")

        flash("Invalid credentials.", 'danger')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():

    do_logout()
    flash("You've been logged out.")
    return redirect('/login')


##############################################################################
# Homepage routes

@app.route('/')
def show_homepage():

    return render_template('homepage.html')

@app.route('/new_user')
def show_new_user_page():

    user = g.user

    return render_template('new_user.html', username=user.username)


@app.route('/new_tester')
def show_new_tester_page():

    user = g.user

    return render_template('new_tester.html', username=user.username)


##############################################################################
# Error Routes

@app.route('/submit_text', methods=["GET", "POST"])
def submit_text():

    form = SubmitTextForm()

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/signup")
    
    user = g.user

    print('USER', user)
    
    if len(user.texts) >= 25:
        return render_template('over_text_limit.html')

    if form.is_submitted() and form.validate():

        # user = g.user
        
        text_to_submit = form.text.data
        # print('text_to_submit', text_to_submit)
        # text_to_submit = "Hi, how are you doing. I is doing well. I'm not have time."

        if len(text_to_submit) > 1200:
            flash("Text must be less than 1200 characters.", "danger")
            return redirect('/submit_text')

        api_response = generate_api_response(text_to_submit)
        # print('API_RESPONSE =>', api_response)
        # api_response = {
        # "edits": [
        #   {
        #     "end": 22,
        #     "error_type": "R:PUNCT",
        #     "general_error_type": "Spelling",
        #     "id": "4bb963a4-cc19-523e-9bb2-9e6b5a270bfc",
        #     "replacement": "doing?",
        #     "sentence": "Hi, how are you doing.",
        #     "sentence_start": 0,
        #     "start": 16
        #   },
        #   {
        #     "end": 4,
        #     "error_type": "R:VERB:SVA",
        #     "general_error_type": "Spelling",
        #     "id": "4bb963a4-cc19-523e-9bb2-9e6b5a270bfp",
        #     "replacement": "am",
        #     "sentence": "I is doing well.",
        #     "sentence_start": 23,
        #     "start": 2
        #   },
        #   {
        #     "end": 7,
        #     "error_type": "R:CONTR",
        #     "general_error_type": "Spelling",
        #     "id": "4bb963a4-cc19-523e-9bb2-9e6b5a270bfl",
        #     "replacement": "I don't",
        #     "sentence": "I'm not have time.",
        #     "sentence_start": 40,
        #     "start": 0
        #   }
        # ]
        # }

        grammar_errors_from_api = isolate_errors_from_api_response(api_response, 'Grammar')
 
        spelling_errors_from_api = isolate_errors_from_api_response(api_response, 'Spelling')

        if not grammar_errors_from_api and not spelling_errors_from_api:
            return render_template('review_text_submission_no_errors.html', text=text_to_submit)

        corrected_text = apply_all_corrections(text_to_submit, grammar_errors_from_api, spelling_errors_from_api)

        new_text = add_text_to_db(user.id, text_to_submit, corrected_text)

        add_errors_to_db(grammar_errors_from_api, spelling_errors_from_api, user.id, new_text.id)

        grammar_html_errors = create_review_text_html_errors(grammar_errors_from_api, 'Grammar')
        spelling_html_errors = create_review_text_html_errors(spelling_errors_from_api, 'Spelling')

        db.session.add(new_text)
        db.session.commit()

        return render_template('review_text_submission.html', text=new_text, grammar_html_errors=grammar_html_errors, spelling_html_errors=spelling_html_errors) 

    return render_template('submit_text.html', form=form)


@app.route('/show_all_grammar_errors', methods=["GET"])
def show_all_grammar_errors():

    user = g.user

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/signup")

    error_type_counts = get_error_type_counts(user.id, 'Grammar')

    if not error_type_counts:
        flash("You don't have any grammar errors yet! Keep submitting text to have your grammar errors collected.", "danger")
        return redirect("/submit_text")

    error_types, error_counts = create_graph_lists(error_type_counts, 'Grammar')

    create_errors_graph(error_types, error_counts, 'Grammar', user.username)

    html_errors = create_show_all_html_errors(error_type_counts, user.id, 'Grammar')

    all_serialized_errors = []
    for grammar_error in html_errors:
        serialized_errors = [serialize_grammar_error(error) for error in grammar_error["errors"]]
        grammar_error["errors"] = serialized_errors
        all_serialized_errors.append(grammar_error)

    return render_template('all_grammar_errors.html', all_grammar_errors=html_errors, username = user.username)


@app.route('/show_all_spelling_errors', methods=["GET"])
def show_all_spelling_errors():

    user = g.user

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/signup")

    error_type_counts = get_error_type_counts(user.id, 'Spelling')

    if not error_type_counts:
        flash("You don't have any spelling errors yet! Keep submitting text to have your spelling errors collected.", "danger")
        return redirect("/submit_text")

    error_types, error_counts = create_graph_lists(error_type_counts, 'Spelling')

    create_errors_graph(error_types, error_counts, 'Spelling', user.username)

    html_errors = create_show_all_html_errors(error_type_counts, user.id, 'Spelling')

    return render_template('all_spelling_errors.html', all_spelling_errors=html_errors, username=user.username)


@app.route('/get_more_errors', methods=['GET'])
def get_more_errors():

    general_error_type = request.args.get('general_error_type')
    error_type = request.args.get('error_type')
    page = request.args.get('page')

    errors_per_page = 6

    print('page', page)
    print('general_error_type', general_error_type)
    print('error_type', error_type) 

    offset = (int(page) - 1) * errors_per_page

    if general_error_type == 'Grammar':
        errors = Grammar_Error.query.filter_by(error_type=error_type, user_id=g.user.id).offset(offset).limit(errors_per_page).all()
    elif general_error_type == 'Spelling':
        errors = Spelling_Error.query.filter_by(replacement=error_type, user_id=g.user.id).offset(offset).limit(errors_per_page).all()
    else:

        return jsonify({"errors": [], "has_more": False})
    
    print('errors', errors)

    error_list = []
    for error in errors:
        error_dict = {
            "start": error.start,
            "end": error.end,
            "replacement": error.replacement,
            "sentence": error.sentence
        }
        if general_error_type == 'Grammar':
            error_dict["error_name"] = parse_error_subcategory(error.error_type)

        error_list.append(error_dict)

    has_more = len(error_list) == errors_per_page

    response_data = {
        "errors": error_list,
        "has_more": has_more
    }

    print('jsonify(response_data)', jsonify(response_data))

    return jsonify(response_data)


