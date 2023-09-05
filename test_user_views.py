import os
from unittest import TestCase

from models import db, User

os.environ['DATABASE_URL'] = "postgresql:///capstone1-test"
from app import app, CURR_USER_KEY

# app.app_context().push()

app.config['WTF_CSRF_ENABLED'] = False
# Make Flask errors be real errors, not HTML pages with error info
app.config['TESTING'] = True
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']


class UserViewsTestCase(TestCase):

    def setUp(self):
        with app.app_context():

            db.drop_all()
            db.create_all()

            setup_user = User.signup('setup_user', 'setup_user@email.com', 'setup_user_password')
            db.session.commit()

            setup_tester = User.signup('setup_tester', 'setup_tester@email.com', 'setup_tester_password')
            db.session.commit()

            setup_user_id = setup_user.id
            setup_user = User.query.get(setup_user_id)
            self.setup_user_id = setup_user.id

            setup_tester_id = setup_tester.id
            setup_tester = User.query.get(setup_tester_id)
            self.setup_tester_id = setup_tester.id

            self.client = app.test_client()


    def tearDown(self):
        with app.app_context():
            db.session.rollback()
            db.drop_all()


    def test_login_valid(self):
        with self.client as c:
            resp = c.post("/login", data={
                "username": "setup_user",
                "password": "setup_user_password"
            }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Welcome back, setup_user!", str(resp.data))
            self.assertIn("Submit new text", str(resp.data))
    

    def test_login_invalid_username(self):
        with self.client as c:
            resp = c.post("/login", data={
                "username": "wrong_username",
                "password": "setup_user_password"
            }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid credentials.", str(resp.data))
            self.assertNotIn("Hello, setup_user!", str(resp.data))
            self.assertNotIn("Submit new text", str(resp.data))
            self.assertIn("Please login", str(resp.data))

    
    def test_login_invalid_password(self):
        with self.client as c:
            resp = c.post("/login", data={
                "username": "setup_user",
                "password": "wrong_password"
            }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid credentials.", str(resp.data))
            self.assertNotIn("Hello, setup_user!", str(resp.data))
            self.assertNotIn("Submit new text", str(resp.data))
            self.assertIn("Please login", str(resp.data))

    
    def test_signup_user_valid(self):
        with self.client as c:
            resp = c.post("/signup", data={
                "username": "new_user",
                "email": "new_user@email.com",
                "password": "new_user_password"
            }, follow_redirects=True)

            user = User.query.filter_by(username="new_user").first()

            self.assertEqual(len(user.texts), 0)
            self.assertEqual(len(user.grammar_errors), 0)
            self.assertEqual(len(user.spelling_errors), 0)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Hello new_user, and thanks for joining GrammarChecker!", str(resp.data))
            self.assertIn('To get started, click <a class="in-text-link" href="/submit_text">"Submit new text"<', str(resp.data))


    def test_signup_tester_valid(self):
        with self.client as c:
            resp1 = c.post("/signup", data={
                "username": "user_tester",
                "email": "user_tester@email.com",
                "password": "user_tester_password"
            }, follow_redirects=True)

            resp2 = c.post("/add_tester_texts")

            tester = User.query.filter_by(username="user_tester").one()

            self.assertNotEqual(len(tester.texts), 0)
            self.assertNotEqual(len(tester.grammar_errors), 0)
            self.assertNotEqual(len(tester.spelling_errors), 0)

            self.assertEqual(resp2.status_code, 200)
            self.assertIn("Hello user_tester, and thanks for joining GrammarChecker.", str(resp2.data))
            self.assertIn("You have signed up for a demonstration account", str(resp2.data))


    def test_signup_username_taken(self):
        with self.client as c:
            resp = c.post("/signup", data={
                "username": "setup_user",
                "email": "setup_user2@email.com",
                "password": "setup_user_password"
            }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Username already taken", str(resp.data))

    
    def test_signup_email_taken(self):
        with self.client as c:
            resp = c.post("/signup", data={
                "username": "setup_user2",
                "email": "setup_user@email.com",
                "password": "setup_user_password"
            }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Email already taken", str(resp.data))


    def test_logout(self):
        with self.client as c:
            resp = c.get("/logout", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("You&#39;ve been logged out.", str(resp.data))
            self.assertIn("Welcome back! Please login.", str(resp.data))


    def test_homepage_not_logged_in(self):
        with self.client as c:
            resp = c.get("/", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("To get started, simply create an account", str(resp.data))


    def test_homepage_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.setup_user_id

            resp = c.get("/new_user", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Hello setup_user", str(resp.data))
            self.assertIn('To get started, click <a class="in-text-link" href="/submit_text">"Submit new text"</a>', str(resp.data))
            self.assertNotIn("You have signed up for a demonstration account", str(resp.data))


    def test_homepage_tester(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.setup_tester_id

            resp = c.get("/new_tester", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Hello setup_tester", str(resp.data))
            self.assertIn("You have signed up for a demonstration account", str(resp.data))

    


