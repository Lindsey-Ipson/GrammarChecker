import os
from unittest import TestCase

from models import db, User, Text, Grammar_Error, Spelling_Error

os.environ['DATABASE_URL'] = "postgresql:///capstone1-test"
from app import app, CURR_USER_KEY

# app.app_context().push()

app.config['WTF_CSRF_ENABLED'] = False
# Make Flask errors be real errors, not HTML pages with error info
app.config['TESTING'] = True
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

class ErrorsViewsTestCase(TestCase):

    def setUp(self):
        with app.app_context():

            db.drop_all()
            db.create_all()

            setup_user = User.signup('setup_user', 'setup_user@email.com', 'setup_user_password')
            db.session.commit()

            setup_text = Text(
                user_id=setup_user.id,
                original_text='Here are a grammar error example. Hear is a spelling error example.',
                edited_text='Here is a grammar error example. Here is a spelling error example.'
            )
            db.session.add(setup_text)
            db.session.commit()

            setup_grammar_error = Grammar_Error(
                user_id=setup_user.id,
                text_id=setup_text.id,
                error_type='R:VERB:SVA',
                start=5,
                end=8,
                replacement='is',
                sentence='Here are a grammar error example.'
            )
            db.session.add(setup_grammar_error)
            db.session.commit()

            setup_spelling_error = Spelling_Error(
                user_id=setup_user.id,
                text_id=setup_text.id,
                start=0,
                end=4,
                replacement='Here',
                sentence='Hear is a spelling error example.'
            )
            db.session.add(setup_spelling_error)
            db.session.commit()

            setup_tester = User.signup('setup_tester', 'setup_tester@email.com', 'setup_tester_password')
            db.session.commit()

            self.setup_text_id = setup_text.id

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


# To test:
# - get_submit_text_form_valid - DONE
# - get_submit_text_form_not_logged_in - DONE
# - submit_text_valid - DONE
# - submit_text_over_text_limit - DONE
# - submit_text_over_characer_limit - DONE
# - submit_text_empty - DONE
# - submit_text_no_user - DONE
# - submit_text_invalid_user - DONE
# - ---
# - show_all_grammar_errors_valid - DONE
# - show_all_grammar_errors_not_logged_in - DONE
# - show_all_grammar_errors_no_errors - DONE
# - ---
# - show_all_spelling_errors_valid - DONE
# - show_all_spelling_errors_not_logged_in - DONE
# - show_all_spelling_errors_no_errors - DONE
# - ---
# - get_more_errors - DONE

    def test_get_submit_text_form_valid(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.setup_user_id

            resp = c.get('/submit_text')

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h1>Submit New Text</h1>', str(resp.data))
            self.assertIn('Add some text', str(resp.data))


    def test_get_submit_text_form_not_logged_in(self):
        with self.client as c:
            resp = c.get('/submit_text', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.', str(resp.data))
            self.assertIn('Sign up to start improving your grammar and spelling skills today!', str(resp.data))


    def test_submit_text_valid(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.setup_user_id

            resp = c.post('/submit_text', data={
                'text': 'This are another grammar error example. This is another speling error example.'
            }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("<h1>Let\\\'s review your text!</h1>", str(resp.data))
            self.assertIn('<p class="submission-p">This are another grammar error example. This is another speling error example.</p>', str(resp.data))
            self.assertIn('<p class="submission-p">This is another grammar error example. This is another spelling error example.</p>', str(resp.data))
            self.assertIn('<p>\\n        This <b>are</b> another grammar error example. <span class="divider">\\xe2\\x86\\x92</span> \\n         \\n          <b>is</b>', str(resp.data))
            self.assertIn('<p>\\n            This is another <b>speling</b> error example. <span class="divider">\\xe2\\x86\\x92</span> \\n         \\n          <b>spelling</b>', str(resp.data))

    
    def test_submit_text_over_text_limit(self):
        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.setup_user_id

                    user = User.query.get(self.setup_user_id)

                    for _ in range(25):
                        new_text = Text(
                            user_id=self.setup_user_id,
                            original_text='Another text'
                        )
                        user.texts.append(new_text)

                resp = c.post('/submit_text', data={
                    'text': 'This are another grammar error example. This is another speling error example.'
                }, follow_redirects=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn('Over Text Limit', str(resp.data))
                self.assertIn('Unfortunately, you have now exceeded the current limit for text submissions.', str(resp.data))

    
    def test_submit_text_over_character_limit(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.setup_user_id

                new_text = ''
                for _ in range(2500):
                    new_text += 'a'

            resp = c.post('/submit_text', data={
                'text': new_text
            }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Field must be between 5 and 1200 characters long.', str(resp.data))
            self.assertIn('<h1>Submit New Text</h1>', str(resp.data))
            self.assertNotIn("<h1>Let's review your text!</h1>", str(resp.data))

    
    def test_submit_text_empty(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.setup_user_id

            resp = c.post('/submit_text', data={
                'text': ''
            }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('This field is required.', str(resp.data))
            self.assertNotIn("Let's review your text!", str(resp.data))


    def test_submit_text_no_user(self):
        with self.client as c:
            resp = c.post('/submit_text', data={
                'text': 'This are another grammar error example. This is another speling error example.'
            }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.', str(resp.data))
            self.assertIn('Sign up to start improving your grammar and spelling skills today!', str(resp.data))

    
    def test_submit_text_invalid_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 9999999

            resp = c.post('/submit_text', data={
                'text': 'This are another grammar error example. This is another speling error example.'
            }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.', str(resp.data))
            self.assertIn('Sign up to start improving your grammar and spelling skills today!', str(resp.data))


    def test_show_all_grammar_errors_valid(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.setup_user_id

            resp = c.get(f'/show_all_grammar_errors')

            self.assertEqual(resp.status_code, 200)
            self.assertIn("<h1>Let\\\'s review your grammar errors</h1>", str(resp.data))
            self.assertIn('alt="Grammar Errors Plot" id="grammar-graph-image', str(resp.data))
            self.assertIn('<h3 class="error-heading"><span class="error-type">Incorrect subject-verb agreement</span><span class="error-count"> <span class="line-divider">\\xe2\\x94\\x82</span> 1 count', str(resp.data))


    def test_show_all_grammar_errors_not_logged_in(self):
        with self.client as c:
            resp = c.get(f'/show_all_grammar_errors', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.', str(resp.data))
            self.assertIn('Sign up to start improving your grammar and spelling skills today!', str(resp.data))


    def test_show_all_grammar_errors_no_errors(self):
        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.setup_tester_id

                resp = c.get(f'/show_all_grammar_errors', follow_redirects=True)

                self.assertEqual(resp.status_code, 200)
                self.assertNotIn("<h1>Let\\\'s review your grammar errors</h1>", str(resp.data))
                self.assertIn("You don&#39;t have any grammar errors yet! Keep submitting text to have your grammar errors collected.", str(resp.data))
                self.assertIn('<h1>Submit New Text</h1>', str(resp.data))

 
    def test_show_all_spelling_errors_valid(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.setup_user_id

            resp = c.get(f'/show_all_spelling_errors', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("<h1>Let\\\'s review your spelling errors</h1>", str(resp.data))
            self.assertIn('<img src="/static/plots/spelling_errors_plot-setup_user.png" alt="Spelling Errors Plot" id="grammar-graph-image">', str(resp.data))


            self.assertIn('<h3 class="error-heading"><span class="error-type">Here</span><span class="error-count"> <span class="line-divider">\\xe2\\x94\\x82</span> 1 count</span>', str(resp.data))

    
    def test_show_all_spelling_errors_not_logged_in(self):
        with self.client as c:
            resp = c.get(f'/show_all_spelling_errors', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.', str(resp.data))
            self.assertIn('Sign up to start improving your grammar and spelling skills today!', str(resp.data))


    def test_show_all_spelling_errors_no_errors(self):
        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.setup_tester_id

                resp = c.get(f'/show_all_spelling_errors', follow_redirects=True)

                self.assertEqual(resp.status_code, 200)
                self.assertNotIn("<h1>Let\\\'s review your spelling errors</h1>", str(resp.data))
                self.assertIn("You don&#39;t have any spelling errors yet! Keep submitting text to have your spelling errors collected.", str(resp.data))
                self.assertIn('<h1>Submit New Text</h1>', str(resp.data))


    def test_get_more_errors(self):
        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.setup_user_id

                for _ in range(7):
                    new_grammar_error = Grammar_Error(
                        user_id=self.setup_user_id,
                        text_id=self.setup_text_id,
                        error_type='R:VERB:SVA',
                        start=5,
                        end=8,
                        replacement='is',
                        sentence='Here are another grammar error example.'
                    )   
                    db.session.add(new_grammar_error)
                    db.session.commit()

                resp = c.get('/get_more_errors', query_string={
                    'general_error_type': 'Grammar', 
                    'error_type': 'R:VERB:SVA',
                    'page': 2
                }, follow_redirects=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn('{\\n  "errors": [\\n    {\\n      "end": 8,\\n      "error_name": "Incorrect subject-verb agreement",\\n      "replacement": "is",\\n      "sentence": "Here are another grammar error example.",\\n      "start": 5\\n    },\\n    {\\n      "end": 8,\\n      "error_name": "Incorrect subject-verb agreement",\\n      "replacement": "is",\\n      "sentence": "Here are a grammar error example.",\\n      "start": 5\\n    }\\n  ],\\n  "has_more": false\\n}\\n', str(resp.data))
                

