from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, Length


class SignupForm(FlaskForm):

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])
    email = StringField('E-mail', validators=[DataRequired(), Email()])


class LoginForm(FlaskForm):

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])


# TODO ?????
class SubmitTextForm(FlaskForm):

    text = TextAreaField('Text', validators=[DataRequired()])
    



# Possible add functionaliry to edit profile later
# class EditProfileForm(FlaskForm):
#     """Form for editing profile if logged in"""
#     username = StringField('Username', validators=[DataRequired()])
#     email = StringField('E-mail', validators=[DataRequired(), Email()])
#     image_url = StringField('(Optional) Image URL')
#     header_image_url = StringField('(Optional) Header Image URL')
#     bio = StringField('(Optional) Bio')
#     password = PasswordField('Password', validators=[Length(min=6)])
