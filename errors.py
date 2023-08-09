import json
import requests
import uuid
import os
from datetime import datetime

from flask import session, g
from models import Grammar_Error, Spelling_Error, Text, db
from app import app, CURR_USER_KEY


API_key = os.environ.get("SAPLING_API_KEY") # to write in local machine: export SAPLING_API_KEY=value


grammar_error_descriptions = {
    "M:PART": "Missing particle",
    "M:PUNCT": "Missing punctuation",
    "M:CONJ": "Missing conjunction",
    "M:DET": "Missing determiner",
    "M:DET:ART": "Missing article",
    "M:PREP": "Missing preposition",
    "M:PRON": "Missing pronoun",
    "M:VERB": "Missing verb",
    "M:VERB:TENSE": "Missing verb tense",
    "M:ADJ": "Missing adjective",
    "M:NOUN": "Missing noun",
    "M:NOUN:POSS": "Missing possessive noun",
    "M:OTHER": "Missing other elements",
    "R:PART": "Incorrect particle",
    "R:PUNCT": "Incorrect punctuation",
    "R:ORTH": "Incorrect orthography",
    "R:SPELL": "Incorrect spelling",
    "R:WO": "Incorrect word order",
    "R:MORPH": "Incorrect word form",
    "R:ADV": "Incorrect adverb",
    "R:CONTR": "Incorrect contraction",
    "R:CONJ": "Incorrect conjunction",
    "R:DET": "Incorrect determiner",
    "R:DET:ART": "Incorrect article",
    "R:PREP": "Incorrect preposition",
    "R:PRON": "Incorrect pronoun",
    "R:VERB:FORM": "Incorrect verb form",
    "R:VERB:TENSE": "Incorrect verb tense",
    "R:VERB:SVA": "Incorrect subject-verb agreement",
    "R:ADJ:FORM": "Incorrect adjective form",
    "R:NOUN:INFL": "Incorrect noun inflection",
    "R:NOUN:NUM": "Incorrect noun number",
    "R:OTHER": "Replacement of phrase not easily categorized",
    "U:PART": "Unnecessary particle",
    "U:PUNCT": "Unnecessary punctuation",
    "U:ADV": "Unnecessary adverb",
    "U:CONTR": "Unnecessary contraction",
    "U:CONJ": "Unnecessary conjunction",
    "U:DET": "Unnecessary determiner",
    "U:DET:ART": "Unnecessary article",
    "U:PREP": "Unnecessary preposition",
    "U:PRON": "Unnecessary pronoun",
    "U:VERB": "Unnecessary verb",
    "U:ADJ": "Unnecessary adjective",
    "U:NOUN": "Unnecessary noun",
    "U:NOUN:POSS": "Unnecessary possessive noun",
    "U:OTHER": "Unnecessary text"
}


def generate_api_response(user_text):

    url = 'https://api.sapling.ai/api/v1/edits'

    # Generate a random UUID (version 4) as a string
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

    if general_error_type == 'grammar':
        for error in api_response_data['edits']:
            if error['general_error_type'] == 'Grammar':
                errors_list.append(error)

    elif general_error_type == 'spelling':
        for error in api_response_data['edits']:
            if error['general_error_type'] == 'Spelling':
                errors_list.append(error)

    return errors_list


def add_errors_to_db(grammar_errors_list, spelling_errors_list, user_id, text_object_id): 
# NOTE change text object?
        
    with app.app_context():
        
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


def add_spelling_errors_to_db(spelling_errors_list, user_id, text_object_id): 
    with app.app_context():

        for error in spelling_errors_list:
    
            new_grammar_error = Grammar_Error(
                user_id=user_id,
                text_id=text_object_id,
                start=error['start'],
                end=error['end'],
                replacement=error['replacement'],
                sentence=error['sentence']
            )
    
            db.session.add(new_grammar_error)
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


def generate_grammar_errors_html(error_array, grammar_error_descriptions):
    html_errors_list = []

    for error in error_array:

        error_type = error["error_type"]
        error_description = grammar_error_descriptions.get(error_type, "Unknown error")

        sentence = error["sentence"]
        error_start = error["start"]
        error_end = error["end"]

        replacement = error["replacement"]
        if replacement == "":
            replacement = "(None - simply remove)"

        html = f"""
        <li>{error_description}</li>
        <li class="hide-bullet">{sentence[:error_start]}<b>{sentence[error_start:error_end]}</b>{sentence[error_end:]}</li>
        <li class="hide-bullet">Replacement: <b>{replacement}</b></li>
        """

        html_errors_list.append(html)
    
    return html_errors_list


def generate_spelling_errors_html(error_array):
    html_errors_list = []

    for error in error_array:

        sentence = error["sentence"]
        error_start = error["start"]
        error_end = error["end"]

        replacement = error["replacement"]

        html = f"""
        <li>{sentence[:error_start]}<b>{sentence[error_start:error_end]}</b>{sentence[error_end:]}</li>
        <li class="hide-bullet">Replacement: <b>{replacement}</b></li>
        """

        html_errors_list.append(html)
    
    return html_errors_list


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


