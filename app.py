import os

from flask import Flask, render_template, request, flash, redirect, session, g, jsonify
from flask_debugtoolbar import DebugToolbarExtension

from errors import generate_api_response, isolate_errors_from_api_response, add_errors_to_db, apply_all_corrections, add_errors_to_db, add_text_to_db, get_error_type_counts, create_review_text_html_errors, create_show_all_html_errors, create_graph_lists, create_errors_graph, add_tester_texts_to_db

from forms import SignupForm, LoginForm, SubmitTextForm
from models import db, connect_db, Text, User, Grammar_Error, Spelling_Error

import pdb

CURR_USER_KEY = ""

app = Flask(__name__)

app.static_folder = 'static'

app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql://kksluwoo:k-o2ThSbwF-GIbqCJKw7iQ9hnSv0Xd7X@mahmud.db.elephantsql.com/kksluwoo'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', True)

# When testing, uncomment the following line:
# toolbar = DebugToolbarExtension(app)

connect_db(app)

with app.app_context():  
#     db.drop_all()
    db.create_all()
    db.session.commit()


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

    db.session.close()


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

            return render_template('homepage_user.html', username=user.username)

    return render_template('signup.html', form=form)


@app.route('/set_up_tester', methods=['GET', 'POST'])
def set_up_tester():
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/signup")
    
    user = g.user

    if not user.username.endswith('_tester'):
        flash("Access unauthorized.", "danger")
        return redirect("/")

    if len(user.texts) >= 13:
        flash("You've already set up your tester account.", "danger")
        return redirect("/submit_text")

    return render_template('new_tester.html', username=user.username)


@app.route('/add_tester_texts', methods=['POST'])
def add_tester_texts():
    user = g.user

    add_tester_texts_to_db(user)

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
    return redirect('/')


##############################################################################
# Homepage routes

@app.route('/')
def show_homepage_no_user():

    if g.user:
        user = g.user
        if user.username.endswith('_tester'):
            return render_template('homepage_tester.html', username=user.username)
        return render_template('homepage_user.html', username=user.username)

    return render_template('homepage_no_user.html')


@app.route('/homepage_user')
def show_user_homepage():

    user = g.user

    return render_template('homepage_user.html', username=user.username)


@app.route('/homepage_tester')
def show_tester_homepage():

    user = g.user

    return render_template('homepage_tester.html', username=user.username)


##############################################################################
# Error Routes

@app.route('/submit_text', methods=["GET", "POST"])
def submit_text():

    form = SubmitTextForm()

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/signup")
    
    user = g.user
    
    if len(user.texts) >= 35:
        return render_template('over_text_limit.html')

    if form.is_submitted() and form.validate():
        
        text_to_submit = form.text.data

        if len(text_to_submit) > 1400:
            flash("Text must be less than 1400 characters.", "danger")
            return redirect('/submit_text')

        api_response = generate_api_response(text_to_submit)

        grammar_errors_from_api = isolate_errors_from_api_response(api_response, 'Grammar')
 
        spelling_errors_from_api = isolate_errors_from_api_response(api_response, 'Spelling')

        if not grammar_errors_from_api and not spelling_errors_from_api:
            return render_template('review_text_submission_no_errors.html', text=text_to_submit)

        corrected_text = apply_all_corrections(text_to_submit, grammar_errors_from_api, spelling_errors_from_api)

        new_text = add_text_to_db(user.id, text_to_submit, corrected_text)

        add_errors_to_db(grammar_errors_from_api, spelling_errors_from_api, user.id, new_text.id)

        grammar_html_errors = create_review_text_html_errors(grammar_errors_from_api, 'dict_objects', 'Grammar')
        spelling_html_errors = create_review_text_html_errors(spelling_errors_from_api, 'dict_objects', 'Spelling')

        db.session.add(new_text)
        db.session.commit()

        return render_template('review_text_submission.html', text=new_text, grammar_html_errors=grammar_html_errors, spelling_html_errors=spelling_html_errors) 

    return render_template('submit_text.html', form=form)


@app.route('/review_previous_text/<text_id>', methods=["GET"])
def review_review_previous_text(text_id):

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/signup")

    user = g.user

    text = Text.query.filter_by(id=text_id).first()

    if not text:
        flash("Text not found.", "danger")
        return redirect("/submit_text")

    grammar_errors = Grammar_Error.query.filter_by(text_id=text_id).all()
    spelling_errors = Spelling_Error.query.filter_by(text_id=text_id).all()

    grammar_html_errors = create_review_text_html_errors(grammar_errors, 'class_instances', 'Grammar')

    spelling_html_errors = create_review_text_html_errors(spelling_errors, 'class_instances', 'Spelling')

    return render_template('review_text_submission.html', text=text, grammar_html_errors=grammar_html_errors, spelling_html_errors=spelling_html_errors) 


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

    img_tag = create_errors_graph(error_types, error_counts, 'Grammar')

    html_errors = create_show_all_html_errors(error_type_counts, user.id, 'Grammar')

    return render_template('all_grammar_errors.html', img_tag=img_tag, all_grammar_errors=html_errors, username = user.username)


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

    img_tag = create_errors_graph(error_types, error_counts, 'Spelling')

    html_errors = create_show_all_html_errors(error_type_counts, user.id, 'Spelling')

    return render_template('all_spelling_errors.html', img_tag=img_tag, all_spelling_errors=html_errors, username=user.username)


@app.route('/get_more_errors', methods=['GET'])
def get_more_errors():

    general_error_type = request.args.get('general_error_type')
    error_type = request.args.get('error_type')
    page = request.args.get('page')
    
    errors_per_page = 4

    offset = (int(page) - 1) * errors_per_page

    if general_error_type == 'Grammar':
        errors = Grammar_Error.query.filter_by(error_type=error_type, user_id=g.user.id).order_by(Grammar_Error.timestamp.desc()).offset(offset).limit(errors_per_page).all()
        following_error = Grammar_Error.query.filter_by(error_type=error_type, user_id=g.user.id).order_by(Grammar_Error.timestamp.desc()).offset(offset + errors_per_page).limit(1).all()

    elif general_error_type == 'Spelling':
        errors = Spelling_Error.query.filter_by(replacement=error_type, user_id=g.user.id).order_by(Spelling_Error.timestamp.desc()).offset(offset).limit(errors_per_page).all()
        following_error = Spelling_Error.query.filter_by(replacement=error_type, user_id=g.user.id).order_by(Spelling_Error.timestamp.desc()).offset(offset + errors_per_page).limit(1).all()
    else:
        return jsonify({"errors": [], "has_more": False})

    error_list = create_review_text_html_errors(errors, "class_instances", general_error_type)

    has_more = len(following_error) > 0

    response_data = {
        "errors": error_list,
        "has_more": has_more
    }

    return jsonify(response_data)







