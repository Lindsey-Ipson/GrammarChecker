import os
from unittest import TestCase
from flask import Flask
from models import db, Text, User, Grammar_Error

os.environ['DATABASE_URL'] = "postgresql:///grammar_checker_test"

app = Flask(__name__)
app.config['TESTING'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

class GrammarModelTestCase(TestCase):

    def setUp(self):
        with app.app_context():

            db.drop_all()
            db.create_all()

            setup_user = User.signup('setup_user', 'setup_user@email.com', 'setup_user_password')
    
            db.session.commit()

            self.setup_user_id = setup_user.id

            setup_text = Text(
                user_id=setup_user.id,
                original_text='Here are an example.',
                edited_text='Here is an example.'
            )

            db.session.add(setup_text)
            db.session.commit()

            self.setup_text_id = setup_text.id

            grammar_error = Grammar_Error(
                user_id = self.setup_user_id, 
                text_id = setup_text.id, 
                error_type = 'R:VERB:SVA', 
                start = 5, 
                end = 8, 
                replacement = 'is', 
                sentence = 'Here are an example.')

            db.session.add(grammar_error)
            db.session.commit()

            self.setup_grammar_error_id = grammar_error.id


    def tearDown(self):
        with app.app_context():
            db.session.rollback()
            db.drop_all()


    def test_grammar_error_model(self):
        with app.app_context():

            new_grammar_error = Grammar_Error(
                user_id=self.setup_user_id,
                text_id=self.setup_text_id,
                error_type='R:VERB:SVA',
                start=5,
                end=8,
                replacement='is',
                sentence='Here are another example.'
            )

            db.session.add(new_grammar_error)
            db.session.commit()
             
            self.assertEqual(new_grammar_error.user_id, self.setup_user_id)
            self.assertEqual(new_grammar_error.text_id, self.setup_text_id)
            self.assertEqual(new_grammar_error.error_type, 'R:VERB:SVA')
            self.assertEqual(new_grammar_error.start, 5)
            self.assertEqual(new_grammar_error.end, 8)
            self.assertEqual(new_grammar_error.replacement, 'is')
            self.assertEqual(new_grammar_error.sentence, 'Here are another example.')


    def test_repr_method(self):
        with app.app_context():

            grammar_error = Grammar_Error.query.get(self.setup_grammar_error_id)

            expected_repr = f"<Grammar_Error id: {self.setup_grammar_error_id}, user: {self.setup_user_id}, error_type: R:VERB:SVA, replacement: is>"

            self.assertEqual(repr(grammar_error), expected_repr)


    def test_query_grammar_errors_by_user(self):
        with app.app_context():

            user_grammar_error2 = Grammar_Error(
                user_id=self.setup_user_id,
                text_id=self.setup_text_id,
                error_type='R:VERB:SVA',
                start=5,
                end=8,
                replacement='is',
                sentence='Here are another example.'
            )
            user_grammar_error3 = Grammar_Error(
                user_id=self.setup_user_id,
                text_id=self.setup_text_id,
                error_type='R:VERB:SVA',
                start=5,
                end=8,
                replacement='is',
                sentence='Here are another example.'
            )

            db.session.add_all([user_grammar_error2, user_grammar_error3])
            db.session.commit()
            
            other_user = User.signup('other_user', 'other_user@email.com', 'other_password')

            db.session.commit()

            other_text = Text(
                user_id=other_user.id,
                original_text='Here are another example.',
                edited_text='Here is another example.'
            )

            db.session.add(other_text)
            db.session.commit()

            other_grammar_error = Grammar_Error(
                user_id=other_user.id,
                text_id=other_text.id,
                error_type='R:VERB:SVA',
                start=5,
                end=8,
                replacement='is',
                sentence='Here are another example.'
            )

            db.session.add(other_grammar_error)
            db.session.commit()

            user_grammar_errors = Grammar_Error.query.filter_by(user_id=self.setup_user_id).all()

            self.assertEqual(len(user_grammar_errors), 3)



    