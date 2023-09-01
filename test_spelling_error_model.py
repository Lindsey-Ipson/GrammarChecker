import os
from unittest import TestCase
from flask import Flask
from models import db, Text, User, Spelling_Error

os.environ['DATABASE_URL'] = "postgresql:///capstone1-test"

app = Flask(__name__)
app.config['TESTING'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

class SpellingModelTestCase(TestCase):

    def setUp(self):
        with app.app_context():

            db.drop_all()
            db.create_all()

            setup_user = User.signup('setup_user', 'setup_user@email.com', 'setup_user_password')
    
            db.session.commit()

            self.setup_user_id = setup_user.id

            setup_text = Text(
                user_id=setup_user.id,
                original_text='Hear is an example.',
                edited_text='Here is an example.'
            )

            db.session.add(setup_text)
            db.session.commit()

            self.setup_text_id = setup_text.id

            spelling_error = Spelling_Error(
                user_id=self.setup_user_id,
                text_id=setup_text.id,
                start=0,
                end=4,
                replacement='Here',
                sentence='Hear is an example.'
            )

            db.session.add(spelling_error)
            db.session.commit()

            self.setup_spelling_error_id = spelling_error.id


    def tearDown(self):
        with app.app_context():
            db.session.rollback()
            db.drop_all()


    def test_spelling_error_model(self):
        with app.app_context():

            new_spelling_error = Spelling_Error(
                user_id=self.setup_user_id,
                text_id=self.setup_text_id,
                start=0,
                end=4,
                replacement='Here',
                sentence='Hear is another example.'
            )

            db.session.add(new_spelling_error)
            db.session.commit()
             
            self.assertEqual(new_spelling_error.user_id, self.setup_user_id)
            self.assertEqual(new_spelling_error.text_id, self.setup_text_id)
            self.assertEqual(new_spelling_error.start, 0)
            self.assertEqual(new_spelling_error.end, 4)
            self.assertEqual(new_spelling_error.replacement, 'Here')
            self.assertEqual(new_spelling_error.sentence, 'Hear is another example.')


    def test_repr_method(self):
        with app.app_context():

            spelling_error = Spelling_Error.query.get(self.setup_spelling_error_id)

            expected_repr = f"<Spelling_Error id: {self.setup_spelling_error_id}, user: {self.setup_user_id}, replacement: Here>"

            self.assertEqual(repr(spelling_error), expected_repr)


    def test_query_spelling_errors_by_user(self):
        with app.app_context():

            user_spelling_error2 = Spelling_Error(
                user_id=self.setup_user_id,
                text_id=self.setup_text_id,
                start=0,
                end=4,
                replacement='Here',
                sentence='Hear is another example.'
            )

            user_spelling_error3 = Spelling_Error(
                user_id=self.setup_user_id,
                text_id=self.setup_text_id,
                start=0,
                end=4,
                replacement='Here',
                sentence='Hear is another example.'
            )

            db.session.add_all([user_spelling_error2, user_spelling_error3])
            db.session.commit()
            
            other_user = User.signup('other_user', 'other_user@email.com', 'other_password')

            db.session.commit()

            other_text = Text(
                user_id=other_user.id,
                original_text='Hear is another example.',
                edited_text='Here is another example.'
            )

            db.session.add(other_text)
            db.session.commit()

            other_spelling_error = Spelling_Error(
                user_id=other_user.id,
                text_id=other_text.id,
                start=0,
                end=4,
                replacement='Here',
                sentence='Hear is another example.'
            )

            db.session.add(other_spelling_error)
            db.session.commit()

            user_spelling_errors = Spelling_Error.query.filter_by(user_id=self.setup_user_id).all()

            self.assertEqual(len(user_spelling_errors), 3)



    