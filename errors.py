import json
import requests
import uuid
import os
from datetime import datetime
from flask import session, g
from sqlalchemy import func, desc
import matplotlib.pyplot as plt

from models import Grammar_Error, Spelling_Error, Text, db
from seed_api_responses import seed_api_responses

API_key = os.environ.get("SAPLING_API_KEY") # to write in local machine: export SAPLING_API_KEY=value
    

# HELPER FUNCTIONS --------------------------------------------------------------------------

def split_text_at_colon(text):

    parts = text.split(":", 1)
    before_colon, after_colon = parts
    return before_colon, after_colon


def parse_error_subcategory(subcategory_code):

    subcategory_part_1_code, subcategory_part_2_code = split_text_at_colon(subcategory_code)

    subcategory_part_1_codes = {'M': 'Missing', 'R': 'Incorrect', 'U': 'Unnecessary'}

    subcategory_part_2_codes = { 'PART': 'particle', 'PUNCT': 'punctuation', 'ORTH': 'orthography', 'SPELL': 'spelling', 'WO': 'word order', 'MORPH': 'word form', 'ADV': 'adverb', 'CONTR': 'contraction', 'CONJ': 'conjunction', 'DET': 'determiner', 'DET:ART': 'article', 'PREP': 'preposition', 'PRON': 'pronoun', 'VERB': 'verb', 'VERB:FORM': 'verb form', 'VERB:TENSE': 'verb tense', 'VERB:SVA': 'subject-verb agreement', 'VERB:INFL': 'verb inflection', 'ADJ': 'adjective', 'ADJ:FORM': 'adjective form', 'NOUN': 'noun', 'NOUN:POSS': 'noun possessive', 'NOUN:INFL': 'noun inflection', 'NOUN:NUM': 'noun number', 'OTHER': 'other' }

    return f'{subcategory_part_1_codes[subcategory_part_1_code]} {subcategory_part_2_codes[subcategory_part_2_code]}'


# API FUNCTIONS --------------------------------------------------------------------------

def generate_api_response(user_text):

    url = 'https://api.sapling.ai/api/v1/edits'

    uuid_string = str(uuid.uuid4())

    data_to_send = {
        "key": API_key,
        "text": user_text,
        "session_id": uuid_string
    }

    try:
        response = requests.post(url, json=data_to_send)

        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"API call failed with status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        # Catch any exceptions that might occur during the API call
        print(f"An error occurred: {e}")
        return


def isolate_errors_from_api_response(api_response_data, general_error_type):

    errors_list = []

    if general_error_type == 'Grammar':
        for error in api_response_data['edits']:
            if error['general_error_type'] == 'Grammar':
                errors_list.append(error)

    elif general_error_type == 'Spelling':
        for error in api_response_data['edits']:
            if error['general_error_type'] == 'Spelling':
                errors_list.append(error)

    return errors_list


# DATABASE FUNCTIONS --------------------------------------------------------------------------

def add_errors_to_db(grammar_errors_list, spelling_errors_list, user_id, text_object_id): 
        
        for error in grammar_errors_list:
            new_grammar_error = Grammar_Error(
                user_id=user_id,
                text_id=text_object_id,
                error_type=error['error_type'],
                start=error['start'],
                end=error['end'],
                replacement=error['replacement'],
                sentence=error['sentence']
            )
            db.session.add(new_grammar_error)
            db.session.commit()

        for error in spelling_errors_list:
            new_spelling_error = Spelling_Error(
                user_id=user_id,
                text_id=text_object_id,
                start=error['start'],
                end=error['end'],
                replacement=error['replacement'],
                sentence=error['sentence']
            )
            db.session.add(new_spelling_error)
            db.session.commit()


def add_text_to_db(user_id, text_to_submit, corrected_text):

    new_text = Text(
        original_text=text_to_submit,
        user_id=user_id,
        timestamp = datetime.utcnow(),
        edited_text = corrected_text
    )

    db.session.add(new_text)
    db.session.commit()

    return new_text


# ERROR FUNCTIONS --------------------------------------------------------------------------

def apply_all_corrections(text, grammar_errors_list, spelling_errors_list):
    
    edits = grammar_errors_list + spelling_errors_list
    text = str(text)
    edits = sorted(edits, key=lambda e: (e['sentence_start'] + e['start']), reverse=True)
    for edit in edits:
        start = edit['sentence_start'] + edit['start']
        end = edit['sentence_start'] + edit['end']
        if start > len(text) or end > len(text):
            print(f'Edit start:{start}/end:{end} outside of bounds of text:{text}')
            continue
        text = text[: start] + edit['replacement'] + text[end:]
    return text


def get_errors_for_type(general_error_type, user_id, error_type):
    
    if general_error_type == "Grammar":
        errors = (
        Grammar_Error.query.filter(Grammar_Error.error_type == error_type, Grammar_Error.user_id == user_id)
        .order_by(Grammar_Error.timestamp.desc())
        .all()
        )
    elif general_error_type == "Spelling":
        errors = (
        Spelling_Error.query.filter(Spelling_Error.user_id == user_id, Spelling_Error.replacement == error_type)
        .order_by(Spelling_Error.timestamp.desc())
        .all()
        )

    else:
        raise ValueError("Invalid error type")

    return errors

    
def get_error_type_counts(user_id, general_error_type):
    
    if general_error_type == "Grammar":
        error_model = Grammar_Error
        error_type = Grammar_Error.error_type
    elif general_error_type == "Spelling":
        error_model = Spelling_Error
        error_type = Spelling_Error.replacement
    else:
        raise ValueError("Invalid error type")

    error_counts = (
        db.session.query(error_type, func.count(error_type))
        .filter(error_model.user_id == user_id)
        .group_by(error_type)
        .order_by(func.count(error_type).desc())
        .all()
    )

    result = [{"error_type": error, "count": count} for error, count in error_counts]

    return result


def create_review_text_html_errors(error_list, general_error_type):
    
    html_errors_list = []

    for error in error_list:

        replacement = error["replacement"]
        if replacement == "":
            replacement = "(None - simply remove)"

        new_error_object = {
            "sentence": error["sentence"],
            "start": error["start"],
            "end": error["end"],
            "replacement": replacement,
        }

        if general_error_type == "Grammar":
            new_error_object["error_name"] = parse_error_subcategory(error["error_type"])       

        html_errors_list.append(new_error_object)
    
    return html_errors_list







def create_review_previous_text_html_errors(error_objects, general_error_type):
    
    html_errors_list = []

    for error in error_objects:

        replacement = error.replacement
        if replacement == "":
            replacement = "(None - simply remove)"

        new_error_object = {
            # "text_id": error.text_id,
            "sentence": error.sentence,
            "start": error.start,
            "end": error.end,
            "replacement": replacement,
        }

        if general_error_type == "Grammar":
            new_error_object["error_name"] = parse_error_subcategory(error.error_type)       

        html_errors_list.append(new_error_object)
    
    return html_errors_list

















def create_show_all_html_errors(error_types_and_counts, user_id, general_error_type):
    
    show_all_errors_objects = []

    for error_type in error_types_and_counts:
        error_type['errors'] = get_errors_for_type(general_error_type, user_id, error_type['error_type'])

        if general_error_type == "Grammar":
            error_type["error_name"] = parse_error_subcategory(error_type["error_type"])  

        show_all_errors_objects.append(error_type)

    return show_all_errors_objects


# GRAPH FUNCTIONS
# -------------------------------------------------------------------------

def create_graph_lists(error_type_counts, general_error_type):
    error_types = []
    error_counts = []

    total_counts = sum([error['count'] for error in error_type_counts])

    for error in error_type_counts:
        if general_error_type == "Grammar":
            error_types.append(parse_error_subcategory(error['error_type']))
        else:
            error_types.append(error['error_type'])
        error_counts.append(round(error['count'] / total_counts * 100, 1))

    return error_types, error_counts


def create_errors_graph(error_types, error_counts, general_error_type, username):
    plt.figure()

    bars = plt.barh(error_types, error_counts, color="orangered")

    plt.rcParams.update({
        'xtick.color': 'purple',
        'ytick.color': 'purple',
        'axes.edgecolor': '#091f91',
    })

    if general_error_type == "Grammar":
        title = "Your Grammar Errors"
        ylabel = "Error Types"
        save_filename = f'static/plots/grammar_errors_plot-{username}.png'
    else:
        title = "Your Spelling Errors"
        ylabel = "Misspelled Words/Phrases"
        save_filename = f'static/plots/spelling_errors_plot-{username}.png'

    for bar in bars:
        plt.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, f'{bar.get_width()}%', ha='left', va='center', color="purple")
        bar.set_color("orangered")

    plt.xlabel("Percentage", color="darkblue", fontsize=12)
    plt.title(title, color="darkblue")
    plt.ylabel(ylabel, color="darkblue", fontsize=12)

    plt.savefig(save_filename, bbox_inches='tight')

    return "Success"
# TODO change return


def serialize_grammar_error(error):
    return {
        "id": error.id,
        "user": error.user_id,
        "error_type": error.error_type,
        "replacement": error.replacement,
        "sentence": error.sentence,
        "start": error.start,
        "end": error.end,
        "timestamp": error.timestamp,
        # JA
        "text_id": error.text_id
    }


def add_tester_texts_to_db(user):
    for  seed_text, seed_api_response in seed_api_responses:

        grammar_errors_from_api = isolate_errors_from_api_response(seed_api_response, 'Grammar')
 
        spelling_errors_from_api = isolate_errors_from_api_response(seed_api_response, 'Spelling')

        corrected_text = apply_all_corrections(seed_text, grammar_errors_from_api, spelling_errors_from_api)

        new_text = add_text_to_db(user.id, seed_text, corrected_text)

        add_errors_to_db(grammar_errors_from_api, spelling_errors_from_api, user.id, new_text.id)

        db.session.commit()