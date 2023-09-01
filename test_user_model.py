import os
from unittest import TestCase
from sqlalchemy import exc

os.environ['DATABASE_URL'] = "postgresql:///capstone1-test"
from app import app

app.config['TESTING'] = True

from models import db, User

class UserModelTestCase(TestCase):

    def setUp(self):
        with app.app_context():

            db.drop_all()
            db.create_all()

            setup_user = User.signup('setup_user', 'setup_user@email.com', 'setup_user_password')

            db.session.commit()

            setup_user_id = setup_user.id

            setup_user = User.query.get(setup_user_id)

            self.setup_user_id = setup_user.id

            self.client = app.test_client()


    def tearDown(self):
        with app.app_context():
            db.session.rollback()
            db.drop_all()


    def test_user_model(self):
        with app.app_context():

            user = User.signup(
                username="test_user",
                email="test_user@email.com",
                password="password"
            )

            db.session.commit()

            self.assertEqual(len(user.texts), 0)
            self.assertEqual(len(user.grammar_errors), 0)
            self.assertEqual(len(user.spelling_errors), 0)


    def test_repr_method(self):
        with app.app_context():

            user = User.signup(
                username="test_user",
                email="test_user@email.com",
                password="password"
            )

            db.session.add(user)
            db.session.commit()

            expected_repr = f"<User id: {user.id}, username: {user.username}>"

            self.assertEqual(repr(user), expected_repr)


#________________________________Signup Tests________________________________

    def test_user_signup_valid(self):
        with app.app_context():

            user = User.signup('test_user', 'test_user@email.com', 'password')
            user_id = 100
            user.id = user_id
            db.session.commit()

            user = User.query.get(user_id)

            self.assertIsNotNone(user)
            self.assertEqual(user.id, 100)
            self.assertEqual(user.username, 'test_user')
            self.assertNotEqual(user.password, 'password')
            self.assertEqual(user.email, 'test_user@email.com')
            self.assertTrue(user.password.startswith("$2b$"))
 

    def test_signup_invalid_username(self):
        with app.app_context():

            with self.assertRaises(exc.IntegrityError):
                User.signup(None, 'test_user@email.com', 'password')
                db.session.commit()

            with self.assertRaises(Exception):
                User.signup('', 'test_user@email.com', 'password')
                db.session.commit()


    def test_signup_invalid_email(self):
        with app.app_context():

            with self.assertRaises(ValueError):
                User.signup("test_user", "TestPassword3", None)

            with self.assertRaises(ValueError):
                User.signup("TestUser3", "TestPassword3", "")


    def test_signup_invalid_password(self):

        with app.app_context():
                     
            with self.assertRaises(ValueError) as context:
                User.signup("test_user", "test_user@email.com", "")

            with self.assertRaises(ValueError) as context:
                User.signup("test_user", "test_user@email.com", None)


# #________________________________Authentication Tests________________________________

def test_authenticate_valid(self):
    with app.app_context():

        authenticated_user = User.authenticate(self.setup_user.username, 'setup_user_password')
        
        self.assertEqual(authenticated_user.id, self.setup_user.id)


def test_authenticate_invalid_username(self):

    authenticated_user = User.authenticate('invalid_username', 'set_up_user_password')
    
    self.assertFalse(authenticated_user)


def test_authenticate_invalid_password(self):

    authenticated_user = User.authenticate(self.setup_user.username, 'invalid_password')

    self.assertFalse(authenticated_user)
