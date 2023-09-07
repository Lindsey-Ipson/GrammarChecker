# GrammarChecker

Deployed at https://capstone1-z7w1.onrender.com

## Summary

GrammarChecker is a web application that edits users’ writing and keeps track of the errors collected over time. It accepts texts up to 1400 characters in length, primary examples including emails, memos, thank you/sympathy/congratulations letters, invitations, short business documents, and more. Once writing is submitted, if any grammar or spelling errors are detected, an edited version of the text will be returned along with the types, locations, and replacement words/phrases for any errors found. Each time a text is submitted, all errors found are collected, organized, and stored. Grammar and Spelling Review pages allow users to see a comprehensive overview of their most common grammar and spelling errors respectively, as well as examples of where those errors were found in their previous texts.

While there already exist some powerful technologies to edit text, many of them fail to provide users with data about what types of errors are found and where. This application seeks to address this gap by not only editing users’ texts, but also providing them with both immediate and long-term comprehensive analyses of their common grammar/spelling errors. Ultimately, this allows users to have their texts edited in the short term, but also affords them the ability to improve their writing as time goes on.

## API

This application uses Sapling API (https://sapling.ai/docs/). This API accepts a body of text and returns JSON with an array of edit objects including attributes such as general error type, sentence, sentence start, error start, error end, replacement, and, if general error type is Grammar, a two-part code representing the specific grammar error type (i.e., “M:PREP” = “missing preposition”).

## Standard User Flow

Users may sign up with either a general user account which does not include any prepopulated data or a “tester” account which does prepopulate with text submissions and grammar/spelling errors. This allows “tester” users to explore the site as if it had a user history.

After signing up, the site’s main functionality can be accessed through the navigation bar. The “Submit text” tab allows users to submit text up to 1400 characters and have it edited and error-reviewed in the following page. The “Grammar” tab displays a bar chart of a user’s most common grammar error types and examples of where those error types were found in the user’s previous texts. Similarly, the “Spelling” tab displays a bar chart of a user’s most commonly misspelled words, along with examples of where those misspellings were found in previous texts. Clicking on any of the error examples in either the “Grammar” or “Spelling” tab displays that text submission’s full summary.

## Example Screenshots
### Review Grammar Errors
![Grammar Errors Screenshot](https://github.com/Lindsey-Ipson/Capstone1/blob/main/README%20Files/Grammar_Errors_Screenshot.png)
### Review Spelling Errors
![Spelling Errors Screenshot](https://github.com/Lindsey-Ipson/Capstone1/blob/main/README%20Files/Spelling_Errors_Screenshot.png)
### Review Text Submission
![Review Text Submission Screenshot](https://github.com/Lindsey-Ipson/Capstone1/blob/main/README%20Files/Text_Review_Screenshot.png)

## Schema
![Database Schema](https://github.com/Lindsey-Ipson/Capstone1/blob/main/README%20Files/Database_Schema_Diagram.png)

## Technology Used:

* Python
* Javascript 
* Matplotlib
* Flask
* SQLAlchemy
* WTForms
* Render
