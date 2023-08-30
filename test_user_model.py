import os
from unittest import TestCase
from models import db, User
from sqlalchemy import exc
from flask import session

os.environ['DATABASE_URL'] = "postgresql:///capstone1-test"
from app import app

app.config['TESTING'] = True

app.app_context().push()

class UserModelTestCase(TestCase):
    """Test user model"""

    def setUp(self):
        """Create test client, add sample data."""
        print('setting up')
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///capstone1-test'

        # with app.app_context():
        db.session.remove()
        print('dropping all')
        db.drop_all()
        print('creatign all')
        db.create_all()

        user1 = User.signup('TestUser1', 'TestUser1@gmail.com', 'TestPassword1')
        user1_id = 1000
        user1.id = user1_id

        db.session.commit()

        print('before User.query.get(user1_id)')
        # user = session.query(User).get(user1_id)
        user1 = User.query.get(1000)
        print('after User.query.get(user1_id)')
        print('user1', user1)

        self.user1 = user1
        self.user1_id = user1.id

        self.client = app.test_client()

    def tearDown(self):
        """Clean up after each test."""
        with app.app_context():
            db.session.rollback()
            db.drop_all()

    # def test_user_model(self):
    #     """Does basic model work?"""
    #     with app.app_context():

    #         user = User.signup(
    #             username="test_user",
    #             email="test@test.com",
    #             password="test_password"
    #         )
    #     # with app.app_context():
    #         db.session.add(user)
    #         db.session.commit()
    #         self.assertEqual(len(user.texts), 0)
    #         self.assertEqual(len(user.grammar_errors), 0)
    #         self.assertEqual(len(user.spelling_errors), 0)

    def test_repr_method(self):
        """Test that repr method returns correctly"""

        with app.app_context():

            user = User.signup(
                username="test_user",
                email="test@test.com",
                password="test_password"
            )

            db.session.add(user)
            db.session.commit()

            expected_repr = f"<User id: {user.id}, username: {user.username}>"

            self.assertEqual(repr(user), expected_repr)






# #________________________________Signup Tests________________________________

#     def test_user_signup_valid(self):
#         """Test that a new user can be signed up given valid credentials"""

#         with app.app_context():

#             # with db.session.no_autoflush:
#             #     self.user1 = User.query.get(self.user1_id)
#             #     self.user2 = User.query.get(self.user2_id)

#             user3 = User.signup('TestUser3', 'TestUser3@gmail.com', 'TestPassword3')
#             user3_id = 3000
#             user3.id = user3_id
#             db.session.commit()

#             user3 = User.query.get(user3_id)

#             self.assertIsNotNone(user3)
#             self.assertEqual(user3.id, 3000)
#             self.assertEqual(user3.username, 'TestUser3')
#             self.assertNotEqual(user3.password, 'TestPassword3')
#             self.assertEqual(user3.email, 'TestUser3@gmail.com')
#             self.assertTrue(user3.password.startswith("$2b$"))
 

#     def test_signup_invalid_username(self):
#         """Test that a new user cannot be signed up given invalid username"""

#         with app.app_context():

#             user3 = User.signup(None, 'TestUser3@gmail.com', 'TestPassword3')

#             with self.assertRaises(exc.IntegrityError):
#                 db.session.add(user3)
#                 db.session.commit()


#     def test_signup_invalid_email(self):
#         """Test that a new user cannot be signed up given invalid email"""

#         with app.app_context():

#             with self.assertRaises(ValueError):
#                 User.signup("TestUser3", "TestPassword3", None)

#             with self.assertRaises(ValueError):
#                 User.signup("TestUser3", "TestPassword3", "")



#     def test_signup_invalid_password(self):

#         with app.app_context():
                     
#             with self.assertRaises(ValueError) as context:
#                 User.signup("TestUser3", "TestEmail3@email.com", "")

#             with self.assertRaises(ValueError) as context:
#                 User.signup("TestUser3", "TestEmail3@email.com", None)


# #________________________________Authenticate Tests________________________________


#     def test_authenticate_valid(self):

#         with app.app_context():

#             authenticated_user = User.authenticate(self.user1.username, 'TestPassword1')

#             self.assertEqual(authenticated_user, self.user1)


#     def test_authenticate_invalid_username(self):

#         with db.session.no_autoflush:
#             self.user1 = User.query.get(self.user1_id)

#         authenticated_user = User.authenticate('invalid_username', 'TestPassword1')
#         self.assertFalse(authenticated_user)
            

#     def test_authenticate_invalid_password(self):

#         with db.session.no_autoflush:
#             self.user1 = User.query.get(self.user1_id)

#         authenticated_user = User.authenticate(self.user1.username, 'invalid_password')
#         self.assertFalse(authenticated_user)
