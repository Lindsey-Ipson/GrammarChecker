import os
from unittest import TestCase
from datetime import datetime, timedelta
from flask import Flask
from models import db, Text, User

os.environ['DATABASE_URL'] = "postgresql:///capstone1-test"

app = Flask(__name__)
app.config['TESTING'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

class TextModelTestCase(TestCase):

    def setUp(self):
        with app.app_context():

            db.drop_all()
            db.create_all()

            setup_user = User.signup('setup_user', 'setup_user@email.com', 'setup_user_password')
    
            db.session.commit()

            self.setup_user_id = setup_user.id

            setup_text = Text(
                user_id=setup_user.id,
                original_text='Original text',
                edited_text='Edited text'
            )

            db.session.add(setup_text)
            db.session.commit()

            self.setup_text_id = setup_text.id


    def tearDown(self):
        with app.app_context():
            db.session.rollback()
            db.drop_all()


    def test_text_model(self):
        with app.app_context():

            new_text = Text(
                user_id=self.setup_user_id,
                original_text='New original text',
                edited_text='New Edited text'
            )
            db.session.add(new_text)
            db.session.commit()

            self.assertEqual(new_text.user_id, self.setup_user_id)
            self.assertEqual(new_text.original_text, 'New original text')
            self.assertEqual(new_text.edited_text, 'New Edited text')


    def test_repr_method(self):
        with app.app_context():

            text = Text.query.get(self.setup_text_id)

            expected_repr = f"<Text id: {self.setup_text_id}, user: {self.setup_user_id}, original_text: Original text>"

            self.assertEqual(repr(text), expected_repr)


    def test_query_texts_by_user(self):
        with app.app_context():

            user_text1 = Text(
                user_id=self.setup_user_id,
                original_text='User text 1',
                edited_text='Edited text 1'
            )
            user_text2 = Text(
                user_id=self.setup_user_id,
                original_text='User text 2',
                edited_text='Edited text 2'
            )
            other_user = User.signup('other_user', 'other@email.com', 'password')
            db.session.commit()
            other_text = Text(
                user_id=other_user.id,
                original_text='Other user text',
                edited_text='Other edited text'
            )

            db.session.add_all([user_text1, user_text2, other_user, other_text])
            db.session.commit()

            user_texts = Text.query.filter_by(user_id=self.setup_user_id).all()

            self.assertEqual(len(user_texts), 3)


    def test_text_timestamp(self):
        with app.app_context():

            current_datetime = datetime.utcnow()

            new_text = Text(
                user_id=self.setup_user_id,
                original_text='New original text',
                edited_text='New Edited text'
            )
            db.session.add(new_text)
            db.session.commit()

            max_time_difference = timedelta(minutes=1)

            time_difference = abs(current_datetime - new_text.timestamp)

            self.assertTrue(time_difference <= max_time_difference)

    